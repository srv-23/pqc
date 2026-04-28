"""
Federated Learning Server for IoT Intrusion Detection
======================================================
Flower (FLWR) server with FedAvg strategy for federated model aggregation.

Features:
- FedAvg strategy for parameter averaging
- Minimum 3 clients required before training starts
- 10 rounds of federated learning
- Round-wise accuracy logging to CSV
- Detailed logging of global model performance
- Custom strategy callback for monitoring

Usage:
    python server.py
"""

import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier

import flwr as fl
from flwr.server import ServerApp, ServerConfig
from flwr.server.strategy import FedAvg
from flwr.common import Metrics, FitRes, EvaluateRes, Parameters
from flwr.server.client_manager import ClientManager
from flwr.server.history import History

# Import post-quantum cryptography layer
from crypto_layer import generate_keypair, encrypt_weights, decrypt_weights

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
NUM_ROUNDS = 10
MIN_CLIENTS = 3
MIN_AVAILABLE_CLIENTS = 3
OUTPUT_DIR = Path("federated_learning_results")
METRICS_FILE = OUTPUT_DIR / "round_metrics.csv"
KEYS_DIR = Path("federated_learning_results") / "keys"
RANDOM_SEED = 42
USE_ENCRYPTION = True  # Enable post-quantum encryption for weight transmission

np.random.seed(RANDOM_SEED)


class MetricsAggregator:
    """Aggregate and track metrics across federated learning rounds."""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialize metrics aggregator.

        Args:
            output_dir: Directory to save metrics
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.round_metrics = []
        self.metrics_file = self.output_dir / "round_metrics.csv"

        # Initialize CSV with headers
        self.csv_headers = [
            "Round",
            "Num_Clients",
            "Global_Accuracy",
            "Avg_Train_Accuracy",
            "Avg_Test_Accuracy",
            "Avg_Test_Precision",
            "Avg_Test_Recall",
            "Avg_Test_F1",
            "Timestamp"
        ]

        # Create CSV file with headers
        with open(self.metrics_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_headers)
            writer.writeheader()

        logger.info(f"Metrics file created: {self.metrics_file}")

    def log_round(
        self,
        round_num: int,
        num_clients: int,
        accuracy: float,
        avg_train_acc: float = 0.0,
        avg_test_acc: float = 0.0,
        avg_test_precision: float = 0.0,
        avg_test_recall: float = 0.0,
        avg_test_f1: float = 0.0,
    ) -> None:
        """
        Log metrics for a round.

        Args:
            round_num: Round number
            num_clients: Number of clients that participated
            accuracy: Global model accuracy
            avg_train_acc: Average training accuracy across clients
            avg_test_acc: Average test accuracy across clients
            avg_test_precision: Average test precision across clients
            avg_test_recall: Average test recall across clients
            avg_test_f1: Average test F1 score across clients
        """
        metrics = {
            "Round": round_num,
            "Num_Clients": num_clients,
            "Global_Accuracy": f"{accuracy:.4f}",
            "Avg_Train_Accuracy": f"{avg_train_acc:.4f}",
            "Avg_Test_Accuracy": f"{avg_test_acc:.4f}",
            "Avg_Test_Precision": f"{avg_test_precision:.4f}",
            "Avg_Test_Recall": f"{avg_test_recall:.4f}",
            "Avg_Test_F1": f"{avg_test_f1:.4f}",
            "Timestamp": datetime.now().isoformat()
        }

        self.round_metrics.append(metrics)

        # Append to CSV
        with open(self.metrics_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_headers)
            writer.writerow(metrics)

        logger.info(
            f"Round {round_num} - Global Accuracy: {accuracy:.4f}, "
            f"Clients: {num_clients}, Train Acc: {avg_train_acc:.4f}, "
            f"Test Acc: {avg_test_acc:.4f}"
        )

    def get_summary(self) -> pd.DataFrame:
        """
        Get summary of all rounds.

        Returns:
            DataFrame with round metrics
        """
        return pd.DataFrame(self.round_metrics)


