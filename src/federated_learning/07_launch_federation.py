"""
Federated Learning Launcher
============================
Launches Flower server and all 3 clients simultaneously using subprocess.

This script:
- Starts the Flower server first
- Waits for server to be ready
- Launches 3 clients in parallel
- Monitors all processes
- Captures output and logs

Usage:
    python launch_federation.py
"""

import subprocess
import time
import logging
import sys
import signal
import os
from pathlib import Path
from typing import List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FederationLauncher:
    """Manages launching and monitoring federated learning processes."""

    def __init__(self):
        """Initialize the launcher."""
        self.processes: List[subprocess.Popen] = []
        self.server_process: Optional[subprocess.Popen] = None
        self.client_processes: List[subprocess.Popen] = []

    def launch_server(self, host: str = "0.0.0.0", port: int = 8080) -> bool:
        """
        Launch the Flower server.

        Args:
            host: Server host
            port: Server port

        Returns:
            True if server started successfully
        """
        logger.info(f"\n{'='*80}")
        logger.info("LAUNCHING FLOWER SERVER")
        logger.info(f"{'='*80}")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")

        try:
            # Start server process
            self.server_process = subprocess.Popen(
                [sys.executable, "server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            self.processes.append(self.server_process)

            logger.info(f"Server process started (PID: {self.server_process.pid})")

            # Wait for server to be ready
            logger.info(f"Waiting {3} seconds for server to initialize...")
            time.sleep(3)

            if self.server_process.poll() is not None:
                logger.error("Server process terminated unexpectedly")
                return False

            logger.info("✓ Server is ready")
            logger.info(f"{'='*80}\n")

            return True

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def launch_client(self, node_id: int, server_address: str = "localhost:8080", server_public_key: Optional[str] = None) -> bool:
        """
        Launch a Flower client.

        Args:
            node_id: Client node ID (1, 2, or 3)
            server_address: Server address
            server_public_key: Path to server's public key for encryption

        Returns:
            True if client started successfully
        """
        logger.info(f"Launching Client (Node {node_id})...")

        try:
            # Build client command
            cmd = [
                sys.executable,
                "client.py",
                "--node-id",
                str(node_id),
                "--server",
                server_address,
            ]
            
            # Add server public key if encryption is enabled
            if server_public_key:
                cmd.extend(["--server-public-key", server_public_key])
                logger.info(f"  Using encryption with key: {server_public_key}")

            # Start client process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            self.client_processes.append(process)
            self.processes.append(process)

            logger.info(f"✓ Client Node {node_id} started (PID: {process.pid})")

            return True

        except Exception as e:
            logger.error(f"Failed to start client {node_id}: {e}")
            return False

    def launch_all_clients(self, num_clients: int = 3, server_address: str = "localhost:8080") -> bool:
        """
        Launch all clients.

        Args:
            num_clients: Number of clients to launch
            server_address: Server address

        Returns:
            True if all clients started successfully
        """
        logger.info(f"\n{'='*80}")
        logger.info("LAUNCHING CLIENTS")
        logger.info(f"{'='*80}")

        # Check if server's public key exists
        public_key_path = Path("federated_learning_results/keys/server_public_key.bin")
        server_public_key = None
        
        if public_key_path.exists():
            server_public_key = str(public_key_path.absolute())
            logger.info(f"✓ Found server public key at: {server_public_key}")
            logger.info(f"  Encryption will be enabled for all clients")
        else:
            logger.warning(f"Server public key not found at: {public_key_path}")
            logger.info(f"  Clients will operate without encryption")

        logger.info(f"{'='*80}\n")

        success = True
        for node_id in range(1, num_clients + 1):
            if not self.launch_client(node_id, server_address, server_public_key):
                success = False
            # Stagger client startup slightly
            time.sleep(0.5)

        if success:
            logger.info(f"✓ All {num_clients} clients launched successfully")
        else:
            logger.error(f"Some clients failed to start")

        logger.info(f"{'='*80}\n")

        return success

    def monitor_processes(self) -> None:
        """Monitor all running processes and log output."""
        logger.info(f"\n{'='*80}")
        logger.info("MONITORING FEDERATED LEARNING")
        logger.info(f"{'='*80}")
        logger.info(f"Server PID: {self.server_process.pid}")
        logger.info(f"Client PIDs: {[p.pid for p in self.client_processes]}")
        logger.info(f"{'='*80}\n")

        try:
            # Wait for all processes to complete
            while True:
                # Check if server is still running
                if self.server_process.poll() is not None:
                    logger.info("Server process has completed")
                    break

                # Check if any clients are still running
                active_clients = [p for p in self.client_processes if p.poll() is None]
                if not active_clients:
                    logger.info("All clients have completed")
                    break

                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\nReceived interrupt signal. Shutting down...")
            self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shutdown all processes."""
        logger.info(f"\n{'='*80}")
        logger.info("SHUTTING DOWN FEDERATION")
        logger.info(f"{'='*80}")

        # Terminate all processes
        for process in self.processes:
            if process.poll() is None:
                logger.info(f"Terminating process {process.pid}...")
                process.terminate()

        # Wait for graceful shutdown
        logger.info("Waiting for processes to terminate...")
        time.sleep(2)

        # Kill any remaining processes
        for process in self.processes:
            if process.poll() is None:
                logger.warning(f"Force killing process {process.pid}...")
                process.kill()

        logger.info("✓ All processes terminated")
        logger.info(f"{'='*80}\n")

    def run(self) -> int:
        """
        Run the complete federated learning setup.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.info(f"\n{'='*80}")
        logger.info("FEDERATED LEARNING LAUNCHER")
        logger.info(f"{'='*80}")

        try:
            # Launch server
            if not self.launch_server():
                logger.error("Failed to launch server")
                return 1

            # Launch clients
            if not self.launch_all_clients(num_clients=3):
                logger.error("Failed to launch all clients")
                self.shutdown()
                return 1

            # Monitor processes
            self.monitor_processes()

            logger.info(f"\n{'='*80}")
            logger.info("FEDERATED LEARNING COMPLETE")
            logger.info(f"{'='*80}")
            logger.info("Results saved to: federated_learning_results/")
            logger.info("To plot convergence: python plot_convergence.py")
            logger.info(f"{'='*80}\n")

            return 0

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            self.shutdown()
            return 1


def main():
    """Main entry point."""
    launcher = FederationLauncher()

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\nReceived shutdown signal")
        launcher.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run launcher
    exit_code = launcher.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
