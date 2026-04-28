"""
N-BaIoT Dataset Loader and Data Cleaning Script
================================================
Loads CSV files from 3 IoT devices, merges them, handles missing values,
and saves a cleaned version with class distribution analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path("datasets")
DEVICES = {
    "Danmini_Doorbell": 1,
    "Ecobee_Thermostat": 2,
    "Ennio_Doorbell": 3
}
OUTPUT_FILE = "cleaned_nbaiot_combined.csv"


def load_device_files(device_id: int, device_name: str) -> pd.DataFrame:
    """
    Load all CSV files for a specific device.
    
    Args:
        device_id: Device ID (1, 2, or 3)
        device_name: Device name for logging
    
    Returns:
        Combined dataframe for the device
    """
    logger.info(f"Loading data for {device_name} (ID: {device_id})...")
    
    dfs = []
    
    # Load benign traffic
    benign_file = DATA_DIR / f"{device_id}.benign.csv"
    if benign_file.exists():
        try:
            df = pd.read_csv(benign_file)
            df['attack_type'] = 'benign'
            dfs.append(df)
            logger.info(f"  Loaded {benign_file.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"  Failed to load {benign_file.name}: {e}")
    
    # Load Mirai attack traffic
    mirai_files = sorted(DATA_DIR.glob(f"{device_id}.mirai*.csv"))
    for file in mirai_files:
        try:
            df = pd.read_csv(file)
            df['attack_type'] = 'mirai'
            dfs.append(df)
            logger.info(f"  Loaded {file.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"  Failed to load {file.name}: {e}")
    
    # Load BASHLITE (Gafgyt) attack traffic
    gafgyt_files = sorted(DATA_DIR.glob(f"{device_id}.gafgyt*.csv"))
    for file in gafgyt_files:
        try:
            df = pd.read_csv(file)
            df['attack_type'] = 'bashlite'
            dfs.append(df)
            logger.info(f"  Loaded {file.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"  Failed to load {file.name}: {e}")
    
    if not dfs:
        logger.warning(f"No CSV files found for {device_name}")
        return pd.DataFrame()
    
    # Combine all files for this device
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df['device'] = device_name
    
    logger.info(f"  Total for {device_name}: {len(combined_df)} rows\n")
    
    return combined_df


def merge_all_devices() -> pd.DataFrame:
    """
    Load and merge data from all 3 devices.
    
    Returns:
        Combined dataframe with data from all devices
    """
    logger.info("=" * 70)
    logger.info("LOADING N-BaIoT DATASET")
    logger.info("=" * 70 + "\n")
    
    all_dfs = []
    
    for device_name, device_id in DEVICES.items():
        df = load_device_files(device_id, device_name)
        if not df.empty:
            all_dfs.append(df)
    
    if not all_dfs:
        raise ValueError("No data loaded from any device")
    
    # Merge all devices
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    logger.info(f"Combined dataset shape: {combined_df.shape}")
    logger.info(f"Total rows: {len(combined_df):,}")
    logger.info(f"Total columns: {len(combined_df.columns)}\n")
    
    return combined_df


def print_class_distribution(df: pd.DataFrame, title: str = "Class Distribution"):
    """
    Print class distribution statistics.
    
    Args:
        df: Dataframe to analyze
        title: Title for the output
    """
    logger.info("=" * 70)
    logger.info(title)
    logger.info("=" * 70)
    
    attack_counts = df['attack_type'].value_counts()
    attack_percentages = (attack_counts / len(df) * 100).round(2)
    
    for attack_type in ['benign', 'mirai', 'bashlite']:
        if attack_type in attack_counts.index:
            count = attack_counts[attack_type]
            percentage = attack_percentages[attack_type]
            bar = "=" * int(percentage / 2)
            logger.info(f"{attack_type:10} | {count:8,} rows | {percentage:6.2f}% | {bar}")
    
    logger.info("=" * 70 + "\n")


def print_device_distribution(df: pd.DataFrame):
    """
    Print distribution by device.
    
    Args:
        df: Dataframe to analyze
    """
    logger.info("Distribution by Device:")
    logger.info("-" * 70)
    
    device_counts = df['device'].value_counts()
    
    for device_name in DEVICES.keys():
        if device_name in device_counts.index:
            count = device_counts[device_name]
            percentage = (count / len(df) * 100)
            logger.info(f"  {device_name:25} : {count:8,} rows ({percentage:6.2f}%)")
    
    logger.info("-" * 70 + "\n")


def handle_missing_values(df: pd.DataFrame) -> tuple:
    """
    Detect and handle missing values.
    
    Args:
        df: Input dataframe
    
    Returns:
        Tuple of (cleaned_df, missing_report)
    """
    logger.info("=" * 70)
    logger.info("HANDLING MISSING VALUES")
    logger.info("=" * 70)
    
    initial_rows = len(df)
    
    # Check for missing values
    missing_count = df.isnull().sum()
    missing_total = missing_count.sum()
    
    if missing_total == 0:
        logger.info("No missing values detected\n")
        return df, {}
    
    logger.info(f"Total missing values: {missing_total}")
    logger.info("\nColumns with missing values:")
    
    missing_report = {}
    for col in missing_count[missing_count > 0].index:
        count = missing_count[col]
        percentage = (count / len(df) * 100)
        logger.info(f"  {col:40} : {count:6,} ({percentage:6.2f}%)")
        missing_report[col] = {"count": count, "percentage": percentage}
    
    # Remove rows with missing values
    df_cleaned = df.dropna()
    removed_rows = initial_rows - len(df_cleaned)
    
    logger.info(f"\nRows removed: {removed_rows} ({removed_rows/initial_rows*100:.2f}%)")
    logger.info(f"Rows retained: {len(df_cleaned):,} ({len(df_cleaned)/initial_rows*100:.2f}%)\n")
    
    return df_cleaned, missing_report


def print_sample_data(df: pd.DataFrame, n_samples: int = 3):
    """
    Print sample rows from the dataset.
    
    Args:
        df: Dataframe to sample from
        n_samples: Number of samples per attack type
    """
    logger.info("=" * 70)
    logger.info("SAMPLE DATA")
    logger.info("=" * 70)
    
    for attack_type in ['benign', 'mirai', 'bashlite']:
        attack_df = df[df['attack_type'] == attack_type]
        if len(attack_df) > 0:
            logger.info(f"\n{attack_type.upper()} - Sample rows:")
            logger.info("-" * 70)
            
            # Show first row with basic info
            sample = attack_df.sample(n=min(n_samples, len(attack_df)), random_state=42)
            
            for idx, (_, row) in enumerate(sample.iterrows(), 1):
                logger.info(f"\nSample {idx}:")
                logger.info(f"  Device: {row['device']}")
                logger.info(f"  Attack Type: {row['attack_type']}")
                logger.info(f"  Features: {len([c for c in df.columns if c not in ['device', 'attack_type']])} network traffic features")
                
                # Show a few feature values
                feature_cols = [c for c in df.columns if c not in ['device', 'attack_type']]
                for feat in feature_cols[:3]:
                    value = row[feat]
                    logger.info(f"    {feat}: {value}")
                logger.info(f"    ... ({len(feature_cols)-3} more features)")
    
    logger.info("\n" + "=" * 70 + "\n")


def print_dataset_info(df: pd.DataFrame):
    """
    Print comprehensive dataset information.
    
    Args:
        df: Dataframe to analyze
    """
    logger.info("=" * 70)
    logger.info("DATASET INFORMATION")
    logger.info("=" * 70)
    
    logger.info(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info(f"\nColumn Information:")
    logger.info("-" * 70)
    
    # Show data types
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notna().sum()
        logger.info(f"  {col:40} : {dtype:10} ({non_null:,} non-null)")
    
    logger.info("-" * 70)
    logger.info(f"\nMemory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB\n")


def save_cleaned_data(df: pd.DataFrame, output_file: str) -> Path:
    """
    Save cleaned dataframe to CSV file.
    
    Args:
        df: Dataframe to save
        output_file: Output filename
    
    Returns:
        Path to saved file
    """
    logger.info("=" * 70)
    logger.info("SAVING CLEANED DATA")
    logger.info("=" * 70)
    
    output_path = Path(output_file)
    df.to_csv(output_path, index=False)
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Saved to: {output_path.absolute()}")
    logger.info(f"File size: {file_size_mb:.2f} MB\n")
    
    return output_path


def main():
    """Main execution function."""
    try:
        # Load and merge data
        df = merge_all_devices()
        
        # Print original class distribution
        print_class_distribution(df, "ORIGINAL CLASS DISTRIBUTION (All Devices)")
        
        # Print device distribution
        print_device_distribution(df)
        
        # Print dataset info
        print_dataset_info(df)
        
        # Print sample data
        print_sample_data(df, n_samples=2)
        
        # Handle missing values
        df_cleaned, missing_report = handle_missing_values(df)
        
        # Print cleaned class distribution
        print_class_distribution(df_cleaned, "CLEANED CLASS DISTRIBUTION")
        
        # Save cleaned data
        output_path = save_cleaned_data(df_cleaned, OUTPUT_FILE)
        
        # Final summary
        logger.info("=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Original dataset size: {len(df):,} rows")
        logger.info(f"Cleaned dataset size: {len(df_cleaned):,} rows")
        logger.info(f"Rows removed: {len(df) - len(df_cleaned):,}")
        logger.info(f"Data retention rate: {len(df_cleaned) / len(df) * 100:.2f}%")
        logger.info(f"Output file: {output_path.name}")
        logger.info("=" * 70)
        
        return df_cleaned
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    df_result = main()
    
    # Print final confirmation
    print("\n" + "=" * 70)
    print("DATASET READY FOR USE")
    print("=" * 70)
    print(f"Dataframe shape: {df_result.shape}")
    print(f"Columns: {list(df_result.columns)}")
    print("=" * 70)
