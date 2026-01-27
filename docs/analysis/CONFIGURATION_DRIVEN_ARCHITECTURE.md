# Configuration-Driven Architecture Documentation

## 🎯 Overview

The Configuration-Driven Architecture system enables ARCH-FL to create models dynamically from YAML configuration files, making the framework truly adaptive and configurable for different datasets and use cases.

## 🏗️ Components

### 1. Enhanced ModelFactory

**Location:** `src/models/model_factory.py`

**Key Enhancements:**
- **Configuration Loading:** Load YAML configurations from files
- **Dataset Integration:** Create models optimized for specific datasets
- **Fallback Mechanisms:** Graceful degradation when components unavailable
- **Adaptive Architecture:** Uses DatasetAnalyzer for optimal configuration

**New Methods:**
- `load_config_by_name(config_name)`: Load configuration by name
- `create_model_from_dataset(dataset_name, input_shape)`: Create dataset-optimized model
- `_create_fallback_adaptive_model()`: Fallback with hard-coded configs

### 2. YAML Configuration Files

**Location:** `config/model/`

**Files Created:**
- `medical_cnn.yaml`: Base medical CNN configuration
- `architecture_rules.yaml`: AutoML rules for architecture generation

## 📁 Configuration Files

### Medical CNN Configuration (`medical_cnn.yaml`)

**Purpose:** Base configuration for medical imaging tasks

**Key Sections:**
- **architecture**: CNN layer specifications
- **normalization**: Image normalization parameters
- **training**: Default training parameters
- **tasks**: Task-specific configurations
- **dataset_overrides**: Dataset-specific customizations

**Example Usage:**
```python
from src.models.model_factory import ModelFactory

factory = ModelFactory()
config = factory.load_config_by_name('medical_cnn')
model = factory.create_model(config, input_shape=(1, 224, 224))
```

### Architecture Rules (`architecture_rules.yaml`)

**Purpose:** Define rules for automatic architecture generation

**Key Sections:**
- **size_categories**: Image size classification
- **architecture_templates**: Predefined architecture patterns
- **task_complexity**: Complexity multipliers for different tasks
- **validation_rules**: Architecture validation criteria
- **performance_estimation**: Resource usage estimates

## 🔧 Integration with DatasetAnalyzer

The enhanced ModelFactory integrates seamlessly with DatasetAnalyzer:

```python
from src.models.model_factory import ModelFactory

factory = ModelFactory()

# Create model optimized for MIMIC-CXR
mimic_model = factory.create_model_from_dataset('mimic_cxr', (1, 224, 224))

# Create model optimized for CheXpert
chexpert_model = factory.create_model_from_dataset('chexpert', (1, 320, 320))

# Create model optimized for PneumoniaMNIST
pneumonia_model = factory.create_model_from_dataset('pneumoniamnist', (1, 28, 28))
```

## 📊 Architecture Generation Process

### For Known Datasets

1. **Dataset Analysis:** DatasetAnalyzer extracts characteristics
2. **Configuration Generation:** Recommended architecture based on analysis
3. **Model Creation:** ModelFactory creates model from configuration
4. **Validation:** Automatic shape validation and error checking

### For Unknown Datasets

1. **Fallback Analysis:** Use generic dataset analysis
2. **Size-Based Recommendation:** Architecture based on image size
3. **Model Creation:** Create model with fallback configuration
4. **Graceful Degradation:** Work even with limited metadata

## 🎯 Architecture Recommendation Logic

### Based on Image Size

| Size Category | Area Range | Example Size | Recommended Architecture |
|---------------|------------|--------------|--------------------------|
| Small | < 10,000 px | 28×28 | Simple CNN (2 conv layers) |
| Medium | 10,000-100,000 px | 224×224 | Medium CNN (3 conv layers) |
| Large | > 100,000 px | 320×320 | Large CNN (4 conv layers) |

### Based on Task Type

| Task Type | Output Layer | Loss Function | Activation |
|------------|--------------|---------------|------------|
| Binary Classification | 2 units | CrossEntropyLoss | Softmax |
| Multi-label Classification | N units | BCEWithLogitsLoss | Sigmoid |

## 🚀 Usage Examples

### Example 1: Create Model from Configuration File

```python
from src.models.model_factory import ModelFactory
import torch

# Initialize factory
factory = ModelFactory()

# Load configuration
config = factory.load_config_by_name('medical_cnn')

# Create model
input_shape = (1, 224, 224)  # 1 channel, 224x224 images
model = factory.create_model(config, input_shape)

# Test model
test_input = torch.randn(1, *input_shape)
output = model(test_input)
print(f"Model output shape: {output.shape}")
```

### Example 2: Create Dataset-Optimized Model

