# Post-Quantum Cryptography Guide

## Overview

This project implements post-quantum secure federated learning using NIST-standardized cryptographic algorithms.

## Algorithm Selection

The system automatically selects the best available algorithm:

### Primary Choice: Kyber768 (Recommended)
- **Status:** NIST-standardized (ML-KEM)
- **Security:** Post-quantum resistant
- **Key Size:** 1088 bytes (ciphertext)
- **Speed:** ~0.1ms encapsulation
- **Availability:** Linux/Mac with liboqs
- **Status on Windows:** Not available (fallback to RSA)

### Secondary Choice: NTRU-Prime-857
- **Status:** NIST finalist
- **Security:** Post-quantum resistant
- **Key Size:** 1184 bytes (ciphertext)
- **Speed:** ~0.15ms encapsulation
- **Availability:** Linux/Mac with liboqs
- **Status on Windows:** Not available

### Fallback Choice: RSA-4096
- **Status:** Classical cryptography
- **Security:** Secure (not post-quantum resistant)
- **Key Size:** 512 bytes (ciphertext overhead)
- **Speed:** 0.55ms encryption, 279ms decryption
- **Availability:** All platforms (always works)
- **Status:** Currently active on Windows

## Hybrid Encryption Details

All modes use hybrid encryption combining asymmetric and symmetric algorithms:

```
Plaintext (Model Weights)
    ↓
[1] Serialize (pickle)
    ↓
Serialized Bytes
    ↓
[2] Symmetric Encryption (AES-256-GCM)
    ├─ Key: 256-bit (from HKDF)
    ├─ IV: 128-bit (random)
    └─ Output: Ciphertext + Authentication Tag
    ↓
[3] Asymmetric Encryption (RSA-4096/Kyber/NTRU)
    ├─ Encrypt AES key
    └─ Output: Encrypted AES Key
    ↓
Final Format: [EncryptedKey | IV | Ciphertext | Tag]
```

## Cryptographic Primitives

### Symmetric Encryption: AES-256-GCM

**Parameters:**
- Algorithm: AES (Advanced Encryption Standard)
- Mode: GCM (Galois/Counter Mode)
- Key Size: 256 bits
- IV Size: 128 bits (nonce)
- Tag Size: 128 bits (authentication)

**Properties:**
- Provides both confidentiality and authenticity
- Detects tampering during decryption
- Decryption fails if weights modified

**Example:**
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

# Generate key and IV
key = os.urandom(32)  # 256 bits
iv = os.urandom(16)   # 128 bits

# Create cipher
cipher = AESGCM(key)

# Encrypt
ciphertext = cipher.encrypt(iv, plaintext, aad=None)
# Output includes tag automatically

# Decrypt
plaintext = cipher.decrypt(iv, ciphertext, aad=None)
# Raises exception if tag invalid
```

### Key Derivation: HKDF-SHA256

**Purpose:** Derive AES key from shared secret

**Parameters:**
- Hash: SHA-256
- Salt: Random (part of ciphertext)
- Info: "AES-256" (context string)
- Length: 32 bytes (256 bits)

**Flow:**
```
Shared Secret (from KEM)
    ↓
HKDF-Expand
    ├─ Hash Function: SHA-256
    ├─ Salt: Random
    └─ Info: "AES-256"
    ↓
256-bit AES Key
```

### Asymmetric Encryption: RSA-4096

**Parameters:**
- Key Size: 4096 bits
- Padding: OAEP (Optimal Asymmetric Encryption Padding)
- Hash: SHA-256

**Key Sizes:**
- Public Key: 512 bytes
- Private Key: 4096 bytes (kept secret)

**Example:**
```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# Generate keypair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
)
public_key = private_key.public_key()

