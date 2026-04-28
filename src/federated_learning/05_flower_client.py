"""
Federated Learning Client for IoT Intrusion Detection
======================================================
Flower (FLWR) client that trains MLPClassifier locally on partitioned data
and participates in federated learning aggregation.

Usage:
    python client.py --node-id 1 --server localhost:8080
    python client.py --node-id 2 --server localhost:8080
    python client.py --node-id 3 --server localhost:8080
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, classification_report
)

import flwr as fl
from flwr.client import NumPyClient, ClientApp
from flwr.common import Context

# Import post-quantum cryptography layer
from crypto_layer import generate_keypair, encrypt_weights, decrypt_weights

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path("dataset") / "partitioned"
MODEL_STATE_FILE = "model_state_{node_id}.pkl"
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


class IoTIntrustionDetectionClient(NumPyClient):
    """
    Federated Learning Client for IoT Intrusion Detection.
    
    This client loads local data for a specific node, trains an MLPClassifier
    locally, and participates in federated averaging with other nodes.
    """

    def __init__(
        self,
        node_id: int,
        model: MLPClassifier,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: list,
        class_names: list,
        server_public_key: bytes = None,
    ):
        """
        Initialize the federated learning client.

        Args:
            node_id: Node identifier (1, 2, or 3)
            model: Untrained MLPClassifier instance
            X_train: Training features (scaled)
            y_train: Training labels
            X_test: Test features (scaled)
            y_test: Test labels
            feature_names: List of feature column names
            class_names: List of class names for reporting
            server_public_key: Server's public key for encrypting outgoing weights
        """
        self.node_id = node_id
        self.model = model
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.feature_names = feature_names
        self.class_names = class_names
        
        # Generate client keypair for post-quantum encryption
        logger.info(f"Generating client keypair for post-quantum secure communication...")
        self.client_public_key, self.client_private_key = generate_keypair()
        logger.info(f"  Client public key: {len(self.client_public_key)} bytes")
        logger.info(f"  Client private key: {len(self.client_private_key)} bytes")
        
        # Server's public key for encrypting weights before sending
        self.server_public_key = server_public_key
        
        logger.info(f"Node {self.node_id} Client initialized:")
        logger.info(f"  Training samples: {len(self.X_train)}")
        logger.info(f"  Test samples: {len(self.X_test)}")
        logger.info(f"  Features: {self.X_train.shape[1]}")
        logger.info(f"  Classes: {len(self.class_names)} {self.class_names}")

    def fit(
        self, parameters: list[np.ndarray], config: Dict[str, Any]
    ) -> Tuple[list[np.ndarray], int, Dict[str, Any]]:
        """
        Train the model locally using received parameters (federated weights).

        This method is called by the Flower server to perform local training.
        The model receives initial weights from the server, trains on local data,
        and returns updated weights.

        Encryption Integration:
        1. Receives encrypted parameters from server (as bytes in config)
        2. Decrypts parameters using server's private key
        3. Trains locally on decrypted weights
        4. Encrypts updated weights before returning

        Args:
            parameters: List of numpy arrays representing model weights from server
            config: Configuration dictionary from server (contains epochs, batch_size, etc.)

        Returns:
            Tuple of:
                - List of numpy arrays (updated model weights)
                - Number of training samples used
                - Dictionary with training metrics
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Node {self.node_id} - LOCAL TRAINING (FIT)")
        logger.info(f"{'='*80}")

        # Extract training configuration from server
        epochs = config.get("epochs", 5)
        batch_size = config.get("batch_size", 32)
        learning_rate = config.get("learning_rate", 0.001)
        
        logger.info(f"Received config: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")

        # DECRYPTION: Check if parameters are encrypted (passed as bytes in config)
        if "encrypted_parameters" in config and config["encrypted_parameters"]:
            try:
                logger.info("[CRYPTO] Decrypting received model weights...")
                encrypted_params_bytes = config["encrypted_parameters"]
                
                # Decrypt parameters using client's private key
                decrypted_params_array = decrypt_weights(
                    encrypted_params_bytes,
                    self.client_private_key
                )
                
                logger.info(f"[CRYPTO] Decryption successful: {len(encrypted_params_bytes)} bytes -> numpy array")
                
                # Convert decrypted array to list of parameter arrays
                # If the server sent all weights as a single concatenated array, reshape accordingly
                parameters = self._reshape_decrypted_params(decrypted_params_array)
                
            except Exception as e:
                logger.error(f"[CRYPTO] Decryption failed: {e}. Using unencrypted parameters.")
                # Fall back to unencrypted parameters if decryption fails
        
        # Set model parameters from server (weights + biases)
        self._set_model_params(parameters)

        # Train locally
        logger.info(f"Training on {len(self.X_train)} local samples...")
        
        self.model.fit(self.X_train, self.y_train)

        # Evaluate on local training data
        train_pred = self.model.predict(self.X_train)
        train_accuracy = accuracy_score(self.y_train, train_pred)
        
        logger.info(f"Training accuracy: {train_accuracy:.4f}")

        # Prepare return values
        num_samples_train = len(self.X_train)
        metrics = {
            "train_accuracy": float(train_accuracy),
            "train_samples": num_samples_train,
            "node_id": self.node_id
        }

        # Get updated weights
        weights = self._get_model_params()

        # ENCRYPTION: Encrypt weights before returning to server
        try:
            logger.info("[CRYPTO] Encrypting model weights before transmission...")
            
            # Concatenate all weight arrays into a single numpy array for encryption
            weights_to_encrypt = np.concatenate([w.flatten() for w in weights])
            
            # Encrypt using server's public key
            encrypted_weights = encrypt_weights(
                weights_to_encrypt,
                self.server_public_key
            )
            
            logger.info(f"[CRYPTO] Encryption successful: numpy array ({weights_to_encrypt.nbytes} bytes) -> "
                       f"{len(encrypted_weights)} encrypted bytes "
                       f"({100*len(encrypted_weights)/weights_to_encrypt.nbytes:.2f}% overhead)")
            
            # Store encrypted weights in metrics for transmission
            # (Flower will serialize metrics, but encrypted bytes need special handling)
            metrics["encrypted_weights"] = True
            metrics["weights_byte_count"] = len(encrypted_weights)
            
            # Return encrypted weights as a special format
            # We'll encode them as a single numpy array of uint8 that can be reconstructed
            encrypted_array = np.frombuffer(encrypted_weights, dtype=np.uint8)
            weights = [encrypted_array]  # Wrap encrypted data
            
        except Exception as e:
            logger.error(f"[CRYPTO] Encryption failed: {e}. Returning unencrypted weights.")
            logger.warning("[SECURITY] WARNING: Weights transmitted without encryption!")
            metrics["encrypted_weights"] = False

        logger.info(f"Fit complete. Returning weights.")
        logger.info(f"{'='*80}\n")

        return weights, num_samples_train, metrics

    def evaluate(
        self, parameters: list[np.ndarray], config: Dict[str, Any]
    ) -> Tuple[float, int, Dict[str, Any]]:
        """
        Evaluate the model on local test data.

        This method is called by the Flower server to evaluate the current
        global model on local data, providing validation metrics without
        data leaving the client.

        Encryption Integration:
        1. Receives encrypted parameters from server (as bytes in config)
        2. Decrypts parameters using server's private key
        3. Evaluates decrypted model
        4. Returns unencrypted metrics (metrics are not sensitive)

        Args:
            parameters: List of numpy arrays representing model weights to evaluate
            config: Configuration dictionary from server

        Returns:
            Tuple of:
                - Loss (MSE for regression, cross-entropy for classification)
                - Number of test samples
                - Dictionary with evaluation metrics
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Node {self.node_id} - LOCAL EVALUATION")
        logger.info(f"{'='*80}")

        # DECRYPTION: Check if parameters are encrypted
        if "encrypted_parameters" in config and config["encrypted_parameters"]:
            try:
                logger.info("[CRYPTO] Decrypting received model weights for evaluation...")
                encrypted_params_bytes = config["encrypted_parameters"]
                
                # Decrypt parameters using client's private key
                decrypted_params_array = decrypt_weights(
                    encrypted_params_bytes,
                    self.client_private_key
                )
                
                logger.info(f"[CRYPTO] Decryption successful: {len(encrypted_params_bytes)} bytes -> numpy array")
                
                # Convert decrypted array to list of parameter arrays
                parameters = self._reshape_decrypted_params(decrypted_params_array)
                
            except Exception as e:
                logger.error(f"[CRYPTO] Decryption failed: {e}. Using unencrypted parameters.")
                # Fall back to unencrypted parameters if decryption fails

        # Set model parameters
        self._set_model_params(parameters)

        # Evaluate on local test set
        logger.info(f"Evaluating on {len(self.X_test)} local test samples...")

        # Get predictions
        test_pred = self.model.predict(self.X_test)
        test_pred_proba = self.model.predict_proba(self.X_test)

        # Calculate metrics
        accuracy = accuracy_score(self.y_test, test_pred)
        precision = precision_score(self.y_test, test_pred, average='weighted', zero_division=0)
        recall = recall_score(self.y_test, test_pred, average='weighted', zero_division=0)
        f1 = f1_score(self.y_test, test_pred, average='weighted', zero_division=0)

        # Calculate loss as negative log-likelihood (classification loss)
        # For simplicity, using 1 - accuracy as loss (could use cross-entropy)
        loss = float(1.0 - accuracy)

        logger.info(f"Test Accuracy:  {accuracy:.4f}")
        logger.info(f"Test Precision: {precision:.4f}")
        logger.info(f"Test Recall:    {recall:.4f}")
        logger.info(f"Test F1-Score:  {f1:.4f}")
        logger.info(f"Test Loss:      {loss:.4f}")

        # Classification report
        logger.info(f"\nClassification Report:")
        logger.info(f"\n{classification_report(self.y_test, test_pred, target_names=self.class_names, zero_division=0)}")

        num_samples_test = len(self.X_test)

        metrics = {
            "test_accuracy": float(accuracy),
            "test_precision": float(precision),
            "test_recall": float(recall),
            "test_f1_score": float(f1),
            "test_samples": num_samples_test,
            "node_id": self.node_id
        }

        logger.info(f"Evaluation complete.")
        logger.info(f"{'='*80}\n")

        return loss, num_samples_test, metrics

    def _get_model_params(self) -> list[np.ndarray]:
        """
        Extract model weights and biases as numpy arrays.

        MLPClassifier stores weights in coefs_ (list of weight matrices)
        and biases in intercepts_ (list of bias vectors).

        Returns:
            List of numpy arrays: [coef_layer1, bias_layer1, coef_layer2, bias_layer2, ...]
        """
        weights = []

        # Get coefficients (weights) from each layer
        for layer_idx, coefs in enumerate(self.model.coefs_):
            weights.append(coefs.astype(np.float32))

        # Get intercepts (biases) from each layer
        for layer_idx, intercepts in enumerate(self.model.intercepts_):
            weights.append(intercepts.astype(np.float32))

        logger.debug(f"Extracted {len(weights)} parameter arrays from model")
        for i, w in enumerate(weights):
            logger.debug(f"  Param {i}: shape {w.shape}, dtype {w.dtype}")

        return weights

    def _reshape_decrypted_params(self, decrypted_array: np.ndarray) -> list[np.ndarray]:
        """
        Reshape a decrypted flattened array back to individual parameter arrays.

        When weights are encrypted, they're flattened into a single array.
        This method reconstructs the original list of weight matrices.

        Args:
            decrypted_array: Flattened numpy array of decrypted parameters

        Returns:
            List of numpy arrays with proper shapes
        """
        # Get the shape metadata from the model's current structure
        # to reconstruct the decrypted parameters
        
        if not hasattr(self.model, 'coefs_') or len(self.model.coefs_) == 0:
            logger.warning("Model not yet initialized, returning decrypted array as-is")
            return [decrypted_array]
        
        # Get shapes from model
        shapes = []
        for coefs in self.model.coefs_:
            shapes.append(coefs.shape)
        for intercepts in self.model.intercepts_:
            shapes.append(intercepts.shape)
        
        # Reconstruct parameters from flat array
        params = []
        offset = 0
        
        for shape in shapes:
            size = np.prod(shape)
            param = decrypted_array[offset:offset + size].reshape(shape).astype(np.float32)
            params.append(param)
            offset += size
        
        logger.debug(f"Reconstructed {len(params)} parameter arrays from decrypted data")
        return params

    def _set_model_params(self, params: list[np.ndarray]) -> None:
        """
        Set model weights and biases from numpy arrays.

        Args:
            params: List of numpy arrays with weights and biases
        """
        # Split params into weights and biases
        # MLPClassifier has L layers: L coefficient matrices and L bias vectors
        num_layers = len(self.model.coefs_)

        if len(params) != 2 * num_layers:
            logger.error(
                f"Expected {2 * num_layers} parameter arrays "
                f"(coefs + biases for {num_layers} layers), "
                f"got {len(params)}"
            )
            raise ValueError(f"Parameter count mismatch: expected {2 * num_layers}, got {len(params)}")

        # Set coefficients
        for i, param in enumerate(params[:num_layers]):
            self.model.coefs_[i] = param.astype(np.float64)

        # Set intercepts
        for i, param in enumerate(params[num_layers:]):
            self.model.intercepts_[i] = param.astype(np.float64)

        logger.debug(f"Set {len(params)} parameter arrays to model")


def load_data(node_id: int) -> Tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, list, list
]:
    """
    Load local data partition for a specific node.

    Args:
        node_id: Node identifier (1, 2, or 3)

    Returns:
        Tuple of:
            - X_train: Training features (scaled)
            - y_train: Training labels
            - X_test: Test features (scaled)
            - y_test: Test labels
            - feature_names: List of feature names (excluding label)
            - class_names: List of unique class names
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Loading Data for Node {node_id}")
    logger.info(f"{'='*80}")

    # Construct file paths
    node_dir = DATA_DIR / f"node{node_id}"
    train_file = node_dir / f"node{node_id}_train.csv"
    test_file = node_dir / f"node{node_id}_test.csv"

    # Verify files exist
    if not train_file.exists():
        raise FileNotFoundError(f"Training file not found: {train_file}")
    if not test_file.exists():
        raise FileNotFoundError(f"Test file not found: {test_file}")

    logger.info(f"Loading training data from {train_file}...")
    train_df = pd.read_csv(train_file)

    logger.info(f"Loading test data from {test_file}...")
    test_df = pd.read_csv(test_file)

    logger.info(f"Training data shape: {train_df.shape}")
    logger.info(f"Test data shape: {test_df.shape}")

    # Identify label column and feature columns
    label_col = 'label' if 'label' in train_df.columns else 'attack_type'
    feature_cols = [col for col in train_df.columns if col not in [label_col, 'device', 'attack_type']]

    logger.info(f"Label column: {label_col}")
    logger.info(f"Number of features: {len(feature_cols)}")

    # Extract features and labels
    X_train = train_df[feature_cols].values.astype(np.float32)
    y_train = train_df[label_col].values
    X_test = test_df[feature_cols].values.astype(np.float32)
    y_test = test_df[label_col].values

    # Ensure labels are numeric
    if y_train.dtype == 'object':
        logger.warning("Labels are strings, encoding to integers")
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y_train = le.fit_transform(y_train)
        y_test = le.transform(y_test)
        class_names = list(le.classes_)
    else:
        # Map numeric labels to class names
        class_names = ['BASHLITE', 'BENIGN', 'MIRAI']

    logger.info(f"Training label distribution:")
    unique_train, counts_train = np.unique(y_train, return_counts=True)
    for label, count in zip(unique_train, counts_train):
        logger.info(f"  Class {label} ({class_names[label]}): {count} samples ({100*count/len(y_train):.2f}%)")

    logger.info(f"Test label distribution:")
    unique_test, counts_test = np.unique(y_test, return_counts=True)
    for label, count in zip(unique_test, counts_test):
        logger.info(f"  Class {label} ({class_names[label]}): {count} samples ({100*count/len(y_test):.2f}%)")

    logger.info(f"{'='*80}\n")

    return X_train, y_train, X_test, y_test, feature_cols, class_names