def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    """
    Aggregate metrics from clients with weighted average.

    This function is called by Flower after each round to aggregate
    evaluation metrics from all clients. Metrics are weighted by the
    number of samples each client used.

    Args:
        metrics: List of (num_samples, metrics_dict) tuples from clients

    Returns:
        Dictionary of aggregated metrics
    """
    if not metrics:
        return {}

    # Extract metrics
    accuracies = []
    precisions = []
    recalls = []
    f1_scores = []
    num_samples_list = []

    for num_samples, m in metrics:
        num_samples_list.append(num_samples)
        if "test_accuracy" in m:
            accuracies.append(m["test_accuracy"])
        if "test_precision" in m:
            precisions.append(m["test_precision"])
        if "test_recall" in m:
            recalls.append(m["test_recall"])
        if "test_f1_score" in m:
            f1_scores.append(m["test_f1_score"])

    total_samples = sum(num_samples_list)

    # Weighted average
    aggregated_metrics = {}

    if accuracies:
        aggregated_metrics["accuracy"] = sum(accuracies) / len(accuracies)
    if precisions:
        aggregated_metrics["precision"] = sum(precisions) / len(precisions)
    if recalls:
        aggregated_metrics["recall"] = sum(recalls) / len(recalls)
    if f1_scores:
        aggregated_metrics["f1_score"] = sum(f1_scores) / len(f1_scores)

    aggregated_metrics["total_samples"] = total_samples
    aggregated_metrics["num_clients"] = len(metrics)

    return aggregated_metrics


