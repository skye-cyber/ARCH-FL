# Dashboard Components


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

