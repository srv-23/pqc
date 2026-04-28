# N-BaIoT Federated Learning with Post-Quantum Cryptography

A production-ready federated learning pipeline for IoT intrusion detection using the Flower framework with post-quantum cryptographic security.

## Project Structure

```
pqc/
├── data/                          # Data directories
│   ├── raw/                       # Original datasets (to be populated)
│   ├── processed/                 # Processed data
│   └── partitioned/               # Federated learning partitions (node1, node2, node3)
│
├── src/                           # Source code
│   ├── __init__.py
│   ├── data_pipeline/             # Data preprocessing and preparation
│   │   ├── __init__.py
│   │   ├── 01_load_clean_data.py           # Load and clean raw datasets
│   │   ├── 02_preprocess_and_partition.py  # Partition for federated learning
│   │   └── utils_data.py                   # Data utilities
│   │
│   ├── models/                    # Model training and definitions
│   │   ├── __init__.py
│   │   ├── 03_train_autoencoder.py         # Autoencoder for anomaly detection
│   │   ├── 04_train_node_model.py          # Node-level model training
│   │   └── model_utils.py                  # Model utilities
│   │
│   ├── federated_learning/        # Federated learning with Flower
│   │   ├── __init__.py
│   │   ├── 05_flower_client.py             # Flower client implementation
│   │   ├── 06_flower_server.py             # Flower server implementation
│   │   ├── 07_launch_federation.py         # Orchestrator for distributed training
│   │   └── fl_utils.py                     # FL utilities
│   │
│   ├── crypto/                    # Post-quantum cryptography
│   │   ├── __init__.py
│   │   ├── crypto_layer.py                 # PQC implementation
│   │   └── crypto_utils.py                 # Crypto utilities
│   │
│   └── utils/                     # Common utilities
│       ├── __init__.py
│       ├── plot_convergence.py             # Visualization utilities
│       ├── verify_imports.py               # Dependency checker
│       └── common.py                       # Common functions
│
├── configs/                       # Configuration files
│   ├── config.py                  # Main configuration
│   └── default_config.yaml        # Default settings (optional)
│
├── tests/                         # Test files
│   ├── __init__.py
│   ├── test_crypto_layer.py       # Crypto layer tests
│   └── test_data_pipeline.py      # Data pipeline tests
│
├── results/                       # Generated outputs (git-ignored)
│   ├── models/                    # Trained models
│   ├── plots/                     # Visualizations
│   ├── metrics/                   # Training metrics
│   └── logs/                      # Log files
│
├── docs/                          # Documentation
│   ├── README_SETUP.md            # Installation and setup guide
│   ├── README_USAGE.md            # Usage guide
│   ├── README_ARCHITECTURE.md     # Architecture documentation
│   ├── README_CRYPTO.md           # Cryptography details
│   ├── README_FEDERATED.md        # Federated learning guide
│   └── TROUBLESHOOTING.md         # Troubleshooting guide
│
├── scripts/                       # Utility scripts
│   ├── run_pipeline.py            # Main pipeline runner
│   ├── run_federated_learning.py  # FL runner (shortcut)
│   └── setup_environment.py       # Environment setup
│
├── .gitignore                     # Git ignore patterns
├── requirements.txt               # Python dependencies
├── README.md                      # Main project README
└── CHANGELOG.md                   # Version history
```

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Data

```bash
# Load and clean data
python src/data_pipeline/01_load_clean_data.py

# Partition for federated learning
python src/data_pipeline/02_preprocess_and_partition.py
```

### 3. Train Models (Optional)

```bash
# Train autoencoder
python src/models/03_train_autoencoder.py

# Train node models
python src/models/04_train_node_model.py
```

### 4. Run Federated Learning

```bash
# Automatic orchestration (recommended)
python src/federated_learning/07_launch_federation.py

# Or run manually in separate terminals:

# Terminal 1: Server
python src/federated_learning/06_flower_server.py

# Terminal 2, 3, 4: Clients
python src/federated_learning/05_flower_client.py --node-id 1 --server localhost:8080 --server-public-key results/keys/server_public_key.bin
python src/federated_learning/05_flower_client.py --node-id 2 --server localhost:8080 --server-public-key results/keys/server_public_key.bin
python src/federated_learning/05_flower_client.py --node-id 3 --server localhost:8080 --server-public-key results/keys/server_public_key.bin
```

