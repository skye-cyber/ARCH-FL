"""
Systematic Experiments for ARCH-FL

This module implements the experimental design matrix from the project proposal,
testing privacy-utility trade-offs and non-IID impacts on federated learning performance.
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    from src.utils.metrics import calculate_accuracy, calculate_loss
    from src.training.fedavg import FederatedTrainer
    from src.core.client import Client, XClient
    from src.core.coordinator import Coordinator
    from src.data.loaders import get_data_loaders
    from src.data.mimic_cxr_loader import create_mimic_cxr_data_loaders
    from src.models.architectures import SimpleCNN
    from src.models.large_cnn import MediumCNN
except Exceptions as e:
    print(e)


class ExperimentRunner:
    """
    Systematic experiment runner for ARCH-FL.

    Implements the experimental design matrix from the project proposal.
    """

    def __init__(self,
                 experiment_name: str = "baseline",
                 results_dir: str = "results/experiments",
                 device: str = "cpu"):
        """Initialize experiment runner."""
        self.experiment_name = experiment_name
        self.results_dir = results_dir
        self.device = device

        # Create results directory
        os.makedirs(results_dir, exist_ok=True)

        # Experiment configuration from proposal
        self.privacy_levels = [1.0, 2.0, 4.0, 8.0, float('inf')]
        self.non_iid_levels = [0.1, 0.5, 1.0, 5.0, 10.0]
        self.client_fractions = [0.3, 0.5, 0.7]
        self.sample_sizes = [1000, 2000]  # Start with smaller sizes

        print(f"🔬 Experiment Runner initialized: {experiment_name}")
        print(f"📁 Results will be saved to: {results_dir}")

    def run_privacy_utility_experiment(self, dataset: str = "mimic_cxr", sample_size: int = 1000,
                                      num_clients: int = 5,
                                      client_fraction: float = 0.5,
                                      iid: bool = True,
                                      alpha: float = 1.0,
                                      num_rounds: int = 10,
                                      local_epochs: int = 1) -> Dict[str, Any]:
        """
        Run privacy-utility trade-off experiment.

        Tests different privacy levels (ε) while keeping other variables constant.
        """
        print(f"\n🔒 Running Privacy-Utility Experiment")
        print(f"   Dataset: {dataset}")
        print(f"   Sample Size: {sample_size}")
        print(f"   Clients: {num_clients}")
        print(f"   IID: {iid}")
        print(f"   Rounds: {num_rounds}")

        results = {
            'experiment_type': 'privacy_utility',
            'dataset': dataset,
            'sample_size': sample_size,
            'num_clients': num_clients,
            'iid': iid,
            'alpha': alpha,
            'num_rounds': num_rounds,
            'local_epochs': local_epochs,
            'results': []
        }

        # Load dataset
        if dataset == "mimic_cxr":
            client_loaders, test_loader = create_mimic_cxr_data_loaders(
                num_clients=num_clients,
                max_samples=sample_size,
                batch_size=32,
                iid=iid,
                alpha=alpha
            )
        else:
            # Fallback to synthetic data
            client_loaders, test_loader = get_data_loaders(
                dataset_name="PneumoniaMNIST",
                num_clients=num_clients,
                iid=iid,
                batch_size=32,
                alpha=alpha
            )

        # Select subset of clients based on client_fraction
        num_selected_clients = int(num_clients * client_fraction)
        selected_client_indices = list(range(num_selected_clients))

        # Test each privacy level
        for epsilon in self.privacy_levels:
            print(f"\n--- Testing ε = {epsilon} ---")

            # Create clients
            clients = []
            for i, loader in enumerate(client_loaders[:num_selected_clients]):
                if epsilon == float('inf'):
                    # No DP
                    client = Client(
                        client_id=i,
                        model=MediumCNN(num_classes=2),
                        train_loader=loader
                    )
                else:
                    # With DP
                    dp_config = {
                        'enabled': True,
                        'epsilon': epsilon,
                        'delta': 1e-5,
                        'max_grad_norm': 1.0
                    }
                    client = XClient(
                        client_id=i,
                        model=MediumCNN(num_classes=2),
                        train_loader=loader,
                        device=self.device,
                        dp_config=dp_config
                    )
                clients.append(client)

            # Create coordinator and trainer
            global_model = MediumCNN(num_classes=2)
            coordinator = Coordinator(global_model)
            trainer = FederatedTrainer(coordinator, clients, test_loader, self.device)

            # Run federated training
            accuracies = []
            losses = []
            privacy_spent = []

            for round_num in range(num_rounds):
                accuracy = trainer.train_round(
                    client_indices=selected_client_indices,
                    local_epochs=local_epochs,
                    lr=0.01
                )

                # Calculate test loss
                test_loss = calculate_loss(
                    coordinator.global_model,
                    test_loader,
                    torch.nn.CrossEntropyLoss(),
                    self.device
                )

                accuracies.append(accuracy)
                losses.append(test_loss)

                # Get privacy spent for DP clients
                if epsilon != float('inf') and clients:
                    _, privacy_info = clients[0].local_train(
                        coordinator.get_global_model(),
                        local_epochs=1,
                        lr=0.01
                    )
                    privacy_spent.append(privacy_info['epsilon'])
                else:
                    privacy_spent.append(None)

                print(f"   Round {round_num + 1}: Accuracy = {accuracy:.2f}%, Loss = {test_loss:.4f}")

            # Store results for this privacy level
            results['results'].append({
                'epsilon': epsilon,
                'final_accuracy': accuracies[-1] if accuracies else 0,
                'final_loss': losses[-1] if losses else float('inf'),
                'accuracies': accuracies,
                'losses': losses,
                'privacy_spent': privacy_spent,
                'convergence_rounds': len(accuracies)
            })

        # Save results
        self._save_results(results)
        return results

    def run_non_iid_experiment(self, dataset: str = "mimic_cxr",
                              sample_size: int = 1000,
                              num_clients: int = 5,
                              client_fraction: float = 0.5,
                              epsilon: float = float('inf'),
                              num_rounds: int = 10,
                              local_epochs: int = 1) -> Dict[str, Any]:
        """
        Run non-IID data distribution experiment.

        Tests different non-IID levels (α) while keeping other variables constant.
        """
        print(f"\n📊 Running Non-IID Experiment")
        print(f"   Dataset: {dataset}")
        print(f"   Sample Size: {sample_size}")
        print(f"   Clients: {num_clients}")
        print(f"   Privacy: ε={epsilon}")
        print(f"   Rounds: {num_rounds}")

        results = {
            'experiment_type': 'non_iid',
            'dataset': dataset,
            'sample_size': sample_size,
            'num_clients': num_clients,
            'epsilon': epsilon,
            'num_rounds': num_rounds,
            'local_epochs': local_epochs,
            'results': []
        }

        # Test each non-IID level
        for alpha in self.non_iid_levels:
            print(f"\n--- Testing α = {alpha} (non-IID level) ---")

            # Load dataset with current non-IID level
            if dataset == "mimic_cxr":
                client_loaders, test_loader = create_mimic_cxr_data_loaders(
                    num_clients=num_clients,
                    max_samples=sample_size,
                    batch_size=32,
                    iid=False,
                    alpha=alpha
                )
            else:
                client_loaders, test_loader = get_data_loaders(
                    dataset_name="PneumoniaMNIST",
                    num_clients=num_clients,
                    iid=False,
                    batch_size=32,
                    alpha=alpha
                )

            # Select subset of clients
            num_selected_clients = int(num_clients * client_fraction)
            selected_client_indices = list(range(num_selected_clients))

            # Create clients
            clients = []
            for i, loader in enumerate(client_loaders[:num_selected_clients]):
                if epsilon == float('inf'):
                    client = Client(
                        client_id=i,
                        model=MediumCNN(num_classes=2),
                        train_loader=loader
                    )
                else:
                    dp_config = {
                        'enabled': True,
                        'epsilon': epsilon,
                        'delta': 1e-5,
                        'max_grad_norm': 1.0
                    }
                    client = XClient(
                        client_id=i,
                        model=MediumCNN(num_classes=2),
                        train_loader=loader,
                        device=self.device,
                        dp_config=dp_config
                    )
                clients.append(client)

            # Create coordinator and trainer
            global_model = MediumCNN(num_classes=2)
            coordinator = Coordinator(global_model)
            trainer = FederatedTrainer(coordinator, clients, test_loader, self.device)

            # Run federated training
            accuracies = []
            losses = []

            for round_num in range(num_rounds):
                accuracy = trainer.train_round(
                    client_indices=selected_client_indices,
                    local_epochs=local_epochs,
                    lr=0.01
                )

                test_loss = calculate_loss(
                    coordinator.global_model,
                    test_loader,
                    torch.nn.CrossEntropyLoss(),
                    self.device
                )

                accuracies.append(accuracy)
                losses.append(test_loss)

                print(f"   Round {round_num + 1}: Accuracy = {accuracy:.2f}%, Loss = {test_loss:.4f}")

            # Calculate data distribution statistics
            client_sizes = [len(loader.dataset) for loader in client_loaders]

            results['results'].append({
                'alpha': alpha,
                'final_accuracy': accuracies[-1] if accuracies else 0,
                'final_loss': losses[-1] if losses else float('inf'),
                'accuracies': accuracies,
                'losses': losses,
                'client_sizes': client_sizes,
                'data_skew': max(client_sizes) / min(client_sizes) if min(client_sizes) > 0 else 0,
                'convergence_rounds': len(accuracies)
            })

        # Save results
        self._save_results(results)
        return results

    def run_comprehensive_experiment(self, dataset: str = "mimic_cxr", sample_size: int = 1000) -> Dict[str, Any]:
        """
        Run comprehensive experiment covering privacy and non-IID variables.

        This implements the full experimental design matrix from the proposal.
        """
        print(f"\n🎯 Running Comprehensive Experiment")
        print(f"   Dataset: {dataset}")
        print(f"   Sample Size: {sample_size}")

        comprehensive_results = {
            'experiment_type': 'comprehensive',
            'dataset': dataset,
            'sample_size': sample_size,
            'timestamp': datetime.now().isoformat(),
            'privacy_utility_results': [],
            'non_iid_results': []
        }

        # Test privacy-utility trade-off with IID data
        print("\n=== Privacy-Utility Trade-off (IID) ===")
        pu_results = self.run_privacy_utility_experiment(
            dataset=dataset,
            sample_size=sample_size,
            num_clients=5,
            iid=True
        )
        comprehensive_results['privacy_utility_results'].append(pu_results)

        # Test privacy-utility trade-off with non-IID data
        print("\n=== Privacy-Utility Trade-off (Non-IID, α=0.5) ===")
        pu_non_iid_results = self.run_privacy_utility_experiment(
            dataset=dataset,
            sample_size=sample_size,
            num_clients=5,
            iid=False,
            alpha=0.5
        )
        comprehensive_results['privacy_utility_results'].append(pu_non_iid_results)

        # Test non-IID impact with no privacy
        print("\n=== Non-IID Impact (No DP) ===")
        non_iid_results = self.run_non_iid_experiment(
            dataset=dataset,
            sample_size=sample_size,
            num_clients=5,
            epsilon=float('inf')  # No DP
        )
        comprehensive_results['non_iid_results'].append(non_iid_results)

        # Test non-IID impact with moderate privacy
        print("\n=== Non-IID Impact (ε=2.0) ===")
        non_iid_dp_results = self.run_non_iid_experiment(
            dataset=dataset,
            sample_size=sample_size,
            num_clients=5,
            epsilon=2.0
        )
        comprehensive_results['non_iid_results'].append(non_iid_dp_results)

        # Save comprehensive results
        self._save_results(comprehensive_results, filename="comprehensive_results.json")
        return comprehensive_results

    def _save_results(self, results: Dict[str, Any], filename: str = None) -> None:
        """Save experiment results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_type = results.get('experiment_type', 'unknown')
            filename = f"{experiment_type}_{timestamp}.json"

        filepath = os.path.join(self.results_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"💾 Results saved to: {filepath}")

    def analyze_results(self, results_file: str) -> Dict[str, Any]:
        """Analyze experiment results and generate insights."""
        filepath = os.path.join(self.results_dir, results_file)
        with open(filepath, 'r') as f:
            results = json.load(f)

        analysis = {
            'original_results': results,
            'insights': {}
        }

        if results['experiment_type'] == 'privacy_utility':
            # Privacy-utility trade-off analysis
            epsilons = [r['epsilon'] for r in results['results']]
            accuracies = [r['final_accuracy'] for r in results['results']]

            analysis['insights']['privacy_utility_tradeoff'] = {
                'epsilons': epsilons,
                'accuracies': accuracies,
                'best_accuracy': max(accuracies),
                'best_epsilon': epsilons[accuracies.index(max(accuracies))]
            }

            # Calculate privacy-utility ratio
            if max(accuracies) > 0:
                ratios = [acc / (epsilon if epsilon != float('inf') else 1.0)
                         for acc, epsilon in zip(accuracies, epsilons)]
                analysis['insights']['privacy_utility_ratio'] = {
                    'ratios': ratios,
                    'best_ratio': max(ratios),
                    'best_ratio_epsilon': epsilons[ratios.index(max(ratios))]
                }

        elif results['experiment_type'] == 'non_iid':
            # Non-IID impact analysis
            alphas = [r['alpha'] for r in results['results']]
            accuracies = [r['final_accuracy'] for r in results['results']]
            skews = [r['data_skew'] for r in results['results']]

            analysis['insights']['non_iid_impact'] = {
                'alphas': alphas,
                'accuracies': accuracies,
                'data_skews': skews,
                'best_accuracy': max(accuracies),
                'best_alpha': alphas[accuracies.index(max(accuracies))],
                'worst_skew': max(skews)
            }

        # Save analysis
        analysis_filename = f"analysis_{results_file}"
        analysis_path = os.path.join(self.results_dir, analysis_filename)

        with open(analysis_path, 'w') as f:
            json.dump(analysis, f, indent=2)

        print(f"📊 Analysis saved to: {analysis_path}")
        return analysis


