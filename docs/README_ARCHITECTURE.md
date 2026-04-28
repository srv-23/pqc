# Architecture and Design

## System Overview

The project implements a distributed federated learning system for IoT intrusion detection with post-quantum cryptographic security.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Federated Learning System                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Client 1   │  │   Client 2   │  │   Client 3   │         │
│  │  (Node 1)    │  │  (Node 2)    │  │  (Node 3)    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │                                    │
│         ┌─────────────────▼─────────────────┐                  │
│         │     Flower Server (FedAvg)        │                  │
│         │  - Aggregation                    │                  │
│         │  - Model Broadcasting             │                  │
│         │  - Encryption/Decryption          │                  │
│         └─────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Data Pipeline (`src/data_pipeline/`)

**Purpose:** Data loading, cleaning, and partitioning

```
Raw Data (N-BaIoT)
    ↓
[01] Load & Clean
    ├─ Load CSV files
    ├─ Handle missing values
    ├─ Remove outliers
    └─ Normalize features
    ↓
Processed Data
    ↓
[02] Preprocess & Partition
    ├─ Feature scaling
    ├─ Train/test split
    └─ Distribute to nodes
    ↓
Partitioned Data
```

**Key Files:**
- `01_load_clean_data.py` - Data loading and preprocessing
- `02_preprocess_and_partition.py` - Data partitioning for federated learning
- `utils_data.py` - Data utility functions

**Data Format:**
- Input: CSV files with 105 features + 1 label column
- Output: train.csv, test.csv per node (node1, node2, node3)
- Classes: BENIGN, MIRAI, GAFGYT

### 2. Models (`src/models/`)

**Purpose:** Model definition and training

```
[03] Autoencoder
    ├─ Purpose: Anomaly detection
    ├─ Architecture: 105 → 64 → 32 → 64 → 105
    └─ Output: model_autoencoder.pkl

[04] Node Models
    ├─ Purpose: Intrusion detection
    ├─ Architecture: MLPClassifier (105 → 256 → 128 → 64 → 3)
    └─ Output: model_node*.pkl
```

**Key Files:**
- `03_train_autoencoder.py` - Autoencoder training
- `04_train_node_model.py` - Node-level model training
- `model_utils.py` - Model utilities

**Model Details:**
- Type: scikit-learn MLPClassifier
- Hidden layers: (256, 128, 64)
- Activation: ReLU
- Optimizer: Adam
- Loss: Categorical cross-entropy

### 3. Federated Learning (`src/federated_learning/`)

**Purpose:** Distributed model training with encryption

```
┌─────────────────────────────────────────────────────┐
│           Flower Federated Learning                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Server [06_flower_server.py]                       │
│  ├─ Manage global model                            │
│  ├─ Aggregate client updates (FedAvg)              │
│  ├─ Decrypt incoming weights                       │
│  ├─ Encrypt outgoing weights                       │
│  └─ Track metrics per round                        │
│                                                    │
│ Client [05_flower_client.py]                       │
│  ├─ Receive global model                           │
│  ├─ Decrypt weights (asymmetric)                   │
│  ├─ Train locally (fit)                            │
│  ├─ Encrypt updated weights                        │
│  └─ Send to server                                 │
│                                                    │
│ Launcher [07_launch_federation.py]                 │
│  ├─ Start server process                           │
│  ├─ Generate encryption keys                       │
│  └─ Launch 3 client processes                      │
│                                                    │
└─────────────────────────────────────────────────────┘
```

**Key Files:**
- `05_flower_client.py` - Flower client implementation
- `06_flower_server.py` - Flower server implementation
- `07_launch_federation.py` - Orchestrator script
- `fl_utils.py` - Federated learning utilities

**Flow per Round:**
1. Server encrypts aggregated model → sends to clients
2. Client receives encrypted model → decrypts
3. Client trains locally → encrypts updated weights
4. Server receives encrypted updates → decrypts
5. Server aggregates updates → repeats

### 4. Cryptography (`src/crypto/`)

**Purpose:** Post-quantum secure communication

```
┌──────────────────────────────────────┐
│   Post-Quantum Cryptography Layer    │
├──────────────────────────────────────┤
│                                      │
│ Algorithm Selection (Auto-Fallback)  │
│  1. Kyber768 (NIST PQC)             │
│  2. NTRU-Prime-857 (NIST PQC)       │
│  3. RSA-4096 (Classical, fallback)  │
│                                      │
│ Hybrid Encryption                    │
│  ├─ Asymmetric: Wraps AES key       │
│  ├─ Symmetric: AES-256-GCM          │
│  └─ Key Derivation: HKDF-SHA256     │
│                                      │
│ Operations                           │
│  ├─ generate_keypair()              │
│  ├─ encrypt_weights()               │
│  ├─ decrypt_weights()               │
│  └─ benchmark_crypto()              │
│                                      │
└──────────────────────────────────────┘
```

**Key Files:**
- `crypto_layer.py` - Core cryptography implementation
- `crypto_utils.py` - Crypto utilities

**Encryption Details:**
- Primary: RSA-4096 (when Kyber/NTRU unavailable)
- Symmetric: AES-256-GCM
- Key Derivation: HKDF-SHA256
- Overhead: 0.52% for 131KB weights
- Per-round impact: 1-2% training time

### 5. Utilities (`src/utils/`)

**Purpose:** Common utilities and visualization

```
Visualization
  └─ plot_convergence.py
     ├─ Reads: round_metrics.csv
     └─ Outputs: *.png plots

Validation
  └─ verify_imports.py
     └─ Checks: dependencies

Common
  └─ common.py
     └─ Shared: helper functions
```

## Data Flow

### Complete Pipeline Flow

