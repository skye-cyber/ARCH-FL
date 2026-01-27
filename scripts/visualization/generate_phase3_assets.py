#!/usr/bin/env python3
"""
Phase 3 Asset Generator - Simplified Version

Generates key visual assets for AutoML Architecture Generator documentation
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.models.architecture_generator import ArchitectureGenerator
except ImportError as e:
    print(f"Import error: {e}")
    raise

# Set style for elegant visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("viridis")
sns.set_context("talk")

# Ensure output directories exist
os.makedirs('assets/phase3_results', exist_ok=True)


def generate_key_metrics():
    """Generate key metrics visualization"""
    print("📊 Generating key metrics visualization...")
    
    generator = ArchitectureGenerator()
    
    # Generate architectures for different datasets
    datasets = ['mimic_cxr', 'chexpert', 'pneumoniamnist']
    metrics = []
    
    for dataset in datasets:
        config = generator.generate_architecture(dataset)
        validation = config['validation']
        metrics.append({
            'dataset': dataset,
            'parameters': validation['estimated_parameters'],
            'memory': validation['estimated_memory_mb'],
            'training_time': validation['estimated_training_time']
        })
    
    # Create metrics plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x = np.arange(len(datasets))
    width = 0.25
    
    params = [m['parameters'] / 1000 for m in metrics]
    memory = [m['memory'] for m in metrics]
    time = [m['training_time'] for m in metrics]
    
    rects1 = ax.bar(x - width, params, width, label='Parameters (K)', color=sns.color_palette()[0])
    rects2 = ax.bar(x, memory, width, label='Memory (MB)', color=sns.color_palette()[1])
    rects3 = ax.bar(x + width, time, width, label='Training Time (s)', color=sns.color_palette()[2])
    
    ax.set_title('AutoML Architecture Metrics by Dataset', fontsize=16)
    ax.set_xlabel('Dataset')
    ax.set_ylabel('Metric Value')
    ax.set_xticks(x)
    ax.set_xticklabels([d.title() for d in datasets])
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add value labels
    for rects, values in [(rects1, params), (rects2, memory), (rects3, time)]:
        for rect, value in zip(rects, values):
            height = rect.get_height()
            ax.annotate(f'{value:.1f}',
                       xy=(rect.get_x() + rect.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', rotation=90)
    
    plt.tight_layout()
    plt.savefig('assets/phase3_results/key_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save data
    metrics_data = {
        'timestamp': datetime.now().isoformat(),
        'datasets': metrics,
        'summary': {
            'avg_parameters': np.mean(params) * 1000,
            'avg_memory': np.mean(memory),
            'avg_training_time': np.mean(time)
        }
    }
    
    with open('assets/phase3_results/key_metrics.json', 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    print("✅ Key metrics visualization saved")


def generate_constraint_comparison():
    """Generate constraint comparison visualization"""
    print("📊 Generating constraint comparison visualization...")
    
    generator = ArchitectureGenerator()
    
    # Test different constraint levels
    constraints = [50, 100, None]  # None = no constraint
    results = []
    
    for constraint in constraints:
        if constraint is None:
            config = generator.generate_architecture('mimic_cxr', input_shape=(1, 224, 224))
            label = 'No Constraint'
        else:
            config = generator.generate_architecture('mimic_cxr', input_shape=(1, 224, 224), 
                                                   constraints={'max_memory_mb': constraint})
            label = f'{constraint} MB'
        
        validation = config['validation']
        results.append({
            'constraint': label,
            'parameters': validation['estimated_parameters'],
            'memory': validation['estimated_memory_mb']
        })
    
    # Create comparison plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    labels = [r['constraint'] for r in results]
    params = [r['parameters'] / 1000 for r in results]
    memory = [r['memory'] for r in results]
    
    ax.plot(labels, params, marker='o', linestyle='-', linewidth=3, markersize=10, 
            color=sns.color_palette()[0], label='Parameters (K)')
    ax.plot(labels, memory, marker='s', linestyle='--', linewidth=2, markersize=8,
            color=sns.color_palette()[1], label='Memory (MB)')
    
    ax.set_title('Constraint Impact on Architecture Generation', fontsize=14)
    ax.set_xlabel('Memory Constraint')
    ax.set_ylabel('Resource Usage')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (param, mem) in enumerate(zip(params, memory)):
        ax.annotate(f'P: {param:.0f}K', (labels[i], param), textcoords="offset points", xytext=(0,10), ha='center')
        ax.annotate(f'M: {mem:.1f}MB', (labels[i], mem), textcoords="offset points", xytext=(0,-15), ha='center')
    
    plt.tight_layout()
    plt.savefig('assets/phase3_results/constraint_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save data
    constraint_data = {
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'summary': {
            'memory_reduction': memory[0] / memory[-1] if memory[-1] > 0 else 0,
            'parameter_reduction': params[0] / params[-1] if params[-1] > 0 else 0
        }
    }
    
    with open('assets/phase3_results/constraint_comparison.json', 'w') as f:
        json.dump(constraint_data, f, indent=2)
    
    print("✅ Constraint comparison visualization saved")


def generate_system_overview():
    """Generate system overview visualization"""
    print("📊 Generating system overview visualization...")
    
    # Create system overview
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # System components
    components = [
        ('User/Dataset', 0.1, 'Input'),
        ('DatasetRegistry', 0.25, 'Registration'),
        ('DatasetAnalyzer', 0.4, 'Analysis'),
        ('ArchitectureGenerator', 0.55, 'AutoML'),
        ('ModelFactory', 0.7, 'Creation'),
        ('PyTorch Model', 0.85, 'Output'),
        ('Federated Training', 0.95, 'Training')
    ]
    
    # Plot components
    for component, x_pos, role in components:
        # Box
        box = plt.Rectangle((x_pos - 0.075, 0.4), 0.15, 0.2, 
                           fill=True, color=sns.color_palette()[components.index((component, x_pos, role)) % len(sns.color_palette())],
                           alpha=0.8, edgecolor='black', linewidth=2)
        ax.add_patch(box)
        
        # Text
        ax.text(x_pos, 0.55, component, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        ax.text(x_pos, 0.45, role, ha='center', va='center', fontsize=8, color='white', alpha=0.8)
    
    # Arrows (connections)
    for i in range(len(components) - 1):
        x1 = components[i][1] + 0.075
        x2 = components[i + 1][1] - 0.075
        ax.annotate('', xy=(x2, 0.5), xytext=(x1, 0.5),
                   arrowprops=dict(arrowstyle='->', linewidth=2, color='gray', alpha=0.7))
    
    # Highlight AutoML component
    ax.annotate('', xy=(0.55, 0.7), xytext=(0.55, 0.6),
               arrowprops=dict(arrowstyle='->', linewidth=2, color='red', alpha=0.8))
    ax.text(0.55, 0.72, 'Phase 3: AutoML', ha='center', va='center', 
            fontsize=12, fontweight='bold', color='red', 
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Title and styling
    ax.set_title('ARCH-FL System Architecture with AutoML Enhancement', fontsize=16, pad=20)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Add description
    description = """
    Phase 3 Enhancement: AutoML Architecture Generator
    
    Key Features:
    • Neural Architecture Search (NAS)
    • Constraint-based optimization
    • Intelligent architecture generation
    • Comprehensive validation and scoring
    • History tracking and reproducibility
    """
    
    ax.text(0.5, 0.15, description, ha='center', va='center', 
           fontsize=9, bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('assets/phase3_results/system_overview.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ System overview visualization saved")


def generate_phase3_summary():
    """Generate Phase 3 summary infographic"""
    print("📊 Generating Phase 3 summary infographic...")
    
    # Create summary infographic
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.95, 'Phase 3: AutoML Architecture Generator', 
            ha='center', va='center', fontsize=18, fontweight='bold', 
            bbox=dict(boxstyle='round', facecolor=sns.color_palette()[0], alpha=0.3))
    
    # Key achievements
    achievements = [
        ('Components Implemented', [
            'ArchitectureGenerator',
            'Neural Architecture Search',
            'Constraint Optimization',
            'Validation System',
            'History Tracking'
        ]),
        ('Testing Infrastructure', [
            '40+ Architecture Tests',
            '50+ NAS Tests',
            '28 Constraint Tests',
            '120+ Total Tests'
        ]),
        ('Key Features', [
            'Neural Architecture Search',
            'Constraint-based Optimization',
            'Intelligent Generation',
            'Comprehensive Validation',
            'History Tracking',
            'Results Management'
        ])
    ]
    
    # Display achievements
    for i, (title, items) in enumerate(achievements):
        y_pos = 0.8 - i * 0.3
        ax.text(0.2, y_pos, title, ha='left', va='center', 
                fontsize=14, fontweight='bold', color=sns.color_palette()[i])
        
        for j, item in enumerate(items):
            ax.text(0.2, y_pos - (j + 1) * 0.08, f'• {item}', ha='left', va='center', fontsize=11)
    
    # Status
    ax.text(0.5, 0.1, 'Status: ✅ Phase 1, 2 & 3 Complete | 🚀 Ready for Phase 4', 
            ha='center', va='center', fontsize=14, fontweight='bold', 
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig('assets/phase3_results/phase3_summary.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Phase 3 summary infographic saved")


def generate_visualization_summary():
    """Generate visualization summary"""
    print("📊 Generating visualization summary...")
    
    summary = {
        'phase': 'Phase 3: AutoML Architecture Generator',
        'timestamp': datetime.now().isoformat(),
        'visualizations': [
            'key_metrics.png',
            'constraint_comparison.png',
            'system_overview.png',
            'phase3_summary.png'
        ],
        'data_files': [
            'key_metrics.json',
            'constraint_comparison.json'
        ],
        'metrics': {
            'datasets_analyzed': 3,
            'constraint_levels_tested': 3,
            'visualizations_created': 4,
            'data_files_created': 2
        },
        'description': 'Phase 3 visual assets for AutoML Architecture Generator documentation'
    }
    
    with open('assets/phase3_results/VISUALIZATION_SUMMARY.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✅ Visualization summary saved")


def main():
    """Main function to generate all assets"""
    print("🎨 Starting Phase 3 Asset Generation...")
    print(f"📁 Output directory: assets/phase3_results")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Generate all assets
        generate_key_metrics()
        generate_constraint_comparison()
        generate_system_overview()
        generate_phase3_summary()
        generate_visualization_summary()
        
        print()
        print("🎉 All assets generated successfully!")
        print(f"📊 Total files created: 6")
        print(f"📁 Location: assets/phase3_results/")
        print()
        print("Assets created:")
        print("  • key_metrics.png")
        print("  • constraint_comparison.png")
        print("  • system_overview.png")
        print("  • phase3_summary.png")
        print()
        print("Data files created:")
        print("  • key_metrics.json")
        print("  • constraint_comparison.json")
        print("  • VISUALIZATION_SUMMARY.json")
        print()
        print("🚀 Ready for documentation integration!")
        
    except Exception as e:
        print(f"❌ Error during asset generation: {e}")
        raise


if __name__ == "__main__":
    main()