def run_basic_experiment():
    """Run a basic experiment to test the framework."""
    print("🧪 Running basic experiment test...")

    runner = ExperimentRunner(experiment_name="basic_test")

    # Run privacy-utility experiment with small subset
    results = runner.run_privacy_utility_experiment(
        dataset="mimic_cxr",
        sample_size=500,  # Small subset for quick testing
        num_clients=3,
        num_rounds=5,  # Fewer rounds for testing
        local_epochs=1
    )

    # Analyze results
    analysis = runner.analyze_results("privacy_utility_*.json")

    print("\n🎉 Basic experiment completed!")
    print(f"   Best accuracy: {analysis['insights']['privacy_utility_tradeoff']['best_accuracy']:.2f}%")
    print(f"   Best epsilon: {analysis['insights']['privacy_utility_tradeoff']['best_epsilon']}")


if __name__ == "__main__":
    print("🚀 ARCH-FL Systematic Experiments")
    print("=" * 50)

    # Run basic test
    run_basic_experiment()

    print("\n✅ Experiment framework ready for comprehensive testing!")
    print("📋 Next steps:")
    print("   1. Run full privacy-utility experiments")
    print("   2. Run non-IID impact experiments")
    print("   3. Run comprehensive experimental matrix")
    print("   4. Analyze results and generate insights")
