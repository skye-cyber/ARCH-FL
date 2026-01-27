# Dataset Characterization System Documentation

## 🎯 Overview

The Dataset Characterization System is the foundation of ARCH-FL's adaptive architecture. It automatically analyzes medical imaging datasets to extract key characteristics that inform optimal model architecture selection.

## 🏗️ Components

### 1. DatasetRegistry

**Location:** `src/data/registry.py`

**Purpose:** Maintains a registry of supported datasets and their known characteristics.

**Key Features:**
- Pre-registered information about MIMIC-CXR, CheXpert, and PneumoniaMNIST
- Methods to register new datasets
- Dataset metadata retrieval
- Path resolution for built-in datasets

**Usage Example:**
```python
from src.data.registry import DatasetRegistry

registry = DatasetRegistry()

# List all registered datasets
datasets = registry.list_datasets()

# Get information about a specific dataset
mimic_info = registry.get_dataset_info('mimic_cxr')

# Check if a dataset is supported
is_supported = registry.is_supported('custom_dataset')
```

### 2. DatasetAnalyzer

**Location:** `src/data/analyzer.py`

**Purpose:** Analyzes datasets to extract characteristics for adaptive architecture generation.

**Key Features:**
- Automatic detection of image dimensions, channels, and classes
- Dataset-specific analysis for known datasets
- Generic analysis for unknown datasets
- Recommended architecture generation
- Metadata serialization/deserialization

**Supported Datasets:**
- **MIMIC-CXR**: 224x224 grayscale, binary classification
- **CheXpert**: 320x320 grayscale, multi-label classification (14 classes)
- **PneumoniaMNIST**: 28x28 grayscale, binary classification

**Usage Example:**
```python
from src.data.analyzer import DatasetAnalyzer

# Analyze a known dataset
analyzer = DatasetAnalyzer(dataset_name='mimic_cxr')
metadata = analyzer.analyze()

# Get recommended architecture configuration
config = analyzer.get_recommended_architecture_config()

# Save metadata for documentation
analyzer.save_metadata('docs/analysis/mimic_cxr_metadata.json')
```

## 📊 Dataset Analysis Results

### MIMIC-CXR Analysis

**Metadata File:** `docs/analysis/mimic_cxr_metadata.json`

**Key Characteristics:**
- Image Size: 224x224 pixels
- Channels: 1 (grayscale)
- Number of Classes: 2 (binary classification)
- Task Type: Binary classification (pneumonia vs normal)
- Data Type: Chest X-ray
- Dataset Size: Large (>30K images)
- Recommended Architecture: Medium CNN

**Recommended Configuration:**
```json
{
  "name": "ConfigurableCNN",
  "num_classes": 2,
  "input_channels": 1,
  "task_type": "binary_classification",
  "architecture": {
    "input_channels": 1,
    "conv_layers": [
      {"out_channels": 32, "kernel_size": 3, "stride": 2, "padding": 1},
      {"out_channels": 64, "kernel_size": 3, "stride": 2, "padding": 1},
      {"out_channels": 128, "kernel_size": 3, "stride": 2, "padding": 1}
    ],
    "fc_layers": [
      {"out_features": 256},
      {"out_features": 2}
    ],
    "activation": "ReLU",
    "pooling": "MaxPool2d",
    "pool_kernel": 2,
    "dropout": 0.5
  }
}
```

### CheXpert Analysis

**Metadata File:** `docs/analysis/chexpert_metadata.json`

**Key Characteristics:**
- Image Size: 320x320 pixels
- Channels: 1 (grayscale)
- Number of Classes: 14 (multi-label classification)
- Task Type: Multi-label classification
- Data Type: Chest X-ray
- Dataset Size: Very Large (>220K images)
- Recommended Architecture: Large CNN

**Recommended Configuration:**
```json
{
  "name": "ConfigurableCNN",
  "num_classes": 14,
  "input_channels": 1,
  "task_type": "multi_label_classification",
  "architecture": {
    "input_channels": 1,
    "conv_layers": [
      {"out_channels": 32, "kernel_size": 3, "stride": 2, "padding": 1},
      {"out_channels": 64, "kernel_size": 3, "stride": 2, "padding": 1},
      {"out_channels": 128, "kernel_size": 3, "stride": 2, "padding": 1},
      {"out_channels": 256, "kernel_size": 3, "stride": 2, "padding": 1}
    ],
    "fc_layers": [
      {"out_features": 512},
      {"out_features": 14}
    ],
    "activation": "ReLU",
    "pooling": "MaxPool2d",
    "pool_kernel": 2,
    "dropout": 0.5
  }
}
```

