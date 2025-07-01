"""
This script calculates the metrics for the stop+wm
experiment and logs the metrics to the console.
"""

import ast
import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from stop_wm.config import ANALYSIS_DIR, PREPROCESSED_DATA_DIR
from stop_wm.flags import FLAGS


class TaskData(ABC):
    """Abstract base class for task data analysis."""

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.data = pd.read_csv(csv_path)

    @abstractmethod
    def preprocess(self) -> pd.DataFrame:
        """Preprocess the raw data."""
        pass

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """Analyze the data and return metrics."""
        pass


class RaceEthnicityTask(TaskData):
    """Race/ethnicity survey task data."""

    def preprocess(self) -> pd.DataFrame:
        """Filter to survey trials only."""
        return self.data[self.data['trial_type'] == 'survey']

    def analyze(self) -> Dict[str, Any]:
        """Extract survey responses."""
        survey_df = self.preprocess()
        assert len(survey_df) == 1, f'Expected 1 survey row, got {len(survey_df)}'

        survey_row = survey_df.iloc[0]
        metrics = {}

        for field in ['race', 'race_other', 'latino']:
            response, key = parse_survey_response(survey_row[field])
            metrics[key] = response

        return metrics


class StopSignalTask(TaskData):
    """Stop signal task data."""

    def preprocess(self) -> pd.DataFrame:
        """Filter to test trials only."""
        return self.data[self.data['trial_id'] == 'test_trial']

    def analyze(self) -> Dict[str, Any]:
        """Calculate stop signal task metrics."""
        test_trials = self.preprocess()

        # Go trials analysis
        go_trials = test_trials[test_trials['condition'] == 'go']
        go_correct_trials = go_trials[go_trials['correct_trial'] == 1]
        go_omission_trials = go_trials[go_trials['rt'].isna()]

        # Stop trials analysis
        stop_trials = test_trials[test_trials['condition'] == 'stop']
        stop_correct_trials = stop_trials[stop_trials['correct_trial'] == 1]

        return {
            'go_accuracy': calculate_ratio(go_correct_trials, go_trials),
            'go_mean_rt': go_correct_trials['rt'].mean(),
            'go_omission_rate': calculate_ratio(go_omission_trials, go_trials),
            'stop_accuracy': calculate_ratio(stop_correct_trials, stop_trials),
            'stop_mean_rt': stop_trials['rt'].mean(),
            'min_SSD': test_trials['SSD'].min(),
            'max_SSD': test_trials['SSD'].max(),
            'mean_SSD': test_trials['SSD'].mean(),
            'final_SSD': test_trials['SSD'].iloc[-1] if len(test_trials) > 0 else None,
        }


class StopSignalWMTask(TaskData):
    """Stop signal working memory task data."""

    def preprocess(self) -> pd.DataFrame:
        """TODO: implement preprocessing if needed. Return data as-is for now."""
        return self.data

    def analyze(self) -> Dict[str, Any]:
        """Analyze stop signal + working memory task."""
        data = self.preprocess()

        # Extract different trial types
        # - I think these are all the different trial types...?
        memory_trials = data[data['trial_id'] == 'test_memory_trial']
        stop_trials = data[data['trial_id'] == 'test_stop_trial']
        recognition_trials = data[data['trial_id'] == 'test_memory_recognition']

        # TODO: Implement specific metrics for WM + stop signal task
        return {
            # TODO: Add metrics here.
        }


def create_task_analyzer(csv_path: Path, exp_id: str) -> TaskData:
    """Create mapping to correct task analyzer class."""
    task_classes = {
        'race_ethnicity_RMR_survey_rdoc': RaceEthnicityTask,
        'stop_signal': StopSignalTask,
        'stop_signal_wm_task': StopSignalWMTask,
    }

    if exp_id not in task_classes:
        raise ValueError(f'Unknown experiment ID: {exp_id}')

    return task_classes[exp_id](csv_path)