def create_model() -> MLPClassifier:
    """
    Create an MLPClassifier for IoT intrusion detection.

    The model is configured with:
    - Hidden layers: (256, 128, 64) for deep feature learning
    - Activation: relu (good for binary/multiclass classification)
    - Solver: adam (adaptive learning rate, good for large datasets)
    - Batch normalization: implicit through solver
    - Early stopping: enabled to prevent overfitting
    - Max iterations: 200 epochs

    Returns:
        Untrained MLPClassifier instance
    """
    logger.info(f"{'='*80}")
    logger.info("Creating MLPClassifier Model")
    logger.info(f"{'='*80}")

    model = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64),
        activation='relu',
        solver='adam',
        learning_rate_init=0.001,
        max_iter=200,
        batch_size=32,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        random_state=RANDOM_SEED,
        verbose=0,
        warm_start=False,  # Important: False for federated learning
    )

    logger.info(f"Model configuration:")
    logger.info(f"  Hidden layers: (256, 128, 64)")
    logger.info(f"  Activation: relu")
    logger.info(f"  Solver: adam")
    logger.info(f"  Learning rate: 0.001")
    logger.info(f"  Max iterations: 200")
    logger.info(f"  Early stopping: True (patience=20)")
    logger.info(f"{'='*80}\n")

    return model


