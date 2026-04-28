"""
Example: Using crypto_layer.py for Federated Learning

This script demonstrates how to integrate post-quantum cryptography
into a federated learning system.
"""

import numpy as np
from crypto_layer import generate_keypair, encrypt_weights, decrypt_weights, benchmark_crypto


def example_basic_usage():
    """Basic encryption/decryption example."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Encryption/Decryption")
    print("="*80)

    # Generate keypair
    print("\n1. Generating keypair...")
    public_key, private_key = generate_keypair()
    print(f"   [OK] Public key: {len(public_key)} bytes")
    print(f"   [OK] Private key: {len(private_key)} bytes")

    # Create mock model weights
    print("\n2. Creating model weights...")
    weights = np.random.randn(256, 128).astype(np.float32)
    print(f"   [OK] Shape: {weights.shape}")
    print(f"   [OK] Size: {weights.nbytes} bytes")
    print(f"   [OK] Dtype: {weights.dtype}")

    # Encrypt weights
    print("\n3. Encrypting weights...")
    encrypted = encrypt_weights(weights, public_key)
    print(f"   [OK] Encrypted size: {len(encrypted)} bytes")
    print(f"   [OK] Overhead: {100*(len(encrypted)-weights.nbytes)/weights.nbytes:.2f}%")

    # Decrypt weights
    print("\n4. Decrypting weights...")
    decrypted = decrypt_weights(encrypted, private_key)
    print(f"   [OK] Decrypted shape: {decrypted.shape}")
    print(f"   [OK] Dtype: {decrypted.dtype}")

    # Verify integrity
    print("\n5. Verifying integrity...")
    match = np.allclose(weights, decrypted, rtol=1e-5)
    print(f"   [OK] Weights match: {match}")

    if not match:
        max_diff = np.max(np.abs(weights - decrypted))
        print(f"   [ERROR] WARNING: Max difference: {max_diff}")


def example_federated_client():
    """Simulate a federated learning client with encrypted weight updates."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Federated Learning Client Simulation")
    print("="*80)

    # Simulate node receiving server's global model
    print("\n1. Simulating federated learning client...")
    print("   (Assuming client receives global weights from server)")

    # Generate keypair for this node
    print("\n2. Node generates keypair...")
    public_key, private_key = generate_keypair()
    print(f"   [OK] Public key registered with server")

    # Simulate local training updating weights
    print("\n3. Node trains locally and gets updated weights...")
    local_weights = np.random.randn(256, 128).astype(np.float32)
    print(f"   [OK] Local weights: {local_weights.shape}")

    # Encrypt weights before sending to server
    print("\n4. Node encrypts weights before transmission...")
    encrypted_weights = encrypt_weights(local_weights, public_key)
    print(f"   [OK] Encrypted size: {len(encrypted_weights)} bytes")
    print(f"   [OK] Ready to transmit securely")

    # Server would aggregate without decrypting (privacy-preserving)
    print("\n5. Server receives encrypted weights...")
    print("   (Server can aggregate without decrypting - privacy preserved!)")

    # Only decryption would happen locally or after aggregation
    print("\n6. Optional: Decryption after secure aggregation...")
    decrypted_weights = decrypt_weights(encrypted_weights, private_key)
    print(f"   [OK] Decrypted weights: {decrypted_weights.shape}")


def example_multi_node():
    """Simulate multiple nodes sending encrypted weights."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Multi-Node Secure Aggregation")
    print("="*80)

    num_nodes = 3
    model_shape = (256, 128)

    print(f"\nSimulating {num_nodes} nodes aggregating weights...\n")

    # Each node generates keypair and weights
    nodes = []
    for i in range(num_nodes):
        public_key, private_key = generate_keypair()
        weights = np.random.randn(*model_shape).astype(np.float32)
        encrypted = encrypt_weights(weights, public_key)

        nodes.append({
            'id': i + 1,
            'public_key': public_key,
            'private_key': private_key,
            'weights': weights,
            'encrypted': encrypted
        })

        print(f"Node {i+1}:")
        print(f"  - Original weights: {weights.shape} ({weights.nbytes} bytes)")
        print(f"  - Encrypted size: {len(encrypted)} bytes")

    # Server would receive encrypted weights and aggregate
    print(f"\n[OK] Server receives {num_nodes} encrypted weight updates")
    total_encrypted_size = sum(len(n['encrypted']) for n in nodes)
    print(f"  - Total encrypted data: {total_encrypted_size} bytes")
    print(f"  - No plaintext weights transmitted!")

    # Verify decryption works for each node
    print(f"\n[OK] Verifying encryption/decryption integrity:")
    for node in nodes:
        decrypted = decrypt_weights(node['encrypted'], node['private_key'])
        match = np.allclose(node['weights'], decrypted, rtol=1e-5)
        print(f"  - Node {node['id']}: {match}")


def example_different_dtypes():
    """Test encryption with different data types."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Different Data Types")
    print("="*80)

    public_key, private_key = generate_keypair()

    dtypes = ['float32', 'float64', 'int32', 'int64']

    print("\nTesting encryption with different numpy dtypes:\n")

    for dtype in dtypes:
        weights = np.random.randn(128, 64).astype(dtype)
        encrypted = encrypt_weights(weights, public_key)
        decrypted = decrypt_weights(encrypted, private_key)

        match = np.allclose(weights, decrypted, rtol=1e-5) if weights.dtype in ['float32', 'float64'] else np.array_equal(weights, decrypted)

        print(f"  {dtype:8s}: {weights.shape} -> encrypted {len(encrypted):5d}B -> {match}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("POST-QUANTUM CRYPTOGRAPHY FOR FEDERATED LEARNING")
    print("="*80)

    # Run examples
    example_basic_usage()
    example_federated_client()
    example_multi_node()
    example_different_dtypes()

    # Run benchmarks
    print("\n" + "="*80)
    print("PERFORMANCE BENCHMARKS")
    print("="*80)
    results = benchmark_crypto(num_iterations=3, weights_shape=(256, 128))

    print("\n[OK] All examples completed successfully!")
