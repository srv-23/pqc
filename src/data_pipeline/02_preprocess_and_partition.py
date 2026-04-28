"""
N-BaIoT Dataset Preprocessing and Partitioning
===============================================
Preprocessing pipeline for federated learning:
- Feature scaling (MinMaxScaler)
- Label encoding
- Feature variance filtering
- Dataset partitioning into 3 nodes (simulating IoT devices)
- Train-test splitting per node
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from pathlib import Path
import logging
from typing import Tuple, Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
INPUT_FILE = "cleaned_nbaiot_combined.csv"
OUTPUT_DIR = Path("dataset") / "partitioned"
VARIANCE_THRESHOLD = 0.01
TRAIN_TEST_SPLIT = 0.8  # 80% train, 20% test
NUM_NODES = 3
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


def create_output_directories():
    """Create output directories for node partitions."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for node_id in range(1, NUM_NODES + 1):
        node_dir = OUTPUT_DIR / f"node{node_id}"
        node_dir.mkdir(exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR.absolute()}")


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load cleaned N-BaIoT dataset.
    
    Args:
        file_path: Path to input CSV
    
    Returns:
        Loaded dataframe
    """
    logger.info(f"Loading dataset from {file_path}...")
    
    df = pd.read_csv(file_path)
    logger.info(f"Dataset loaded: {df.shape[0]:,} rows × {df.shape[1]} columns\n")
    
    return df


def print_dataset_info(df: pd.DataFrame):
    """Print dataset information."""
    logger.info("="*80)
    logger.info("ORIGINAL DATASET INFORMATION")
    logger.info("="*80)
    logger.info(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info(f"Data types:\n{df.dtypes.value_counts()}")
    logger.info(f"\nClass distribution:")
    
    class_counts = df['attack_type'].value_counts()
    for attack_type, count in class_counts.items():
        pct = (count / len(df) * 100)
        logger.info(f"  {attack_type:20} : {count:10,} ({pct:6.2f}%)")


def encode_labels(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Encode attack type labels as integers.
    
    Args:
        df: Input dataframe
    
    Returns:
        Tuple of (encoded_df, label_mapping)
    """
    logger.info("\n" + "="*80)
    logger.info("LABEL ENCODING")
    logger.info("="*80)
    
    df_encoded = df.copy()
    
    # Create label encoder
    le = LabelEncoder()
    df_encoded['attack_type_encoded'] = le.fit_transform(df['attack_type'])
    
    # Create mapping dictionary
    label_mapping = dict(zip(le.classes_, le.transform(le.classes_)))
    
    logger.info("Label mapping:")
    for label, code in sorted(label_mapping.items(), key=lambda x: x[1]):
        logger.info(f"  {label:20} → {code}")
    
    # Drop original label column
    df_encoded = df_encoded.drop('attack_type', axis=1)
    df_encoded = df_encoded.rename(columns={'attack_type_encoded': 'label'})
    
    logger.info(f"\nEncoded label distribution:")
    for label_code in sorted(df_encoded['label'].unique()):
        original_label = [k for k, v in label_mapping.items() if v == label_code][0]
        count = (df_encoded['label'] == label_code).sum()
        logger.info(f"  {original_label:20} (code {label_code}) : {count:10,}")
    
    return df_encoded, label_mapping


def select_numeric_features(df: pd.DataFrame) -> List[str]:
    """Get all numeric feature columns."""
    exclude_cols = {'label', 'device'}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    return [col for col in numeric_cols if col not in exclude_cols]