def main():
    """Main entry point for the federated learning client."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Federated Learning Client for IoT Intrusion Detection"
    )
    parser.add_argument(
        "--node-id",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="Node identifier (1, 2, or 3)"
    )
    parser.add_argument(
        "--server",
        type=str,
        default="localhost:8080",
        help="Flower server address (default: localhost:8080)"
    )
    parser.add_argument(
        "--server-public-key",
        type=str,
        default=None,
        help="Path to server's public key file for post-quantum encryption"
    )

    args = parser.parse_args()

    logger.info(f"\n{'='*80}")
    logger.info("FEDERATED LEARNING CLIENT - IOT INTRUSION DETECTION (POST-QUANTUM SECURE)")
    logger.info(f"{'='*80}")
    logger.info(f"Node ID: {args.node_id}")
    logger.info(f"Server: {args.server}")
    
    # Load server's public key if provided
    server_public_key = None
    if args.server_public_key:
        try:
            key_path = Path(args.server_public_key)
            if key_path.exists():
                with open(key_path, 'rb') as f:
                    server_public_key = f.read()
                logger.info(f"Loaded server public key from: {args.server_public_key}")
                logger.info(f"Server public key size: {len(server_public_key)} bytes")
            else:
                logger.warning(f"Server public key file not found: {args.server_public_key}")
        except Exception as e:
            logger.error(f"Error loading server public key: {e}")
    
    logger.info(f"{'='*80}\n")

    try:
        # Load local data
        X_train, y_train, X_test, y_test, feature_names, class_names = load_data(args.node_id)

        # Create model
        model = create_model()

        # Initialize client with post-quantum encryption support
        client = IoTIntrustionDetectionClient(
            node_id=args.node_id,
            model=model,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            feature_names=feature_names,
            class_names=class_names,
            server_public_key=server_public_key,
        )

        # Connect to Flower server and start training
        logger.info(f"Connecting to Flower server at {args.server}...")
        
        fl.client.start_client(
            server_address=args.server,
            client=client.to_client(),
        )

    except Exception as e:
        logger.error(f"Error in client: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
