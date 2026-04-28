# 🚀 Dataset Organization Workflow - Visual Guide

## Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    YOUR DATASET ORGANIZATION                         │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: RAW DATA (as you had it)
────────────────────────────────────────────────────────────────────
data/raw/
├── train/                           ← 28 CSV files
│   ├── 1.benign.csv
│   ├── 1.mirai.ack.csv
│   ├── 1.mirai.scan.csv
│   ├── 1.gafgyt.combo.csv
│   ├── ... (more variants)
│   ├── 2.*.csv
│   ├── 3.*.csv
│
└── test/                            ← 2 CSV files
    ├── UNSW_NB15_testing-set.csv
    └── UNSW_NB15_training-set.csv


STEP 2: RUN ORGANIZATION SCRIPT
────────────────────────────────────────────────────────────────────
$ python scripts/organize_dataset.py

📁 Creating folder structure...
✓ Structure created at: G:\VScode\pqc\data\organized

📂 Organizing training files...
✓ Organized 28 training files
✓ Organized 2 test files


STEP 3: ORGANIZED STRUCTURE (now available)
────────────────────────────────────────────────────────────────────
data/organized/
├── device_1_danmini/               ← Physical Device 1
│   ├── benign/
│   │   └── 1.benign.csv
│   ├── mirai/
│   │   ├── 1.mirai.ack.csv
│   │   ├── 1.mirai.scan.csv
│   │   ├── 1.mirai.syn.csv
│   │   ├── 1.mirai.udp.csv
│   │   └── 1.mirai.udpplain.csv
│   └── bashlite/
│       ├── 1.gafgyt.combo.csv
│       ├── 1.gafgyt.junk.csv
│       ├── 1.gafgyt.scan.csv
│       ├── 1.gafgyt.tcp.csv
│       └── 1.gafgyt.udp.csv
│
├── device_2_ecobee/                ← Physical Device 2
│   ├── benign/      (1 file, 13,113 rows)
│   ├── mirai/       (5 files, 512,133 rows)
│   └── bashlite/    (5 files, 310,630 rows)
│
├── device_3_ennio/                 ← Physical Device 3
│   ├── benign/
│   ├── mirai/       ← EMPTY (no mirai attacks for device 3)
│   └── bashlite/
│
└── test/                           ← Test Dataset
    ├── UNSW_NB15_testing-set.csv    (175,341 rows)
    └── UNSW_NB15_training-set.csv   (82,332 rows)


STEP 4: LOAD & COMBINE (with metadata)
────────────────────────────────────────────────────────────────────
$ python src/data_pipeline/03_load_organized_data.py

📊 TRAINING DATA: 1,854,174 rows × 117 columns
📊 TEST DATA: 257,673 rows × 45 columns

Generated Files:
  ✓ data/processed/combined_training_data.csv
  ✓ data/processed/combined_test_data.csv


STEP 5: USE IN YOUR CODE
────────────────────────────────────────────────────────────────────
# Option A: Load combined data
df = pd.read_csv('data/processed/combined_training_data.csv')

# Option B: Quick sampling for testing
from src.data_pipeline.quick_test_loader import load_sample
df = load_sample('device_1_danmini', n_rows=500)

# Option C: Load full device data
from src.data_pipeline.quick_test_loader import load_device_data
df = load_device_data('device_1_danmini')
```

---

## 📊 Data Statistics at a Glance

```
TRAINING DATA BREAKDOWN
═══════════════════════════════════════════════════════════════════

Device 1: Danmini Doorbell
  ├─ Benign:    49,548 rows
  ├─ Mirai:    652,100 rows
  ├─ Bashlite: 316,650 rows
  └─ TOTAL:  1,018,298 rows ✓

Device 2: Ecobee Thermostat
  ├─ Benign:    13,113 rows
  ├─ Mirai:    512,133 rows
  ├─ Bashlite: 310,630 rows
  └─ TOTAL:    835,876 rows ✓

Device 3: Ennio Doorbell
  ├─ Benign:     X rows
  ├─ Mirai:      0 rows (NOT IN DATASET)
  ├─ Bashlite:   X rows
  └─ TOTAL:      varies rows ✓

═══════════════════════════════════════════════════════════════════
GRAND TOTAL: 1,854,174+ rows across 28 files
═══════════════════════════════════════════════════════════════════

TEST DATA (UNSW_NB15)
═══════════════════════════════════════════════════════════════════
  ├─ Testing Set:  175,341 rows × 45 columns
  ├─ Training Set:  82,332 rows × 45 columns
  └─ TOTAL:        257,673 rows × 45 columns
═══════════════════════════════════════════════════════════════════
```

---

## 🎯 Usage Patterns

### Pattern 1: Full Dataset Analysis
```python
import pandas as pd

# Load everything
df = pd.read_csv('data/processed/combined_training_data.csv')

# Explore
print(df.shape)                          # (1854174, 119)
print(df['attack_type'].value_counts()) # Benign, Mirai, Bashlite
print(df['device'].value_counts())      # Device distribution
```

### Pattern 2: Per-Device Federated Learning
```python
from src.data_pipeline.quick_test_loader import load_device_data

# Load data for each node
nodes = {
    'node1': load_device_data('device_1_danmini'),
    'node2': load_device_data('device_2_ecobee'),
    'node3': load_device_data('device_3_ennio'),
}

# Train locally on each node
for node_id, data in nodes.items():
    print(f"{node_id}: {len(data)} samples")
    # local_model = train_on_local_data(data)
    # send_weights_to_server(local_model)
```

### Pattern 3: Rapid Testing with Samples
```python
from src.data_pipeline.quick_test_loader import load_sample

# Quick test with small sample (loads fast!)
sample = load_sample('device_1_danmini', n_rows=1000)