### 5. View Results

```bash
# Plot convergence
python src/utils/plot_convergence.py

# Results stored in:
# - results/metrics/round_metrics.csv
# - results/plots/convergence.png
# - results/logs/
```

## Pipeline Steps

The project follows a numbered pipeline structure:

| Step | Script | Purpose |
|------|--------|---------|
| 01 | load_clean_data.py | Load N-BaIoT dataset, clean, normalize |
| 02 | preprocess_and_partition.py | Partition data for 3 nodes |
| 03 | train_autoencoder.py | Train anomaly detection model |
| 04 | train_node_model.py | Train intrusion detection model |
| 05 | flower_client.py | Federated learning client |
| 06 | flower_server.py | Federated learning server |
| 07 | launch_federation.py | Orchestrate federated training |

## Configuration

Edit `configs/config.py` to customize:
- Model hyperparameters
- Training rounds
- Batch sizes
- Data split ratios
- Encryption settings
- Server address and port

## Features

✅ **Post-Quantum Cryptography** - RSA-4096 + AES-256-GCM encryption  
✅ **Federated Learning** - Decentralized training with 3 nodes  
✅ **IoT Intrusion Detection** - N-BaIoT dataset (1.57M samples, 105 features)  
✅ **Metrics Tracking** - Per-round accuracy, precision, recall, F1  
✅ **Visualization** - Convergence plots and analysis  
✅ **Comprehensive Logging** - All operations tracked and logged  

## File Naming Convention

- **Numbered scripts (01-07):** Pipeline steps in execution order
- **Utility modules:** `*_utils.py` - Helper functions
- **Test files:** `test_*.py` - Unit and integration tests
- **Config files:** `config.py`, `*_config.yaml` - Settings
- **Documentation:** `README_*.md`, `*.md` - Guides

## Environment Variables

Optional environment variables:
```bash
FLASK_ENV=development  # For Flask-based utilities
LOG_LEVEL=INFO        # Logging verbosity
DATA_PATH=./data      # Data directory
RESULTS_PATH=./results # Results directory
```

## Dependencies

See `requirements.txt` for the complete list. Key dependencies:
- `flower` (1.29.0+) - Federated learning framework
- `scikit-learn` - Machine learning models
- `numpy`, `pandas` - Data processing
- `cryptography` - Cryptographic operations
- `liboqs-python` - Post-quantum cryptography (optional, Windows fallback provided)

## Documentation

Detailed documentation available in `docs/`:
- **Setup Guide** - Installation, environment setup
- **Usage Guide** - How to run the pipeline
- **Architecture** - System design and data flow
- **Cryptography** - PQC implementation details
- **Federated Learning** - FL concepts and configuration
- **Troubleshooting** - Common issues and solutions

## Results

All generated outputs stored in `results/`:
```
results/
├── models/               # Trained models (h5, pkl)
├── plots/                # Visualizations (PNG)
├── metrics/              # CSV metrics files
├── keys/                 # Encryption keys
└── logs/                 # Log files
```

Results directory is git-ignored and can be safely deleted to restart clean.

## Removing Results (Clean Slate)

```bash
# Delete all generated results
rm -r results/

# The pipeline will recreate results/ as needed
python src/federated_learning/07_launch_federation.py
```

## Contributing

When adding new scripts:
1. Place in appropriate `src/` subdirectory
2. Follow naming convention: `NN_descriptive_name.py` for pipeline steps
3. Add docstrings and logging
4. Update this README
5. Add tests in `tests/` directory

## License

Proprietary - All rights reserved

## Contact

For questions or issues, refer to documentation in `docs/` directory.

---

**Project Status:** Production Ready  
**Last Updated:** 2026  
**Maintained By:** Federated Learning Team
#   p q c  
 