### PneumoniaMNIST Analysis

**Metadata File:** `docs/analysis/pneumoniamnist_metadata.json`

**Key Characteristics:**
- Image Size: 28x28 pixels
- Channels: 1 (grayscale)
- Number of Classes: 2 (binary classification)
- Task Type: Binary classification
- Data Type: Chest X-ray
- Dataset Size: Small (~5K images)
- Recommended Architecture: Simple CNN

**Recommended Configuration:**
```json
{
  "name": "ConfigurableCNN",
  "num_classes": 2,
  "input_channels": 1,
  "task_type": "binary_classification",
  "architecture": {
    "input_channels": 1,
    "conv_layers": [
      {"out_channels": 32, "kernel_size": 3, "stride": 1, "padding": 1},
      {"out_channels": 64, "kernel_size": 3, "stride": 1, "padding": 1}
    ],
    "fc_layers": [
      {"out_features": 128},
      {"out_features": 2}
    ],
    "activation": "ReLU",
    "pooling": "MaxPool2d",
    "pool_kernel": 2,
    "dropout": 0.5
  }
}
```

## 🎯 Architecture Recommendation Logic

The system uses the following logic to recommend architectures:

### Based on Image Size

1. **Small Images** (< 100x100 pixels, < 10,000 pixels area):
   - Recommended: Simple CNN
   - Example: PneumoniaMNIST (28x28 = 784 pixels)
   - Rationale: Lightweight architecture sufficient for small images

2. **Medium Images** (100x100 to 300x300 pixels, 10,000-100,000 pixels area):
   - Recommended: Medium CNN
   - Example: MIMIC-CXR (224x224 = 50,176 pixels)
   - Rationale: Balanced architecture for standard medical images

3. **Large Images** (> 300x300 pixels, > 100,000 pixels area):
   - Recommended: Large CNN
   - Example: CheXpert (320x320 = 102,400 pixels)
   - Rationale: Deeper architecture needed for high-resolution images

### Based on Task Complexity

1. **Binary Classification:**
   - Final layer: 2 output units with softmax
   - Example: Pneumonia vs Normal

2. **Multi-label Classification:**
   - Final layer: N output units with sigmoid (where N = number of labels)
   - Example: CheXpert with 14 pathology labels

## 🔧 Integration with ModelFactory

The DatasetAnalyzer integrates seamlessly with the ModelFactory:

```python
from src.data.analyzer import DatasetAnalyzer
from src.models.model_factory import ModelFactory

# Analyze dataset
analyzer = DatasetAnalyzer(dataset_name='mimic_cxr')
metadata = analyzer.analyze()

# Get recommended configuration
config = analyzer.get_recommended_architecture_config()

# Create model using ModelFactory
factory = ModelFactory()
input_shape = metadata['properties']['expected_input_shape']
model = factory.create_model(config, input_shape)

# Model is now ready for training
```

## 🚀 Future Enhancements

### Planned Improvements:

1. **Automatic Dataset Detection:**
   - Analyze dataset directory structure automatically
   - Detect image formats and metadata without manual specification

2. **Advanced Statistics:**
   - Class distribution analysis
   - Image quality metrics
   - Dataset balance assessment

3. **Custom Dataset Support:**
   - User-friendly interface for registering new datasets
   - GUI for dataset characterization
   - Interactive configuration generation

4. **Performance Profiling:**
   - Memory usage estimation for different architectures
   - Training time prediction
   - Hardware requirement analysis

## 📋 Summary

The Dataset Characterization System provides:

✅ **Automatic dataset analysis** for known datasets
✅ **Generic analysis** for unknown datasets  
✅ **Intelligent architecture recommendations** based on data characteristics
✅ **Seamless integration** with ModelFactory
✅ **Extensible design** for future datasets
✅ **Comprehensive documentation** of dataset properties

This system enables ARCH-FL to be truly adaptive and work with any medical imaging dataset, fulfilling the project's vision of a flexible, configurable federated learning framework.