```python
from src.models.model_factory import ModelFactory
import torch

# Initialize factory
factory = ModelFactory()

# Create model optimized for MIMIC-CXR
mimic_model = factory.create_model_from_dataset('mimic_cxr', (1, 224, 224))

# Test with sample data
test_input = torch.randn(1, 1, 224, 224)
output = mimic_model(test_input)
print(f"MIMIC-CXR model output: {output.shape}")

# Create model optimized for CheXpert
chexpert_model = factory.create_model_from_dataset('chexpert', (1, 320, 320))
test_input = torch.randn(1, 1, 320, 320)
output = chexpert_model(test_input)
print(f"CheXpert model output: {output.shape}")
```

### Example 3: Custom Configuration

```python
from src.models.model_factory import ModelFactory
import torch

# Initialize factory
factory = ModelFactory()

# Define custom configuration
custom_config = {
    'name': 'CustomCNN',
    'num_classes': 3,  # 3-class classification
    'architecture': {
        'input_channels': 1,
        'conv_layers': [
            {'out_channels': 16, 'kernel_size': 3, 'stride': 1, 'padding': 1},
            {'out_channels': 32, 'kernel_size': 3, 'stride': 2, 'padding': 1}
        ],
        'fc_layers': [
            {'out_features': 64},
            {'out_features': 3}
        ],
        'activation': 'ReLU',
        'pooling': 'MaxPool2d',
        'pool_kernel': 2,
        'dropout': 0.3
    }
}

# Create model from custom configuration
model = factory.create_model(custom_config, (1, 128, 128))
test_input = torch.randn(1, 1, 128, 128)
output = model(test_input)
print(f"Custom model output: {output.shape}")
```

## 🔧 Configuration File Structure

### Medical CNN Configuration (`medical_cnn.yaml`)

```yaml
name: "MedicalCNN"
version: "1.0"
description: "Base medical CNN configuration for chest X-ray analysis"

architecture:
  input_channels: 1
  conv_layers:
    - out_channels: 32
      kernel_size: 3
      stride: 2
      padding: 1
    - out_channels: 64
      kernel_size: 3
      stride: 2
      padding: 1
    - out_channels: 128
      kernel_size: 3
      stride: 2
      padding: 1
  fc_layers:
    - out_features: 256
    - out_features: 2
  activation: "ReLU"
  pooling: "MaxPool2d"
  pool_kernel: 2
  dropout: 0.5

# Additional sections: normalization, training, tasks, dataset_overrides
```

### Architecture Rules (`architecture_rules.yaml`)

```yaml
version: "1.0"
description: "AutoML rules for adaptive architecture generation"

size_categories:
  small:
    max_area: 10000
    description: "Small images (e.g., 28x28, 32x32)"
    recommended_architecture: "simple_cnn"
    complexity: "low"
  
  medium:
    min_area: 10000
    max_area: 100000
    description: "Medium images (e.g., 224x224)"
    recommended_architecture: "medium_cnn"
    complexity: "medium"

# Additional sections: architecture_templates, task_complexity, validation_rules
```

## 📋 Benefits of Configuration-Driven Architecture

### ✅ Flexibility
- Work with any medical imaging dataset
- Support different image sizes and formats
- Adapt to various task types

### ✅ Maintainability
- Centralized configuration management
- Easy to update and modify architectures
- Version-controlled configurations

### ✅ Extensibility
- Add new architectures via YAML files
- Support custom datasets without code changes
- Integrate with AutoML systems

### ✅ Reproducibility
- Configuration files document experimental setup
- Easy to share and replicate experiments
- Version control for configurations

### ✅ Performance Optimization
- Optimal architecture for each dataset
- Resource-aware configurations
- Performance estimation and validation

## 🚀 Future Enhancements

### Planned Improvements:

1. **AutoML Integration:**
   - Automatic hyperparameter optimization
   - Neural architecture search
   - Bayesian optimization for configurations

2. **Advanced Configuration:**
   - Attention mechanisms
   - Residual connections
   - Advanced normalization techniques

3. **Performance Profiling:**
   - Memory usage estimation
   - Training time prediction
   - Hardware requirement analysis

4. **Configuration Management:**
   - Configuration versioning
   - Configuration inheritance
   - Configuration validation tools

## 📋 Summary

The Configuration-Driven Architecture system provides:

- [ ] **YAML-based configuration** for flexible model creation
- [ ] **Dataset-optimized models** via intelligent analysis
- [ ] **Seamless integration** with DatasetAnalyzer
- [ ] **Fallback mechanisms** for robustness
- [ ] **Extensible design** for future enhancements
- [ ] **Comprehensive documentation** of configurations

This system enables ARCH-FL to be truly adaptive and work with any medical imaging dataset, fulfilling the project's vision of a flexible, configurable federated learning framework that can adapt to real-world medical datasets during training.
