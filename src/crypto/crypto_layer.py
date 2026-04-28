"""
Post-Quantum Cryptography Layer for Federated Learning
=======================================================

This module provides post-quantum secure communication for federated learning systems
using NIST-standardized algorithms (Kyber, NTRU-Prime, etc.) via liboqs-python.

Key functions:
- generate_keypair(): Generate PQC key pair
- encrypt_weights(): Encrypt model weights (numpy arrays)
- decrypt_weights(): Decrypt model weights
- benchmark_crypto(): Performance benchmarking

Example:
    >>> from crypto_layer import generate_keypair, encrypt_weights, decrypt_weights
    >>> import numpy as np
    >>>
    >>> # Generate keypair
    >>> public_key, private_key = generate_keypair()
    >>>
    >>> # Create and encrypt weights
    >>> weights = np.random.randn(256, 128).astype(np.float32)
    >>> encrypted = encrypt_weights(weights, public_key)
    >>>
    >>> # Decrypt weights
    >>> decrypted = decrypt_weights(encrypted, private_key)
    >>> assert np.allclose(weights, decrypted)
"""

import os
import time
import pickle
import logging
from typing import Tuple, Dict, Any
from pathlib import Path

import numpy as np
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Try to import liboqs (NIST-standardized post-quantum algorithms)
try:
    import liboqs
    HAS_LIBOQS = True
    AVAILABLE_ALGORITHMS = liboqs.get_enabled_kem_mechanisms()
