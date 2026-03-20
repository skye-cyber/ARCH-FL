"""
Architecture Registry for ARCH-FL

Class-based registry system for managing and creating custom model architectures.
This system allows users to register their own architectures and ensures compatibility
with the federated learning framework.
"""

import sys
import os
from typing import Dict, Any, Optional, List, Callable, Tuple
import torch.nn as nn
import yaml
from pathlib import Path

# Handle both direct execution and module import
if __name__ == "__main__":
    # When running directly, add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class ArchitectureRegistry:
    """
    Registry for managing custom model architectures.

    This class maintains a collection of architecture configurations and provides
    methods to register new architectures, validate configurations, and create models
    that are compatible with the federated learning framework.
    """

    def __init__(self):
        """Initialize architecture registry."""
        self.architectures = {}
        self._register_builtin_architectures()
        self._config_dir = (
            Path(__file__).resolve().parent.parent.parent / "config/model"
        )

    def _register_builtin_architectures(self) -> None:
        """Register built-in architecture configurations."""
        # Register SimpleCNN
        self.register_architecture(
            "simple_cnn",
            self._get_simple_cnn_config(),
            description="Simple CNN for basic medical imaging tasks",
            compatible_datasets=["pneumoniamnist"],
        )

        # Register MediumCNN
        self.register_architecture(
            "medium_cnn",
            self._get_medium_cnn_config(),
            description="Medium CNN for moderate complexity medical imaging",
            compatible_datasets=["mimic_cxr", "chexpert"],
        )

        # Register LargeCNN
        self.register_architecture(
            "large_cnn",
            self._get_large_cnn_config(),
            description="Large CNN for complex medical imaging tasks",
            compatible_datasets=["chexpert"],
        )

        # Register ResNet18
        self.register_architecture(
            "resnet18",
            self._get_resnet18_config(),
            description="ResNet18 with medical imaging modifications",
            compatible_datasets=["mimic_cxr", "chexpert", "pneumoniamnist"],
        )

    def register_architecture(
        self,
        arch_name: str,
        config: Dict[str, Any],
        description: str = "",
        compatible_datasets: Optional[List[str]] = None,
        validator: Optional[Callable] = None,
    ) -> None:
        """
        Register a new architecture in the registry.

        Args:
            arch_name: Name/key for the architecture
            config: Architecture configuration dictionary
            description: Description of the architecture
            compatible_datasets: List of datasets this architecture is compatible with
            validator: Optional validation function for this architecture
        """
        arch_name = arch_name.lower()

        # Validate the configuration
        if not self._validate_architecture_config(config):
            raise ValueError(f"Invalid architecture configuration for {arch_name}")

        self.architectures[arch_name] = {
            "config": config,
            "description": description,
            "compatible_datasets": compatible_datasets or [],
            "validator": validator,
        }

        # print(f"Registered architecture: {arch_name}")

    def register_architecture_from_file(
        self,
        arch_name: str,
        config_file: str,
        description: str = "",
        compatible_datasets: Optional[List[str]] = None,
    ) -> None:
        """
        Register an architecture from a YAML configuration file.

        Args:
            arch_name: Name/key for the architecture
            config_file: Path to YAML configuration file
            description: Description of the architecture
            compatible_datasets: List of datasets this architecture is compatible with
        """
        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            self.register_architecture(
                arch_name, config, description, compatible_datasets
            )

        except Exception as e:
            raise ValueError(f"Failed to load architecture from {config_file}: {e}")

    def get_architecture_info(self, arch_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered architecture.

        Args:
            arch_name: Name of the architecture

        Returns:
            Dictionary with architecture information, or None if not found
        """
        arch_name = arch_name.lower()
        return self.architectures.get(arch_name)

    def get_architecture_config(self, arch_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a registered architecture.

        Args:
            arch_name: Name of the architecture

        Returns:
            Architecture configuration dictionary, or None if not found
        """
        arch_name = arch_name.lower()
        arch_info = self.architectures.get(arch_name)
        return arch_info["config"] if arch_info else None

    def list_architectures(self) -> List[str]:
        """List all registered architectures."""
        return list(self.architectures.keys())

    def is_supported(self, arch_name: str) -> bool:
        """Check if an architecture is supported."""
        arch_name = arch_name.lower()
        return arch_name in self.architectures

    def get_compatible_architectures(self, dataset_name: str) -> List[str]:
        """
        Get architectures that are compatible with a specific dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            List of architecture names that are compatible with the dataset
        """
        dataset_name = dataset_name.lower()
        compatible_archs = []

        for arch_name, arch_info in self.architectures.items():
            # Check if this architecture is compatible with the dataset
            if (
                not arch_info["compatible_datasets"]
                or dataset_name in arch_info["compatible_datasets"]
            ):
                compatible_archs.append(arch_name)

        return compatible_archs

    def validate_architecture_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate an architecture configuration.

        Args:
            config: Architecture configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        return self._validate_architecture_config(config)

    def _validate_architecture_config(self, config: Dict[str, Any]) -> bool:
        """
        Internal method to validate architecture configuration.

        Args:
            config: Architecture configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required fields
        required_fields = ["name", "num_classes"]

        for field in required_fields:
            if field not in config:
                print(f"⚠️ Missing required field: {field}")
                return False

        # Check architecture section
        if "architecture" in config:
            arch_config = config["architecture"]

            # Check if it's a configurable CNN
            if "conv_layers" in arch_config:
                # Validate convolutional layers
                conv_layers = arch_config["conv_layers"]
                if not isinstance(conv_layers, list) or len(conv_layers) == 0:
                    print("⚠️ Invalid conv_layers configuration")
                    return False

                for i, layer in enumerate(conv_layers):
                    required_layer_fields = [
                        "out_channels",
                        "kernel_size",
                        "stride",
                        "padding",
                    ]
                    for field in required_layer_fields:
                        if field not in layer:
                            print(f"⚠️ Missing field in conv layer {i}: {field}")
                            return False

            # Validate fully connected layers
            if "fc_layers" in arch_config:
                fc_layers = arch_config["fc_layers"]
                if not isinstance(fc_layers, list) or len(fc_layers) == 0:
                    print("⚠️ Invalid fc_layers configuration")
                    return False

                for i, layer in enumerate(fc_layers):
                    if "out_features" not in layer:
                        print(f"⚠️ Missing out_features in fc layer {i}")
                        return False

        return True

    def _get_simple_cnn_config(self) -> Dict[str, Any]:
        """Get configuration for SimpleCNN."""
        return {
            "name": "SimpleCNN",
            "num_classes": 2,
            "description": "Simple CNN for basic medical imaging tasks",
            "input_shape": (1, 28, 28),
            "architecture": {
                "input_channels": 1,
                "conv_layers": [
                    {"out_channels": 32, "kernel_size": 3, "stride": 1, "padding": 1},
                    {"out_channels": 64, "kernel_size": 3, "stride": 1, "padding": 1},
                ],
                "fc_layers": [{"out_features": 128}, {"out_features": 2}],
                "activation": "ReLU",
                "pooling": "MaxPool2d",
                "pool_kernel": 2,
                "dropout": 0.5,
            },
        }

    def _get_medium_cnn_config(self) -> Dict[str, Any]:
        """Get configuration for MediumCNN."""
        return {
            "name": "ConfigurableCNN",
            "num_classes": 2,
            "description": "Medium CNN for moderate complexity medical imaging",
            "input_shape": (1, 224, 224),
            "architecture": {
                "input_channels": 1,
                "conv_layers": [
                    {"out_channels": 32, "kernel_size": 3, "stride": 2, "padding": 1},
                    {"out_channels": 64, "kernel_size": 3, "stride": 2, "padding": 1},
                    {"out_channels": 128, "kernel_size": 3, "stride": 2, "padding": 1},
                ],
                "fc_layers": [{"out_features": 256}, {"out_features": 2}],
                "activation": "ReLU",
                "pooling": "MaxPool2d",
                "pool_kernel": 2,
                "dropout": 0.5,
            },
        }

    def _get_large_cnn_config(self) -> Dict[str, Any]:
        """Get configuration for LargeCNN."""
        return {
            "name": "ConfigurableCNN",
            "num_classes": 14,
            "description": "Large CNN for complex medical imaging tasks",
            "input_shape": (1, 320, 320),
            "architecture": {
                "input_channels": 1,
                "conv_layers": [
                    {"out_channels": 32, "kernel_size": 3, "stride": 2, "padding": 1},
                    {"out_channels": 64, "kernel_size": 3, "stride": 2, "padding": 1},
                    {"out_channels": 128, "kernel_size": 3, "stride": 2, "padding": 1},
                    {"out_channels": 256, "kernel_size": 3, "stride": 2, "padding": 1},
                ],
                "fc_layers": [{"out_features": 512}, {"out_features": 14}],
                "activation": "ReLU",
                "pooling": "MaxPool2d",
                "pool_kernel": 2,
                "dropout": 0.5,
            },
        }

    def _get_resnet18_config(self) -> Dict[str, Any]:
        """Get configuration for ResNet18."""
        return {
            "name": "ResNet18",
            "num_classes": 2,
            "description": "ResNet18 with medical imaging modifications",
            "input_shape": (1, 224, 224),
            "pretrained": False,
            "modifications": {
                "first_conv": {
                    "in_channels": 1,
                    "out_channels": 64,
                    "kernel_size": 7,
                    "stride": 2,
                    "padding": 3,
                }
            },
        }

    def create_model_from_architecture(
        self,
        arch_name: str,
        input_shape: Optional[Tuple] = None,
        num_classes: Optional[int] = None,
    ) -> nn.Module:
        """
        Create a model from a registered architecture.

        Args:
            arch_name: Name of the registered architecture
            input_shape: Optional input shape override
            num_classes: Optional number of classes override

        Returns:
            PyTorch model instance
        """
        arch_name = arch_name.lower()

        # Get architecture configuration
        config = self.get_architecture_config(arch_name)
        if not config:
            raise ValueError(f"Architecture '{arch_name}' not found")

        # Apply overrides
        if input_shape:
            config["input_shape"] = input_shape
        if num_classes:
            config["num_classes"] = num_classes
            # Update final FC layer if architecture has fc_layers
            if "architecture" in config and "fc_layers" in config["architecture"]:
                fc_layers = config["architecture"]["fc_layers"]
                if fc_layers and len(fc_layers) > 0:
                    fc_layers[-1]["out_features"] = num_classes

        # Create model using ModelFactory
        try:
            from src.models.model_factory import ModelFactory

            factory = ModelFactory()
            return factory.create_model(
                config, input_shape or config.get("input_shape")
            )
        except ImportError:
            # Fallback to direct import
            try:
                from models.model_factory import ModelFactory

                factory = ModelFactory()
                return factory.create_model(
                    config, input_shape or config.get("input_shape")
                )
            except ImportError as e:
                raise RuntimeError(f"Could not import ModelFactory: {e}")

    def register_custom_architecture(
        self,
        arch_name: str,
        config: Dict[str, Any],
        description: str = "",
        compatible_datasets: Optional[List[str]] = None,
    ) -> None:
        """
        Register a custom architecture with validation.

        This method provides a user-friendly way to register custom architectures
        while ensuring they meet the framework's requirements.

        Args:
            arch_name: Name for the custom architecture
            config: Architecture configuration
            description: Description of the architecture
            compatible_datasets: List of compatible datasets
        """
        # Validate the configuration
        if not self.validate_architecture_config(config):
            raise ValueError("Invalid architecture configuration")

        # Register the architecture
        self.register_architecture(arch_name, config, description, compatible_datasets)

        print(f"✅ Custom architecture '{arch_name}' registered successfully!")


def get_architecture_registry() -> ArchitectureRegistry:
    """Get singleton instance of ArchitectureRegistry."""
    return ArchitectureRegistry()


# Test the registry
if __name__ == "__main__":
    print("🧪 Testing ArchitectureRegistry...")

    registry = ArchitectureRegistry()

    # List all architectures
    print(f"\n📋 Registered architectures: {registry.list_architectures()}")

    # Get info for each architecture
    for arch_name in registry.list_architectures():
        info = registry.get_architecture_info(arch_name)
        print(f"\n🏗️ {arch_name}:")
        print(f"   Description: {info['description']}")
        print(f"   Compatible datasets: {info['compatible_datasets']}")

        # Show config summary
        config = info["config"]
        print(f"   Model type: {config.get('name', 'Unknown')}")
        print(f"   Input shape: {config.get('input_shape', 'Variable')}")
        print(f"   Classes: {config.get('num_classes', 'Variable')}")

    # Test creating models from architectures
    print(f"\n🔧 Testing model creation...")

    try:
        # Test SimpleCNN
        model_simple = registry.create_model_from_architecture("simple_cnn")
        print(f"✅ Created SimpleCNN model: {type(model_simple)}")

        # Test MediumCNN
        model_medium = registry.create_model_from_architecture(
            "medium_cnn", input_shape=(1, 224, 224)
        )
        print(f"✅ Created MediumCNN model: {type(model_medium)}")

        # Test custom architecture registration
        print(f"\n🛠️ Testing custom architecture registration...")

        custom_config = {
            "name": "ConfigurableCNN",
            "num_classes": 2,
            "description": "Custom test architecture",
            "input_shape": (1, 64, 64),
            "architecture": {
                "input_channels": 1,
                "conv_layers": [
                    {"out_channels": 16, "kernel_size": 3, "stride": 1, "padding": 1},
                    {"out_channels": 32, "kernel_size": 3, "stride": 1, "padding": 1},
                ],
                "fc_layers": [{"out_features": 64}, {"out_features": 2}],
                "activation": "ReLU",
                "pooling": "MaxPool2d",
                "pool_kernel": 2,
                "dropout": 0.3,
            },
        }

        registry.register_custom_architecture(
            "custom_test", custom_config, "Test custom architecture", ["pneumoniamnist"]
        )

        # Test creating model from custom architecture
        custom_model = registry.create_model_from_architecture("custom_test")
        print(f"✅ Created custom model: {type(custom_model)}")

    except Exception as e:
        print(f"❌ Error creating models: {e}")
        import traceback

        traceback.print_exc()

    # Test validation
    print(f"\n🔍 Testing architecture validation...")

    # Valid configuration
    valid_config = {
        "name": "TestCNN",
        "num_classes": 2,
        "architecture": {
            "conv_layers": [
                {"out_channels": 32, "kernel_size": 3, "stride": 1, "padding": 1}
            ],
            "fc_layers": [{"out_features": 2}],
        },
    }

    is_valid = registry.validate_architecture_config(valid_config)
    print(f"Valid config validation: {'✅ PASS' if is_valid else '❌ FAIL'}")

    # Invalid configuration (missing required field)
    invalid_config = {
        "num_classes": 2,
        "architecture": {
            "conv_layers": [
                {"out_channels": 32, "kernel_size": 3, "stride": 1, "padding": 1}
            ]
        },
    }

    is_invalid = not registry.validate_architecture_config(invalid_config)
    print(f"Invalid config validation: {'✅ PASS' if is_invalid else '❌ FAIL'}")

    print(f"\n🎉 ArchitectureRegistry tests completed!")
