# Pipeline Execution Guide

## Quick Start (Recommended)

**Single command to run entire pipeline:**

```bash
python src/federated_learning/07_launch_federation.py
```

This will automatically:
1. ✅ Check for data (load if missing)
2. ✅ Partition data (partition if missing)  
3. ✅ Start server with encryption
4. ✅ Launch 3 clients
5. ✅ Run 10 federated learning rounds
6. ✅ Generate metrics and plots
7. ✅ Save results to `results/`

**Expected output:**
```
================================================================================
FEDERATED LEARNING LAUNCHER
================================================================================
LAUNCHING FLOWER SERVER
================================================================================
Server process started (PID: xxxx)
✓ Server is ready

================================================================================
LAUNCHING CLIENTS
================================================================================
✓ Client Node 1 started (PID: xxxx)
✓ Client Node 2 started (PID: xxxx)
✓ Client Node 3 started (PID: xxxx)

================================================================================
MONITORING FEDERATED LEARNING
================================================================================
[CRYPTO] Encrypting model weights for clients...
[CRYPTO] Decrypting received weights from clients...
...
(10 rounds of federated learning)
...
================================================================================
FEDERATED LEARNING COMPLETE
================================================================================
Results saved to: federated_learning_results/
```

**Runtime:** 5-10 minutes

---

## Step-by-Step Execution

### Step 1: Load and Clean Data

```bash
python src/data_pipeline/01_load_clean_data.py
```

**Input:** CSV files in `data/raw/`  
**Output:** `data/processed/train.csv`, `data/processed/test.csv`  
**Time:** 1-2 minutes

**What it does:**
- Loads all CSV files from `data/raw/`
- Removes missing values
- Normalizes features (0-1 scale)
- Handles class imbalance
- Saves cleaned data to `data/processed/`

### Step 2: Preprocess and Partition

```bash
python src/data_pipeline/02_preprocess_and_partition.py
```

**Input:** `data/processed/train.csv`, `data/processed/test.csv`  
**Output:** `data/partitioned/node{1,2,3}/*.csv`  
**Time:** 1-2 minutes

**What it does:**
- Loads processed data
- Splits into 3 non-overlapping partitions
- Saves node1/, node2/, node3/ directories
- Each node gets: train.csv, test.csv

**Partition Structure:**
```
data/partitioned/
├── node1/
│   ├── train.csv (667 MB)
│   └── test.csv  (167 MB)
├── node2/
│   ├── train.csv (667 MB)
│   └── test.csv  (167 MB)
└── node3/
    ├── train.csv (667 MB)
    └── test.csv  (167 MB)
```

### Step 3: Train Autoencoder (Optional)

```bash
python src/models/03_train_autoencoder.py
```

**Input:** `data/processed/train.csv`  
**Output:** `results/models/autoencoder/`  
**Time:** 2-3 minutes

**What it does:**
- Trains anomaly detection autoencoder
- Architecture: 105 → 64 → 32 → 64 → 105
- Saves trained model
- Generates training curves

**Note:** Optional step. Skip if only doing federated learning.

### Step 4: Train Node Models (Optional)

```bash
python src/models/04_train_node_model.py
```

**Input:** `data/partitioned/node{1,2,3}/train.csv`  
**Output:** `results/models/node{1,2,3}_model.pkl`  
**Time:** 2-3 minutes

**What it does:**
- Trains intrusion detection models locally on each node
- Architecture: 105 → 256 → 128 → 64 → 3
- Saves models for each node
- Logs baseline accuracy

**Note:** Optional step. Useful for comparison.

### Step 5: Run Federated Learning - Server

```bash
python src/federated_learning/06_flower_server.py
```

**Starts on:** `localhost:8080`  
**Time:** Waits for clients

**What it does:**
- Generates encryption keypairs
- Saves server public key to `results/keys/server_public_key.bin`
- Waits for 3 clients to connect
- Aggregates model updates using FedAvg
- Decrypts incoming weights
- Re-encrypts aggregated model
- Tracks metrics per round

**Output:**
```
[CRYPTO] Generating server keypair...
[CRYPTO] Public key saved to: results/keys/server_public_key.bin
Waiting for 3 clients to connect...
```

### Step 6: Run Federated Learning - Clients

**In separate terminals:**

```bash
# Client 1
python src/federated_learning/05_flower_client.py --node-id 1 \
  --server localhost:8080 \
  --server-public-key results/keys/server_public_key.bin

# Client 2
python src/federated_learning/05_flower_client.py --node-id 2 \
  --server localhost:8080 \
  --server-public-key results/keys/server_public_key.bin

# Client 3
python src/federated_learning/05_flower_client.py --node-id 3 \
  --server localhost:8080 \
  --server-public-key results/keys/server_public_key.bin
```

**What each client does:**
- Loads node data: `data/partitioned/node{id}/`
- Receives encrypted model from server
- Decrypts using local private key
- Trains locally for 10 epochs
- Encrypts updated weights
- Sends to server
- Repeats for 10 rounds

**Time per client:** ~60-120 seconds total

### Step 7: Visualize Results

```bash
python src/utils/plot_convergence.py
```

**Input:** `results/metrics/round_metrics.csv`  
**Output:** `results/plots/convergence.png` (and others)  
**Time:** <1 minute

