# Quick Reference Card

## 🚀 START HERE

### One-Line Command to Run Everything
```bash
python src/federated_learning/07_launch_federation.py
```

**This will:**
- ✅ Load and clean data
- ✅ Partition for 3 nodes
- ✅ Start encrypted server
- ✅ Launch 3 clients
- ✅ Run 10 FL rounds
- ✅ Save results

**Time:** 5-10 minutes

---

## 📁 Project Structure (Clean)

```
src/                          ← MAIN SOURCE CODE
├── data_pipeline/            [Steps 01-02: Data]
├── models/                   [Steps 03-04: Training]
├── federated_learning/       [Steps 05-07: FL]
├── crypto/                   [Encryption]
└── utils/                    [Utilities]

data/                         ← DATASETS
├── raw/                      [Original files]
├── processed/                [Cleaned]
└── partitioned/              [For FL]

results/                      ← GENERATED OUTPUTS
├── models/
├── metrics/
├── plots/
├── logs/
└── keys/

configs/                      ← CONFIGURATION
docs/                         ← DOCUMENTATION
tests/                        ← TESTS
```

---

## 📚 Documentation Files

| File | Purpose | Read Time |
|------|---------|-----------|
| `README.md` | Project overview | 5 min |
| `PIPELINE_GUIDE.md` | Execution steps | 10 min |
| `PROJECT_STRUCTURE.md` | Layout details | 10 min |
| `docs/README_SETUP.md` | Installation | 10 min |
| `docs/README_USAGE.md` | Usage guide | 15 min |
| `docs/README_ARCHITECTURE.md` | System design | 20 min |
| `docs/README_CRYPTO.md` | Cryptography | 15 min |
| `CHANGELOG.md` | Version history | 5 min |
| `CLEANUP_SUMMARY.md` | What changed | 10 min |

**Total reading:** ~90 minutes (comprehensive)  
**Quick start:** `PIPELINE_GUIDE.md` (10 minutes)

---

## 🔧 Common Commands

### Verify Setup
```bash
python src/utils/verify_imports.py
```

### Prepare Data
```bash
python src/data_pipeline/01_load_clean_data.py
python src/data_pipeline/02_preprocess_and_partition.py
```

### Run Federated Learning
```bash
# Automatic (RECOMMENDED)
python src/federated_learning/07_launch_federation.py

# Or manual:
python src/federated_learning/06_flower_server.py
python src/federated_learning/05_flower_client.py --node-id 1 --server localhost:8080 --server-public-key results/keys/server_public_key.bin
python src/federated_learning/05_flower_client.py --node-id 2 --server localhost:8080 --server-public-key results/keys/server_public_key.bin
python src/federated_learning/05_flower_client.py --node-id 3 --server localhost:8080 --server-public-key results/keys/server_public_key.bin
```

### View Results
```bash
python src/utils/plot_convergence.py
cat results/metrics/round_metrics.csv
```

### Run Tests
```bash
python -m pytest tests/ -v
```

---

## 🔐 Security Features

| Feature | Details |
|---------|---------|
| **Encryption** | RSA-4096 + AES-256-GCM |
| **Authentication** | GCM tag verification |
| **Key Derivation** | HKDF-SHA256 |
| **Overhead** | 0.52% (negligible) |
| **Post-Quantum** | Kyber768 ready (Linux) |

---

## 📊 Expected Results

| Metric | Expected Value |
|--------|-----------------|
| Final Accuracy | >85% |
| Rounds | 10 |
| Per-round Time | 30-60s |
| Encryption Overhead | 1-2% |
| Total Runtime | 5-10 min |

---

## ⚙️ Configuration

Edit `configs/config.py` to change:
- Model architecture
- Training parameters
- Batch size
- Learning rate
- Number of rounds
- Encryption settings

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Data not found" | Run `01_load_clean_data.py` first |
| "Port in use" | Change `SERVER_ADDRESS` in `06_flower_server.py` |
| "Import error" | Run `python src/utils/verify_imports.py` |
| "Decryption failed" | Ensure same public key file used by all clients |
| "Out of memory" | Reduce `BATCH_SIZE` in `configs/config.py` |

---

## 📈 Pipeline Steps

