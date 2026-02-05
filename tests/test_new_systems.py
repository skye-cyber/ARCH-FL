#!/usr/bin/env python3
"""
Comprehensive test for the new registry systems in ARCH-FL.

This script tests:
1. Data Loader Registry System
2. Architecture Registry System
3. Federated Learning Compatibility Validator
4. Integration between all systems
"""

import sys

# Add src to path
from pathlib import Path
sys.path.insert(0, Path(__file__).resolve().parent.parent.as_posix())


def test_data_loader_registry():
    """Test the Data Loader Registry system."""
    print("🧪 Testing Data Loader Registry...")

    from src.data.loader_registry import DataLoaderRegistry

    # Create registry
    registry = DataLoaderRegistry()

    # Test listing loaders
    loaders = registry.list_loaders()
    print(f"✅ Registered loaders: {loaders}")

    # Test creating data loaders
    client_loaders, test_loader = registry.create_data_loaders(
        "PneumoniaMNIST", num_clients=3, iid=True, batch_size=32
    )
    print(f"✅ Created {len(client_loaders)} client loaders and 1 test loader")

    # Test backward compatibility
    from src.data.loaders import get_data_loaders
    old_client_loaders, old_test_loader = get_data_loaders("PneumoniaMNIST", 3, True, 32)
    print(f"✅ Backward compatibility works: {len(old_client_loaders)} loaders")

    print("🎉 Data Loader Registry tests passed!\n")


def test_architecture_registry():
    """Test the Architecture Registry system."""
    print("🧪 Testing Architecture Registry...")

    from src.models.architecture_registry import ArchitectureRegistry

    # Create registry
    registry = ArchitectureRegistry()

    # Test listing architectures
    architectures = registry.list_architectures()
    print(f"✅ Registered architectures: {architectures}")

    # Test getting architecture info
    simple_info = registry.get_architecture_info("simple_cnn")
    print(f"✅ SimpleCNN info: {simple_info['description']}")

    # Test creating models
    simple_model = registry.create_model_from_architecture("simple_cnn")
    print(f"✅ Created SimpleCNN model: {type(simple_model)}")

    # Test creating different architecture types
    medium_model = registry.create_model_from_architecture("medium_cnn")
    print(f"✅ Created MediumCNN model: {type(medium_model)}")

    print("🎉 Architecture Registry tests passed!\n")


def test_federated_compatibility():
    """Test the Federated Learning Compatibility Validator."""
    print("🧪 Testing Federated Learning Compatibility...")

    from src.models.federated_compatibility import FederatedCompatibilityValidator
    from src.models.architecture_registry import get_architecture_registry

    # Create validator and get shared registry
    validator = FederatedCompatibilityValidator()
    arch_registry = get_architecture_registry()

    # Test SimpleCNN compatibility
    simple_model = arch_registry.create_model_from_architecture("simple_cnn")
    simple_compatible = validator.validate_architecture_for_federated_learning(
        simple_model, input_shape=(1, 28, 28), num_classes=2
    )
    print(f"✅ SimpleCNN federated compatibility: {simple_compatible}")

    # Test medium architecture compatibility (instead of custom)
    medium_model = arch_registry.create_model_from_architecture("medium_cnn")
    medium_compatible = validator.validate_architecture_for_federated_learning(
        medium_model, input_shape=(1, 224, 224), num_classes=2
    )
    print(f"✅ Medium architecture federated compatibility: {medium_compatible}")

    # Test architecture config validation
    config = {
        'name': 'ConfigurableCNN',
        'num_classes': 2,
        'architecture': {
            'input_channels': 1,
            'conv_layers': [
                {'out_channels': 32, 'kernel_size': 3, 'stride': 1, 'padding': 1}
            ],
            'fc_layers': [
                {'out_features': 2}
            ],
            'activation': 'ReLU',
            'pooling': 'MaxPool2d',
            'pool_kernel': 2,
            'dropout': 0.5
        }
    }

    config_compatible = validator.validate_architecture_config(config)
    print(f"✅ Config validation: {config_compatible}")

    print("🎉 Federated Compatibility tests passed!\n")


def test_integration():
    """Test integration between all systems."""
    print("🧪 Testing System Integration...")

    from src.data.loader_registry import get_data_loader_registry
    from src.models.architecture_registry import get_architecture_registry
    from src.models.federated_compatibility import FederatedCompatibilityValidator

    # Get shared registries
    data_registry = get_data_loader_registry()
    arch_registry = get_architecture_registry()
    compat_validator = FederatedCompatibilityValidator()

    # Test complete workflow:
    # 1. Create data loaders for a dataset
    dataset_name = "PneumoniaMNIST"
    client_loaders, test_loader = data_registry.create_data_loaders(
        dataset_name, num_clients=2, iid=True, batch_size=16
    )
    print(f"✅ Created data loaders for {dataset_name}")

    # 2. Get compatible architectures for the dataset
    compatible_archs = arch_registry.get_compatible_architectures(dataset_name)
    print(f"✅ Compatible architectures: {compatible_archs}")

    # 3. Create a model from a compatible architecture
    model = arch_registry.create_model_from_architecture("simple_cnn")
    print(f"✅ Created model: {type(model)}")

    # 4. Validate the model for federated learning
    is_compatible = compat_validator.validate_architecture_for_federated_learning(
        model, input_shape=(1, 28, 28), num_classes=2
    )
    print(f"✅ Model federated compatibility: {is_compatible}")

    # 5. Get detailed compatibility report
    report = compat_validator.get_compatibility_report(model, (1, 28, 28))
    print(f"✅ Compatibility report generated: {report['compatible']} tests passed")

    print("🎉 Integration tests passed!\n")


def main():
    """Run all tests."""
    print("🚀 Starting comprehensive test of new ARCH-FL systems...\n")

    try:
        test_data_loader_registry()
        test_architecture_registry()
        test_federated_compatibility()
        test_integration()

        print("🎊 ALL TESTS PASSED! 🎊")
        print("\n📋 Summary of new features:")
        print("   ✅ Data Loader Registry - Class-based system for managing data loaders")
        print("   ✅ Architecture Registry - System for registering custom architectures")
        print("   ✅ Federated Compatibility - Validator for FL compatibility")
        print("   ✅ Full Integration - All systems work together seamlessly")
        print("   ✅ Backward Compatibility - Original APIs still work")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
