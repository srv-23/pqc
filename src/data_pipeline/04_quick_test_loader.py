"""
Quick Test Data Loader
======================
Simple utility for loading and testing with dataset samples
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up 3 levels to project root
ORG_DIR = PROJECT_ROOT / "data" / "organized"


def load_device_data(device_name: str, attack_class: str = None) -> pd.DataFrame:
    """
    Load data for a specific device, optionally filtered by attack class.
    
    Args:
        device_name: 'device_1_danmini', 'device_2_ecobee', or 'device_3_ennio'
        attack_class: 'benign', 'mirai', 'bashlite' (or None for all)
    
    Returns:
        DataFrame with the requested data
    
    Example:
        >>> df = load_device_data('device_1_danmini', 'benign')
        >>> print(df.shape)
    """
    device_path = ORG_DIR / device_name
    
    if not device_path.exists():
        raise ValueError(f"Device path not found: {device_path}")
    
    dfs = []
    
    if attack_class:
        # Load specific class
        class_path = device_path / attack_class
        if not class_path.exists():
            raise ValueError(f"Class path not found: {class_path}")
        
        for csv_file in class_path.glob("*.csv"):
            df = pd.read_csv(csv_file)
            df['attack_type'] = attack_class
            df['device'] = device_name
            dfs.append(df)
            print(f"  Loaded {csv_file.name}: {len(df)} rows")
    else:
        # Load all classes
        for class_name in ['benign', 'mirai', 'bashlite']:
            class_path = device_path / class_name
            if not class_path.exists():
                continue
            
            for csv_file in class_path.glob("*.csv"):
                df = pd.read_csv(csv_file)
                df['attack_type'] = class_name
                df['device'] = device_name
                dfs.append(df)
                print(f"  Loaded {csv_file.name}: {len(df)} rows ({class_name})")
    
    if not dfs:
        raise ValueError(f"No data found for {device_name}/{attack_class or 'all'}")
    
    return pd.concat(dfs, ignore_index=True)


def load_test_data() -> pd.DataFrame:
    """Load test data (UNSW_NB15)"""
    test_path = ORG_DIR / "test"
    
    if not test_path.exists():
        raise ValueError(f"Test path not found: {test_path}")
    
    dfs = []
    for csv_file in test_path.glob("*.csv"):
        df = pd.read_csv(csv_file)
        dfs.append(df)
        print(f"  Loaded {csv_file.name}: {len(df)} rows")
    
    if not dfs:
        raise ValueError("No test data found")
    
    return pd.concat(dfs, ignore_index=True)


def load_sample(device_name: str, attack_class: str = None, n_rows: int = 1000) -> pd.DataFrame:
    """Load a small sample of data for quick testing (loads from first N rows of each file)"""
    device_path = ORG_DIR / device_name
    
    if not device_path.exists():
        raise ValueError(f"Device path not found: {device_path}")
    
    dfs = []
    rows_per_file = max(100, n_rows // 5)  # Distribute across files
    
    if attack_class:
        class_path = device_path / attack_class
        for csv_file in class_path.glob("*.csv"):
            df = pd.read_csv(csv_file, nrows=rows_per_file)
            df['attack_type'] = attack_class
            df['device'] = device_name
            dfs.append(df)
    else:
        for class_name in ['benign', 'mirai', 'bashlite']:
            class_path = device_path / class_name
            if not class_path.exists():
                continue
            
            for csv_file in class_path.glob("*.csv"):
                df = pd.read_csv(csv_file, nrows=rows_per_file)
                df['attack_type'] = class_name
                df['device'] = device_name
                dfs.append(df)
    
    if not dfs:
        raise ValueError(f"No data found")
    
    result = pd.concat(dfs, ignore_index=True)
    return result.sample(min(n_rows, len(result)), random_state=42) if len(result) > n_rows else result


# ============================================================================
# EXAMPLE USAGE
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("DATASET LOADING EXAMPLES (USING SAMPLES FOR SPEED)")
    print("=" * 70)
    
    # Example 1: Load sample for device 1
    print("\n1️⃣  Load sample for Device 1 (Danmini) - 500 rows:")
    df1 = load_sample("device_1_danmini", n_rows=500)
    print(f"   Shape: {df1.shape}")
    print(f"   Attack types: {df1['attack_type'].unique()}")
    
    # Example 2: Load only benign data sample
    print("\n2️⃣  Load benign sample:")
    df_benign = load_sample("device_1_danmini", "benign", n_rows=100)
    print(f"   Shape: {df_benign.shape}")
    print(f"   Classes: {df_benign['attack_type'].unique()}")
    
    # Example 3: Load mirai data sample
    print("\n3️⃣  Load mirai sample:")
    df_mirai = load_sample("device_1_danmini", "mirai", n_rows=100)
    print(f"   Shape: {df_mirai.shape}")
    
    # Example 4: Compare samples from all devices
    print("\n4️⃣  Load samples from all devices (200 rows each):")
    devices = ["device_1_danmini", "device_2_ecobee", "device_3_ennio"]
    for device in devices:
        try:
            df = load_sample(device, n_rows=200)
            print(f"   {device}: {df.shape[0]} rows, {df['attack_type'].nunique()} classes")
        except Exception as e:
            print(f"   {device}: Error - {e}")
    
    # Example 5: Load test data
    print("\n5️⃣  Load test data:")
    try:
        df_test = load_test_data()
        print(f"   Shape: {df_test.shape}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 70)
    print("✅ All examples completed!")
    print("=" * 70)
    print("\n💡 TIPS:")
    print("   - Use load_sample() for quick testing with large files")
    print("   - Use load_device_data() to load all data (slower)")
    print("   - Use load_test_data() for UNSW_NB15 test dataset")
