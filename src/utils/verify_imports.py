"""
Environment Verification Script
================================
Verifies all required packages are installed and imports are working correctly.
Run this script after installing dependencies to confirm setup is complete.
"""

import sys
import importlib
from typing import Dict, List, Tuple


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def print_section(title: str):
    """Print formatted section."""
    print(f"\n{title}")
    print("-" * 70)


def check_python_version():
    """Check Python version compatibility."""
    print_section("Python Version Check")
    
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    print(f"Python Executable: {sys.executable}")
    
    # Check if Python 3.10 or higher
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("[!] WARNING: Python 3.10+ is recommended for this project")
        return False
    else:
        print("[OK] Python version is compatible")
        return True


def verify_package_import(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    Verify a package can be imported.
    
    Args:
        package_name: Name of the package (used for display)
        import_name: Name to import (defaults to package_name if not provided)
    
    Returns:
        Tuple of (success: bool, version: str)
    """
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError as e:
        return False, str(e)


def main():
    """Main verification routine."""
    print_header("FEDERATED LEARNING ENVIRONMENT VERIFICATION")
    
    # Check Python version
    py_version_ok = check_python_version()
    
    # Define packages to verify
    packages = [
        ("NumPy", "numpy"),
        ("Pandas", "pandas"),
        ("Scikit-Learn", "sklearn"),
        ("Matplotlib", "matplotlib"),
        ("Seaborn", "seaborn"),
        ("Flower (FLWR)", "flwr"),
        ("PQCrypto", "pqcrypto"),
    ]
    
    # Verify imports
    print_section("Package Imports Verification")
    
    results: Dict[str, Tuple[bool, str]] = {}
    all_imports_ok = True
    
    for package_display_name, import_name in packages:
        success, version = verify_package_import(package_display_name, import_name)
        results[package_display_name] = (success, version)
        
        if success:
            print(f"[OK] {package_display_name:20} v{version}")
        else:
            print(f"[XX] {package_display_name:20} FAILED - {version}")
            all_imports_ok = False
    
    # Detailed import tests
    print_section("Detailed Import Tests")
    
    # NumPy
    if results["NumPy"][0]:
        try:
            import numpy as np
            arr = np.array([1, 2, 3])
            print(f"[OK] NumPy: Array creation successful - {arr}")
        except Exception as e:
            print(f"[XX] NumPy: Array creation failed - {e}")
            all_imports_ok = False
    
    # Pandas
    if results["Pandas"][0]:
        try:
            import pandas as pd
            df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            print(f"[OK] Pandas: DataFrame creation successful - shape {df.shape}")
        except Exception as e:
            print(f"[XX] Pandas: DataFrame creation failed - {e}")
            all_imports_ok = False
    
    # Scikit-Learn
    if results["Scikit-Learn"][0]:
        try:
            from sklearn.model_selection import train_test_split
            from sklearn.ensemble import RandomForestClassifier
            print("[OK] Scikit-Learn: Core modules imported successfully")
        except Exception as e:
            print(f"[XX] Scikit-Learn: Import failed - {e}")
            all_imports_ok = False
    
    # Matplotlib
    if results["Matplotlib"][0]:
        try:
            import matplotlib.pyplot as plt
            print("[OK] Matplotlib: pyplot module imported successfully")
        except Exception as e:
            print(f"[XX] Matplotlib: Import failed - {e}")
            all_imports_ok = False
    
    # Seaborn
    if results["Seaborn"][0]:
        try:
            import seaborn as sns
            print("[OK] Seaborn: Module imported successfully")
        except Exception as e:
            print(f"[XX] Seaborn: Import failed - {e}")
            all_imports_ok = False
    
    # Flower
    if results["Flower (FLWR)"][0]:
        try:
            import flwr as fl
            print(f"[OK] Flower: Federated learning framework ready")
        except Exception as e:
            print(f"[XX] Flower: Import failed - {e}")
            all_imports_ok = False
    
    # PQCrypto
    if results["PQCrypto"][0]:
        try:
            import pqcrypto
            print("[OK] PQCrypto: Post-quantum cryptography module imported")
        except Exception as e:
            print(f"[XX] PQCrypto: Import failed - {e}")
            all_imports_ok = False
    
    # Summary
    print_header("SUMMARY")
    
    missing_packages = [pkg for pkg, (success, _) in results.items() if not success]
    
    if all_imports_ok and py_version_ok:
        print("\n[OK] ALL CHECKS PASSED!")
        print("\nYour environment is ready for federated learning development.")
        print("You can proceed with:")
        print("  - Data preparation (prepare_datasets.py)")
        print("  - Flower server/client setup")
        print("  - Model training and evaluation")
        return 0
    else:
        print("\n[XX] SOME CHECKS FAILED")
        if missing_packages:
            print(f"\nMissing or failed packages: {', '.join(missing_packages)}")
            print("\nRun the following to install missing packages:")
            print(f"  pip install {' '.join([pkg.lower() for pkg in missing_packages])}")
        if not py_version_ok:
            print("\nPlease upgrade Python to version 3.10 or higher")
        return 1


if __name__ == "__main__":
    exit_code = main()
    print("\n" + "=" * 70 + "\n")
    sys.exit(exit_code)
