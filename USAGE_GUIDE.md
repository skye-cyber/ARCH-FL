# ARCH-FL Usage Guide

This guide provides comprehensive instructions for using the ARCH-FL federated learning framework and its dashboard.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/ARCH-FL.git
cd ARCH-FL

# Install Python dependencies
pip install -r requirements.txt

# Install dashboard dependencies
cd dashboard/backend
pip install -r requirements.txt
cd ../frontend
npm install
cd ../..
```

## 🏗️ System Architecture

ARCH-FL consists of several key components:

1. **Core System** (`src/`)
   - `core/`: Coordinator and aggregation logic
   - `models/`: Model architectures and registry
   - `data/`: Data loaders and partitioning
   - `training/`: Federated learning algorithms
   - `privacy/`: Differential privacy mechanisms

2. **Dashboard** (`dashboard/`)
   - `backend/`: FastAPI server
   - `frontend/`: React application
   - `data/`: SQLite database

3. **Experiments** (`experiments/`)
   - Pre-configured experiment scripts

4. **Tests** (`tests/`)
   - Comprehensive test suite

## 📋 Basic Usage

### Running Experiments

#### Option 1: Using the Dashboard (Recommended)

1. **Start the backend**
   ```bash
   cd dashboard/backend
   uvicorn main:app --reload
   ```

2. **Start the frontend**
   ```bash
   cd dashboard/frontend
   npm run dev
   ```

3. **Access the dashboard**
   Open your browser to `http://localhost:3000`

4. **Create and run experiments**
   - Navigate to Experiments section
   - Create new experiment with your configuration
   - Click "Run" to execute

#### Option 2: Using Python API

```python
from src.core.coordinator import Coordinator
from src.models.architecture_registry import get_architecture_registry
from src.data.loader_registry import get_data_loader_registry
from src.training.fedavg import federated_average

# Get registries
arch_registry = get_architecture_registry()
data_registry = get_data_loader_registry()

# Create model
model = arch_registry.create_model("simple_cnn", input_size=28)

# Create coordinator
coordinator = Coordinator(model, aggregation_method="fed_avg")

# Run federated training
federated_average(
    coordinator=coordinator,
    dataset_name="pneumoniamnist",
    num_clients=5,
    num_rounds=10,
    iid=True
)
```

### Using the Dashboard API

The dashboard provides a RESTful API for programmatic access:

```bash
# List experiments
curl http://localhost:8008/api/experiments

# Create experiment
curl -X POST http://localhost:8008/api/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Experiment",
    "description": "Testing federated learning",
    "dataset_name": "pneumoniamnist",
    "architecture_name": "simple_cnn",
    "num_clients": 5,
    "iid": true,
    "parameters": {
      "num_rounds": 10,
      "learning_rate": 0.01,
      "aggregation_method": "fed_avg"
    }
  }'

# Run experiment
curl -X POST http://localhost:8008/api/experiments/1/run

# Get experiment results
curl http://localhost:8008/api/experiments/1/results
```

## 🛠️ Configuration

### Experiment Configuration

Experiments can be configured with various parameters:

```python
{
  "name": "My Experiment",
  "description": "Detailed description",
  "dataset_name": "pneumoniamnist",  # or "mimic_cxr", "chexpert"
  "architecture_name": "simple_cnn",  # or "medium_cnn", "resnet18"
  "num_clients": 5,
  "iid": true,  # Independent and identically distributed data
  "parameters": {
    "num_rounds": 10,
    "learning_rate": 0.01,
    "batch_size": 32,
    "aggregation_method": "fed_avg",  # or "weighted", "secure"
    "privacy": {
      "enabled": true,
      "epsilon": 1.0,
      "delta": 1e-5
    }
  }
}
```

### Dataset Configuration

Available datasets:

- **PneumoniaMNIST**: Simple pneumonia classification dataset
- **MIMIC-CXR**: Chest X-ray dataset from MIMIC
- **CheXpert**: Chest X-ray dataset from Stanford

### Architecture Configuration

Available architectures:

- **Simple CNN**: Basic convolutional neural network
- **Medium CNN**: Configurable CNN with more layers
- **ResNet18**: Residual network for complex tasks

## 🔬 Advanced Usage

### Custom Architectures

You can create and register custom architectures:

```python
from src.models.architecture_registry import get_architecture_registry
from src.models.architectures import register_custom_architecture

# Define your custom architecture
class CustomCNN(nn.Module):
    def __init__(self, input_size=28):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(32 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, 2)
    
    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = x.view(-1, 32 * 7 * 7)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Register the architecture
registry = get_architecture_registry()
registry.register_custom_architecture(
    "custom_cnn",
    {"name": "CustomCNN", "input_size": 28},
    "Custom CNN architecture",
    ["pneumoniamnist"]
)
```

### Differential Privacy

Enable differential privacy for privacy-preserving federated learning:

```python
from src.privacy.dp_engine import DPEngine

# Create DP engine
dp_engine = DPEngine(epsilon=1.0, delta=1e-5)

# Apply DP to model updates
coordinator = Coordinator(model)
client_updates = [...]  # Client model updates

# Add noise for differential privacy
noisy_updates = dp_engine.add_noise_to_updates(client_updates)
coordinator.aggregate(noisy_updates, client_sizes)
```

