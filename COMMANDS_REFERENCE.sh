#!/bin/bash
# DATASET ORGANIZATION - QUICK COMMAND REFERENCE
# Copy-paste these commands to use the dataset scripts

# ============================================================================
# STEP 1: ORGANIZE RAW DATA (one time)
# ============================================================================
python scripts/organize_dataset.py
# Creates: data/organized/ folder structure
# Time: ~30 seconds
# Output: 28 training files + 2 test files organized by device/class


# ============================================================================
# STEP 2: GENERATE COMBINED DATA FILES
# ============================================================================
python src/data_pipeline/03_load_organized_data.py
# Creates: data/processed/combined_training_data.csv
#          data/processed/combined_test_data.csv
# Time: 2-3 minutes (depending on disk speed)
# Output: Ready-to-use CSV files with metadata


# ============================================================================
# STEP 3: TEST THE LOADER
# ============================================================================
python src/data_pipeline/04_quick_test_loader.py
# Verifies everything works
# Output: Sample data loaded successfully


# ============================================================================
# PYTHON CODE USAGE EXAMPLES
# ============================================================================

# Load full combined data
# ─────────────────────────────────────────────────────────────────────────
python -c "
import pandas as pd
df = pd.read_csv('data/processed/combined_training_data.csv')
print(f'Shape: {df.shape}')
print(f'Columns: {list(df.columns[:5])}...')
print(f'Devices: {df[\"device\"].unique()}')
print(f'Attack types: {df[\"attack_type\"].unique()}')
"

# Load quick sample (fast)
# ─────────────────────────────────────────────────────────────────────────
python -c "
from src.data_pipeline.quick_test_loader import load_sample
df = load_sample('device_1_danmini', n_rows=500)
print(f'Sample shape: {df.shape}')
print(f'Classes: {df[\"attack_type\"].value_counts()}')
"

# Load full device data
# ─────────────────────────────────────────────────────────────────────────
python -c "
from src.data_pipeline.quick_test_loader import load_device_data
df = load_device_data('device_1_danmini')
print(f'Device 1: {len(df)} rows')
print(f'Classes: {df[\"attack_type\"].value_counts()}')
"

# Load test data
# ─────────────────────────────────────────────────────────────────────────
python -c "
from src.data_pipeline.quick_test_loader import load_test_data
df = load_test_data()
print(f'Test data shape: {df.shape}')
"

# ============================================================================
# FEDERATED LEARNING SETUP
# ============================================================================

python -c "
from src.data_pipeline.quick_test_loader import load_device_data

devices = ['device_1_danmini', 'device_2_ecobee', 'device_3_ennio']
for i, device in enumerate(devices, 1):
    data = load_device_data(device)
    print(f'Node {i} ({device}): {len(data)} samples')
    # Train on data here
"


# ============================================================================
# VERIFY EVERYTHING WORKS
# ============================================================================

# Check organized folder exists
echo "Checking organized folder..."
ls -la data/organized/

# Check combined data files exist
echo "Checking processed folder..."
ls -lh data/processed/

# Count rows in combined data
python -c "
import pandas as pd
df = pd.read_csv('data/processed/combined_training_data.csv')
print(f'✓ Combined training data: {len(df):,} rows')
df = pd.read_csv('data/processed/combined_test_data.csv')
print(f'✓ Combined test data: {len(df):,} rows')
"


# ============================================================================
# HELPFUL ALIASES (Add to .bashrc or .zshrc)
# ============================================================================

# alias organize_dataset='python scripts/organize_dataset.py'
# alias load_dataset='python src/data_pipeline/03_load_organized_data.py'
# alias test_loader='python src/data_pipeline/04_quick_test_loader.py'


# ============================================================================
# DATA LOCATIONS
# ============================================================================

# Original data (unchanged)
# data/raw/train/      ← 28 CSV files
# data/raw/test/       ← 2 CSV files

# Organized structure (NEW)
# data/organized/device_1_danmini/
# data/organized/device_2_ecobee/
# data/organized/device_3_ennio/
# data/organized/test/

# Combined output (GENERATED)
# data/processed/combined_training_data.csv
# data/processed/combined_test_data.csv


# ============================================================================
# DOCUMENTATION FILES
# ============================================================================

# - README_DATASET_SETUP.md          (read this first!)
# - QUICK_REFERENCE.py              (code examples)
# - DATASET_WORKFLOW.md             (visual guide)
# - DATASET_ORGANIZATION_GUIDE.md   (detailed reference)
# - DATASET_SETUP_SUMMARY.md        (what was created)


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Issue: "No such file or directory"
# Fix: Run: python scripts/organize_dataset.py

# Issue: MemoryError loading large files
# Fix: Use load_sample() instead of load_device_data()

# Issue: slow loading
# Fix: Use load_sample() with n_rows parameter

# Issue: Need to re-generate combined data
# Fix: Delete data/processed/* then rerun load script


# ============================================================================
echo "✅ Ready to use! See documentation files for details."
# ============================================================================