def parse_survey_response(value: str | None) -> tuple[str, str]:
    """Parse survey response from string format."""
    if value is None:
        raise ValueError('Survey response value is None')
    parsed_value = ast.literal_eval(value)
    return parsed_value['response'], parsed_value['key']


def calculate_ratio(numerator: pd.DataFrame, denominator: pd.DataFrame) -> float:
    """Calculate ratio as numerator/denominator."""
    # TODO: consider using a more robust way to calculate these values.
    return (
        numerator.shape[0] / denominator.shape[0] if denominator.shape[0] > 0 else 0.0
    )


def is_flagged(metrics_row: Dict[str, Any], task_name: str) -> bool:
    """Check if a metrics row should be flagged based on criteria."""
    if task_name not in FLAGS or FLAGS[task_name] is None:
        return False

    criteria = FLAGS[task_name]

    for metric_name, limits in criteria.items():
        if metric_name not in metrics_row:
            continue

        value = metrics_row[metric_name]
        if value is None or pd.isna(value):
            continue

        # Check minimum threshold
        if 'min' in limits and value < limits['min']:
            return True

        # Check maximum threshold
        if 'max' in limits and value > limits['max']:
            return True

        # Check range (both min and max)
        if 'min' in limits and 'max' in limits:
            if not (limits['min'] <= value <= limits['max']):
                return True

    return False


def main() -> None:
    """Main function to analyze preprocessed data."""

    logging.basicConfig(level=logging.INFO)
    logging.info('Calculating metrics...')

    # Collect metrics by task type
    metrics_by_task, flagged_by_task = {}, {}

    # Load the preprocessed data
    for subject_dir in PREPROCESSED_DATA_DIR.iterdir():
        if not subject_dir.is_dir():
            logging.warning(f'Skipping non-directory: {subject_dir}')
            continue

        for task_dir in subject_dir.iterdir():
            if not task_dir.is_dir():
                logging.warning(f'Skipping non-directory: {task_dir}')
                continue

            csv_files = list(task_dir.glob('*.csv'))

            if len(csv_files) != 1:
                logging.warning(f'Found {len(csv_files)} CSV files in {task_dir}')
                continue

            datafile = csv_files[0]
            try:
                task_analyzer = create_task_analyzer(datafile, task_dir.name)
                metrics = task_analyzer.analyze()

                # Add subject info to metrics
                metrics_row = {'prolific_id': subject_dir.name, **metrics}

                # Group by task name
                task_name = task_dir.name
                if task_name not in metrics_by_task:
                    metrics_by_task[task_name] = []
                    flagged_by_task[task_name] = []

                metrics_by_task[task_name].append(metrics_row)

                # Check if row should be flagged
                if is_flagged(metrics_row, task_name):
                    flagged_by_task[task_name].append(metrics_row)

            except ValueError as ve:
                logging.warning(f'Skipping unknown task {task_dir.name}: {ve}')
            except Exception as ex:
                logging.error(
                    f'Error analyzing {subject_dir.name}/{task_dir.name}: {ex}'
                )

    # Save metrics to separate CSV files by task
    if metrics_by_task:
        for task_name, task_metrics in metrics_by_task.items():
            # Save all metrics
            metrics_df = pd.DataFrame(task_metrics)
            output_path = ANALYSIS_DIR / f'{task_name}_metrics.csv'
            metrics_df.to_csv(output_path, index=False)
            logging.info(
                f'Saved {len(task_metrics)} {task_name} metrics to {output_path}'
            )

            # Save flagged metrics if any exist
            if flagged_by_task[task_name]:
                flagged_df = pd.DataFrame(flagged_by_task[task_name])
                flagged_path = ANALYSIS_DIR / f'{task_name}_metrics__flagged.csv'
                flagged_df.to_csv(flagged_path, index=False)
                logging.info(
                    f'Saved {len(flagged_by_task[task_name])} flagged {task_name} '
                    f'metrics to {flagged_path}'
                )
    else:
        logging.warning('No metrics collected')

    logging.info('Done!')
    sys.exit(0)


if __name__ == '__main__':
    main()