```
[1] Load & Clean        python src/data_pipeline/01_load_clean_data.py
     ↓
[2] Partition           python src/data_pipeline/02_preprocess_and_partition.py
     ↓
[3] Train Autoencoder   python src/models/03_train_autoencoder.py (optional)
     ↓
[4] Train Models        python src/models/04_train_node_model.py (optional)
     ↓
[5] FL Server           python src/federated_learning/06_flower_server.py
     ↓
[6] FL Clients          python src/federated_learning/05_flower_client.py (×3)
     ↓
[7] Visualize           python src/utils/plot_convergence.py
```

**RECOMMENDED:** Use `07_launch_federation.py` to run all at once

---

## 📂 Results Location

After running pipeline:

```
results/
├── models/
│   ├── autoencoder/        [Saved autoencoder]
│   ├── node1_model.pkl     [Node 1 model]
│   ├── node2_model.pkl     [Node 2 model]
│   └── node3_model.pkl     [Node 3 model]
├── metrics/
│   └── round_metrics.csv   [IMPORTANT: Per-round accuracy]
├── plots/
│   └── convergence.png     [Training curves]
├── logs/
│   ├── server.log
│   ├── client_1.log
│   ├── client_2.log
│   └── client_3.log
└── keys/
    └── server_public_key.bin [Encryption key]
```

---

## 🎯 Quick Decision Tree

**I want to...**

- **Run everything:** `python src/federated_learning/07_launch_federation.py`
- **Understand the system:** Read `docs/README_ARCHITECTURE.md`
- **Learn how to use it:** Read `PIPELINE_GUIDE.md`
- **Customize settings:** Edit `configs/config.py`
- **Check encryption:** Read `docs/README_CRYPTO.md`
- **Fix an issue:** Check `docs/README_SETUP.md` or `PIPELINE_GUIDE.md`
- **See what changed:** Read `CLEANUP_SUMMARY.md`
- **Run tests:** `python -m pytest tests/`

---

## 🔄 Full Workflow

```
1. Setup
   └─ python -m venv .venv
   └─ .venv\Scripts\activate (Windows) or source .venv/bin/activate
   └─ pip install -r requirements.txt

2. Verify
   └─ python src/utils/verify_imports.py

3. Prepare
   └─ python src/data_pipeline/01_load_clean_data.py
   └─ python src/data_pipeline/02_preprocess_and_partition.py

4. Train
   └─ python src/federated_learning/07_launch_federation.py

5. Analyze
   └─ python src/utils/plot_convergence.py
   └─ cat results/metrics/round_metrics.csv
```

**Total time:** ~30 minutes (including waiting)

---

## 💡 Tips

- **Speed up:** Use smaller `NUM_ROUNDS`, `NUM_EPOCHS`, `BATCH_SIZE`
- **Better accuracy:** Use larger `NUM_ROUNDS`, `NUM_EPOCHS`
- **Clean restart:** `rm -r results/` then re-run
- **Compare:** Disable encryption in `06_flower_server.py` (set `USE_ENCRYPTION = False`)
- **Debug:** Check logs in `results/logs/`
- **Scale:** Add more clients by modifying launcher

---

## 🚀 Next Steps

1. **Read:** `PIPELINE_GUIDE.md` (10 min)
2. **Run:** `python src/federated_learning/07_launch_federation.py` (10 min)
3. **Analyze:** `python src/utils/plot_convergence.py`
4. **Experiment:** Modify `configs/config.py` and re-run

---

## 📞 Need Help?

| Question | Answer |
|----------|--------|
| How do I start? | Read `PIPELINE_GUIDE.md` |
| What's the structure? | See `PROJECT_STRUCTURE.md` |
| How does it work? | Read `docs/README_ARCHITECTURE.md` |
| What was cleaned? | See `CLEANUP_SUMMARY.md` |
| How do I encrypt? | Read `docs/README_CRYPTO.md` |
| Setup issues? | Check `docs/README_SETUP.md` |
| Usage questions? | See `docs/README_USAGE.md` |

---

## ✅ Pre-Flight Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Imports verified (`python src/utils/verify_imports.py`)
- [ ] Data downloaded (in `data/raw/`)
- [ ] Configuration reviewed (`configs/config.py`)
- [ ] Ready to run: `python src/federated_learning/07_launch_federation.py`

---

**You're all set! Start with:**
```bash
python src/federated_learning/07_launch_federation.py
```

🎉 **Good luck!**