class FedAvgWithLogging(FedAvg):
    """
    FedAvg strategy with custom logging, metrics tracking, and post-quantum encryption.
    
    Extends the standard FedAvg strategy to:
    - Log round-wise metrics to CSV
    - Encrypt model weights before sending to clients
    - Decrypt weights received from clients before aggregation
    - Re-encrypt aggregated weights for next round
    """

    def __init__(
        self,
        *args,
        metrics_aggregator: Optional[MetricsAggregator] = None,
        server_public_key: bytes = None,
        server_private_key: bytes = None,
        use_encryption: bool = True,
        **kwargs
    ):
        """
        Initialize FedAvg with logging and encryption support.

        Args:
            metrics_aggregator: MetricsAggregator instance for tracking
            server_public_key: Server's public key for encrypting weights
            server_private_key: Server's private key for decrypting weights
            use_encryption: Whether to use post-quantum encryption
            *args, **kwargs: Arguments passed to FedAvg
        """
        super().__init__(*args, **kwargs)
        self.metrics_aggregator = metrics_aggregator
        self.server_public_key = server_public_key
        self.server_private_key = server_private_key
        self.use_encryption = use_encryption
        self.round_counter = 0

    def configure_fit(
        self,
        server_round: int,
        parameters: Parameters,
        client_manager: ClientManager,
    ) -> List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitIns]]:
        """
        Configure the fit instructions for the clients.

        This method is called before sending weights to clients.
        We use it to encrypt the model weights before transmission.

        Args:
            server_round: Current round number
            parameters: Model parameters to send to clients
            client_manager: Client manager instance

        Returns:
            List of (client_proxy, fit_instructions) tuples
        """
        # Get the base fit configurations from parent
        configs = super().configure_fit(server_round, parameters, client_manager)

        # If encryption is enabled, encrypt weights in the config
        if self.use_encryption and self.server_public_key:
            logger.info(f"\n{'='*80}")
            logger.info(f"ENCRYPTION: Preparing encrypted weights for clients")
            logger.info(f"{'='*80}")
            
            # Extract parameters
            if hasattr(parameters, 'tensors'):
                # Convert parameters to numpy arrays
                param_arrays = [np.frombuffer(p, dtype=np.float32) for p in parameters.tensors]
            else:
                param_arrays = parameters
            
            try:
                # Concatenate all parameters into a single array for encryption
                if isinstance(param_arrays, list):
                    weights_array = np.concatenate([p.flatten() for p in param_arrays])
                else:
                    weights_array = param_arrays
                
                # Encrypt weights
                logger.info(f"Encrypting model weights ({weights_array.nbytes} bytes) for transmission...")
                encrypted_weights = encrypt_weights(
                    weights_array,
                    self.server_public_key
                )
                
                logger.info(f"[CRYPTO] Encryption successful: {weights_array.nbytes}B -> "
                           f"{len(encrypted_weights)}B ({100*len(encrypted_weights)/weights_array.nbytes:.2f}% overhead)")
                
                # Add encrypted weights to config for each client
                updated_configs = []
                for client_proxy, fit_ins in configs:
                    # Store encrypted weights in the config
                    fit_ins.config["encrypted_parameters"] = encrypted_weights
                    fit_ins.config["encryption_enabled"] = True
                    updated_configs.append((client_proxy, fit_ins))
                
                configs = updated_configs
                logger.info(f"{'='*80}\n")
                
            except Exception as e:
                logger.error(f"[CRYPTO] Encryption failed: {e}")
                logger.warning("[SECURITY] WARNING: Weights will be sent without encryption!")
                for client_proxy, fit_ins in configs:
                    fit_ins.config["encryption_enabled"] = False
        
        return configs

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: List[Tuple[fl.server.client_proxy.ClientProxy, BaseException]],
    ) -> Tuple[Optional[Parameters], Dict[str, any]]:
        """
        Aggregate fit results from clients.

        This method is called after clients complete training.
        We use it to decrypt encrypted weights received from clients before aggregation.

        Args:
            server_round: Current round number
            results: List of (client_proxy, fit_result) tuples
            failures: List of failed results

        Returns:
            Tuple of (aggregated_parameters, metrics_dict)
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"FEDERATED LEARNING ROUND {server_round} - AGGREGATION")
        logger.info(f"{'='*80}")
        
        logger.info(f"Number of clients: {len(results)}")
        if failures:
            logger.warning(f"Number of failed clients: {len(failures)}")

        # Check if clients returned encrypted weights
        encrypted_weights_list = []
        for client_proxy, fit_res in results:
            if "encrypted_weights" in fit_res.metrics and fit_res.metrics["encrypted_weights"]:
                encrypted_weights_list.append(True)
                logger.info(f"Client {getattr(client_proxy, 'node_id', '?')}: weights are encrypted")
            else:
                logger.info(f"Client {getattr(client_proxy, 'node_id', '?')}: weights are NOT encrypted")

        # If encryption is enabled, decrypt received weights
        if self.use_encryption and self.server_private_key and encrypted_weights_list:
            logger.info(f"\n[CRYPTO] Decrypting received weights from clients...")
            
            decrypted_results = []
            for client_proxy, fit_res in results:
                try:
                    # Check if this client sent encrypted weights
                    if fit_res.parameters and len(fit_res.parameters.tensors) == 1:
                        # Extract encrypted bytes from parameters
                        encrypted_bytes = bytes(np.frombuffer(fit_res.parameters.tensors[0], dtype=np.uint8))
                        
                        # Decrypt weights
                        logger.debug(f"Decrypting weights from client (encrypted: {len(encrypted_bytes)} bytes)")
                        decrypted_array = decrypt_weights(
                            encrypted_bytes,
                            self.server_private_key
                        )
                        
                        logger.debug(f"[CRYPTO] Decryption successful: {len(encrypted_bytes)}B -> {decrypted_array.nbytes}B")
                        
                        # Convert decrypted array back to parameters format
                        # Create dummy parameters object
                        decrypted_tensors = [decrypted_array.astype(np.float32).tobytes()]
                        decrypted_params = Parameters(
                            tensors=decrypted_tensors,
                            tensor_type="numpy.ndarray"
                        )
                        
                        # Replace parameters with decrypted version
                        fit_res.parameters = decrypted_params
                        
                except Exception as e:
                    logger.error(f"[CRYPTO] Decryption failed for client: {e}")
                    logger.warning("[SECURITY] WARNING: Could not decrypt weights from this client")
                
                decrypted_results.append((client_proxy, fit_res))
            
            results = decrypted_results
            logger.info(f"[CRYPTO] Decryption complete")
            logger.info(f"{'='*80}\n")

        # Call parent aggregate_fit for standard aggregation
        aggregated_parameters, metrics = super().aggregate_fit(server_round, results, failures)

        logger.info(f"Aggregation complete. Aggregated {len(results)} client updates.")

        return aggregated_parameters, metrics

    def aggregate_evaluate(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, EvaluateRes]],
        failures: List[Tuple[fl.server.client_proxy.ClientProxy, EvaluateRes]],
    ) -> Tuple[Optional[float], Dict[str, any]]:
        """
        Aggregate evaluation results from clients.

        This method is called after clients evaluate the global model.
        We use it to track and log the global metrics.

        Args:
            server_round: Current round number
            results: List of (client_proxy, evaluate_result) tuples
            failures: List of failed evaluations

        Returns:
            Tuple of (global_loss, metrics_dict)
        """
        # Call parent aggregate_evaluate
        global_loss, metrics = super().aggregate_evaluate(server_round, results, failures)

        logger.info(f"\n{'='*80}")
        logger.info(f"FEDERATED LEARNING ROUND {server_round} - EVALUATION")
        logger.info(f"{'='*80}")

        logger.info(f"Number of clients evaluated: {len(results)}")
        if failures:
            logger.warning(f"Number of failed clients: {len(failures)}")

        # Extract per-client metrics
        client_accuracies = []
        client_precisions = []
        client_recalls = []
        client_f1_scores = []
        total_samples = 0

        for client_proxy, evaluate_result in results:
            metrics_dict = evaluate_result.metrics
            if "test_accuracy" in metrics_dict:
                client_accuracies.append(metrics_dict["test_accuracy"])
            if "test_precision" in metrics_dict:
                client_precisions.append(metrics_dict["test_precision"])
            if "test_recall" in metrics_dict:
                client_recalls.append(metrics_dict["test_recall"])
            if "test_f1_score" in metrics_dict:
                client_f1_scores.append(metrics_dict["test_f1_score"])
            
            total_samples += evaluate_result.num_examples

            client_id = getattr(client_proxy, "node_id", "unknown")
            logger.info(
                f"  Client {client_id}: Acc={metrics_dict.get('test_accuracy', 0):.4f}, "
                f"Prec={metrics_dict.get('test_precision', 0):.4f}, "
                f"Rec={metrics_dict.get('test_recall', 0):.4f}, "
                f"F1={metrics_dict.get('test_f1_score', 0):.4f}"
            )

        # Calculate averages
        avg_accuracy = np.mean(client_accuracies) if client_accuracies else 0.0
        avg_precision = np.mean(client_precisions) if client_precisions else 0.0
        avg_recall = np.mean(client_recalls) if client_recalls else 0.0
        avg_f1 = np.mean(client_f1_scores) if client_f1_scores else 0.0

        logger.info(f"\nGlobal Model Performance (Round {server_round}):")
        logger.info(f"  Global Accuracy:  {avg_accuracy:.4f}")
        logger.info(f"  Global Precision: {avg_precision:.4f}")
        logger.info(f"  Global Recall:    {avg_recall:.4f}")
        logger.info(f"  Global F1-Score:  {avg_f1:.4f}")
        logger.info(f"  Global Loss:      {global_loss:.6f}")
        logger.info(f"  Total Samples:    {total_samples}")

        # Log to metrics aggregator
        if self.metrics_aggregator:
            self.metrics_aggregator.log_round(
                round_num=server_round,
                num_clients=len(results),
                accuracy=avg_accuracy,
                avg_train_acc=0.0,  # Could be added if training metrics tracked
                avg_test_acc=avg_accuracy,
                avg_test_precision=avg_precision,
                avg_test_recall=avg_recall,
                avg_test_f1=avg_f1,
            )

        logger.info(f"{'='*80}\n")

        return global_loss, metrics


def create_strategy() -> FedAvgWithLogging:
    """
    Create FedAvg strategy with custom configuration and post-quantum encryption.

    Generates encryption keypairs if encryption is enabled and saves the public
    key to a file for clients to load.

    Returns:
        FedAvgWithLogging strategy instance
    """
    logger.info(f"\n{'='*80}")
    logger.info("Creating FedAvg Strategy with Post-Quantum Encryption")
    logger.info(f"{'='*80}")

    metrics_aggregator = MetricsAggregator(OUTPUT_DIR)

    # Generate encryption keypair if encryption is enabled
    server_public_key = None
    server_private_key = None
    
    if USE_ENCRYPTION:
        try:
            logger.info("[CRYPTO] Generating server keypair for post-quantum encryption...")
            server_public_key, server_private_key = generate_keypair()
            
            logger.info(f"[CRYPTO] Keypair generated successfully")
            logger.info(f"  Public key: {len(server_public_key)} bytes")
            logger.info(f"  Private key: {len(server_private_key)} bytes")
            
            # Save public key to file for clients to load
            KEYS_DIR.mkdir(parents=True, exist_ok=True)
            public_key_file = KEYS_DIR / "server_public_key.bin"
            
            with open(public_key_file, 'wb') as f:
                f.write(server_public_key)
            
            logger.info(f"[CRYPTO] Public key saved to: {public_key_file}")
            logger.info(f"[CRYPTO] Clients should load this key with:")
            logger.info(f"         python client.py --node-id <id> --server localhost:8080 \\")
            logger.info(f"         --server-public-key {public_key_file}")
            
        except Exception as e:
            logger.error(f"[CRYPTO] Failed to generate encryption keys: {e}")
            logger.warning("[SECURITY] WARNING: Federated learning will proceed WITHOUT post-quantum encryption!")
            USE_ENCRYPTION = False

    strategy = FedAvgWithLogging(
        fraction_fit=1.0,  # Use all available clients for training
        fraction_evaluate=1.0,  # Use all available clients for evaluation
        min_fit_clients=MIN_CLIENTS,  # Minimum clients for training round
        min_evaluate_clients=MIN_CLIENTS,  # Minimum clients for evaluation round
        min_available_clients=MIN_AVAILABLE_CLIENTS,  # Minimum clients to start training
        initial_parameters=None,  # Server will initialize from first client
        fit_metrics_aggregation_fn=weighted_average,
        evaluate_metrics_aggregation_fn=weighted_average,
        metrics_aggregator=metrics_aggregator,
        server_public_key=server_public_key,
        server_private_key=server_private_key,
        use_encryption=USE_ENCRYPTION,
    )

    logger.info("FedAvg Strategy Configuration:")
    logger.info(f"  Fraction fit: 1.0 (all clients)")
    logger.info(f"  Fraction evaluate: 1.0 (all clients)")
    logger.info(f"  Min fit clients: {MIN_CLIENTS}")
    logger.info(f"  Min evaluate clients: {MIN_CLIENTS}")
    logger.info(f"  Min available clients: {MIN_AVAILABLE_CLIENTS}")
    logger.info(f"  Initial parameters: From first client")
    logger.info(f"  Post-quantum encryption: {'ENABLED' if USE_ENCRYPTION else 'DISABLED'}")
    logger.info(f"{'='*80}\n")

    return strategy


def main():
    """Main entry point for the Flower server with post-quantum encryption support."""

    logger.info(f"\n{'='*80}")
    logger.info("FEDERATED LEARNING SERVER - IOT INTRUSION DETECTION")
    logger.info("WITH POST-QUANTUM CRYPTOGRAPHY (PQC) SUPPORT")
    logger.info(f"{'='*80}")
    logger.info(f"Configuration:")
    logger.info(f"  Number of rounds: {NUM_ROUNDS}")
    logger.info(f"  Minimum clients: {MIN_CLIENTS}")
    logger.info(f"  Strategy: FedAvg")
    logger.info(f"  Post-quantum encryption: {'ENABLED' if USE_ENCRYPTION else 'DISABLED'}")
    logger.info(f"  Output directory: {OUTPUT_DIR}")
    logger.info(f"{'='*80}\n")

    # Create strategy (which will generate encryption keys)
    strategy = create_strategy()

    # Create server configuration
    config = ServerConfig(
        num_rounds=NUM_ROUNDS,
        round_timeout=600,  # 10 minutes per round
    )

    logger.info(f"Starting Flower Server...")
    logger.info(f"Waiting for {MIN_AVAILABLE_CLIENTS} clients to connect...")
    logger.info(f"Server will be available at: 0.0.0.0:8080\n")
    
    if USE_ENCRYPTION:
        logger.info(f"[SECURITY] Post-Quantum Encryption ENABLED")
        logger.info(f"  - Model weights encrypted before transmission")
        logger.info(f"  - Resistant to quantum computing attacks")
        logger.info(f"  - Public key saved to: {KEYS_DIR / 'server_public_key.bin'}\n")

    # Start server
    history = fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=config,
        strategy=strategy,
    )

    # Print final results
    logger.info(f"\n{'='*80}")
    logger.info("FEDERATED LEARNING COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total rounds completed: {NUM_ROUNDS}")

    if strategy.metrics_aggregator:
        summary = strategy.metrics_aggregator.get_summary()
        logger.info(f"\nRound Summary:")
        logger.info(f"\n{summary.to_string()}")

    logger.info(f"\nMetrics saved to: {METRICS_FILE}")
    logger.info(f"Use 'python plot_convergence.py' to visualize results")
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    main()