**What it does:**
- Reads metrics from federated learning
- Plots convergence curves
- Generates accuracy/loss plots
- Saves visualizations to `results/plots/`

---

## Execution Paths

### Path A: Automatic (RECOMMENDED)
```
[One Command]
python src/federated_learning/07_launch_federation.py
└─ Runs all steps automatically
```

### Path B: Manual (Full Control)
```
[Step 1] python src/data_pipeline/01_load_clean_data.py
[Step 2] python src/data_pipeline/02_preprocess_and_partition.py
[Step 3] python src/models/03_train_autoencoder.py          (optional)
[Step 4] python src/models/04_train_node_model.py           (optional)
[Step 5] python src/federated_learning/06_flower_server.py  (terminal 1)
[Step 6] python src/federated_learning/05_flower_client.py  (terminal 2,3,4)
[Step 7] python src/utils/plot_convergence.py
```

### Path C: Minimal (Data + FL)
```
[Step 1] python src/data_pipeline/01_load_clean_data.py
[Step 2] python src/data_pipeline/02_preprocess_and_partition.py
[Step 7] python src/federated_learning/07_launch_federation.py
└─ Skip model training, go straight to FL
```

---

## Testing

### Verify Installation
```bash
python src/utils/verify_imports.py
```

**Expected output:**
```
[OK] Importing flwr...
[OK] Importing numpy...
[OK] Importing pandas...
[OK] Importing sklearn...
[OK] Importing cryptography...
All imports successful!
```

### Run Crypto Tests
```bash
python -m pytest tests/test_crypto_layer.py -v
```

### Run All Tests
```bash
python -m pytest tests/ -v
```

---

## Configuration

### Edit Settings

Edit `configs/config.py` to customize:

```python
# Model
HIDDEN_LAYERS = (256, 128, 64)
BATCH_SIZE = 32
LEARNING_RATE = 0.001
NUM_EPOCHS = 10

# Federated Learning
NUM_ROUNDS = 10
MIN_CLIENTS = 3

# Data Paths
DATA_DIR = './data'
RESULTS_DIR = './results'

# Encryption
ENABLE_ENCRYPTION = True
```

### Disable Encryption (For Comparison)

In `src/federated_learning/06_flower_server.py`:
```python
USE_ENCRYPTION = False
```

Then run pipeline without `--server-public-key` argument.

---

## Results Location

After running pipeline, find results in:

```
results/
├── models/               # Saved models
│   ├── autoencoder/
│   ├── node1_model.pkl
│   ├── node2_model.pkl
│   └── node3_model.pkl
├── metrics/              # CSV metrics
│   └── round_metrics.csv
├── plots/                # Visualizations
│   └── convergence.png
├── logs/                 # Log files
│   ├── server.log
│   ├── client_1.log
│   ├── client_2.log
│   └── client_3.log
└── keys/                 # Encryption keys
    └── server_public_key.bin
```

### View Metrics
```bash
# Linux/Mac
cat results/metrics/round_metrics.csv

# Windows PowerShell
Get-Content results/metrics/round_metrics.csv

# View in Excel/Sheets
# Open results/metrics/round_metrics.csv
```

### View Plots
```bash
# Windows
start results/plots/convergence.png

# Linux
xdg-open results/plots/convergence.png

# Mac
open results/plots/convergence.png
```

---

## Troubleshooting

### Issue: "Data files not found"
```bash
# Ensure data/raw/ has CSV files
ls data/raw/
# Should show: 1.benign.csv, 1.gafgyt.*.csv, etc.

# Then run:
python src/data_pipeline/01_load_clean_data.py
```

### Issue: "Port 8080 already in use"
```bash
# Find process using port
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # Linux/Mac

# Or change port in src/federated_learning/06_flower_server.py:
SERVER_ADDRESS = "0.0.0.0:8081"
```

### Issue: "Decryption failed"
```bash
# Ensure all clients use same public key file:
--server-public-key results/keys/server_public_key.bin

# And that server has generated keys:
# (Should appear in logs: "[CRYPTO] Public key saved to:")
```

### Issue: Out of memory
```bash
# Reduce batch size in configs/config.py:
BATCH_SIZE = 16  # Lower from 32

# Or use subset of data in step 1
```

---

## Performance Tips

### Speed Up
- Reduce `NUM_ROUNDS` to 5
- Reduce `NUM_EPOCHS` to 5
- Use smaller `BATCH_SIZE` (16)
- Skip optional models (steps 3-4)

### Improve Accuracy
- Increase `NUM_ROUNDS` to 20
- Increase `NUM_EPOCHS` to 20
- Use larger `BATCH_SIZE` (64)
- Use GPU if available

### Clean Restart
```bash
# Remove all results
rm -r results/  # Linux/Mac
Remove-Item results -Recurse -Force  # Windows PowerShell

# Restart pipeline
python src/federated_learning/07_launch_federation.py
```

---

## Next Steps

1. **Setup:** Follow this guide Step 1-2
2. **Run:** Execute Step 7 (Recommended) or Step 5-6
3. **Analyze:** Run Step 7 for visualization
4. **Understand:** Read `docs/README_ARCHITECTURE.md`
5. **Experiment:** Modify `configs/config.py` and re-run

---

**Ready to start?** Run this command:
```bash
python src/federated_learning/07_launch_federation.py
```

For detailed information, see `docs/README_USAGE.md`
