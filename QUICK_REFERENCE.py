"""
QUICK REFERENCE: How to Use the Dataset Scripts
================================================

Copy-paste ready examples for loading and working with your organized dataset.
"""

# ============================================================================
# BASIC LOADING
# ============================================================================

# Example 1: Load all combined training data
import pandas as pd

df_train = pd.read_csv('data/processed/combined_training_data.csv')
df_test = pd.read_csv('data/processed/combined_test_data.csv')

print(f"Training shape: {df_train.shape}")
print(f"Test shape: {df_test.shape}")


# ============================================================================
# FILTERING BY DEVICE
# ============================================================================

# Example 2: Get data for specific device
danmini = df_train[df_train['device'] == 'Danmini_Doorbell']
ecobee = df_train[df_train['device'] == 'Ecobee_Thermostat']
ennio = df_train[df_train['device'] == 'Ennio_Doorbell']

print(f"Danmini rows: {len(danmini)}")
print(f"Ecobee rows: {len(ecobee)}")
print(f"Ennio rows: {len(ennio)}")


# ============================================================================
# FILTERING BY ATTACK TYPE
# ============================================================================

# Example 3: Get data for specific attack class
benign = df_train[df_train['attack_type'] == 'benign']
mirai = df_train[df_train['attack_type'] == 'mirai']
bashlite = df_train[df_train['attack_type'] == 'bashlite']

print(f"Benign rows: {len(benign)}")
print(f"Mirai rows: {len(mirai)}")
print(f"Bashlite rows: {len(bashlite)}")


# ============================================================================
# COMBINED FILTERING (DEVICE + ATTACK TYPE)
# ============================================================================

# Example 4: Get specific device + attack combination
danmini_mirai = df_train[(df_train['device'] == 'Danmini_Doorbell') & 
                         (df_train['attack_type'] == 'mirai')]

ecobee_benign = df_train[(df_train['device'] == 'Ecobee_Thermostat') & 
                         (df_train['attack_type'] == 'benign')]

print(f"Danmini Mirai: {len(danmini_mirai)} rows")
print(f"Ecobee Benign: {len(ecobee_benign)} rows")


# ============================================================================
# QUICK TESTING WITH SAMPLES
# ============================================================================

# Example 5: Load samples for fast testing
from src.data_pipeline.quick_test_loader import load_sample, load_device_data

# Quick sample (only loads first N rows from each file)
sample = load_sample('device_1_danmini', n_rows=500)
print(f"Sample shape: {sample.shape}")

# Sample from specific attack class
mirai_sample = load_sample('device_1_danmini', attack_class='mirai', n_rows=200)
print(f"Mirai sample: {len(mirai_sample)} rows")


# ============================================================================
# LOADING FULL DEVICE DATA
# ============================================================================

# Example 6: Load all data for a device (slower, more memory)
from src.data_pipeline.quick_test_loader import load_device_data

device1_all = load_device_data('device_1_danmini')
device2_all = load_device_data('device_2_ecobee')
device3_all = load_device_data('device_3_ennio')

print(f"Device 1: {len(device1_all)} rows")
print(f"Device 2: {len(device2_all)} rows")
print(f"Device 3: {len(device3_all)} rows")


# ============================================================================
# FEDERATED LEARNING SETUP
# ============================================================================

# Example 7: Prepare data for federated learning (one device per node)
from src.data_pipeline.quick_test_loader import load_device_data

devices = ['device_1_danmini', 'device_2_ecobee', 'device_3_ennio']
node_data = {}

for i, device in enumerate(devices, start=1):
    node_data[f'node{i}'] = load_device_data(device)
    print(f"Node {i} ({device}): {len(node_data[f'node{i}'])} rows")

# Use node_data in federated learning training loop
for node_name, data in node_data.items():
    print(f"Training {node_name} with {len(data)} samples...")
    # model = train_on_node(data)


# ============================================================================
# CLASS DISTRIBUTION ANALYSIS
# ============================================================================

# Example 8: Analyze class distribution
print("\nGlobal Attack Type Distribution:")
print(df_train['attack_type'].value_counts())
print(df_train['attack_type'].value_counts(normalize=True) * 100)

print("\nGlobal Device Distribution:")
print(df_train['device'].value_counts())

