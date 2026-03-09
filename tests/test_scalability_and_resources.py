"""
Comprehensive scalability and resource usage tests for ARCH-FL.
Tests different client counts (1, 10, 100) and tracks resource usage.
"""

import pytest
import time
import torch
import psutil
import os
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, Path(__file__).resolve().parent.parent.as_posix())

from src.models.model_factory import ModelFactory
from src.core.coordinator import Coordinator
from src.data.partitioning import partition_iid, partition_non_iid
from src.core.client import Client
from src.data.datasets import MedicalDataset
from src.utils.metrics import calculate_accuracy


class ResourceTracker:
    """Track resource usage during experiments."""
    
    def __init__(self):
        self.timestamps = []
        self.cpu_percentages = []
        self.memory_usage = []
        self.start_time = None
        self.end_time = None
        
    def start_tracking(self):
        """Start tracking resources."""
        self.start_time = time.time()
        self._record_resources()
    
    def stop_tracking(self):
        """Stop tracking resources."""
        self.end_time = time.time()
        self._record_resources()
    
    def _record_resources(self):
        """Record current resource usage."""
        process = psutil.Process(os.getpid())
        self.timestamps.append(time.time())
        self.cpu_percentages.append(psutil.cpu_percent(interval=0.1))
        self.memory_usage.append(process.memory_info().rss / (1024 * 1024))  # MB
    
    def get_duration(self) -> float:
        """Get experiment duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    def get_average_cpu(self) -> float:
        """Get average CPU usage."""
        if self.cpu_percentages:
            return sum(self.cpu_percentages) / len(self.cpu_percentages)
        return 0.0
    
    def get_max_memory(self) -> float:
        """Get maximum memory usage."""
        if self.memory_usage:
            return max(self.memory_usage)
        return 0.0
    
    def to_dict(self) -> Dict:
        """Convert resource data to dictionary."""
        return {
            'duration_seconds': self.get_duration(),
            'average_cpu_percent': self.get_average_cpu(),
            'max_memory_mb': self.get_max_memory(),
            'timestamps': self.timestamps,
            'cpu_percentages': self.cpu_percentages,
            'memory_usage_mb': self.memory_usage
        }


class FederatedLearningExperiment:
    """Run federated learning experiments with resource tracking."""
    
    def __init__(self, num_clients: int, dataset_size: int = 1000):
        self.num_clients = num_clients
        self.dataset_size = dataset_size
        self.resource_tracker = ResourceTracker()
        self.accuracy_history = []
        self.aggregation_times = []
        
    def setup_dataset(self) -> MedicalDataset:
        """Create synthetic dataset for testing."""
        # Create synthetic dataset
        dataset = MedicalDataset(
            data=[torch.randn(1, 224, 224) for _ in range(self.dataset_size)],
            labels=[0 if i % 2 == 0 else 1 for i in range(self.dataset_size)]
        )
        return dataset
    
    def setup_model(self) -> torch.nn.Module:
        """Create model for the experiment."""
        factory = ModelFactory()
        return factory.create_model_from_dataset('mimic_cxr', (1, 224, 224))
    
    def run_experiment(self, num_rounds: int = 5, iid: bool = True) -> Dict:
        """Run federated learning experiment."""
        # Setup
        dataset = self.setup_dataset()
        model = self.setup_model()
        coordinator = Coordinator(model)
        
        # Partition dataset
        if iid:
            client_datasets = partition_iid(dataset, self.num_clients)
        else:
            client_datasets = partition_non_iid(dataset, self.num_clients, alpha=0.5)
        
        # Create clients
        clients = []
        for i, client_dataset in enumerate(client_datasets):
            client_model = self.setup_model()
            client = Client(client_id=i, model=client_model, train_loader=client_dataset)
            clients.append(client)
        
        # Start resource tracking
        self.resource_tracker.start_tracking()
        
        # Run federated learning rounds
        for round_num in range(1, num_rounds + 1):
            start_time = time.time()
            
            # Each client trains
            client_updates = []
            client_sizes = []
            
            for client in clients:
                # Train for 1 epoch
                client.train(num_epochs=1)
                client_updates.append(client.get_model().state_dict())
                client_sizes.append(len(client.train_loader))
            
            # Aggregate at server
            coordinator.aggregate(client_updates, client_sizes, round_num=round_num)
            
            # Track aggregation time
            aggregation_time = time.time() - start_time
            self.aggregation_times.append(aggregation_time)
            
            # Calculate accuracy (simplified)
            accuracy = self._calculate_accuracy(coordinator.get_global_model(), dataset)
            self.accuracy_history.append(accuracy)
            
            print(f"Round {round_num}/{num_rounds}: Accuracy={accuracy:.4f}, "
                  f"Aggregation time={aggregation_time:.4f}s")
        
        # Stop resource tracking
        self.resource_tracker.stop_tracking()
        
        # Return results
        return self._get_results()
    
    def _calculate_accuracy(self, model: torch.nn.Module, dataset: MedicalDataset) -> float:
        """Calculate model accuracy on dataset."""
        model.eval()
        with torch.no_grad():
            correct = 0
            total = 0
            for i in range(min(100, len(dataset))):  # Test on subset for speed
                image, label = dataset[i]
                image = image.unsqueeze(0)
                outputs = model(image)
                _, predicted = torch.max(outputs.data, 1)
                total += 1
                correct += (predicted == label).item()
        return correct / total
    
    def _get_results(self) -> Dict:
        """Get experiment results."""
        return {
            'num_clients': self.num_clients,
            'dataset_size': self.dataset_size,
            'num_rounds': len(self.accuracy_history),
            'final_accuracy': self.accuracy_history[-1] if self.accuracy_history else 0,
            'avg_accuracy': sum(self.accuracy_history) / len(self.accuracy_history) if self.accuracy_history else 0,
            'avg_aggregation_time': sum(self.aggregation_times) / len(self.aggregation_times) if self.aggregation_times else 0,
            'total_duration': self.resource_tracker.get_duration(),
            'rounds_per_minute': (len(self.accuracy_history) / self.resource_tracker.get_duration()) * 60 if self.resource_tracker.get_duration() > 0 else 0,
            'resources': self.resource_tracker.to_dict(),
            'accuracy_history': self.accuracy_history,
            'aggregation_times': self.aggregation_times
        }


@pytest.fixture
def experiment_results_dir(tmp_path):
    """Create directory for experiment results."""
    results_dir = tmp_path / "experiment_results"
    results_dir.mkdir()
    return results_dir


def test_single_client_experiment(experiment_results_dir):
    """Test federated learning with 1 client."""
    print("\n" + "="*60)
    print("Testing with 1 client")
    print("="*60)
    
    experiment = FederatedLearningExperiment(num_clients=1, dataset_size=500)
    results = experiment.run_experiment(num_rounds=3)
    
    # Save results
    results_file = experiment_results_dir / "single_client_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nSingle Client Results:")
    print(f"  Final Accuracy: {results['final_accuracy']:.4f}")
    print(f"  Avg Accuracy: {results['avg_accuracy']:.4f}")
    print(f"  Rounds per Minute: {results['rounds_per_minute']:.2f}")
    print(f"  Avg Aggregation Time: {results['avg_aggregation_time']:.4f}s")
    print(f"  Max Memory Usage: {results['resources']['max_memory_mb']:.2f} MB")
    print(f"  Total Duration: {results['resources']['duration_seconds']:.2f}s")
    
    # Basic assertions
    assert results['final_accuracy'] > 0.4  # Should have some accuracy
    assert results['rounds_per_minute'] > 0
    assert results['resources']['max_memory_mb'] > 0


def test_ten_clients_experiment(experiment_results_dir):
    """Test federated learning with 10 clients."""
    print("\n" + "="*60)
    print("Testing with 10 clients")
    print("="*60)
    
    experiment = FederatedLearningExperiment(num_clients=10, dataset_size=1000)
    results = experiment.run_experiment(num_rounds=3)
    
    # Save results
    results_file = experiment_results_dir / "ten_clients_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nTen Clients Results:")
    print(f"  Final Accuracy: {results['final_accuracy']:.4f}")
    print(f"  Avg Accuracy: {results['avg_accuracy']:.4f}")
    print(f"  Rounds per Minute: {results['rounds_per_minute']:.2f}")
    print(f"  Avg Aggregation Time: {results['avg_aggregation_time']:.4f}s")
    print(f"  Max Memory Usage: {results['resources']['max_memory_mb']:.2f} MB")
    print(f"  Total Duration: {results['resources']['duration_seconds']:.2f}s")
    
    # Basic assertions
    assert results['final_accuracy'] > 0.4  # Should have some accuracy
    assert results['rounds_per_minute'] > 0
    assert results['resources']['max_memory_mb'] > 0


def test_hundred_clients_experiment(experiment_results_dir):
    """Test federated learning with 100 clients."""
    print("\n" + "="*60)
    print("Testing with 100 clients")
    print("="*60)
    
    experiment = FederatedLearningExperiment(num_clients=100, dataset_size=2000)
    results = experiment.run_experiment(num_rounds=3)
    
    # Save results
    results_file = experiment_results_dir / "hundred_clients_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nHundred Clients Results:")
    print(f"  Final Accuracy: {results['final_accuracy']:.4f}")
    print(f"  Avg Accuracy: {results['avg_accuracy']:.4f}")
    print(f"  Rounds per Minute: {results['rounds_per_minute']:.2f}")
    print(f"  Avg Aggregation Time: {results['avg_aggregation_time']:.4f}s")
    print(f"  Max Memory Usage: {results['resources']['max_memory_mb']:.2f} MB")
    print(f"  Total Duration: {results['resources']['duration_seconds']:.2f}s")
    
    # Basic assertions
    assert results['final_accuracy'] > 0.4  # Should have some accuracy
    assert results['rounds_per_minute'] > 0
    assert results['resources']['max_memory_mb'] > 0


def test_scalability_comparison(experiment_results_dir):
    """Compare scalability across different client counts."""
    print("\n" + "="*60)
    print("Scalability Comparison")
    print("="*60)
    
    # Load results
    results_files = {
        '1_client': experiment_results_dir / "single_client_results.json",
        '10_clients': experiment_results_dir / "ten_clients_results.json",
        '100_clients': experiment_results_dir / "hundred_clients_results.json"
    }
    
    all_results = {}
    for name, file_path in results_files.items():
        if file_path.exists():
            with open(file_path, 'r') as f:
                all_results[name] = json.load(f)
    
    # Extract metrics
    client_counts = []
    rounds_per_minute = []
    avg_aggregation_time = []
    max_memory = []
    final_accuracy = []
    
    for name, results in all_results.items():
        client_counts.append(results['num_clients'])
        rounds_per_minute.append(results['rounds_per_minute'])
        avg_aggregation_time.append(results['avg_aggregation_time'])
        max_memory.append(results['resources']['max_memory_mb'])
        final_accuracy.append(results['final_accuracy'])
    
    # Print comparison table
    print(f"\n{'Client Count':<15} {'Rounds/min':<15} {'Avg Agg Time (s)':<20} {'Max Memory (MB)':<20} {'Final Accuracy':<15}")
    print("-" * 90)
    for i, count in enumerate(client_counts):
        print(f"{count:<15} {rounds_per_minute[i]:<15.2f} {avg_aggregation_time[i]:<20.4f} "
              f"{max_memory[i]:<20.2f} {final_accuracy[i]:<15.4f}")
    
    # Generate plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Rounds per minute vs Client count
    axes[0, 0].plot(client_counts, rounds_per_minute, 'bo-')
    axes[0, 0].set_xlabel('Number of Clients')
    axes[0, 0].set_ylabel('Rounds per Minute')
    axes[0, 0].set_title('Throughput vs Number of Clients')
    axes[0, 0].grid(True)
    
    # Plot 2: Aggregation time vs Client count
    axes[0, 1].plot(client_counts, avg_aggregation_time, 'ro-')
    axes[0, 1].set_xlabel('Number of Clients')
    axes[0, 1].set_ylabel('Average Aggregation Time (seconds)')
    axes[0, 1].set_title('Aggregation Time vs Number of Clients')
    axes[0, 1].grid(True)
    
    # Plot 3: Memory usage vs Client count
    axes[1, 0].plot(client_counts, max_memory, 'go-')
    axes[1, 0].set_xlabel('Number of Clients')
    axes[1, 0].set_ylabel('Max Memory Usage (MB)')
    axes[1, 0].set_title('Memory Usage vs Number of Clients')
    axes[1, 0].grid(True)
    
    # Plot 4: Accuracy vs Client count
    axes[1, 1].plot(client_counts, final_accuracy, 'mo-')
    axes[1, 1].set_xlabel('Number of Clients')
    axes[1, 1].set_ylabel('Final Accuracy')
    axes[1, 1].set_title('Accuracy vs Number of Clients')
    axes[1, 1].grid(True)
    
    plt.tight_layout()
    
    # Save plots
    plots_dir = experiment_results_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    comparison_plot = plots_dir / "scalability_comparison.png"
    plt.savefig(comparison_plot)
    print(f"\n📊 Saved scalability comparison plot to: {comparison_plot}")
    plt.close()
    
    # Generate individual accuracy plots
    for name, results in all_results.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(range(1, len(results['accuracy_history']) + 1), 
                results['accuracy_history'], 'b-', marker='o')
        ax.set_xlabel('Training Round')
        ax.set_ylabel('Accuracy')
        ax.set_title(f'Accuracy Progress - {name.replace("_", " ").title()}')
        ax.grid(True)
        ax.set_ylim(0, 1)
        
        plot_file = plots_dir / f"accuracy_{name}.png"
        plt.savefig(plot_file)
        print(f"📊 Saved accuracy plot for {name} to: {plot_file}")
        plt.close()
    
    # Generate resource usage plot
    for name, results in all_results.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot memory usage over time
        if results['resources']['timestamps']:
            timestamps = [t - results['resources']['timestamps'][0] for t in results['resources']['timestamps']]
            ax.plot(timestamps, results['resources']['memory_usage_mb'], 'b-', label='Memory Usage')
            ax.set_xlabel('Time (seconds)')
            ax.set_ylabel('Memory Usage (MB)')
            ax.set_title(f'Resource Usage - {name.replace("_", " ").title()}')
            ax.grid(True)
            ax.legend()
        
        plot_file = plots_dir / f"resources_{name}.png"
        plt.savefig(plot_file)
        print(f"📊 Saved resource usage plot for {name} to: {plot_file}")
        plt.close()
    
    # Save comparison summary
    comparison_summary = {
        'client_counts': client_counts,
        'rounds_per_minute': rounds_per_minute,
        'avg_aggregation_time': avg_aggregation_time,
        'max_memory_mb': max_memory,
        'final_accuracy': final_accuracy
    }
    
    summary_file = experiment_results_dir / "scalability_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(comparison_summary, f, indent=2)
    
    print(f"\n📊 Saved scalability summary to: {summary_file}")


def test_non_iid_scalability(experiment_results_dir):
    """Test scalability with non-IID data distribution."""
    print("\n" + "="*60)
    print("Testing Non-IID Scalability (10 clients)")
    print("="*60)
    
    experiment = FederatedLearningExperiment(num_clients=10, dataset_size=1000)
    results = experiment.run_experiment(num_rounds=3, iid=False)
    
    # Save results
    results_file = experiment_results_dir / "non_iid_10_clients_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nNon-IID (10 clients) Results:")
    print(f"  Final Accuracy: {results['final_accuracy']:.4f}")
    print(f"  Avg Accuracy: {results['avg_accuracy']:.4f}")
    print(f"  Rounds per Minute: {results['rounds_per_minute']:.2f}")
    print(f"  Avg Aggregation Time: {results['avg_aggregation_time']:.4f}s")
    print(f"  Max Memory Usage: {results['resources']['max_memory_mb']:.2f} MB")
    
    # Basic assertions
    assert results['final_accuracy'] > 0.4  # Should have some accuracy
    assert results['rounds_per_minute'] > 0


def test_resource_usage_tracking():
    """Test that resource tracking works correctly."""
    tracker = ResourceTracker()
    
    # Start tracking
    tracker.start_tracking()
    
    # Simulate some work
    time.sleep(0.5)
    
    # Stop tracking
    tracker.stop_tracking()
    
    # Verify results
    assert tracker.get_duration() > 0.4  # Should be at least 0.4 seconds
    assert tracker.get_duration() < 1.0  # Should be less than 1 second
    assert tracker.get_average_cpu() >= 0
    assert tracker.get_max_memory() > 0
    
    # Verify dictionary conversion
    data = tracker.to_dict()
    assert 'duration_seconds' in data
    assert 'average_cpu_percent' in data
    assert 'max_memory_mb' in data
    assert 'timestamps' in data
    assert 'cpu_percentages' in data
    assert 'memory_usage_mb' in data


if __name__ == "__main__":
    # Run tests manually for debugging
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir) / "experiment_results"
        results_dir.mkdir()
        
        test_single_client_experiment(results_dir)
        test_ten_clients_experiment(results_dir)
        test_hundred_clients_experiment(results_dir)
        test_scalability_comparison(results_dir)
        test_non_iid_scalability(results_dir)
        test_resource_usage_tracking()
        
        print("\n" + "="*60)
        print("All scalability tests completed successfully!")
        print("="*60)
