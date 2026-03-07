#!/usr/bin/env python3
"""
ARCH-FL Dashboard Diagram Generator

Generates visual diagrams for documentation and the dashboard.
"""

import os
import sys
from pathlib import Path

def generate_mermaid_diagrams():
    """Generate Mermaid.js diagrams for documentation."""
    
    diagrams_dir = Path(__file__).parent / "docs" / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. System Architecture Diagram
    architecture_diagram = """
```mermaid
graph TD
    A[User] -->|Interacts with| B[Dashboard Frontend]
    B -->|API Calls| C[Dashboard Backend]
    C -->|Integrates with| D[ARCH-FL Core]
    D -->|Uses| E[Data Loader Registry]
    D -->|Uses| F[Architecture Registry]
    D -->|Uses| G[Model Factory]
    C -->|Stores in| H[SQLite Database]
    
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#bbf,stroke:#333
    style D fill:#f96,stroke:#333
    style E fill:#9f9,stroke:#333
    style F fill:#9f9,stroke:#333
    style G fill:#9f9,stroke:#333
    style H fill:#66f,stroke:#333
```
"""
    
    # 2. Federated Learning Process Diagram
    fl_process_diagram = """
```mermaid
graph LR
    subgraph Global Server
        A[Global Model] -->|Send to| B[Client 1]
        A -->|Send to| C[Client 2]
        A -->|Send to| D[Client N]
        B -->|Local Updates| A
        C -->|Local Updates| A
        D -->|Local Updates| A
    end
    
    subgraph Client Process
        B --> E[Train on Local Data]
        E --> F[Compute Updates]
        F --> B
    end
    
    style A fill:#66f,stroke:#333
    style B fill:#9f9,stroke:#333
    style C fill:#9f9,stroke:#333
    style D fill:#9f9,stroke:#333
    style E fill:#ff9,stroke:#333
    style F fill:#f96,stroke:#333
```
"""
    
    # 3. Dashboard Component Diagram
    component_diagram = """
```mermaid
graph TD
    subgraph Frontend Components
        A[Layout] --> B[Navigation]
        A --> C[Pages]
        C --> D[Home]
        C --> E[Experiments]
        C --> F[ExperimentDetail]
        C --> G[Architectures]
        C --> H[Settings]
        C --> I[ExperimentCreate]
    end
    
    subgraph Backend Services
        J[API Endpoints] --> K[ExperimentService]
        J --> L[ArchitectureService]
        J --> M[DatasetService]
        K --> N[SQLite Database]
        L --> N
        M --> N
    end
    
    A -->|Fetches data from| J
    
    style A fill:#bbf,stroke:#333
    style B fill:#99f,stroke:#333
    style C fill:#99f,stroke:#333
    style D fill:#66f,stroke:#333
    style E fill:#66f,stroke:#333
    style F fill:#66f,stroke:#333
    style G fill:#66f,stroke:#333
    style H fill:#66f,stroke:#333
    style I fill:#66f,stroke:#333
    style J fill:#f66,stroke:#333
    style K fill:#f96,stroke:#333
    style L fill:#f96,stroke:#333
    style M fill:#f96,stroke:#333
    style N fill:#66f,stroke:#333
```
"""
    
    # 4. Experiment Workflow Diagram
    workflow_diagram = """
```mermaid
graph LR
    A[Start] --> B[Configure Experiment]
    B --> C[Select Dataset]
    C --> D[Choose Architecture]
    D --> E[Set Parameters]
    E --> F[Review Configuration]
    F --> G[Start Experiment]
    G --> H[Monitor Progress]
    H --> I[Analyze Results]
    I --> J[Save/Export]
    J --> K[End]
    
    style A fill:#999,stroke:#333
    style B fill:#66f,stroke:#333
    style C fill:#66f,stroke:#333
    style D fill:#66f,stroke:#333
    style E fill:#66f,stroke:#333
    style F fill:#66f,stroke:#333
    style G fill:#9f9,stroke:#333
    style H fill:#ff9,stroke:#333
    style I fill:#f96,stroke:#333
    style J fill:#99f,stroke:#333
    style K fill:#999,stroke:#333
```
"""
    
    # Write diagrams to files
    diagrams = [
        ("architecture.md", "ARCH-FL Dashboard Architecture", architecture_diagram),
        ("federated_learning.md", "Federated Learning Process", fl_process_diagram),
        ("components.md", "Dashboard Components", component_diagram),
        ("workflow.md", "Experiment Workflow", workflow_diagram)
    ]
    
    for filename, title, content in diagrams:
        file_path = diagrams_dir / filename
        with open(file_path, 'w') as f:
            f.write(f"# {title}\n\n")
            f.write(content)
            f.write("\n")
        print(f"✅ Generated {filename}")
    
    print(f"\n🎉 All diagrams generated in {diagrams_dir}")

def generate_simple_visualizations():
    """Generate simple visual assets for the dashboard."""
    
    assets_dir = Path(__file__).parent / "frontend" / "src" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple CSS file for visual enhancements
    css_content = """
/* Dashboard Visual Enhancements */

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}

/* Gradient backgrounds */
.bg-gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.bg-gradient-success {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

/* Card hover effects */
.card-hover {
  transition: all 0.3s ease;
}

.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* Status badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-completed {
  background-color: #d1fae5;
  color: #065f46;
}

.status-running {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-failed {
  background-color: #fee2e2;
  color: #991b1b;
}

.status-pending {
  background-color: #fef3c7;
  color: #92400e;
}
"""
    
    css_file = assets_dir / "dashboard.css"
    with open(css_file, 'w') as f:
        f.write(css_content)
    print(f"✅ Generated {css_file}")

def main():
    """Main function to generate all diagrams and assets."""
    
    print("🚀 Starting diagram and asset generation...")
    print("=" * 50)
    
    try:
        generate_mermaid_diagrams()
        print()
        generate_simple_visualizations()
        print()
        print("🎉 All diagrams and assets generated successfully!")
        print()
        print("Generated files:")
        print("- Mermaid diagrams in dashboard/docs/diagrams/")
        print("- CSS enhancements in dashboard/frontend/src/assets/dashboard.css")
        
    except Exception as e:
        print(f"❌ Error generating diagrams: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()