### Data Partitioning

Control how data is partitioned among clients:

```python
from src.data.partitioning import partition_dataset

# IID partitioning (default)
partitions = partition_dataset(dataset, num_clients, iid=True)

# Non-IID partitioning
partitions = partition_dataset(dataset, num_clients, iid=False, alpha=0.5)
```

## 📊 Monitoring and Results

### Real-time Monitoring

The dashboard provides real-time monitoring via WebSocket:

```javascript
// Connect to WebSocket
const socket = new WebSocket('ws://localhost:8008/ws/monitoring');

// Listen for updates
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Monitoring update:', data);
  
  // Update your UI with the new data
  updateDashboard(data);
};
```

### Analyzing Results

Results are stored in the dashboard database and can be accessed via API:

```python
import requests
import matplotlib.pyplot as plt

# Get experiment results
response = requests.get('http://localhost:8008/api/experiments/1/results')
results = response.json()

# Plot accuracy over rounds
rounds = [r['round'] for r in results]
accuracies = [r['accuracy'] for r in results]

plt.plot(rounds, accuracies, 'b-')
plt.xlabel('Round')
plt.ylabel('Accuracy')
plt.title('Training Progress')
plt.show()
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_coordinator.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src
```

### Test Structure

- `test_coordinator.py`: Coordinator and aggregation tests
- `test_dashboard_integration.py`: Dashboard integration tests
- `test_architecture_generator.py`: Architecture generation tests
- `test_data_partitioning.py`: Data partitioning tests
- `test_dp_engine.py`: Differential privacy tests

## 📚 API Reference

### Core API

#### Coordinator

```python
from src.core.coordinator import Coordinator

# Create coordinator
coordinator = Coordinator(model, aggregation_method="fed_avg")

# Aggregate client updates
coordinator.aggregate(client_updates, client_sizes)

# Get global model
params = coordinator.get_global_model()

# Get model summary
summary = coordinator.get_model_summary()
```

#### Architecture Registry

```python
from src.models.architecture_registry import get_architecture_registry

# Get registry
registry = get_architecture_registry()

# List architectures
architectures = registry.list_architectures()

# Get architecture info
info = registry.get_architecture_info("simple_cnn")

# Create model
model = registry.create_model("simple_cnn", input_size=28)
```

#### Data Loader Registry

```python
from src.data.loader_registry import get_data_loader_registry

# Get registry
registry = get_data_loader_registry()

# List datasets
datasets = registry.list_loaders()

# Get dataset info
info = registry.get_dataset_info("pneumoniamnist")

# Load dataset
loader = registry.get_loader("pneumoniamnist")
```

### Dashboard API

#### Experiments

- `GET /api/experiments` - List all experiments
- `POST /api/experiments` - Create new experiment
- `GET /api/experiments/{id}` - Get experiment details
- `PUT /api/experiments/{id}` - Update experiment
- `POST /api/experiments/{id}/run` - Run experiment
- `GET /api/experiments/{id}/results` - Get experiment results

#### Architectures

- `GET /api/architectures` - List registered architectures
- `POST /api/architectures` - Register new architecture
- `GET /api/architectures/{name}` - Get architecture details
- `GET /api/architectures/registry` - Get architectures from ARCH-FL registry

#### Datasets

- `GET /api/datasets` - List available datasets

#### System

- `GET /api/health` - Health check
- `WS /ws/monitoring` - Real-time monitoring WebSocket

## 💡 Tips and Best Practices

### Performance Optimization

1. **Batch Size**: Use appropriate batch sizes for your hardware
2. **Aggregation Method**: Choose the right method for your use case
3. **Data Distribution**: Consider IID vs non-IID data partitioning
4. **Privacy Budget**: Balance privacy (epsilon) with utility

### Debugging

1. **Check logs**: `src/utils/logger.py` for detailed logging
2. **Use health endpoint**: `http://localhost:8008/api/health`
3. **Inspect database**: Dashboard uses SQLite at `dashboard/data/dashboard.db`
4. **Enable verbose mode**: Add `--verbose` to pytest commands

### Common Issues

**Issue**: Import errors
- **Solution**: Ensure you're running from the project root

**Issue**: Database connection errors
- **Solution**: Ensure dashboard/data directory exists and is writable

**Issue**: WebSocket connection failures
- **Solution**: Check CORS settings in dashboard/backend/main.py

**Issue**: Missing dependencies
- **Solution**: Run `pip install -r requirements.txt`

## 🤝 Contributing

See `CONTRIBUTING.md` for guidelines on contributing to ARCH-FL.

## 📝 License

This project is licensed under the MIT License. See `LICENSE` for details.

## 📞 Support

For issues and questions, please open an issue on GitHub or contact the maintainers.

---

This guide provides a comprehensive overview of ARCH-FL usage. For more detailed information on specific components, refer to the individual module docstrings and the dashboard documentation.