def filter_low_variance_features(df: pd.DataFrame, threshold: float = 0.01) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove features with variance below threshold.
    
    Args:
        df: Input dataframe
        threshold: Minimum variance threshold
    
    Returns:
        Tuple of (filtered_df, removed_features)
    """
    logger.info("\n" + "="*80)
    logger.info("FEATURE VARIANCE FILTERING")
    logger.info("="*80)
    
    numeric_features = select_numeric_features(df)
    feature_variances = df[numeric_features].var()
    
    logger.info(f"Total numeric features: {len(numeric_features)}")
    logger.info(f"Variance threshold: {threshold}")
    
    # Identify low-variance features
    low_var_features = feature_variances[feature_variances < threshold].index.tolist()
    
    logger.info(f"Features with variance < {threshold}: {len(low_var_features)}")
    
    if low_var_features:
        logger.info("\nLow-variance features (removed):")
        for feat in sorted(low_var_features):
            var = feature_variances[feat]
            logger.info(f"  {feat:40} : variance = {var:.8f}")
    
    # Remove low-variance features
    df_filtered = df.drop(columns=low_var_features)
    
    remaining_features = len(numeric_features) - len(low_var_features)
    logger.info(f"\nFeatures after filtering: {remaining_features}")
    logger.info(f"Shape after filtering: {df_filtered.shape}")
    
    return df_filtered, low_var_features


def scale_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, MinMaxScaler]:
    """
    Scale numeric features using MinMaxScaler (0-1 range).
    
    Args:
        df: Input dataframe
    
    Returns:
        Tuple of (scaled_df, scaler)
    """
    logger.info("\n" + "="*80)
    logger.info("FEATURE SCALING (MinMaxScaler)")
    logger.info("="*80)
    
    df_scaled = df.copy()
    
    # Get numeric features (excluding label and device)
    numeric_features = select_numeric_features(df)
    
    logger.info(f"Features to scale: {len(numeric_features)}")
    
    # Apply MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1))
    df_scaled[numeric_features] = scaler.fit_transform(df[numeric_features])
    
    # Print scaling statistics
    logger.info("\nScaling statistics (sample features):")
    logger.info(f"{'Feature':40} {'Min':12} {'Max':12} {'Mean':12} {'Std':12}")
    logger.info("-"*80)
    
    for feat in numeric_features[:5]:
        min_val = df_scaled[feat].min()
        max_val = df_scaled[feat].max()
        mean_val = df_scaled[feat].mean()
        std_val = df_scaled[feat].std()
        logger.info(f"{feat:40} {min_val:12.6f} {max_val:12.6f} {mean_val:12.6f} {std_val:12.6f}")
    
    logger.info("  ... (and {} more features)".format(len(numeric_features) - 5))
    
    return df_scaled, scaler


def partition_data(df: pd.DataFrame, num_partitions: int = 3) -> List[pd.DataFrame]:
    """
    Partition dataset into equal non-overlapping partitions.
    
    Args:
        df: Input dataframe
        num_partitions: Number of partitions
    
    Returns:
        List of partition dataframes
    """
    logger.info("\n" + "="*80)
    logger.info(f"DATA PARTITIONING ({num_partitions} nodes)")
    logger.info("="*80)
    
    # Shuffle data before partitioning to ensure randomness
    df_shuffled = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    
    partition_size = len(df_shuffled) // num_partitions
    partitions = []
    
    logger.info(f"Total samples: {len(df_shuffled):,}")
    logger.info(f"Partition size: {partition_size:,} samples per node\n")
    
    for i in range(num_partitions):
        start_idx = i * partition_size
        if i == num_partitions - 1:
            # Last partition gets remaining rows
            end_idx = len(df_shuffled)
        else:
            end_idx = (i + 1) * partition_size
        
        partition = df_shuffled.iloc[start_idx:end_idx].reset_index(drop=True)
        partitions.append(partition)
        
        logger.info(f"Node {i+1}: samples {start_idx:,} to {end_idx:,} ({len(partition):,} rows)")
    
    return partitions


def split_train_test(df: pd.DataFrame, test_size: float = 0.2, 
                     random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split partition into train and test sets with stratification.
    
    Args:
        df: Input partition dataframe
        test_size: Proportion of test data
        random_state: Random seed for reproducibility
    
    Returns:
        Tuple of (train_df, test_df)
    """
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df['label']  # Stratify by label to maintain class distribution
    )
    
    return train_df, test_df


def print_partition_stats(partitions: List[pd.DataFrame], label_mapping: dict):
    """
    Print statistics for each partition.
    
    Args:
        partitions: List of partition dataframes
        label_mapping: Label encoding mapping
    """
    logger.info("\n" + "="*80)
    logger.info("PARTITION STATISTICS")
    logger.info("="*80)
    
    for node_id, partition in enumerate(partitions, 1):
        logger.info(f"\nNode {node_id}:")
        logger.info("-"*80)
        logger.info(f"Total samples: {len(partition):,}")
        logger.info(f"Features: {len(partition.columns) - 1}")  # Exclude label
        logger.info(f"\nClass distribution:")
        
        class_counts = partition['label'].value_counts().sort_index()
        for label_code, count in class_counts.items():
            original_label = [k for k, v in label_mapping.items() if v == label_code][0]
            pct = (count / len(partition) * 100)
            bar = "=" * int(pct / 2)
            logger.info(f"  {original_label:20} : {count:8,} ({pct:6.2f}%) {bar}")