print("\nCross-tabulation (Device × Attack Type):")
print(pd.crosstab(df_train['device'], df_train['attack_type']))


# ============================================================================
# STRATIFIED SAMPLING FOR BALANCED TRAINING
# ============================================================================

# Example 9: Get stratified sample by attack type
stratified = df_train.groupby('attack_type', group_keys=False).apply(
    lambda x: x.sample(min(1000, len(x)), random_state=42)
)
print(f"Stratified sample: {len(stratified)} rows")
print(stratified['attack_type'].value_counts())


# ============================================================================
# SAVE PROCESSED DATA
# ============================================================================

# Example 10: Save filtered data for later use
# Save device-specific data
device1_data = df_train[df_train['device'] == 'Danmini_Doorbell']
device1_data.to_csv('data/processed/device_1_danmini_full.csv', index=False)

# Save attack-type specific data
benign_data = df_train[df_train['attack_type'] == 'benign']
benign_data.to_csv('data/processed/benign_data.csv', index=False)

# Save samples
sample = load_sample('device_1_danmini', n_rows=1000)
sample.to_csv('data/processed/danmini_sample_1k.csv', index=False)


# ============================================================================
# FEATURE EXTRACTION PIPELINE
# ============================================================================

# Example 11: Prepare data for feature engineering
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv('data/processed/combined_training_data.csv')

# Separate features and labels
X = df.drop(['attack_type', 'device'], axis=1)
y = df['attack_type']

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, stratify=y, random_state=42
)

print(f"Train: {X_train.shape}, Test: {X_test.shape}")


# ============================================================================
# WORKING WITH METADATA
# ============================================================================

# Example 12: Utilize added metadata columns
df = pd.read_csv('data/processed/combined_training_data.csv')

# Group by device
for device in df['device'].unique():
    device_df = df[df['device'] == device]
    print(f"\n{device}:")
    print(f"  Total rows: {len(device_df)}")
    print(f"  Attack types: {device_df['attack_type'].unique()}")
    print(f"  Features: {len(device_df.columns) - 2}")  # -2 for metadata cols

# Group by attack type
for attack in df['attack_type'].unique():
    attack_df = df[df['attack_type'] == attack]
    print(f"\n{attack}:")
    print(f"  Total rows: {len(attack_df)}")
    print(f"  Devices: {attack_df['device'].unique()}")


# ============================================================================
# MEMORY EFFICIENT BATCH PROCESSING
# ============================================================================

# Example 13: Process large data in batches without loading everything
batch_size = 10000

for batch in pd.read_csv('data/processed/combined_training_data.csv', 
                         chunksize=batch_size):
    print(f"Processing batch of {len(batch)} rows...")
    # Do your processing here
    # model.partial_fit(batch.drop(['attack_type', 'device'], axis=1), 
    #                   batch['attack_type'])


# ============================================================================
# USEFUL CONSTANTS & MAPPINGS
# ============================================================================

# Device names
DEVICES = {
    'device_1_danmini': 'Danmini_Doorbell',
    'device_2_ecobee': 'Ecobee_Thermostat',
    'device_3_ennio': 'Ennio_Doorbell'
}

# Attack classes
ATTACK_CLASSES = ['benign', 'mirai', 'bashlite']

# File paths
PATHS = {
    'train': 'data/processed/combined_training_data.csv',
    'test': 'data/processed/combined_test_data.csv',
    'organized': 'data/organized',
    'raw_train': 'data/raw/train',
    'raw_test': 'data/raw/test'
}


# ============================================================================
# DEBUGGING & VALIDATION
# ============================================================================

# Example 14: Validate your data
df = pd.read_csv('data/processed/combined_training_data.csv')

print("Data Validation:")
print(f"  Shape: {df.shape}")
print(f"  Missing values: {df.isnull().sum().sum()}")
print(f"  Duplicates: {df.duplicated().sum()}")
print(f"  Devices: {df['device'].nunique()}")
print(f"  Attack types: {df['attack_type'].nunique()}")
print(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# Check for data quality issues
for col in df.select_dtypes(include='number').columns:
    if df[col].isnull().any():
        print(f"  ⚠️  Column {col} has NaN values")
    if (df[col] == np.inf).any():
        print(f"  ⚠️  Column {col} has infinity values")


# ============================================================================
print("✅ Copy-paste the examples above into your code!")
# ============================================================================
