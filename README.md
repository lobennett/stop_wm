# stop_wm

> Codebase for stop_wm experiment hosted on Prolific.

## Complete the setup

1. Initialize a git repository with `git init`
2. Run `uv sync` to install the dependencies
3. Install pre-commit (if you haven’t already)

- `pip install pre-commit`

4. Run `pre-commit install` to install the pre-commit hooks

- pre-commit installed at `.git/hooks/pre-commit`

5. (Optional) Set up VS Code so that it lints/formats on save

- Create `.vscode/settings.json` to configure your workspace settings: `mkdir .vscode && touch .vscode/settings.json`
- Paste the following settings into `.vscode/settings.json`:

```json
{
  "notebook.formatOnSave.enabled": true,
  "notebook.formatOnCellExecution": true,
  "notebook.defaultFormatter": "charliermarsh.ruff",
  "notebook.codeActionsOnSave": {
    "notebook.source.fixAll": "explicit",
    "notebook.source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  }
}
```

## Data Analysis Pipeline

This repository provides a complete pipeline for analyzing experimental data from the stop+wm study. The pipeline consists of three main steps:

1. **Data Download** - Pull raw data from the Expfactory Deploy server
2. **Preprocessing** - Convert raw JSON data to CSV files
3. **Analysis** - Calculate task-specific metrics and export results

## Pipeline Usage

### Step 1: Data Download

Before running any analysis, you must download the raw data from the Expfactory Deploy server:

```bash
# Set up authentication key (contact logan or ross for real key)
cp ef_download.example ef_download

# Then download data from server
# Data will be downloaded to ./raw_data/
./download.sh
```

**Note**: The `ef_download.example` file contains a dummy SSH key. Ask Logan to give you the real key.

You could also set the key as an environment variable:
```bash
export EF_DOWNLOAD_KEY="$(cat path/to/real/ef_download)"
./download.sh
```

### Step 2: Preprocess Raw Data

Convert the downloaded JSON files to structured CSV format:

```bash
uv run preprocess
```

This command:
- Reads `raw_data/results_export/unified.csv` 
- Filters for study collection ID 68 (stop+wm study)
- Converts each participant's JSON data to CSV
- Saves preprocessed files to `data/preprocessed_data/[prolific_id]/[task_name]/`

### Step 3: Analyze Data

Calculate task-specific metrics and export results:

```bash
uv run analyze
```

This command:
- Processes all CSV files in `data/preprocessed_data/`
- Calculates metrics using task-specific analyzer classes 
- Saves results to separate CSV files in `data/analysis/`

## Data Organization

### Raw Data
- **Location**: `raw_data/results_export/`
- **Format**: JSON files with participant trial data
- **Key file**: `unified.csv` - master file of all participant sessions

### Preprocessed Data
- **Location**: `data/preprocessed_data/[prolific_id]/[task_name]/`
- **Format**: CSV files with structured trial data
- **Naming**: `sub-[prolific_id]_task-[task_name]_date-[datetime].csv`

### Analysis Results
- **Location**: `data/analysis/`
- **Files**:
  - `stop_signal_metrics.csv` - Stop signal task performance metrics
  - `stop_signal_wm_task_metrics.csv` - Working memory + stop signal metrics
  - `race_ethnicity_RMR_survey_rdoc_metrics.csv` - Demographic survey responses

## Analysis Classes

The analysis pipeline uses an object-oriented design with task-specific analyzers:

### Base Class
- **`TaskData`** - Abstract base class for all task analyzers
  - Takes CSV file path in constructor
  - Defines `preprocess()` and `analyze()` methods

### Task-Specific Analyzers
- **`StopSignalTask`** - Analyzes stop signal task performance
  - Metrics: Go trial RT, omission rate, stop accuracy, SSD parameters
- **`StopSignalWMTask`** - Analyzes working memory + stop signal task
  - Currently template implementation (TODO: add metrics)
- **`RaceEthnicityTask`** - Extracts demographic survey responses
  - Parses race, ethnicity, and other demographic data

### Shared Utilities
- `parse_survey_response()` - Parses JSON survey responses
- `calculate_accuracy()` - Computes accuracy
- `calculate_omission_rate()` - Computes omission rates