def save_partition_splits(partitions: List[pd.DataFrame], label_mapping: dict):
    """
    Save train-test splits for each partition.
    
    Args:
        partitions: List of partition dataframes
        label_mapping: Label encoding mapping
    """
    logger.info("\n" + "="*80)
    logger.info("SAVING PARTITIONS")
    logger.info("="*80)
    
    for node_id, partition in enumerate(partitions, 1):
        # Split into train and test
        train_df, test_df = split_train_test(partition, test_size=0.2, 
                                             random_state=RANDOM_SEED + node_id)
        
        # Save train set
        train_path = OUTPUT_DIR / f"node{node_id}" / f"node{node_id}_train.csv"
        train_df.to_csv(train_path, index=False)
        
        # Save test set
        test_path = OUTPUT_DIR / f"node{node_id}" / f"node{node_id}_test.csv"
        test_df.to_csv(test_path, index=False)
        
        logger.info(f"\nNode {node_id}:")
        logger.info(f"  Train samples: {len(train_df):,} ({len(train_df)/len(partition)*100:.1f}%)")
        logger.info(f"  Test samples: {len(test_df):,} ({len(test_df)/len(partition)*100:.1f}%)")
        logger.info(f"  Saved: {train_path.name}, {test_path.name}")
        
        # Print train-test distribution
        logger.info(f"\n  Train set class distribution:")
        train_counts = train_df['label'].value_counts().sort_index()
        for label_code, count in train_counts.items():
            original_label = [k for k, v in label_mapping.items() if v == label_code][0]
            pct = (count / len(train_df) * 100)
            logger.info(f"    {original_label:18} : {count:7,} ({pct:5.2f}%)")
        
        logger.info(f"\n  Test set class distribution:")
        test_counts = test_df['label'].value_counts().sort_index()
        for label_code, count in test_counts.items():
            original_label = [k for k, v in label_mapping.items() if v == label_code][0]
            pct = (count / len(test_df) * 100)
            logger.info(f"    {original_label:18} : {count:7,} ({pct:5.2f}%)")


def create_metadata_file(partitions: List[pd.DataFrame], label_mapping: dict, 
                        removed_features: List[str]):
    """
    Create metadata file with preprocessing information.
    
    Args:
        partitions: List of partition dataframes
        label_mapping: Label encoding mapping
        removed_features: Features that were removed
    """
    logger.info("\n" + "="*80)
    logger.info("CREATING METADATA")
    logger.info("="*80)
    
    metadata = {
        'preprocessing_info': {
            'input_file': INPUT_FILE,
            'variance_threshold': VARIANCE_THRESHOLD,
            'scaling_method': 'MinMaxScaler (0-1)',
            'train_test_split': f"{int(TRAIN_TEST_SPLIT*100)}/{int((1-TRAIN_TEST_SPLIT)*100)}",
            'num_nodes': NUM_NODES,
            'random_seed': RANDOM_SEED
        },
        'label_mapping': label_mapping,
        'removed_features': removed_features,
        'partition_info': {}
    }
    
    # Add partition info
    for node_id, partition in enumerate(partitions, 1):
        total_samples = int(len(partition))
        train_samples = int(total_samples * TRAIN_TEST_SPLIT)
        test_samples = int(total_samples - train_samples)
        num_features = int(len(partition.columns) - 1)
        
        metadata['partition_info'][f'node{node_id}'] = {
            'total_samples': total_samples,
            'train_samples': train_samples,
            'test_samples': test_samples,
            'features': num_features
        }
    
    # Convert all numpy types to Python native types for JSON serialization
    def convert_to_native(obj):
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        else:
            return obj
    
    metadata = convert_to_native(metadata)
    
    # Save metadata
    import json
    metadata_path = OUTPUT_DIR / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved: {metadata_path.name}")


def main():
    """Main preprocessing pipeline."""
    try:
        # Step 1: Create output directories
        create_output_directories()
        
        # Step 2: Load data
        df = load_data(INPUT_FILE)
        print_dataset_info(df)
        
        # Step 3: Encode labels
        df_encoded, label_mapping = encode_labels(df)
        
        # Step 4: Filter low-variance features
        df_filtered, removed_features = filter_low_variance_features(
            df_encoded, threshold=VARIANCE_THRESHOLD
        )
        
        # Step 5: Scale features
        df_scaled, scaler = scale_features(df_filtered)
        
        # Step 6: Partition data
        partitions = partition_data(df_scaled, num_partitions=NUM_NODES)
        
        # Step 7: Print partition statistics
        print_partition_stats(partitions, label_mapping)
        
        # Step 8: Save partitions with train-test splits
        save_partition_splits(partitions, label_mapping)
        
        # Step 9: Create metadata file
        create_metadata_file(partitions, label_mapping, removed_features)
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("PREPROCESSING COMPLETE")
        logger.info("="*80)
        logger.info(f"Output directory: {OUTPUT_DIR.absolute()}\n")
        logger.info("Generated files:")
        for node_id in range(1, NUM_NODES + 1):
            logger.info(f"  - node{node_id}/node{node_id}_train.csv")
            logger.info(f"  - node{node_id}/node{node_id}_test.csv")
        logger.info("  - metadata.json")
        logger.info("\n[SUCCESS] Preprocessing completed successfully!")
        logger.info("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"[ERROR] {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
