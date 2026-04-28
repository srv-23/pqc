# PROJECT STRUCTURE AND ORGANIZATION

## Final Clean Project Layout

```
pqc/                                    # Project Root
│
├── .gitignore                          # Git ignore patterns
├── README.md                           # Main project documentation
├── CHANGELOG.md                        # Version history
├── requirements.txt                    # Python dependencies
│
├── .venv/                              # Virtual environment (git-ignored)
│
├── src/                                # Source code (main code)
│   ├── __init__.py
│   │
│   ├── data_pipeline/                  # Step 1-2: Data Processing
│   │   ├── __init__.py
│   │   ├── 01_load_clean_data.py       # Load and clean raw datasets
│   │   ├── 02_preprocess_and_partition.py  # Partition for FL
│   │   └── utils_data.py               # Data utilities
│   │
│   ├── models/                         # Step 3-4: Model Training
│   │   ├── __init__.py
│   │   ├── 03_train_autoencoder.py     # Train anomaly detection
│   │   ├── 04_train_node_model.py      # Train node classifiers
│   │   └── model_utils.py              # Model utilities
│   │
│   ├── federated_learning/             # Step 5-7: Distributed Training
│   │   ├── __init__.py
│   │   ├── 05_flower_client.py         # Flower client with encryption
│   │   ├── 06_flower_server.py         # Flower server with PQC
│   │   ├── 07_launch_federation.py     # Orchestrator (RECOMMENDED)
│   │   └── fl_utils.py                 # FL utilities
│   │
│   ├── crypto/                         # Post-Quantum Cryptography
│   │   ├── __init__.py
│   │   ├── crypto_layer.py             # Core PQC implementation
│   │   └── crypto_utils.py             # Crypto utilities
│   │
│   └── utils/                          # Common Utilities
│       ├── __init__.py
│       ├── plot_convergence.py         # Visualization
│       ├── verify_imports.py           # Dependency checker
│       └── common.py                   # Common functions
│
├── configs/                            # Configuration Files
│   ├── config.py                       # Main configuration
│   └── default_config.yaml             # YAML config (optional)
│
├── tests/                              # Test Suite
│   ├── __init__.py
│   ├── test_crypto_layer.py            # Crypto tests
│   └── test_data_pipeline.py           # Data pipeline tests
│
├── data/                               # Data Directory (LOCAL - not in git)
│   ├── raw/                            # Original datasets
│   │   ├── 1.benign.csv
│   │   ├── 1.gafgyt.*.csv
│   │   ├── 1.mirai.*.csv
│   │   ├── 2.*.csv
│   │   ├── 3.*.csv
│   │   └── ... (all N-BaIoT CSV files)
│   │
│   ├── processed/                      # Cleaned and normalized data
│   │   ├── train.csv
│   │   └── test.csv
│   │
│   └── partitioned/                    # Partitioned for FL
│       ├── node1/
│       │   ├── train.csv
│       │   └── test.csv
│       ├── node2/
│       │   ├── train.csv
│       │   └── test.csv
│       └── node3/
│           ├── train.csv
│           └── test.csv
│
├── docs/                               # Documentation
│   ├── README_SETUP.md                 # Installation guide
│   ├── README_USAGE.md                 # Usage guide
│   ├── README_ARCHITECTURE.md          # System architecture
│   ├── README_CRYPTO.md                # Cryptography details
│   ├── README_FEDERATED.md             # FL guide (optional)
│   └── TROUBLESHOOTING.md              # Troubleshooting (optional)
│
├── results/                            # Generated Outputs (git-ignored)
│   ├── models/                         # Trained models
│   │   ├── autoencoder/
│   │   ├── node1_model.pkl
│   │   ├── node2_model.pkl
│   │   └── node3_model.pkl
│   │
│   ├── metrics/                        # CSV metrics files
│   │   ├── round_metrics.csv
│   │   └── node_metrics.csv
│   │
│   ├── plots/                          # PNG visualizations
│   │   ├── convergence.png
│   │   ├── accuracy_per_round.png
│   │   └── confusion_matrix.png
│   │
│   ├── logs/                           # Log files
│   │   ├── server.log
│   │   ├── client_1.log
│   │   ├── client_2.log
│   │   └── client_3.log
│   │
│   └── keys/                           # Encryption keys (SECURE!)
│       └── server_public_key.bin
│
└── scripts/                            # Utility Scripts (optional)
    ├── run_pipeline.py
    ├── run_federated_learning.py
    └── setup_environment.py
```

## Folder Purpose Summary

| Folder | Purpose | Changes |
|--------|---------|---------|
| `src/data_pipeline/` | Data loading and preprocessing | Pipeline steps 01-02 |
| `src/models/` | Model training | Pipeline steps 03-04 |
| `src/federated_learning/` | Distributed training | Pipeline steps 05-07 |
| `src/crypto/` | Encryption utilities | Cryptography support |
| `src/utils/` | Common utilities | Visualization, validation |
| `configs/` | Configuration files | Settings and hyperparameters |
| `tests/` | Unit and integration tests | Quality assurance |
| `data/` | Raw and processed data | Datasets (git-ignored) |
| `docs/` | Documentation | Guides and references |
| `results/` | Generated outputs | Models, metrics, plots (git-ignored) |

