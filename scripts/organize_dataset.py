"""
Dataset Organization Script
Organizes raw dataset into structured folders by device and attack type
"""

import os
import shutil
from pathlib import Path

# ----------------------------
# CONFIG
# ----------------------------
PROJECT_ROOT = Path(__file__).parent.parent
RAW_TRAIN_DIR = PROJECT_ROOT / "data" / "raw" / "train"
RAW_TEST_DIR = PROJECT_ROOT / "data" / "raw" / "test"
ORG_DIR = PROJECT_ROOT / "data" / "organized"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Device mapping (based on filename prefix: 1, 2, 3)
DEVICE_MAP = {
    "1": "device_1_danmini",
    "2": "device_2_ecobee",
    "3": "device_3_ennio"
}

# Attack class categories
ATTACK_CLASSES = ["benign", "mirai", "bashlite"]


# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def get_class(filename):
    """
    Determine attack class from filename
    Example: 1.mirai.udp.csv → 'mirai'
    """
    if "benign" in filename:
        return "benign"
    elif "mirai" in filename:
        return "mirai"
    elif "gafgyt" in filename:
        return "bashlite"
    else:
        return None


def create_structure():
    """Create organized folder structure for training data"""
    print("📁 Creating folder structure...")
    for device in DEVICE_MAP.values():
        for cls in ATTACK_CLASSES:
            path = ORG_DIR / device / cls
            path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Structure created at: {ORG_DIR}")


def organize_training_files():
    """Organize training files from raw/train to organized"""
    print("\n📂 Organizing training files...")
    
    count = 0
    for file in os.listdir(RAW_TRAIN_DIR):
        if not file.endswith(".csv"):
            continue

        # Parse filename: Example: 1.mirai.udp.csv → device_id=1, class=mirai
        parts = file.split(".")
        device_id = parts[0]

        # Skip if device not in mapping
        if device_id not in DEVICE_MAP:
            print(f"⚠ Skipping {file}: device '{device_id}' not in DEVICE_MAP")
            continue

        device_name = DEVICE_MAP[device_id]
        cls = get_class(file)

        if cls is None:
            print(f"⚠ Skipping {file}: couldn't determine class")
            continue

        src_path = RAW_TRAIN_DIR / file
        dest_path = ORG_DIR / device_name / cls / file

        try:
            shutil.copy2(src_path, dest_path)
            count += 1
            print(f"  ✓ {file} → {device_name}/{cls}/")
        except Exception as e:
            print(f"  ✗ Error copying {file}: {e}")

    print(f"✓ Organized {count} training files")


def organize_test_files():
    """Organize test files"""
    print("\n📂 Organizing test files...")
    
    test_org_dir = ORG_DIR / "test"
    test_org_dir.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for file in os.listdir(RAW_TEST_DIR):
        if not file.endswith(".csv"):
            continue
        
        src_path = RAW_TEST_DIR / file
        dest_path = test_org_dir / file
        
        try:
            shutil.copy2(src_path, dest_path)
            count += 1
            print(f"  ✓ {file} → test/")
        except Exception as e:
            print(f"  ✗ Error copying {file}: {e}")
    
    print(f"✓ Organized {count} test files")


def print_summary():
    """Print directory structure summary"""
    print("\n" + "="*60)
    print("📊 DIRECTORY STRUCTURE SUMMARY")
    print("="*60)
    
    print("\n📍 Training Data Structure:")
    for device in DEVICE_MAP.values():
        device_path = ORG_DIR / device
        if device_path.exists():
            print(f"\n  {device}/")
            for cls in ATTACK_CLASSES:
                cls_path = device_path / cls
                if cls_path.exists():
                    file_count = len(list(cls_path.glob("*.csv")))
                    print(f"    ├── {cls}/ ({file_count} files)")
    
    print("\n📍 Test Data Structure:")
    test_path = ORG_DIR / "test"
    if test_path.exists():
        file_count = len(list(test_path.glob("*.csv")))
        print(f"  test/ ({file_count} files)")
    
    print("\n" + "="*60)


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    print("🚀 Starting dataset organization...\n")
    
    try:
        create_structure()
        organize_training_files()
        organize_test_files()
        print_summary()
        print("\n✅ Dataset organization complete!")
        print(f"📁 Output location: {ORG_DIR}")
        
    except Exception as e:
        print(f"\n❌ Error during organization: {e}")
        raise
