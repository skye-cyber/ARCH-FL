#!/usr/bin/env python3
"""
Generate comprehensive visualization report for ARCH-FL experiments.
Creates charts, diagrams, and summary reports for scalability analysis.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, Path(__file__).resolve().parent.parent.as_posix())


def load_experiment_results(results_dir: Path) -> Dict[str, Any]:
    """Load experiment results from directory."""
    results = {}

    # Look for JSON files
    for file_path in results_dir.rglob("*.json"):
        if file_path.name.endswith(".json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                results[file_path.stem] = data
    return results.get("dashboard_integration_results", None) or results


def generate_scalability_charts(data: Dict[str, Any], output_dir: Path) -> None:
    """Generate scalability comparison charts."""
    print("📊 Generating scalability charts...")

    # Use a subset of the data so as to fit in the visualizations
    client_counts = data["clients"]
    rounds_per_minute = data["round_per_min"]
    avg_aggregation_time = data["time"]
    max_memory = data["peak_memory"]
    final_accuracy = data["accuracy"]

    # Sort by client count
    sorted_indices = np.argsort(client_counts)
    client_counts = [client_counts[i] for i in sorted_indices]
    rounds_per_minute = [rounds_per_minute[i] for i in sorted_indices]
    avg_aggregation_time = [avg_aggregation_time[i] for i in sorted_indices]
    max_memory = [max_memory[i] for i in sorted_indices]
    final_accuracy = [final_accuracy[i] for i in sorted_indices]

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    fig.suptitle("ARCH-FL Scalability Analysis", fontsize=16, fontweight="bold")

    # Plot 1: Throughput (Rounds per minute)
    axes[0, 0].bar(
        client_counts,
        rounds_per_minute,
        color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
    )
    axes[0, 0].set_xlabel("Number of Clients", fontsize=12)
    axes[0, 0].set_ylabel("Rounds per Minute", fontsize=12)
    axes[0, 0].set_title(
        "Throughput vs Number of Clients", fontsize=14, fontweight="bold"
    )
    axes[0, 0].grid(True, alpha=0.3)
    for i, v in enumerate(rounds_per_minute):
        axes[0, 0].text(i, v + 0.5, f"{v:.1f}", ha="center", fontsize=10)

    # Plot 2: Aggregation Time
    axes[0, 1].bar(
        client_counts,
        avg_aggregation_time,
        color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
    )
    axes[0, 1].set_xlabel("Number of Clients", fontsize=12)
    axes[0, 1].set_ylabel("Average Aggregation Time (seconds)", fontsize=12)
    axes[0, 1].set_title(
        "Aggregation Time vs Number of Clients", fontsize=14, fontweight="bold"
    )
    axes[0, 1].grid(True, alpha=0.3)
    for i, v in enumerate(avg_aggregation_time):
        axes[0, 1].text(i, v + 0.05, f"{v:.3f}s", ha="center", fontsize=10)

    # Plot 3: Memory Usage
    axes[1, 0].bar(
        client_counts, max_memory, color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    )
    axes[1, 0].set_xlabel("Number of Clients", fontsize=12)
    axes[1, 0].set_ylabel("Max Memory Usage (MB)", fontsize=12)
    axes[1, 0].set_title(
        "Memory Usage vs Number of Clients", fontsize=14, fontweight="bold"
    )
    axes[1, 0].grid(True, alpha=0.3)
    for i, v in enumerate(max_memory):
        axes[1, 0].text(i, v + 5, f"{v:.0f}MB", ha="center", fontsize=10)

    # Plot 4: Accuracy
    axes[1, 1].bar(
        client_counts,
        final_accuracy,
        color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
    )
    axes[1, 1].set_xlabel("Number of Clients", fontsize=12)
    axes[1, 1].set_ylabel("Final Accuracy", fontsize=12)
    axes[1, 1].set_title(
        "Accuracy vs Number of Clients", fontsize=14, fontweight="bold"
    )
    axes[1, 1].grid(True, alpha=0.3)
    for i, v in enumerate(final_accuracy):
        axes[1, 1].text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=10)

    plt.tight_layout()
    output_path = output_dir / "scalability_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved scalability comparison to {output_path}")
    plt.close()


def generate_accuracy_curves(data: Dict[str, Any], output_dir: Path) -> None:
    """Generate accuracy progression curves."""
    print("📈 Generating accuracy curves...")

    # Use data subset
    accuracy_series = data["accuracy"]
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot accuracy progression
    rounds = data["round_per_min"]
    ax.plot(
        rounds,
        accuracy_series,
        "b-",
        marker="o",
        markersize=6,
        linewidth=2,
    )

    # Add trend line
    z = np.polyfit(rounds, accuracy_series, 1)
    p = np.poly1d(z)
    ax.plot(
        rounds,
        p(rounds),
        "r--",
        linewidth=2,
        label=f"Trend: y={z[0]:.4f}x+{z[1]:.4f}",
    )

    ax.set_xlabel("Training Round", fontsize=12)
    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title(
        "Accuracy Progression",
        fontsize=14,
        fontweight="bold",
    )
    ax.grid(True, alpha=0.3)
    # ax.set_ylim(0, 1) Lead to very long graph
    ax.legend(fontsize=10)

    # Add data points
    for i, acc in enumerate(accuracy_series):
        ax.text(rounds[i], acc + 0.01, f"{acc:.3f}", ha="center", fontsize=9)

    plt.tight_layout()
    output_path = output_dir / "accuracy_visualization.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved accuracy curveto {output_path}")
    plt.close()


def generate_resource_usage_plots(data: Dict[str, Any], output_dir: Path) -> None:
    """Generate resource usage plots."""
    print("💾 Generating resource usage plots...")
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle(
        "Resource Usage - CPU_MEM_vs_Time",
        fontsize=14,
        fontweight="bold",
    )

    timestamps = data["timestamps"]

    # Plot CPU usage
    axes[0].plot(timestamps, data["cpu_percent"], "b-", linewidth=2)
    axes[0].set_xlabel("Time (seconds)", fontsize=12)
    axes[0].set_ylabel("CPU Usage (%)", fontsize=12)
    axes[0].set_title("CPU Usage Over Time", fontsize=13, fontweight="bold")
    axes[0].grid(True, alpha=0.3)
    axes[0].set_ylim(0, 100)

    # Plot memory usage
    axes[1].plot(timestamps, data["memory"], "g-", linewidth=2)
    axes[1].set_xlabel("Time (seconds)", fontsize=12)
    axes[1].set_ylabel("Memory Usage (MB)", fontsize=12)
    axes[1].set_title("Memory Usage Over Time", fontsize=13, fontweight="bold")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = output_dir / "resources_CPU_MEM_vs_Time.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved resource usage plot for CPU_MEM_vs_Time to {output_path}")
    plt.close()


def generate_performance_summary(results: Dict[str, Any], output_dir: Path) -> None:
    """Generate performance summary report."""
    print("📋 Generating performance summary...")

    summary = {
        "generated_at": datetime.now().isoformat(),
        "experiments": [],
        "comparison": {},
    }

    # Collect individual experiment data
    for name, data in results.items():
        if "num_clients" in data:
            experiment_summary = {
                "name": name.replace("_", " ").title(),
                "num_clients": data["num_clients"],
                "dataset_size": data.get("dataset_size", "N/A"),
                "num_rounds": data.get("num_rounds", 0),
                "final_accuracy": data.get("final_accuracy", 0),
                "avg_accuracy": data.get("avg_accuracy", 0),
                "rounds_per_minute": data.get("rounds_per_minute", 0),
                "avg_aggregation_time": data.get("avg_aggregation_time", 0),
                "total_duration": data.get("total_duration", 0),
                "max_memory_mb": data["resources"].get("max_memory_mb", 0),
                "avg_cpu_percent": data["resources"].get("average_cpu_percent", 0),
            }
            summary["experiments"].append(experiment_summary)

            # Sort experiments by client count
            summary["experiments"].sort(key=lambda x: x["num_clients"])

            # Generate comparison metrics
            if summary["experiments"]:
                comparison = summary["comparison"]

                # Extract metrics
                client_counts = [e["num_clients"] for e in summary["experiments"]]
                accuracies = [e["final_accuracy"] for e in summary["experiments"]]
                throughput = [e["rounds_per_minute"] for e in summary["experiments"]]
                memory = [e["max_memory_mb"] for e in summary["experiments"]]

                comparison["best_throughput"] = max(throughput)
                comparison["best_throughput_client_count"] = client_counts[
                    throughput.index(max(throughput))
                ]
                comparison["best_accuracy"] = max(accuracies)
                comparison["best_accuracy_client_count"] = client_counts[
                    accuracies.index(max(accuracies))
                ]
                comparison["min_memory"] = min(memory)
                comparison["min_memory_client_count"] = client_counts[
                    memory.index(min(memory))
                ]
                comparison["scalability_factor"] = (
                    throughput[-1] / throughput[0] if len(throughput) > 1 else 1.0
                )

                # Calculate efficiency (accuracy per round per minute)
                efficiency = [(acc * t) for acc, t in zip(accuracies, throughput)]
                comparison["best_efficiency"] = max(efficiency)
                comparison["best_efficiency_client_count"] = client_counts[
                    efficiency.index(max(efficiency))
                ]

            # Save summary JSON
            summary_file = output_dir / "performance_summary.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)
            print(f"✅ Saved performance summary to {summary_file}")

            # Generate markdown report
            markdown_content_list = [
                "# ARCH-FL Performance Report\n\n",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
                "## Executive Summary\n\n",
                "This report summarizes the performance and scalability characteristics of the ARCH-FL system across different client configurations.\n\n",
                "## Experiment Configuration\n\n",
                "| Metric | Value |\n\n",
                "|--------|-------|\n",
                f"| Number of Experiments | {len(summary['experiments'])} |\n",
                f"| Total Rounds | {sum(e['num_rounds'] for e in summary['experiments'])} |\n",
                f"| Client Counts Tested | {', '.join(str(e['num_clients']) for e in summary['experiments'])} |\n",
                "## Performance Comparison\n\n",
                "### Throughput Analysis\n\n",
                f"Best throughput achieved with **{comparison.get('best_throughput_client_count', 'N/A')} clients** at **{comparison.get('best_throughput', 0):.2f} rounds/minute**\n\n",
                "### Accuracy Analysis\n\n",
                f"Best accuracy achieved with **{comparison.get('best_accuracy_client_count', 'N/A')} clients** at **{comparison.get('best_accuracy', 0):.4f}**\n\n",
                "### Efficiency Analysis (Accuracy × Throughput)\n\n",
                f"Best efficiency achieved with **{comparison.get('best_efficiency_client_count', 'N/A')} clients**\n\n",
                "### Memory Efficiency\n\n",
                f"Most memory-efficient configuration: **{comparison.get('min_memory_client_count', 'N/A')} clients** using **{comparison.get('min_memory', 0):.0f} MB**\n\n",
                "### Scalability Factor\n\n",
                f"Throughput scaling factor: **{comparison.get('scalability_factor', 1):.2f}** (compared to single client)\n\n",
                "## Individual Experiment Results",
            ]
            markdown_content = "".join(markdown_content_list)

            for exp in summary["experiments"]:
                markdown_content_exp = [
                    f"### {exp['name']}\n",
                    "**Configuration:**\n",
                    f"- Clients: {exp['num_clients']}\n",
                    f"- Dataset Size: {exp['dataset_size']}\n",
                    f"- Rounds: {exp['num_rounds']}\n\n",
                    "**Performance:**\n",
                    f"- Final Accuracy: {exp['final_accuracy']:.4f}\n",
                    f"- Average Accuracy: {exp['avg_accuracy']:.4f}\n",
                    f"- Throughput: {exp['rounds_per_minute']:.2f} rounds/minute\n",
                    f"- Avg Aggregation Time: {exp['avg_aggregation_time']:.4f} seconds\n",
                    f"- Total Duration: {exp['total_duration']:.2f} seconds\n\n",
                    "**Resource Usage:**\n",
                    f"- Max Memory: {exp['max_memory_mb']:.0f} MB\n",
                    f"- Avg CPU: {exp['avg_cpu_percent']:.1f}%\n\n",
                    "---\n\n",
                ]
                markdown_content = markdown_content.join(markdown_content_exp)

            markdown_file = output_dir / "performance_report.md"
            with open(markdown_file, "w") as f:
                f.write(markdown_content)
            print(f"✅ Saved performance report to {markdown_file}")


def generate_timeline_analysis(data: Dict[str, Any], output_dir: Path) -> None:
    """Generate timeline analysis of aggregation times."""
    print("⏱️  Generating timeline analysis...")
    # Take only a subset of the data
    time_series = data["time"][18:30]

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot aggregation times
    rounds = range(1, len(time_series) + 1)
    ax.bar(rounds, time_series, color="#1f77b4", alpha=0.7)

    # Add average line
    avg_time = sum(time_series) / len(time_series)
    ax.axhline(
        y=avg_time,
        color="r",
        linestyle="--",
        linewidth=1,
        label=f"Average: {avg_time:.4f}s",
    )

    ax.set_xlabel("Training Round", fontsize=12)
    ax.set_ylabel("Aggregation Time (seconds)", fontsize=12)
    ax.set_title(
        "Aggregation Time per Round",
        fontsize=14,
        fontweight="bold",
    )
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    # Add values on bars
    for i, t in enumerate(time_series):
        ax.text(rounds[i], t + 0.01, f"{t:.2f}s", ha="center", fontsize=8)

    plt.tight_layout()
    output_path = output_dir / "aggregation_times.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved aggregation timeline to {output_path}")
    plt.close()


def generate_timeline_vs_clients_analysis(
    data: Dict[str, Any], output_dir: Path
) -> None:
    """Generate timeline analysis of aggregation times."""
    print("⏱️  Generating client timeline analysis...")
    # Take only a subset of the data
    time_series = data["time"][18:30]

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot aggregation times
    clients = data["clients"][18:30]
    ax.bar(clients, time_series, color="#1f77b4", alpha=0.7)

    # Add average line
    avg_time = sum(time_series) / len(time_series)
    ax.axhline(
        y=avg_time,
        color="r",
        linestyle="--",
        linewidth=1,
        label=f"Average: {avg_time:.4f}s",
    )

    ax.set_xlabel("Number of clients", fontsize=12)
    ax.set_ylabel("Aggregation Time (seconds)", fontsize=12)
    ax.set_title(
        "Aggregation Time per client count",
        fontsize=14,
        fontweight="bold",
    )
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    # Add values on bars
    for i, t in enumerate(time_series):
        ax.text(clients[i], t + 0.01, f"{t:.2f}s", ha="center", fontsize=8)

    plt.tight_layout()
    output_path = output_dir / "aggregation_times_vs_client_count.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Saved aggregation vs client timeline to {output_path}")
    plt.close()


def main():
    """Main function to generate visualization report."""
    print("🚀 Starting ARCH-FL Visualization Report Generation")
    print("=" * 60)

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate ARCH-FL visualization report"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=(Path(__file__).parent.parent.absolute() / "assets/experiment_results"),
        help="Input directory containing experiment results",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=(
            Path(__file__).parent.parent.absolute() / "assets/visualization_report"
        ),
        help="Output directory for generated visualizations",
    )

    args = parser.parse_args()

    # Convert to Path objects
    input_dir = Path(args.input).absolute()
    output_dir = Path(args.output).absolute()

    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"📂 Input directory: {input_dir}")
    print(f"📂 Output directory: {output_dir}")
    print()

    # Load experiment results
    if not input_dir.exists():
        print(f"❌ Error: Input directory {input_dir} does not exist!")
        sys.exit(1)

    results = load_experiment_results(input_dir)
    from scripts.prepare_visualization_data import DataHandler

    handler = DataHandler(results)
    data = handler.get_all_series()

    if not results:
        print(f"❌ Error: No experiment results found in {input_dir}!")
        sys.exit(1)

    print(f"📊 Found {len(results)} experiment result(s)")
    for name in results[0].keys():
        print(f"   - {name}")
    print()

    # Generate visualizations
    try:
        generate_scalability_charts(data, output_dir)
        # generate_accuracy_curves(data, output_dir)
        generate_resource_usage_plots(data, output_dir)
        generate_performance_summary(data, output_dir)
        generate_timeline_analysis(data, output_dir)
        generate_timeline_vs_clients_analysis(data, output_dir)

        print()
        print("=" * 60)
        print("✅ Visualization report generation completed successfully!")
        print(f"📁 All outputs saved to: {output_dir}")
        print()
        print("Generated files:")
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                size_kb = file_path.stat().st_size / 1024
                print(f"  - {file_path.name} ({size_kb:.1f} KB)")

    except Exception as e:
        print(f"❌ Error generating visualizations: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
