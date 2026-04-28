"""Post-quantum cryptography utilities."""
from pathlib import Path

# Import main functions for easy access
try:
    from crypto_layer import (
        generate_keypair,
        encrypt_weights,
        decrypt_weights,
        benchmark_crypto,
        PostQuantumCrypto
    )
except ImportError:
    # If running from different location
    pass
