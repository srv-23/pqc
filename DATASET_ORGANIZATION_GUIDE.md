# Dataset Organization Guide

## Overview
Your dataset has been reorganized into a structured format that makes it easy to work with different devices and attack types. This guide explains the new structure and how to use the preprocessing scripts.

## New Directory Structure

```
data/
├── raw/                          # Original files (unchanged)
│   ├── train/                    # Training data
│   │   ├── 1.benign.csv
│   │   ├── 1.mirai.*.csv
│   │   ├── 1.gafgyt.*.csv
│   │   ├── 2.benign.csv
│   │   └── ... (Device 2 & 3 files)
│   │
│   └── test/                     # Test data
│       ├── UNSW_NB15_testing-set.csv
│       └── UNSW_NB15_training-set.csv
│
├── organized/                    # ✅ NEW - Organized structure
│   ├── device_1_danmini/
│   │   ├── benign/              (1 file, 49,548 rows)
│   │   ├── mirai/               (5 files, 652,100 rows)
│   │   └── bashlite/            (5 files, 316,650 rows)
│   │
│   ├── device_2_ecobee/
│   │   ├── benign/              (1 file, 13,113 rows)
│   │   ├── mirai/               (5 files, 512,133 rows)
│   │   └── bashlite/            (5 files, 310,630 rows)
│   │
│   ├── device_3_ennio/
│   │   ├── benign/              (1 file, x rows)
│   │   ├── mirai/               (no files in training set)
│   │   └── bashlite/            (5 files, x rows)
│   │
│   └── test/                     (2 files - UNSW_NB15 dataset)
│
└── processed/                    # Output from preprocessing scripts
    └── (generated after running preprocessing)
```

## Device Mapping

| Device ID | Device Name     | Description    |
|-----------|-----------------|----------------|
| 1         | Danmini_Doorbell | Smart Doorbell |
| 2         | Ecobee_Thermostat | Smart Thermostat |
| 3         | Ennio_Doorbell  | Smart Video Doorbell |

## Attack Classes

- **benign**: Normal, non-attack traffic
- **mirai**: Mirai botnet attack traffic
- **bashlite**: Bashlite/Gafgyt attack traffic

## Scripts

### 1. **organize_dataset.py** - Dataset Organization
Organizes raw CSV files into the structured folder hierarchy.

```bash
python scripts/organize_dataset.py
```

**What it does:**
- Creates folders: `device_*/benign/`, `device_*/mirai/`, `device_*/bashlite/`
- Copies (not moves) files from `raw/train/` to organized structure
- Handles test files separately in `organized/test/`
- Prints a summary of the organized structure

**Output:**
```
✓ Organized 28 training files
✓ Organized 2 test files
✓ Structure created at: data/organized
```

### 2. **03_load_organized_data.py** - Data Loader
Loads and combines data from the organized structure.

```bash
python src/data_pipeline/03_load_organized_data.py
```

**What it does:**
- Loads all CSV files from `organized/` structure
- Adds metadata columns: `attack_type`, `device`
- Combines data from all devices/classes
- Generates statistics and analysis
- Saves combined datasets to `processed/`

**Output Files:**
- `combined_training_data.csv` - All training data combined
- `combined_test_data.csv` - All test data combined

**Features:**
- Progress logging for each file
- Data statistics (row counts, distributions)
- Memory usage reporting
- Error handling and validation

## Quick Start

### Step 1: Organize Your Data
```bash
python scripts/organize_dataset.py
```

### Step 2: Load and Analyze
```bash
python src/data_pipeline/03_load_organized_data.py
```

### Step 3: Use Combined Data
The combined CSV files are now ready for:
- Feature engineering
- Model training
- Data analysis
- Federated learning setup

## Example Usage in Your Code

```python
import pandas as pd

# Load combined training data
df = pd.read_csv('data/processed/combined_training_data.csv')

# Filter by device
danmini_data = df[df['device'] == 'Danmini_Doorbell']

# Filter by attack type
benign_data = df[df['attack_type'] == 'benign']

# Combine filters
danmini_mirai = df[(df['device'] == 'Danmini_Doorbell') & 
                   (df['attack_type'] == 'mirai')]

print(f"Shape: {df.shape}")
print(f"Devices: {df['device'].unique()}")
print(f"Attack Types: {df['attack_type'].unique()}")
```

## Testing with Test Dataset

The test dataset (UNSW_NB15) is automatically organized and available:

```python
# Load test data
test_df = pd.read_csv('data/processed/combined_test_data.csv')
```

## Notes

- Raw files are **copied**, not moved (originals remain in `data/raw/`)
- All scripts use absolute paths from project root
- Logging is enabled for debugging
- File processing shows real-time progress
- Memory usage tracked during data loading

## Troubleshooting

**No files organized?**
- Check that `data/raw/train/` contains CSV files
- Verify filenames follow pattern: `{device_id}.{class_type}.csv`

**Missing device folders?**
- Device 3 has no Mirai files - this is expected
- Bashlite files are derived from gafgyt files

**Large file loading is slow?**
- This is normal - datasets are large
- Consider sampling if memory is limited

## Integration with Existing Code

Your existing preprocessing pipeline can now work with the organized data:

```python
# Old way (single combined file)
df = pd.read_csv('cleaned_nbaiot_combined.csv')

# New way (organized structure)
from src.data_pipeline.load_organized_data import load_organized_data
df = load_organized_data('train')  # Returns combined DataFrame
```

---

**Last Updated:** 2026-04-28  
**Scripts Version:** 1.0