```
[1] data/raw/*.csv
    ↓
[2] 01_load_clean_data.py
    ↓
[3] data/processed/
    ↓
[4] 02_preprocess_and_partition.py
    ↓
[5] data/partitioned/node{1,2,3}/
    ├─ train.csv
    └─ test.csv
    ↓
[6] Optional: Train models
    ├─ 03_train_autoencoder.py
    └─ 04_train_node_model.py
    ↓
[7] 07_launch_federation.py
    ├─ 06_flower_server.py
    │  ├─ Generate keypair
    │  └─ Aggregate updates
    └─ 05_flower_client.py (x3)
       ├─ Decrypt weights
       ├─ Train locally
       └─ Encrypt updates
    ↓
[8] results/
    ├─ models/
    ├─ metrics/
    ├─ plots/
    ├─ logs/
    └─ keys/
```

### Federated Learning Round Flow

```
Round Start
    ↓
Server.configure_fit()
    ├─ Get aggregated weights
    ├─ Encrypt for each client
    └─ Send config["encrypted_parameters"]
    ↓
Client.fit()
    ├─ Receive encrypted_parameters
    ├─ Decrypt with client_private_key
    ├─ Reshape to model structure
    ├─ Train locally
    ├─ Extract weights
    ├─ Encrypt with server_public_key
    └─ Send encrypted_weights
    ↓
Server.aggregate_fit()
    ├─ Receive encrypted_weights from all clients
    ├─ Decrypt with server_private_key
    ├─ Perform FedAvg aggregation
    └─ Return aggregated_parameters
    ↓
Server.aggregate_evaluate()
    ├─ Broadcast aggregated model
    ├─ Clients evaluate locally
    ├─ Return metrics (unencrypted)
    └─ Log metrics
    ↓
Round Complete
```

## Configuration Hierarchy

```
configs/
├─ config.py                    [Main config]
│  ├─ Model parameters
│  ├─ Training parameters
│  ├─ Data paths
│  └─ FL parameters
│
└─ default_config.yaml          [Optional: YAML config]
```

## Result Storage

```
results/
├─ models/                      [Trained models]
│  ├─ autoencoder/
│  ├─ node1_model.pkl
│  ├─ node2_model.pkl
│  └─ node3_model.pkl
├─ metrics/                     [Training metrics]
│  ├─ round_metrics.csv
│  └─ node_metrics.csv
├─ plots/                       [Visualizations]
│  ├─ convergence.png
│  ├─ accuracy_per_round.png
│  └─ confusion_matrix.png
├─ logs/                        [Log files]
│  ├─ server.log
│  ├─ client_1.log
│  ├─ client_2.log
│  └─ client_3.log
└─ keys/                        [Encryption keys]
   └─ server_public_key.bin
```

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Flower | 1.29.0+ |
| ML Models | scikit-learn | 1.0+ |
| Cryptography | cryptography | 42.0+ |
| PQC (Optional) | liboqs-python | Latest |
| Data | pandas, numpy | Latest |
| Visualization | matplotlib | Latest |
| Testing | pytest | Latest |

## Design Decisions

### 1. Federated Learning Strategy
- **Choice:** FedAvg (Federated Averaging)
- **Reason:** Simple, effective, convergence guaranteed
- **Alternative:** FedProx, FedAdam (not implemented)

### 2. Encryption Model
- **Choice:** Hybrid (Asymmetric + Symmetric)
- **Reason:** Security + Performance balance
- **Primary:** Kyber768 (post-quantum)
- **Fallback:** RSA-4096 (classical)

### 3. Model Architecture
- **Choice:** MLPClassifier (3 hidden layers)
- **Reason:** Suitable for tabular IoT data
- **Layers:** 105 → 256 → 128 → 64 → 3

### 4. Data Partitioning
- **Method:** Non-overlapping partitions
- **Strategy:** Equal-sized (1/3 each node)
- **Rationale:** Simulates distributed IoT devices

## Scalability Considerations

### Horizontal Scaling (More Clients)
- Current: 3 clients
- To add: Modify `NUM_CLIENTS` and launch additional clients
- Limitation: Aggregation time increases linearly

### Vertical Scaling (Larger Data)
- Current: ~2.4GB partitioned data
- Can handle: 10-100GB with sufficient RAM
- Limitation: Memory constraints on single machine

### Model Complexity
- Current: ~100KB model size
- Can handle: 1-100MB models
- Limitation: Encryption/decryption time

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Key Generation | 237ms | Per server startup |
| Weight Encryption | 0.55ms | 131KB weights |
| Weight Decryption | 279ms | RSA bottleneck |
| Per-Round Time | 30-60s | 3 clients, 10 epochs |
| Encryption Overhead | 1-2% | Of total round time |
| Final Accuracy | >85% | Typical for N-BaIoT |

## Security Properties

### Confidentiality
✓ Model weights encrypted (RSA-4096 + AES-256-GCM)
✓ Resistant to passive eavesdropping
✓ Future-proof with Kyber support

### Integrity
✓ GCM authentication prevents tampering
✓ Server rejects corrupted weights
✓ Verified per-round

### Limitations
⚠ No mutual authentication (client ↔ server)
⚠ No forward secrecy (same keys all rounds)
⚠ RSA not post-quantum resistant (fallback)
⚠ Honest-but-curious server (can observe structure)

## Future Enhancements

1. **Post-Quantum:** Kyber768 on Linux
2. **Security:** Digital signatures, forward secrecy
3. **Performance:** Parallel decryption, weight compression
4. **Privacy:** Differential privacy, secure aggregation
5. **Scalability:** Load balancing, distributed server
6. **Monitoring:** Real-time metrics dashboard