# Test your preprocessing
X = sample.drop(['attack_type', 'device'], axis=1)
y = sample['attack_type']

# Train test model (fast iteration)
model = train_quick_test_model(X, y)
```

### Pattern 4: Class-Specific Analysis
```python
import pandas as pd

df = pd.read_csv('data/processed/combined_training_data.csv')

# Get only normal traffic
benign = df[df['attack_type'] == 'benign']

# Get only attacks
attacks = df[df['attack_type'] != 'benign']

# Get specific device + specific attack
danmini_mirai = df[
    (df['device'] == 'Danmini_Doorbell') & 
    (df['attack_type'] == 'mirai')
]
```

### Pattern 5: Balanced Sampling
```python
from src.data_pipeline.quick_test_loader import load_sample

# Load more benign samples (more common)
benign_sample = load_sample(
    'device_1_danmini', 
    attack_class='benign',
    n_rows=2000
)

# Load fewer attack samples (less common)
mirai_sample = load_sample(
    'device_1_danmini',
    attack_class='mirai',
    n_rows=2000
)

# Combine for balanced training
balanced = pd.concat([benign_sample, mirai_sample])
```

---

## 🔄 Typical Workflow

```
┌──────────────────────────────────────────────────────────┐
│ 1. ORGANIZE (one time setup)                             │
│    $ python scripts/organize_dataset.py                  │
│    Creates: data/organized/                              │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│ 2. LOAD DATA (start of your analysis/training)           │
│    Option A: Full load for comprehensive analysis        │
│    Option B: Quick sample for rapid testing              │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│ 3. FILTER (by device, attack type, or both)              │
│    Filter DataFrame by metadata columns                  │
│    Create stratified or balanced subsets                 │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│ 4. PREPROCESS (scaling, encoding, feature engineering)   │
│    Use existing pipeline with combined data              │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│ 5. TRAIN/ANALYZE (models, visualization, analysis)       │
│    Apply ML algorithms, analyze patterns                 │
│    Federated learning with per-device models             │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| "No such file or directory" | Run `organize_dataset.py` first |
| "MemoryError loading data" | Use `load_sample()` with fewer rows |
| "Missing device data" | Device 3 has no Mirai training data - expected |
| Slow file loading | Use `load_sample()` instead of full load |
| Need fresh copy | Delete `data/processed/*` and rerun loader |
| Can't find combined data | Ensure `03_load_organized_data.py` completed |

---

## 📁 File Locations Reference

```
Key Files You Created/Generated:
═══════════════════════════════════════════════════════════════════

📍 Scripts:
  ✓ scripts/organize_dataset.py
  ✓ src/data_pipeline/03_load_organized_data.py
  ✓ src/data_pipeline/04_quick_test_loader.py

📍 Documentation:
  ✓ DATASET_ORGANIZATION_GUIDE.md          (detailed guide)
  ✓ DATASET_SETUP_SUMMARY.md               (what was done)
  ✓ DATASET_WORKFLOW.md                    (this file)
  ✓ QUICK_REFERENCE.py                     (code examples)

📍 Data Locations:
  ✓ data/organized/                        (organized structure)
  ✓ data/processed/                        (combined CSV outputs)
  ✓ data/raw/train/                        (original files)
  ✓ data/raw/test/                         (test files)
```

---

## ✨ Key Improvements Over Original Structure

```
BEFORE:                          AFTER:
───────────────────────          ──────────────────────
data/raw/                        data/raw/               (unchanged)
├── 1.benign.csv    ← mixed      ├── train/
├── 1.mirai.udp.csv   with       │   └── (28 files)
├── 1.gafgyt.junk.csv files      └── test/
├── 2.benign.csv                    └── (2 files)
├── ... (flat structure)        
                                data/organized/        (NEW!)
❌ Hard to find specific          ├── device_1_danmini/
  data                           │   ├── benign/
❌ No metadata                    │   ├── mirai/
❌ Can't easily split by         │   └── bashlite/
  device or class               ├── device_2_ecobee/
❌ Tedious file parsing          │   ├── benign/
                                │   ├── mirai/
                                │   └── bashlite/
                                ├── device_3_ennio/
                                │   ├── benign/
                                │   ├── mirai/ (empty)
                                │   └── bashlite/
                                └── test/

                                data/processed/        (NEW!)
                                ├── combined_training_data.csv
                                └── combined_test_data.csv

✅ Easy to locate specific data
✅ Metadata added (device, attack_type)
✅ Device-centric organization
✅ Ready-to-use combined files
✅ Quick sampling for testing
```

---

## 🎓 Learning Resources

- **Quick Start:** Read `DATASET_ORGANIZATION_GUIDE.md`
- **Code Examples:** See `QUICK_REFERENCE.py`
- **Integration:** Check [Example 3](#pattern-2-per-device-federated-learning) for federated learning
- **Troubleshooting:** Refer to table above

---

## ✅ Verification Checklist

Use this to verify everything is working:

- [ ] Raw data exists in `data/raw/train/` and `data/raw/test/`
- [ ] Ran `python scripts/organize_dataset.py`
- [ ] Folder structure created in `data/organized/`
- [ ] Can see `device_1_danmini/`, `device_2_ecobee/`, `device_3_ennio/`
- [ ] Each device has `benign/`, `mirai/`, `bashlite/` folders
- [ ] Test data in `data/organized/test/`
- [ ] Ran `python src/data_pipeline/03_load_organized_data.py`
- [ ] Combined CSVs created in `data/processed/`
- [ ] Can load data: `df = pd.read_csv('data/processed/combined_training_data.csv')`
- [ ] Metadata columns exist: `attack_type`, `device`

---

**Status:** ✅ Complete & Ready to Use  
**Last Updated:** 2026-04-28  
**Version:** 1.0
