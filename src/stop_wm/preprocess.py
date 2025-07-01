"""
Preprocess the raw data downloaded from expfactory
server. This script takes in the unified.csv file
exported from the expfactory server, converts the
raw JSON data to a pandas dataframe, and saves the
preprocessed data to a CSV file.
"""

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from stop_wm.config import PREPROCESSED_DATA_DIR, RAW_DATA_DIR
from stop_wm.utils import load_json


@dataclass
class ServerExperimentalData:
    """Represents experimental data for a single participant session."""

    subject: str
    battery_id: int
    study_collection_id: int
    fname: str
    exp_name: str
    date_time: Optional[str] = None
    prolific_id: Optional[str] = None
    trialdata: Optional[pd.DataFrame] = None

    @classmethod
    def from_row(cls, row: pd.Series, data_dir: Path) -> 'ServerExperimentalData':
        """Create ServerExperimentalData instance from a unified.csv row."""
        fname_path = data_dir / 'results_export' / row['fname']
        data = load_json(fname_path)

        trialdata_raw = data.get('trialdata')
        if isinstance(trialdata_raw, str):
            trialdata_raw = json.loads(trialdata_raw)

        trialdata = pd.DataFrame(trialdata_raw) if trialdata_raw else None

        return cls(
            subject=row['subject'],
            battery_id=row['battery_id'],
            study_collection_id=row['study_collection_id'],
            fname=row['fname'],
            exp_name=row['exp_name'],
            date_time=data.get('dateTime'),
            prolific_id=data.get('prolific_id'),
            trialdata=trialdata,
        )

    def get_output_path(self, base_dir: Path) -> Path:
        """Generate the output path for this experimental data."""
        outdir = base_dir / self.prolific_id / self.exp_name
        outdir.mkdir(parents=True, exist_ok=True)
        return (
            outdir
            / f'sub-{self.prolific_id}_task-{self.exp_name}_date-{self.date_time}.csv'
        )

    def save(self, base_dir: Path) -> None:
        """Save the experimental data to CSV."""
        if self.trialdata is None or self.trialdata.empty:
            logging.warning(f'No trial data for {self.fname}')
            return

        output_path = self.get_output_path(base_dir)
        self.trialdata.to_csv(output_path, index=False)
        logging.info(f'Saved preprocessed data to {output_path}')


def create_unified_df(study_collection_id: int) -> pd.DataFrame:
    """Use unified.csv to create a dataframe with only
    the data relevant to the target study collection.

    Args:
        study_collection_id (int): The study collection ID to filter for.

    Returns:
        pd.DataFrame: A dataframe with only the data relevant to the
        target study collection.
    """
    unified_df = RAW_DATA_DIR / 'results_export' / 'unified.csv'
    if not unified_df.exists():
        raise FileNotFoundError(f'Unified CSV file not found at {unified_df}')

    df = pd.read_csv(unified_df)

    # Filter for the target study collection
    return df[df['study_collection_id'] == study_collection_id]


def main() -> None:
    """Main function to preprocess the raw data."""
    logging.basicConfig(level=logging.INFO)
    logging.info('Fetching data from server and converting to dataframe...')

    # NOTE: USE study_collection_id=68 AS THAT IS THE STOP+WM
    # STUDY COLLECTION ID - https://deploy.expfactory.org/prolific/remote/studies/68
    # The last param of the URL is the study collection id.
    df = create_unified_df(study_collection_id=68)

    for _, row in df.iterrows():
        try:
            exp_data = ServerExperimentalData.from_row(row, RAW_DATA_DIR)
            exp_data.save(PREPROCESSED_DATA_DIR)
        except Exception as e:
            logging.error(f'Error processing {row["fname"]}: {e}')
            continue

    logging.info('Done!')
    sys.exit(0)


if __name__ == '__main__':
    main()