except ImportError:
    HAS_LIBOQS = False
    AVAILABLE_ALGORITHMS = []

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostQuantumCrypto:
    """
    Post-quantum cryptography handler for federated learning.
    
    Uses NIST-standardized algorithms via liboqs for key encapsulation.
    Falls back to RSA-4096 hybrid encryption if liboqs unavailable.
    """

    # Supported algorithms in preference order
    ALGORITHM_PREFERENCES = [
        'Kyber768',      # NIST recommended (ML-KEM)
        'Kyber512',      # Lighter version
        'NTRU-Prime-857',  # Alternative NIST standard
    ]

    # AES-256 parameters for symmetric encryption
    AES_KEY_SIZE = 32  # 256 bits
    AES_TAG_SIZE = 16  # 128 bits for GCM authentication
    
    # RSA parameters for fallback
    RSA_KEY_SIZE = 4096  # Post-quantum resilient RSA size

    def __init__(self, algorithm: str = None, use_fallback: bool = True):
        """
        Initialize the cryptography layer.

        Args:
            algorithm: KEM algorithm to use. If None, auto-selects from preferences.
            use_fallback: If True and liboqs unavailable, use RSA-4096 hybrid encryption

        Raises:
            ImportError: If liboqs not available and use_fallback=False
        """
        self.use_fallback = use_fallback
        
        if HAS_LIBOQS:
            # Select algorithm
            self.algorithm = self._select_algorithm(algorithm)
            self.crypto_mode = 'liboqs'
            logger.info(f"Using algorithm: {self.algorithm} (liboqs)")
        elif use_fallback:
            self.algorithm = 'RSA-4096'
            self.crypto_mode = 'rsa_hybrid'
            logger.warning(f"liboqs unavailable, using fallback: RSA-4096 hybrid encryption")
        else:
            raise ImportError(
                "liboqs-python is required and unavailable. "
                "Install with: pip install liboqs-python"
            )

    def _select_algorithm(self, requested: str = None) -> str:
        """
        Select the best available post-quantum algorithm.

        Args:
            requested: Specific algorithm to use (optional)

        Returns:
            Selected algorithm name
        """
        if requested:
            if requested in AVAILABLE_ALGORITHMS:
                return requested
            logger.warning(f"Algorithm '{requested}' not available, auto-selecting")

        # Find first available from preferences
        for algo in self.ALGORITHM_PREFERENCES:
            if algo in AVAILABLE_ALGORITHMS:
                logger.info(f"Auto-selected algorithm: {algo}")
                return algo

        # Fallback to first available
        if AVAILABLE_ALGORITHMS:
            algo = AVAILABLE_ALGORITHMS[0]
            logger.info(f"Fallback to available algorithm: {algo}")
            return algo

        raise RuntimeError("No post-quantum KEM algorithms available in liboqs")

    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate a post-quantum cryptographic keypair.

        Returns:
            Tuple of (public_key_bytes, private_key_bytes)
        """
        if self.crypto_mode == 'liboqs':
            return self._generate_keypair_liboqs()
        else:
            return self._generate_keypair_rsa()

    def _generate_keypair_liboqs(self) -> Tuple[bytes, bytes]:
        """Generate keypair using liboqs."""
        logger.debug(f"Generating keypair with {self.algorithm} (liboqs)...")

        # Create KEM instance
        kem = liboqs.KeyEncapsulation(self.algorithm)

        # Generate keypair
        public_key = kem.generate_keypair()
        private_key = kem.export_secret_key()

        logger.debug(f"Keypair generated: public_key={len(public_key)}B, "
                    f"private_key={len(private_key)}B")

        return public_key, private_key

    def _generate_keypair_rsa(self) -> Tuple[bytes, bytes]:
        """Generate keypair using RSA-4096."""
        logger.debug(f"Generating keypair with RSA-4096...")

        # Generate RSA keypair
        private_key_obj = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.RSA_KEY_SIZE,
            backend=default_backend()
        )
        public_key_obj = private_key_obj.public_key()

        # Serialize to PEM format
        private_pem = private_key_obj.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = public_key_obj.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        logger.debug(f"Keypair generated: public_key={len(public_pem)}B, "
                    f"private_key={len(private_pem)}B")

        return public_pem, private_pem

    def _derive_symmetric_key(self, shared_secret: bytes) -> Tuple[bytes, bytes]:
        """
        Derive AES-256 key and IV from shared secret using HKDF.

        Args:
            shared_secret: KEM shared secret

        Returns:
            Tuple of (aes_key, iv)
        """
        # Derive 48 bytes: 32 for AES key + 16 for IV
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=48,
            salt=b'fedlearn_aes_v1',
            info=b'encryption_key',
            backend=default_backend()
        )
        derived = hkdf.derive(shared_secret)

        aes_key = derived[:32]
        iv = derived[32:48]

        return aes_key, iv

    def encrypt_weights(self, weights: np.ndarray, public_key: bytes) -> bytes:
        """
        Encrypt model weights using post-quantum cryptography.

        Process (liboqs mode):
        1. Serialize numpy array to bytes (pickle)
        2. Generate ephemeral shared secret via KEM
        3. Derive AES-256 key from shared secret
        4. Encrypt weights with AES-256-GCM
        5. Return: encapsulated_key || ciphertext || tag

        Process (RSA fallback mode):
        1. Serialize numpy array to bytes (pickle)
        2. Generate random AES-256 key
        3. Encrypt weights with AES-256-GCM
        4. Encrypt AES key with RSA-4096
        5. Return: encrypted_aes_key || iv || ciphertext || tag

        Args:
            weights: Numpy array of model weights
            public_key: Public key bytes from generate_keypair()

        Returns:
            Encrypted bytes

        Raises:
            TypeError: If weights is not a numpy array
            ValueError: If encryption fails
        """
        if not isinstance(weights, np.ndarray):
            raise TypeError(f"weights must be numpy array, got {type(weights)}")

        logger.debug(f"Encrypting weights: shape={weights.shape}, dtype={weights.dtype}")

        try:
            # 1. Serialize weights
            plaintext = pickle.dumps(weights, protocol=pickle.HIGHEST_PROTOCOL)
            logger.debug(f"Serialized: {len(plaintext)} bytes")

            if self.crypto_mode == 'liboqs':
                result = self._encrypt_weights_liboqs(plaintext, public_key)
            else:
                result = self._encrypt_weights_rsa(plaintext, public_key)

            logger.info(f"Encryption successful: {len(plaintext)}B → {len(result)}B "
                       f"({100*len(result)/len(plaintext):.1f}% overhead)")

            return result

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Encryption failed: {e}") from e

    def _encrypt_weights_liboqs(self, plaintext: bytes, public_key: bytes) -> bytes:
        """Encrypt using liboqs KEM."""
        # 2. Encapsulate with KEM
        kem = liboqs.KeyEncapsulation(self.algorithm, public_key)
        ciphertext, shared_secret = kem.encap_secret()
        logger.debug(f"KEM encapsulation: ciphertext={len(ciphertext)}B, "
                    f"shared_secret={len(shared_secret)}B")

        # 3. Derive symmetric key
        aes_key, iv = self._derive_symmetric_key(shared_secret)

        # 4. Encrypt plaintext with AES-256-GCM
        cipher = AESGCM(aes_key)
        encrypted_data = cipher.encrypt(iv, plaintext, None)

        logger.debug(f"AES-256-GCM encrypted: {len(encrypted_data)} bytes")

        # 5. Return: encapsulated_key || encrypted_data
        return ciphertext + encrypted_data

    def _encrypt_weights_rsa(self, plaintext: bytes, public_key_pem: bytes) -> bytes:
        """Encrypt using RSA-4096 hybrid encryption."""
        # Load public key
        public_key_obj = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )

        # Generate random AES key and IV
        aes_key = os.urandom(32)  # 256-bit key
        iv = os.urandom(16)  # 128-bit IV

        logger.debug(f"Generated: AES key=32B, IV=16B")

        # Encrypt plaintext with AES-256-GCM
        cipher = AESGCM(aes_key)
        encrypted_plaintext = cipher.encrypt(iv, plaintext, None)

        logger.debug(f"AES-256-GCM encrypted: {len(encrypted_plaintext)} bytes")

        # Encrypt AES key with RSA-4096-OAEP
        encrypted_aes_key = public_key_obj.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=b'fedlearn_aes_key'
            )
        )

        logger.debug(f"RSA-4096-OAEP encrypted AES key: {len(encrypted_aes_key)} bytes")

        # Return: encrypted_aes_key || iv || encrypted_plaintext
        return encrypted_aes_key + iv + encrypted_plaintext

    def decrypt_weights(self, encrypted_data: bytes, private_key: bytes) -> np.ndarray:
        """
        Decrypt model weights using post-quantum cryptography.

        Args:
            encrypted_data: Encrypted bytes from encrypt_weights()
            private_key: Private key bytes from generate_keypair()

        Returns:
            Decrypted numpy array

        Raises:
            ValueError: If decryption fails
        """
        logger.debug(f"Decrypting weights: {len(encrypted_data)} bytes")

        try:
            if self.crypto_mode == 'liboqs':
                result = self._decrypt_weights_liboqs(encrypted_data, private_key)
            else:
                result = self._decrypt_weights_rsa(encrypted_data, private_key)

            logger.info(f"Decryption successful: {len(encrypted_data)}B → "
                       f"{result.nbytes}B (shape={result.shape})")

            return result

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Decryption failed: {e}") from e

    def _decrypt_weights_liboqs(self, encrypted_data: bytes, private_key: bytes) -> np.ndarray:
        """Decrypt using liboqs KEM."""
        # Get encapsulated key size for this algorithm
        kem = liboqs.KeyEncapsulation(self.algorithm)
        encap_key_size = kem.details_kem["length_encapsulated_key"]

        # 1. Extract encapsulated key
        ciphertext = encrypted_data[:encap_key_size]
        encrypted_plaintext = encrypted_data[encap_key_size:]

        logger.debug(f"Extracted: encapsulated_key={len(ciphertext)}B, "
                    f"encrypted_plaintext={len(encrypted_plaintext)}B")

        # 2. Decapsulate with private key
        kem = liboqs.KeyEncapsulation(self.algorithm, private_key)
        shared_secret = kem.decap_secret(ciphertext)

        logger.debug(f"KEM decapsulation successful: shared_secret={len(shared_secret)}B")

        # 3. Derive symmetric key
        aes_key, iv = self._derive_symmetric_key(shared_secret)

        # 4. Decrypt with AES-256-GCM
        cipher = AESGCM(aes_key)
        plaintext = cipher.decrypt(iv, encrypted_plaintext, None)

        logger.debug(f"AES-256-GCM decrypted: {len(plaintext)} bytes")

        # 5. Deserialize to numpy array
        weights = pickle.loads(plaintext)

        if not isinstance(weights, np.ndarray):
            raise ValueError(f"Deserialized object is not numpy array: {type(weights)}")

        return weights

    def _decrypt_weights_rsa(self, encrypted_data: bytes, private_key_pem: bytes) -> np.ndarray:
        """Decrypt using RSA-4096 hybrid encryption."""
        # Load private key
        private_key_obj = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )

        # Get RSA key size to determine encrypted AES key length
        rsa_key_size = private_key_obj.key_size // 8  # Convert bits to bytes
        # For RSA-4096-OAEP, encrypted key size = key_size (512 bytes for 4096-bit key)
        encrypted_aes_key_size = rsa_key_size

        # 1. Extract components
        encrypted_aes_key = encrypted_data[:encrypted_aes_key_size]
        iv = encrypted_data[encrypted_aes_key_size:encrypted_aes_key_size + 16]
        encrypted_plaintext = encrypted_data[encrypted_aes_key_size + 16:]

        logger.debug(f"Extracted: encrypted_aes_key={len(encrypted_aes_key)}B, "
                    f"iv={len(iv)}B, encrypted_plaintext={len(encrypted_plaintext)}B")

        # 2. Decrypt AES key with RSA-4096-OAEP
        aes_key = private_key_obj.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=b'fedlearn_aes_key'
            )
        )

        logger.debug(f"RSA-4096-OAEP decrypted AES key: {len(aes_key)} bytes")

        # 3. Decrypt plaintext with AES-256-GCM
        cipher = AESGCM(aes_key)
        plaintext = cipher.decrypt(iv, encrypted_plaintext, None)

        logger.debug(f"AES-256-GCM decrypted: {len(plaintext)} bytes")

        # 4. Deserialize to numpy array
        weights = pickle.loads(plaintext)

        if not isinstance(weights, np.ndarray):
            raise ValueError(f"Deserialized object is not numpy array: {type(weights)}")

        return weights


# Module-level convenience functions

_GLOBAL_CRYPTO = None


def _get_crypto() -> PostQuantumCrypto:
    """Get or initialize global crypto instance."""
    global _GLOBAL_CRYPTO
    if _GLOBAL_CRYPTO is None:
        _GLOBAL_CRYPTO = PostQuantumCrypto()
    return _GLOBAL_CRYPTO


def generate_keypair() -> Tuple[bytes, bytes]:
    """
    Generate a post-quantum cryptographic keypair.

    Returns:
        Tuple of (public_key_bytes, private_key_bytes)

    Raises:
        ImportError: If liboqs is not installed

    Example:
        >>> public_key, private_key = generate_keypair()
        >>> print(f"Public key: {len(public_key)} bytes")
    """
    return _get_crypto().generate_keypair()


def encrypt_weights(weights: np.ndarray, public_key: bytes) -> bytes:
    """
    Encrypt model weights using post-quantum cryptography.

    Args:
        weights: Numpy array of model weights
        public_key: Public key bytes from generate_keypair()

    Returns:
        Encrypted bytes

    Raises:
        TypeError: If weights is not a numpy array
        ValueError: If encryption fails

    Example:
        >>> weights = np.random.randn(256, 128)
        >>> encrypted = encrypt_weights(weights, public_key)
    """
    return _get_crypto().encrypt_weights(weights, public_key)


def decrypt_weights(encrypted_data: bytes, private_key: bytes) -> np.ndarray:
    """
    Decrypt model weights using post-quantum cryptography.

    Args:
        encrypted_data: Encrypted bytes from encrypt_weights()
        private_key: Private key bytes from generate_keypair()

    Returns:
        Decrypted numpy array

    Raises:
        ValueError: If decryption fails

    Example:
        >>> decrypted = decrypt_weights(encrypted, private_key)
        >>> assert np.allclose(original, decrypted)
    """
    return _get_crypto().decrypt_weights(encrypted_data, private_key)


def benchmark_crypto(
    num_iterations: int = 5,
    weights_shape: Tuple[int, ...] = (256, 128),
    weights_dtype: str = 'float32'
) -> Dict[str, Any]:
    """
    Benchmark post-quantum cryptography operations.

    Measures:
    - Key generation time
    - Encryption time (per model)
    - Decryption time (per model)
    - Ciphertext size vs plaintext size
    - Throughput (MB/s for encryption/decryption)

    Args:
        num_iterations: Number of iterations for each operation
        weights_shape: Shape of weight matrices to test
        weights_dtype: Numpy dtype for weights

    Returns:
        Dictionary with benchmark results

    Example:
        >>> results = benchmark_crypto(num_iterations=10)
        >>> print(f"Encryption: {results['encrypt_time_ms']:.2f} ms")
        >>> print(f"Overhead: {results['ciphertext_overhead_percent']:.1f}%")
    """
    logger.info(f"\n{'='*80}")
    logger.info("POST-QUANTUM CRYPTOGRAPHY BENCHMARK")
    logger.info(f"{'='*80}")

    crypto = _get_crypto()
    results = {}

    # 1. Key Generation Benchmark
    logger.info(f"\n1. KEY GENERATION (algorithm: {crypto.algorithm})")
    logger.info(f"   Iterations: {num_iterations}")

    keygen_times = []
    for i in range(num_iterations):
        start = time.perf_counter()
        public_key, private_key = crypto.generate_keypair()
        elapsed = (time.perf_counter() - start) * 1000  # ms

        keygen_times.append(elapsed)
        logger.info(f"   Iteration {i+1}: {elapsed:.2f} ms")

    results['keygen_time_ms'] = {
        'mean': np.mean(keygen_times),
        'std': np.std(keygen_times),
        'min': np.min(keygen_times),
        'max': np.max(keygen_times),
    }
    results['public_key_size_bytes'] = len(public_key)
    results['private_key_size_bytes'] = len(private_key)

    logger.info(f"   Mean: {results['keygen_time_ms']['mean']:.2f} ms ± {results['keygen_time_ms']['std']:.2f}")
    logger.info(f"   Public Key: {len(public_key)} bytes")
    logger.info(f"   Private Key: {len(private_key)} bytes")

    # 2. Create test weights
    logger.info(f"\n2. TEST WEIGHTS")
    logger.info(f"   Shape: {weights_shape}")
    logger.info(f"   Dtype: {weights_dtype}")

    weights = np.random.randn(*weights_shape).astype(weights_dtype)
    plaintext_size = weights.nbytes

    logger.info(f"   Size: {plaintext_size} bytes ({plaintext_size/1024/1024:.2f} MB)")

    # 3. Encryption Benchmark
    logger.info(f"\n3. ENCRYPTION (iterations: {num_iterations})")

    encrypt_times = []
    ciphertext_size = None

    for i in range(num_iterations):
        start = time.perf_counter()
        encrypted = crypto.encrypt_weights(weights, public_key)
        elapsed = (time.perf_counter() - start) * 1000  # ms

        encrypt_times.append(elapsed)
        if ciphertext_size is None:
            ciphertext_size = len(encrypted)

        logger.info(f"   Iteration {i+1}: {elapsed:.2f} ms")

    results['encrypt_time_ms'] = {
        'mean': np.mean(encrypt_times),
        'std': np.std(encrypt_times),
        'min': np.min(encrypt_times),
        'max': np.max(encrypt_times),
    }
    results['ciphertext_size_bytes'] = ciphertext_size
    results['ciphertext_overhead_percent'] = 100 * (ciphertext_size - plaintext_size) / plaintext_size

    encrypt_throughput = (plaintext_size / 1024 / 1024) / (results['encrypt_time_ms']['mean'] / 1000)

    logger.info(f"   Mean: {results['encrypt_time_ms']['mean']:.2f} ms ± {results['encrypt_time_ms']['std']:.2f}")
    logger.info(f"   Ciphertext Size: {ciphertext_size} bytes")
    logger.info(f"   Overhead: {results['ciphertext_overhead_percent']:.2f}%")
    logger.info(f"   Throughput: {encrypt_throughput:.2f} MB/s")

    # 4. Decryption Benchmark
    logger.info(f"\n4. DECRYPTION (iterations: {num_iterations})")

    decrypt_times = []

    for i in range(num_iterations):
        start = time.perf_counter()
        decrypted = crypto.decrypt_weights(encrypted, private_key)
        elapsed = (time.perf_counter() - start) * 1000  # ms

        decrypt_times.append(elapsed)
        logger.info(f"   Iteration {i+1}: {elapsed:.2f} ms")

    results['decrypt_time_ms'] = {
        'mean': np.mean(decrypt_times),
        'std': np.std(decrypt_times),
        'min': np.min(decrypt_times),
        'max': np.max(decrypt_times),
    }

    decrypt_throughput = (ciphertext_size / 1024 / 1024) / (results['decrypt_time_ms']['mean'] / 1000)

    logger.info(f"   Mean: {results['decrypt_time_ms']['mean']:.2f} ms ± {results['decrypt_time_ms']['std']:.2f}")
    logger.info(f"   Throughput: {decrypt_throughput:.2f} MB/s")

    # 5. Integrity Check
    logger.info(f"\n5. INTEGRITY VERIFICATION")

    match = np.allclose(weights, decrypted, rtol=1e-5)
    logger.info(f"   Encryption/Decryption match: {match}")

    if not match:
        logger.error("   WARNING: Decrypted weights do not match original!")
        max_diff = np.max(np.abs(weights - decrypted))
        logger.error(f"   Max difference: {max_diff}")

    results['integrity_check_pass'] = match

    # 6. Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Algorithm: {crypto.algorithm}")
    logger.info(f"Key Gen: {results['keygen_time_ms']['mean']:.2f} ms")
    logger.info(f"Encrypt: {results['encrypt_time_ms']['mean']:.2f} ms ({encrypt_throughput:.2f} MB/s)")
    logger.info(f"Decrypt: {results['decrypt_time_ms']['mean']:.2f} ms ({decrypt_throughput:.2f} MB/s)")
    logger.info(f"Overhead: {results['ciphertext_overhead_percent']:.2f}%")
    logger.info(f"Integrity: {match}")
    logger.info(f"{'='*80}\n")

    return results


if __name__ == "__main__":
    """Run benchmarks when module is executed directly."""
    try:
        # Run benchmarks
        results = benchmark_crypto(
            num_iterations=5,
            weights_shape=(256, 128),
            weights_dtype='float32'
        )

        # Test with larger weights
        logger.info("\n\nTesting with LARGER weights (1024x512):")
        results_large = benchmark_crypto(
            num_iterations=3,
            weights_shape=(1024, 512),
            weights_dtype='float32'
        )

    except ImportError as e:
        logger.error(f"\nERROR: {e}")
        logger.error("\nInstall liboqs-python with:")
        logger.error("  pip install liboqs-python cryptography")
