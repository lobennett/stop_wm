"""
Configuration file for data paths and settings.
"""

from pathlib import Path

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data directory paths
RAW_DATA_DIR = PROJECT_ROOT / 'raw_data'
PREPROCESSED_DATA_DIR = PROJECT_ROOT / 'data' / 'preprocessed_data'
ANALYSIS_DIR = PROJECT_ROOT / 'data' / 'analysis'

# Ensure directories exist
RAW_DATA_DIR.mkdir(exist_ok=True)
PREPROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration dictionary for easy access
PATHS = {
    'project_root': PROJECT_ROOT,
    'raw_data_dir': RAW_DATA_DIR,
    'preprocessed_data_dir': PREPROCESSED_DATA_DIR,
    'analysis_dir': ANALYSIS_DIR,
}