# Encrypt AES key
encrypted_aes_key = public_key.encrypt(
    aes_key,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

# Decrypt AES key
aes_key = private_key.decrypt(
    encrypted_aes_key,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
```

## Performance Analysis

### Benchmark Results

**System:** Windows, Python 3.13, cryptography 42.0

| Operation | Time | Data | Throughput |
|-----------|------|------|-----------|
| Key Generation | 237.78 ms | - | - |
| Encrypt Weights | 0.55 ms | 131 KB | 238.69 MB/s |
| Decrypt Weights | 278.99 ms | 131 KB | 0.45 MB/s |
| Ciphertext Overhead | - | 131 KB | 0.52% |

**Per-Round Impact (3 clients):**
- Total encryption: 0.55 × 3 = 1.65 ms
- Total decryption: 279.0 × 3 = 837 ms
- Round time: 30-60 seconds
- Encryption overhead: 1-2%

### Optimization Techniques

1. **Larger Weights:** Amortizes overhead (smaller %)
2. **Batch Encryption:** Encrypt multiple updates together
3. **Parallel Decryption:** Decrypt client weights in parallel
4. **Compression:** Compress weights before encryption
5. **Hardware Acceleration:** AES-NI support (automatic)

## Security Analysis

### Threat Model

**Protected Against:**
✓ Passive eavesdropping
✓ Network packet inspection
✓ Weight reconstruction attacks
✓ Weight tampering (GCM detects)
✓ Quantum computing (Kyber/NTRU)

**Not Protected Against:**
✗ Honest-but-curious server (can observe structure)
✗ Malicious server (can perform inference)
✗ Man-in-the-middle (no mutual auth)
✗ Quantum computers (RSA fallback)
✗ Side-channel attacks

### Key Management

**Keypair Generation:**
- Server: 1 keypair (public key shared)
- Client: 1 keypair each (private key kept local)

**Key Storage:**
- Public keys: In files/memory
- Private keys: In memory only (not on disk)
- Duration: Per training run

**Key Exchange:**
- Server generates → saves public key to file
- Clients load public key from file
- No secure key exchange protocol (public keys okay to share)

### Post-Quantum Readiness

**Kyber768 (When available):**
- NIST-standardized (FIPS 203)
- Resistant to quantum attacks
- 256-bit post-quantum security
- Small ciphertext (1088 bytes)
- Fast (~0.1ms)

**RSA-4096 (Current on Windows):**
- Classical cryptography
- NOT quantum-resistant
- 112-bit security (estimated)
- Larger ciphertext (512+ bytes overhead)
- Slower (~0.55ms, ~279ms)

**Upgrade Path:**
1. Install liboqs on Linux/Mac
2. Code automatically switches to Kyber768
3. No changes needed in client/server code

## Encryption Examples

### Example 1: Basic Encryption/Decryption

```python
from src.crypto.crypto_layer import generate_keypair, encrypt_weights, decrypt_weights
import numpy as np

# Generate keypair
public_key, private_key = generate_keypair()

# Create sample weights
weights = np.random.randn(256, 128).astype(np.float32)

# Encrypt weights
encrypted = encrypt_weights(weights, public_key)

# Decrypt weights
decrypted = decrypt_weights(encrypted, private_key)

# Verify
assert np.allclose(weights, decrypted)
print("Encryption/decryption successful!")
```

### Example 2: Per-Round Encryption (Server)

```python
# Server code (simplified)
server_public_key, server_private_key = generate_keypair()

# During aggregation
aggregated_weights = fedavg_aggregation(client_updates)

# Encrypt for each client
encrypted_for_client1 = encrypt_weights(
    aggregated_weights,
    client1_public_key
)

# Send to client
client1_config["encrypted_parameters"] = encrypted_for_client1
```

### Example 3: Weight Encryption (Client)

```python
# Client code (simplified)
client_public_key, client_private_key = generate_keypair()

# Receive and decrypt
received_encrypted = config["encrypted_parameters"]
weights = decrypt_weights(received_encrypted, client_private_key)

# Train locally
model.fit(X_train, y_train)

# Extract and encrypt updated weights
updated_weights = extract_weights(model)
encrypted_updated = encrypt_weights(updated_weights, server_public_key)

# Send to server
return encrypted_updated
```

## Troubleshooting

### Issue: Decryption Fails with "Authentication Tag Mismatch"

**Cause:** Weights were modified in transit or corrupted

**Solution:**
1. Check network connectivity
2. Verify sender and receiver have same algorithm
3. Restart encryption key generation

```bash
# Restart server to regenerate keys
python src/federated_learning/06_flower_server.py
```

### Issue: "ImportError: liboqs not found"

**Cause:** liboqs not installed (expected on Windows)

**Solution:** System automatically uses RSA-4096 fallback
```python
# In crypto_layer.py, algorithm auto-selects:
# 1. Kyber768 (if liboqs available)
# 2. RSA-4096 (fallback - always works)
```

To use Kyber on Linux:
```bash
pip install liboqs-python
# Then restart to use Kyber automatically
```

### Issue: "Encryption/Decryption Very Slow"

**Cause:** RSA decryption is slow (279ms expected)

**Solution:** Normal behavior for RSA-4096
- Per-round: ~0.8 seconds for 3 clients
- Total round: 30-60 seconds
- Overhead: 1-2% (acceptable)

To improve:
1. Use Kyber768 on Linux (100x faster)
2. Parallelize decryption if many clients
3. Compress weights before encryption

## Advanced Topics

### Custom Keypair Generation

```python
from src.crypto.crypto_layer import PostQuantumCrypto

# Use specific algorithm
crypto = PostQuantumCrypto(algorithm='Kyber768')
public_key, private_key = crypto.generate_keypair()

# Or fallback to RSA
crypto = PostQuantumCrypto(use_fallback=True)
public_key, private_key = crypto.generate_keypair()
```

### Custom Encryption Parameters

```python
# Modify AES key size (not recommended)
crypto.AES_KEY_SIZE = 32  # 256 bits (default)

# Modify RSA key size (not recommended)
crypto.RSA_KEY_SIZE = 4096  # Bits (default)
```

### Benchmarking Crypto Operations

```bash
# Run benchmark
python src/crypto/crypto_layer.py

# Output shows:
# - Key generation time
# - Encryption speed
# - Decryption speed
# - Ciphertext overhead
```

## References

- **NIST PQC:** https://csrc.nist.gov/projects/post-quantum-cryptography/
- **Kyber:** https://pq-crystals.org/kyber/
- **NTRU-Prime:** https://ntruprime.cr.yp.to/
- **cryptography.io:** https://cryptography.io/
- **AES-GCM:** NIST SP 800-38D
- **HKDF:** RFC 5869
- **OAEP:** PKCS#1 v2.0

## FAQ

**Q: Is this quantum-safe?**
A: On Linux with Kyber768 - yes. On Windows with RSA-4096 - no, but upgrade path ready.

**Q: Can I use my own keys?**
A: System generates keys automatically. To use custom keys, modify `generate_keypair()`.

**Q: How often should I rotate keys?**
A: Currently per-training-run. For production, implement per-round rotation.

**Q: Can I encrypt other data types?**
A: Yes, any data that can be pickled (numpy arrays, lists, dicts, etc.).

**Q: What happens if a key is compromised?**
A: All weights encrypted with that key are compromised. Restart with new keys.

**Q: Can I disable encryption?**
A: Yes, set `USE_ENCRYPTION = False` in `06_flower_server.py`.

---

**For questions:** See `docs/` directory or refer to code comments.
