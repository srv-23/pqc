"""
Enhanced Data Loader for Organized Dataset
===========================================
Loads data from the organized folder structure created by organize_dataset.py
Works with both training and test datasets
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
ORG_DIR = PROJECT_ROOT / "data" / "organized"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

DEVICE_MAP = {
    "device_1_danmini": "Danmini_Doorbell",
    "device_2_ecobee": "Ecobee_Thermostat",
    "device_3_ennio": "Ennio_Doorbell"
}

ATTACK_CLASSES = ["benign", "mirai", "bashlite"]


# ----------------------------
# DATA LOADING FUNCTIONS
# ----------------------------
def load_organized_data(data_source: str = "train") -> pd.DataFrame:
    """
    Load all organized CSV files and combine them.
    
    Args:
        data_source: "train" or "test"
    
    Returns:
        Combined DataFrame with all data
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Loading Organized {data_source.upper()} Data")
    logger.info(f"{'='*70}\n")
    
    if data_source == "train":
        return _load_training_data()
    elif data_source == "test":
        return _load_test_data()
    else:
        raise ValueError(f"data_source must be 'train' or 'test', got {data_source}")


def _load_training_data() -> pd.DataFrame:
    """Load training data from organized device folders"""
    dfs = []
    
    for device_dir, device_name in DEVICE_MAP.items():
        device_path = ORG_DIR / device_dir
        
        if not device_path.exists():
            logger.warning(f"Device path not found: {device_path}")
            continue
        
        logger.info(f"📱 Loading {device_name}...")
        device_dfs = []
        
        for attack_class in ATTACK_CLASSES:
            class_dir = device_path / attack_class
            
            if not class_dir.exists():
                continue
            
            class_dfs = []
            csv_files = list(class_dir.glob("*.csv"))
            
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    df['attack_type'] = attack_class
                    df['device'] = device_name
                    class_dfs.append(df)
                    logger.info(f"  ✓ {csv_file.name}: {len(df)} rows ({attack_class})")
                except Exception as e:
                    logger.error(f"  ✗ Error loading {csv_file.name}: {e}")
            
            if class_dfs:
                class_combined = pd.concat(class_dfs, ignore_index=True)
                device_dfs.append(class_combined)
                logger.info(f"    └─ {attack_class}: {len(class_combined)} total rows")
        
        if device_dfs:
            device_combined = pd.concat(device_dfs, ignore_index=True)
            dfs.append(device_combined)
            logger.info(f"  📊 Total for {device_name}: {len(device_combined)} rows\n")
    
    if not dfs:
        raise ValueError(f"No training data found in {ORG_DIR}")
    
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"{'='*70}")
    logger.info(f"Total Training Data: {len(combined)} rows")
    logger.info(f"{'='*70}\n")
    
    return combined


def _load_test_data() -> pd.DataFrame:
    """Load test data from test folder"""
    test_dir = ORG_DIR / "test"
    
    if not test_dir.exists():
        logger.warning(f"Test directory not found: {test_dir}")
        return pd.DataFrame()
    
    logger.info(f"Loading test data from {test_dir}...")
    
    dfs = []
    csv_files = list(test_dir.glob("*.csv"))
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
            logger.info(f"  ✓ {csv_file.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"  ✗ Error loading {csv_file.name}: {e}")
    
    if not dfs:
        raise ValueError(f"No test data found in {test_dir}")
    
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total Test Data: {len(combined)} rows\n")
    
    return combined


def analyze_data(df: pd.DataFrame, name: str = "Dataset"):
    """Analyze and display data statistics"""
    logger.info(f"\n📊 {name} Analysis:")
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    if 'attack_type' in df.columns:
        logger.info(f"\n  Attack Type Distribution:")
        for attack, count in df['attack_type'].value_counts().items():
            logger.info(f"    {attack}: {count} ({count/len(df)*100:.1f}%)")
    
    if 'device' in df.columns:
        logger.info(f"\n  Device Distribution:")
        for device, count in df['device'].value_counts().items():
            logger.info(f"    {device}: {count} ({count/len(df)*100:.1f}%)")
    
    logger.info(f"\n  Columns: {len(df.columns)}")
    logger.info(f"  Missing Values: {df.isnull().sum().sum()}")
    logger.info(f"  Data Types:\n{df.dtypes}\n")


def save_combined_data(df: pd.DataFrame, filename: str = "combined_organized_data.csv"):
    """Save combined data to CSV"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename
    
    df.to_csv(output_path, index=False)
    logger.info(f"✅ Saved to: {output_path}")
    logger.info(f"   File size: {output_path.stat().st_size / 1024**2:.2f} MB")


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    try:
        # Load training data
        train_df = load_organized_data("train")
        analyze_data(train_df, "Training Data")
        save_combined_data(train_df, "combined_training_data.csv")
        
        # Load test data
        test_df = load_organized_data("test")
        analyze_data(test_df, "Test Data")
        save_combined_data(test_df, "combined_test_data.csv")
        
        print("\n✅ Data loading complete!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise
