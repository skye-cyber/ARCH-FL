# ARCH-FL Core Architecture

This diagram shows the core architecture of the ARCH-FL framework without the UI components.

```mermaid
graph TD
    subgraph ARCH-FL Core
        A[Data Loader Registry] -->|Provides| B[Dataset Factory]
        B -->|Creates| C[Medical Datasets]

        D[Architecture Registry] -->|Manages| E[Model Architectures]
        E -->|Used by| F[Model Factory]

        G[Federated Learning Coordinator] -->|Uses| C
        G -->|Uses| F
        G -->|Manages| H[Client Management]

        H -->|Coordinates| I[Client 1]
        H -->|Coordinates| J[Client 2]
        H -->|Coordinates| K[Client N]

        L[Privacy Engine] -->|Ensures| G
        L -->|Implements| M[Differential Privacy]
        L -->|Implements| N[Secure Aggregation]

        O[Experiment Manager] -->|Configures| G
        O -->|Tracks| P[Experiment Results]

        Q[Performance Monitor] -->|Logs| P
        Q -->|Analyzes| R[Metrics]
    end

    subgraph External Systems
        S[Medical Data Sources] -->|Provides| A
        T[PyTorch] -->|Used by| F
        U[Researcher] -->|Configures| O
    end

    style A fill:#9f9,stroke:#333
    style B fill:#66f,stroke:#333
    style C fill:#f96,stroke:#333
    style D fill:#9f9,stroke:#333
    style E fill:#66f,stroke:#333
    style F fill:#f96,stroke:#333
    style G fill:#66f,stroke:#333
    style H fill:#9f9,stroke:#333
    style I fill:#f96,stroke:#333
    style J fill:#f96,stroke:#333
    style K fill:#f96,stroke:#333
    style L fill:#ff9,stroke:#333
    style M fill:#ff9,stroke:#333
    style N fill:#ff9,stroke:#333
    style O fill:#66f,stroke:#333
    style P fill:#66f,stroke:#333
    style Q fill:#ff9,stroke:#333
    style R fill:#66f,stroke:#333
    style S fill:#f9f,stroke:#333
    style T fill:#bbf,stroke:#333
    style U fill:#f9f,stroke:#333
```

## Key Components

### 1. Data Loader Registry
- Manages dataset configurations
- Provides access to medical imaging datasets
- Supports custom dataset registration

### 2. Architecture Registry
- Manages model architecture configurations
- Validates architecture compatibility
- Supports custom architecture registration

### 3. Federated Learning Coordinator
- Orchestrates the federated learning process
- Manages global model aggregation
- Coordinates client communication

### 4. Privacy Engine
- Implements differential privacy
- Ensures secure aggregation
- Protects client data privacy

### 5. Experiment Manager
- Configures and tracks experiments
- Manages experiment lifecycle
- Stores experiment results

### 6. Performance Monitor
- Logs training metrics
- Analyzes experiment performance
- Generates performance reports

## Data Flow

1. **Data Loading:** Medical data sources → Data Loader Registry → Dataset Factory → Medical Datasets
2. **Model Creation:** Architecture Registry → Model Factory → Model Architectures
3. **Experiment Execution:** Experiment Manager → Federated Learning Coordinator → Clients
4. **Privacy Protection:** Privacy Engine → Federated Learning Coordinator (secure aggregation)
5. **Result Tracking:** Clients → Federated Learning Coordinator → Experiment Manager → Performance Monitor

## Integration Points

- **Medical Data Sources:** Provides raw medical imaging data
- **PyTorch:** Used for model training and inference
- **Researcher:** Configures experiments and analyzes results