## File Organization by Category

### Pipeline Execution (Numbered)
```
01_load_clean_data.py              → Load raw data
02_preprocess_and_partition.py     → Partition for FL
03_train_autoencoder.py            → Optional: autoencoder
04_train_node_model.py             → Optional: node models
05_flower_client.py                → FL client
06_flower_server.py                → FL server
07_launch_federation.py            → Orchestrator (RECOMMENDED)
```

### Utilities
```
verify_imports.py                  → Check dependencies
plot_convergence.py                → Visualization
common.py                          → Helper functions
crypto_layer.py                    → Encryption
```

### Configuration
```
config.py                          → Hyperparameters
default_config.yaml                → Optional YAML config
```

### Testing
```
test_crypto_layer.py               → Crypto tests
test_data_pipeline.py              → Data pipeline tests
```

## Cleaned Up vs. Original

### Removed (Unused/Duplicate)
- ❌ Old root-level Python files (client.py, server.py, etc.)
- ❌ Old root-level CSV files
- ❌ Old markdown documentation (scattered)
- ❌ Old result directories (eda_plots/, training_plots/, federated_learning_results/)
- ❌ Old dataset structure (dataset/, datasets/)
- ❌ Old models directory
- ❌ Setup scripts (*.bat, *.sh)
- ❌ __pycache__ directories

### Reorganized
- ✅ All source code → `src/` with proper subpackages
- ✅ All config → `configs/`
- ✅ All tests → `tests/`
- ✅ All data → `data/` (raw, processed, partitioned)
- ✅ All results → `results/` (models, metrics, plots, logs, keys)
- ✅ All docs → `docs/` with consistent naming

### Added
- ✅ Proper package structure with `__init__.py` files
- ✅ Comprehensive README.md
- ✅ CHANGELOG.md for version tracking
- ✅ .gitignore for clean repository
- ✅ Multiple documentation files (setup, usage, architecture, crypto)
- ✅ results/ directory for outputs (clean structure)

## Naming Conventions

### Python Files
- **Pipeline steps:** `NN_descriptive_name.py` (01_, 02_, etc.)
- **Utilities:** `*_utils.py` (model_utils.py, fl_utils.py)
- **Tests:** `test_*.py` (test_crypto_layer.py)
- **Config:** `config.py`, `*_config.yaml`
- **Main modules:** `crypto_layer.py`, `common.py`

### Directories
- **Data:** `data/`, with subdirs: `raw/`, `processed/`, `partitioned/`
- **Results:** `results/`, with subdirs: `models/`, `metrics/`, `plots/`, `logs/`, `keys/`
- **Source:** `src/`, with functional packages
- **Docs:** `docs/`, with consistent naming: `README_*.md`

### CSV/Data Files
- **Metrics:** `*_metrics.csv` (round_metrics.csv, node_metrics.csv)
- **Data:** `{dataset}.csv` (train.csv, test.csv, balanced.csv)

### Log Files
- **Server:** `server.log`
- **Clients:** `client_N.log` where N = node ID

## Size Summary

```
Total Project Size:  ~2.5 GB
  - data/raw/       ~1.5 GB (datasets)
  - data/processed/ ~400 MB (cleaned)
  - data/partitioned/ ~500 MB (3 nodes × 167 MB)
  - src/            ~2 MB (source code)
  - docs/           ~200 KB (documentation)
  - results/        Variable (generated)
```

## Git Management

### What's Tracked
- Source code (`src/`)
- Configuration (`configs/`)
- Tests (`tests/`)
- Documentation (`docs/`)
- `.gitignore`, `README.md`, `CHANGELOG.md`, `requirements.txt`

### What's Ignored (Local Only)
- `.venv/` - Virtual environment
- `data/` - Datasets (too large)
- `results/` - Generated outputs
- `__pycache__/` - Cache files
- `.pyc`, `.egg-info/` - Build artifacts

## Quick Start Commands

```bash
# 1. Setup
cd pqc
python -m venv .venv
.venv\Scripts\activate  # or source .venv/bin/activate on Linux
pip install -r requirements.txt

# 2. Verify
python src/utils/verify_imports.py

# 3. Prepare data
python src/data_pipeline/01_load_clean_data.py
python src/data_pipeline/02_preprocess_and_partition.py

# 4. Run federated learning (RECOMMENDED)
python src/federated_learning/07_launch_federation.py

# 5. View results
python src/utils/plot_convergence.py
cat results/metrics/round_metrics.csv
```

## Next Steps

1. **Setup Environment:** Follow `docs/README_SETUP.md`
2. **Understand System:** Read `docs/README_ARCHITECTURE.md`
3. **Prepare Data:** Follow `docs/README_USAGE.md` Step 1-2
4. **Run Pipeline:** Execute `src/federated_learning/07_launch_federation.py`
5. **Analyze Results:** Check `results/` directory

---

**Status:** ✅ PROJECT CLEANED AND REORGANIZED  
**Date:** 2026-04-28  
**Next Action:** Run pipeline to generate fresh results
