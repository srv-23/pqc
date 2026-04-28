"""
Federated Learning Convergence Plotter
========================================
Reads round metrics CSV and plots convergence curves for federated learning.

This script generates:
- Accuracy convergence plot
- Precision, Recall, F1-Score comparison
- Metrics summary statistics

Usage:
    python plot_convergence.py
    python plot_convergence.py --csv-file custom_path/metrics.csv
    python plot_convergence.py --output-dir custom_plots/
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Style configuration
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 5)
plt.rcParams['font.size'] = 11


class ConvergencePlotter:
    """Plot convergence curves from federated learning metrics."""

    def __init__(
        self,
        csv_file: Path = Path("federated_learning_results") / "round_metrics.csv",
        output_dir: Path = Path("federated_learning_results") / "plots",
    ):
        """
        Initialize the plotter.

        Args:
            csv_file: Path to metrics CSV file
            output_dir: Directory to save plots
        """
        self.csv_file = Path(csv_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.df = None
        self.load_metrics()

    def load_metrics(self) -> None:
        """Load metrics from CSV file."""
        logger.info(f"Loading metrics from: {self.csv_file}")

        if not self.csv_file.exists():
            raise FileNotFoundError(f"Metrics file not found: {self.csv_file}")

        self.df = pd.read_csv(self.csv_file)

        logger.info(f"✓ Loaded metrics for {len(self.df)} rounds")
        logger.info(f"\nDataFrame shape: {self.df.shape}")
        logger.info(f"Columns: {list(self.df.columns)}")
        logger.info(f"\nFirst few rows:")
        logger.info(f"{self.df.head()}")

    def plot_accuracy_convergence(self) -> Path:
        """
        Plot global accuracy convergence across rounds.

        Returns:
            Path to saved figure
        """
        logger.info("\nPlotting accuracy convergence...")

        fig, ax = plt.subplots(figsize=(10, 6))

        # Convert accuracy columns to float
        rounds = self.df['Round'].values
        global_acc = pd.to_numeric(self.df['Global_Accuracy'], errors='coerce').values
        train_acc = pd.to_numeric(self.df['Avg_Train_Accuracy'], errors='coerce').values
        test_acc = pd.to_numeric(self.df['Avg_Test_Accuracy'], errors='coerce').values

        # Plot lines
        ax.plot(
            rounds,
            global_acc,
            marker='o',
            linewidth=2.5,
            markersize=8,
            label='Global Accuracy',
            color='#2E86AB',
        )

        ax.plot(
            rounds,
            test_acc,
            marker='s',
            linewidth=2,
            markersize=6,
            label='Avg Test Accuracy',
            color='#A23B72',
            linestyle='--',
        )

        ax.plot(
            rounds,
            train_acc,
            marker='^',
            linewidth=2,
            markersize=6,
            label='Avg Train Accuracy',
            color='#F18F01',
            linestyle='--',
            alpha=0.7,
        )

        # Formatting
        ax.set_xlabel('Round Number', fontsize=12, fontweight='bold')
        ax.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
        ax.set_title(
            'Federated Learning: Model Accuracy Convergence',
            fontsize=14,
            fontweight='bold',
            pad=20,
        )

        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10, loc='lower right')
        ax.set_xticks(rounds)
        ax.set_ylim([min(0, global_acc.min() - 0.05), min(1.0, global_acc.max() + 0.05)])

        # Add value labels on points
        for i, (r, acc) in enumerate(zip(rounds, global_acc)):
            ax.annotate(
                f'{acc:.4f}',
                xy=(r, acc),
                xytext=(0, 8),
                textcoords='offset points',
                ha='center',
                fontsize=9,
            )

        plt.tight_layout()

        # Save
        output_path = self.output_dir / "01_accuracy_convergence.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"✓ Saved: {output_path}")
        plt.close()

        return output_path

    def plot_metrics_comparison(self) -> Path:
        """
        Plot comparison of Precision, Recall, and F1-Score across rounds.

        Returns:
            Path to saved figure
        """
        logger.info("Plotting metrics comparison...")

        fig, ax = plt.subplots(figsize=(12, 6))

        rounds = self.df['Round'].values
        precision = pd.to_numeric(self.df['Avg_Test_Precision'], errors='coerce').values
        recall = pd.to_numeric(self.df['Avg_Test_Recall'], errors='coerce').values
        f1_score = pd.to_numeric(self.df['Avg_Test_F1'], errors='coerce').values

        # Plot lines
        ax.plot(
            rounds,
            precision,
            marker='o',
            linewidth=2.5,
            markersize=8,
            label='Precision',
            color='#06A77D',
        )

        ax.plot(
            rounds,
            recall,
            marker='s',
            linewidth=2.5,
            markersize=8,
            label='Recall',
            color='#D62828',
        )

        ax.plot(
            rounds,
            f1_score,
            marker='^',
            linewidth=2.5,
            markersize=8,
            label='F1-Score',
            color='#F77F00',
        )

        # Formatting
        ax.set_xlabel('Round Number', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_title(
            'Federated Learning: Precision, Recall, F1-Score Convergence',
            fontsize=14,
            fontweight='bold',
            pad=20,
        )

        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11, loc='lower right')
        ax.set_xticks(rounds)
        ax.set_ylim([0, 1.05])

        plt.tight_layout()

        # Save
        output_path = self.output_dir / "02_metrics_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"✓ Saved: {output_path}")
        plt.close()

        return output_path

    def plot_clients_per_round(self) -> Path:
        """
        Plot number of clients participating in each round.

        Returns:
            Path to saved figure
        """
        logger.info("Plotting clients per round...")

        fig, ax = plt.subplots(figsize=(10, 6))

        rounds = self.df['Round'].values
        num_clients = self.df['Num_Clients'].values

        # Bar plot
        bars = ax.bar(
            rounds,
            num_clients,
            color='#4ECDC4',
            edgecolor='#1A535C',
            linewidth=2,
            alpha=0.8,
        )

        # Add value labels
        for bar, nc in zip(bars, num_clients):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{int(nc)}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold',
            )

        # Formatting
        ax.set_xlabel('Round Number', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Clients', fontsize=12, fontweight='bold')
        ax.set_title(
            'Federated Learning: Active Clients per Round',
            fontsize=14,
            fontweight='bold',
            pad=20,
        )

        ax.set_xticks(rounds)
        ax.set_ylim([0, num_clients.max() + 1])
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        # Save
        output_path = self.output_dir / "03_clients_per_round.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"✓ Saved: {output_path}")
        plt.close()

        return output_path

    def plot_summary_dashboard(self) -> Path:
        """
        Plot a summary dashboard with all metrics.

        Returns:
            Path to saved figure
        """
        logger.info("Creating summary dashboard...")

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            'Federated Learning: Summary Dashboard',
            fontsize=16,
            fontweight='bold',
            y=1.00,
        )

        rounds = self.df['Round'].values

        # 1. Accuracy
        ax = axes[0, 0]
        global_acc = pd.to_numeric(self.df['Global_Accuracy'], errors='coerce').values
        ax.plot(rounds, global_acc, marker='o', linewidth=2.5, color='#2E86AB')
        ax.set_xlabel('Round')
        ax.set_ylabel('Accuracy')
        ax.set_title('Global Accuracy')
        ax.grid(True, alpha=0.3)

        # 2. Precision/Recall/F1
        ax = axes[0, 1]
        precision = pd.to_numeric(self.df['Avg_Test_Precision'], errors='coerce').values
        recall = pd.to_numeric(self.df['Avg_Test_Recall'], errors='coerce').values
        f1_score = pd.to_numeric(self.df['Avg_Test_F1'], errors='coerce').values

        ax.plot(rounds, precision, marker='o', label='Precision', linewidth=2)
        ax.plot(rounds, recall, marker='s', label='Recall', linewidth=2)
        ax.plot(rounds, f1_score, marker='^', label='F1-Score', linewidth=2)
        ax.set_xlabel('Round')
        ax.set_ylabel('Score')
        ax.set_title('Classification Metrics')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 3. Clients per round
        ax = axes[1, 0]
        num_clients = self.df['Num_Clients'].values
        ax.bar(rounds, num_clients, color='#4ECDC4', alpha=0.8)
        ax.set_xlabel('Round')
        ax.set_ylabel('Num Clients')
        ax.set_title('Active Clients')
        ax.grid(True, alpha=0.3, axis='y')

        # 4. Improvement
        ax = axes[1, 1]
        improvement = (global_acc - global_acc[0]) * 100  # % improvement
        ax.plot(
            rounds,
            improvement,
            marker='o',
            linewidth=2.5,
            color='#A23B72',
        )
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax.set_xlabel('Round')
        ax.set_ylabel('Improvement (%)')
        ax.set_title('Accuracy Improvement vs Round 1')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save
        output_path = self.output_dir / "04_summary_dashboard.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"✓ Saved: {output_path}")
        plt.close()

        return output_path

    def print_statistics(self) -> None:
        """Print summary statistics."""
        logger.info(f"\n{'='*80}")
        logger.info("CONVERGENCE STATISTICS")
        logger.info(f"{'='*80}")

        global_acc = pd.to_numeric(self.df['Global_Accuracy'], errors='coerce')
        test_acc = pd.to_numeric(self.df['Avg_Test_Accuracy'], errors='coerce')
        precision = pd.to_numeric(self.df['Avg_Test_Precision'], errors='coerce')
        recall = pd.to_numeric(self.df['Avg_Test_Recall'], errors='coerce')
        f1_score = pd.to_numeric(self.df['Avg_Test_F1'], errors='coerce')

        logger.info(f"\nGlobal Accuracy:")
        logger.info(f"  Initial (Round 1): {global_acc.iloc[0]:.4f}")
        logger.info(f"  Final (Round {len(self.df)}): {global_acc.iloc[-1]:.4f}")
        logger.info(f"  Improvement: {(global_acc.iloc[-1] - global_acc.iloc[0]) * 100:.2f}%")
        logger.info(f"  Mean: {global_acc.mean():.4f}")
        logger.info(f"  Std: {global_acc.std():.4f}")

        logger.info(f"\nTest Accuracy:")
        logger.info(f"  Max: {test_acc.max():.4f} (Round {test_acc.idxmax() + 1})")
        logger.info(f"  Min: {test_acc.min():.4f} (Round {test_acc.idxmin() + 1})")
        logger.info(f"  Mean: {test_acc.mean():.4f}")

        logger.info(f"\nF1-Score:")
        logger.info(f"  Max: {f1_score.max():.4f} (Round {f1_score.idxmax() + 1})")
        logger.info(f"  Mean: {f1_score.mean():.4f}")

        logger.info(f"\nPrecision vs Recall:")
        logger.info(f"  Precision (final): {precision.iloc[-1]:.4f}")
        logger.info(f"  Recall (final): {recall.iloc[-1]:.4f}")

        logger.info(f"{'='*80}\n")

    def run(self) -> None:
        """Generate all plots."""
        logger.info(f"\n{'='*80}")
        logger.info("FEDERATED LEARNING CONVERGENCE PLOTTER")
        logger.info(f"{'='*80}")

        try:
            # Generate plots
            self.plot_accuracy_convergence()
            self.plot_metrics_comparison()
            self.plot_clients_per_round()
            self.plot_summary_dashboard()

            # Print statistics
            self.print_statistics()

            logger.info(f"\n{'='*80}")
            logger.info("PLOTTING COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Output directory: {self.output_dir}")
            logger.info(f"{'='*80}\n")

        except Exception as e:
            logger.error(f"Error during plotting: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Plot federated learning convergence curves"
    )
    parser.add_argument(
        "--csv-file",
        type=Path,
        default=Path("federated_learning_results") / "round_metrics.csv",
        help="Path to metrics CSV file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("federated_learning_results") / "plots",
        help="Directory to save plots",
    )

    args = parser.parse_args()

    plotter = ConvergencePlotter(csv_file=args.csv_file, output_dir=args.output_dir)
    plotter.run()


if __name__ == "__main__":
    main()
