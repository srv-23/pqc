"""
Configuration File for Federated Learning IoT Anomaly Detection Project
========================================================================
"""

# ============================================================================
# DATA CONFIGURATION
# ============================================================================

# N-BaIoT Dataset Configuration
NBAIOT_DEVICES = [
    "Danmini_Doorbell",
    "Ecobee_Thermostat",
    "Ennio_Doorbell"
]

# Sampling configuration
TARGET_SAMPLES_PER_DEVICE = 100000
CLASS_DISTRIBUTION = {
    "benign": 0.35,      # 35%
    "mirai": 0.40,       # 40%
    "bashlite": 0.25     # 25%
}

# Label mapping
LABEL_MAPPING = {
    "benign": 0,
    "mirai": 1,
    "bashlite": 2
}

# Data split ratios
TRAIN_RATIO = 0.70  # 70%
VAL_RATIO = 0.15    # 15%
TEST_RATIO = 0.15   # 15%

# ============================================================================
# DIRECTORY CONFIGURATION
# ============================================================================

DATASET_DIR = "dataset"
PROCESSED_DATA_DIR = "dataset/processed"

# Node directories
NODE_DIRECTORIES = {
    "Danmini_Doorbell": "node1_danmini",
    "Ecobee_Thermostat": "node2_ecobee",
    "Ennio_Doorbell": "node3_ennio"
}

# Output files
OUTPUT_FILES = {
    "train": "train.csv",
    "val": "val.csv",
    "test": "test.csv"
}

# UNSW-NB15 configuration
UNSW_NB15_DIR = "dataset/UNSW-NB15"
UNSW_TEST_OUTPUT = "dataset/processed/unsw_test.csv"

# ============================================================================
# REPRODUCIBILITY
# ============================================================================

RANDOM_SEED = 42
NUMPY_SEED = 42
SKLEARN_SEED = 42

# ============================================================================
# FEDERATED LEARNING CONFIGURATION
# ============================================================================

# Flower Framework
FL_SERVER_ADDRESS = "localhost:8080"
FL_NUM_ROUNDS = 10
FL_MIN_CLIENTS = 3
FL_MIN_AVAILABLE_CLIENTS = 3

# Model configuration
MODEL_LEARNING_RATE = 0.001
MODEL_EPOCHS = 5
MODEL_BATCH_SIZE = 32
MODEL_VALIDATION_SPLIT = 0.2

# ============================================================================
# MACHINE LEARNING CONFIGURATION
# ============================================================================

# Classification models
RANDOM_FOREST_PARAMS = {
    "n_estimators": 100,
    "max_depth": 20,
    "random_state": RANDOM_SEED,
    "n_jobs": -1
}

SVM_PARAMS = {
    "kernel": "rbf",
    "C": 1.0,
    "gamma": "scale",
    "random_state": RANDOM_SEED
}

# Preprocessing
FEATURE_SCALING = True
FEATURE_SELECTION = True
NUM_SELECTED_FEATURES = 50

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/fl_project.log"

# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================

# Performance metrics
METRICS = [
    "accuracy",
    "precision",
    "recall",
    "f1_score",
    "roc_auc"
]

# Threshold values
ANOMALY_DETECTION_THRESHOLD = 0.5

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Post-Quantum Cryptography
USE_PQC = True
PQC_ALGORITHM = "CRYSTALS-Kyber"  # or other PQ-safe algorithms

# Federated Learning Privacy
ENABLE_DIFFERENTIAL_PRIVACY = False
DP_EPSILON = 1.0
DP_DELTA = 0.001

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

# Python version requirement
PYTHON_VERSION = "3.10"

# Required packages
REQUIRED_PACKAGES = [
    "numpy>=1.21.0",
    "pandas>=1.3.0",
    "scikit-learn>=1.0.0",
    "matplotlib>=3.4.0",
    "seaborn>=0.11.0",
    "flwr>=1.0.0",
    "pqcrypto>=1.1.0"
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_node_directory(device_name: str) -> str:
    """Get the node directory for a given device name."""
    return NODE_DIRECTORIES.get(device_name, device_name.lower())


def get_output_file_path(node_directory: str, file_type: str) -> str:
    """Get the output file path for a specific node and file type."""
    return f"{PROCESSED_DATA_DIR}/{node_directory}/{OUTPUT_FILES.get(file_type, file_type)}"


def validate_config() -> bool:
    """Validate configuration parameters."""
    issues = []
    
    # Check ratios sum to 1.0
    class_dist_sum = sum(CLASS_DISTRIBUTION.values())
    if abs(class_dist_sum - 1.0) > 0.001:
        issues.append(f"Class distribution doesn't sum to 1.0: {class_dist_sum}")
    
    # Check split ratios sum to 1.0
    split_sum = TRAIN_RATIO + VAL_RATIO + TEST_RATIO
    if abs(split_sum - 1.0) > 0.001:
        issues.append(f"Split ratios don't sum to 1.0: {split_sum}")
    
    # Check positive values
    if TARGET_SAMPLES_PER_DEVICE <= 0:
        issues.append("TARGET_SAMPLES_PER_DEVICE must be positive")
    
    if issues:
        print("Configuration validation FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("Configuration validation PASSED")
    return True


if __name__ == "__main__":
    print("Federated Learning Configuration")
    print("=" * 60)
    print(f"Devices: {NBAIOT_DEVICES}")
    print(f"Target samples per device: {TARGET_SAMPLES_PER_DEVICE}")
    print(f"Class distribution: {CLASS_DISTRIBUTION}")
    print(f"Train/Val/Test split: {TRAIN_RATIO}/{VAL_RATIO}/{TEST_RATIO}")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"FL server address: {FL_SERVER_ADDRESS}")
    print(f"FL rounds: {FL_NUM_ROUNDS}")
    print("=" * 60)
    
    # Validate configuration
    validate_config()
