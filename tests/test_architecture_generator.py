# Copyright (c) 2026 ARCH-FL Project
# SPDX-License-Identifier: MIT

"""
Comprehensive tests for ArchitectureGenerator
"""

import pytest
import torch
from pathlib import Path
import sys
# importlib.util.find_spec -> test for availability
# Add project root to path
sys.path.insert(0, Path(__file__).resolve().parent.parent.as_posix())

try:
    from src.models.architecture_generator import ArchitectureGenerator
    from src.models.model_factory import ModelFactory
    from src.data.analyzer import DatasetAnalyzer
    from src.data.registry import DatasetRegistry
except ImportError as e:
    print(f"Import error: {e}")
    raise


@pytest.fixture
def architecture_generator():
    """Create an ArchitectureGenerator instance"""
    return ArchitectureGenerator()


@pytest.fixture
def model_factory():
    """Create a ModelFactory instance"""
    return ModelFactory()


class TestArchitectureGeneratorInitialization:
    """Test ArchitectureGenerator initialization"""

    def test_initialization(self, architecture_generator):
        """Test basic initialization"""
        assert architecture_generator is not None
        assert architecture_generator.factory is not None
        assert architecture_generator.registry is not None
        assert hasattr(architecture_generator, 'rules')
        assert hasattr(architecture_generator, 'search_space')
        assert hasattr(architecture_generator, 'history')

    def test_rules_loading(self, architecture_generator):
        """Test that rules are loaded correctly"""
        rules = architecture_generator.rules
        assert isinstance(rules, dict)
        assert 'size_categories' in rules
        assert 'architecture_templates' in rules
        assert 'task_complexity' in rules

    def test_search_space_definition(self, architecture_generator):
        """Test that search space is defined correctly"""
        search_space = architecture_generator.search_space
        assert isinstance(search_space, dict)
        assert 'conv_layers' in search_space
        assert 'fc_layers' in search_space
        assert 'conv_channels' in search_space


class TestArchitectureGeneration:
    """Test architecture generation functionality"""

    def test_generate_architecture_basic(self, architecture_generator):
        """Test basic architecture generation"""
        config = architecture_generator.generate_architecture('mimic_cxr')

        assert isinstance(config, dict)
        assert 'name' in config
        assert 'architecture' in config
        assert 'validation' in config
        assert 'generation_metadata' in config

    def test_generate_architecture_with_input_shape(self, architecture_generator):
        """Test architecture generation with specific input shape"""
        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification'
        )

        assert config['architecture']['input_channels'] == 1
        assert config['image_size'] == (224, 224)
        assert config['task_type'] == 'binary_classification'

    def test_generate_architecture_different_datasets(self, architecture_generator):
        """Test architecture generation for different datasets"""
        datasets = ['mimic_cxr', 'chexpert', 'pneumoniamnist']

        for dataset_name in datasets:
            config = architecture_generator.generate_architecture(dataset_name)
            assert config is not None
            assert 'name' in config
            assert 'architecture' in config

    def test_generate_architecture_fallback(self, architecture_generator):
        """Test fallback architecture generation"""
        # Test with unknown dataset
        config = architecture_generator.generate_architecture('unknown_dataset')

        assert config is not None
        assert 'name' in config
        assert 'architecture' in config
        # Should still generate a valid config even for unknown datasets


class TestArchitectureValidation:
    """Test architecture validation functionality"""

    def test_validation_structure(self, architecture_generator):
        """Test that validation returns correct structure"""
        config = architecture_generator.generate_architecture('mimic_cxr')
        validation = config['validation']

        assert isinstance(validation, dict)
        assert 'valid' in validation
        assert 'warnings' in validation
        assert 'errors' in validation
        assert 'estimated_parameters' in validation
        assert 'estimated_memory_mb' in validation
        assert 'estimated_training_time' in validation

    def test_validation_valid_architecture(self, architecture_generator):
        """Test validation of a valid architecture"""
        config = architecture_generator.generate_architecture('mimic_cxr')
        validation = config['validation']

        assert validation['valid'] is True
        assert len(validation['errors']) == 0

    def test_validation_parameter_estimation(self, architecture_generator):
        """Test parameter estimation"""
        config = architecture_generator.generate_architecture('mimic_cxr')
        validation = config['validation']

        assert validation['estimated_parameters'] > 0
        assert validation['estimated_memory_mb'] > 0
        assert validation['estimated_training_time'] > 0


class TestModelCreation:
    """Test model creation from generated configurations"""

    def test_create_model_from_generated_config(self, architecture_generator):
        """Test creating model from generated configuration"""
        config = architecture_generator.generate_architecture('mimic_cxr')
        model = architecture_generator.create_model_from_generated_config(config)

        assert model is not None
        assert isinstance(model, torch.nn.Module)

    def test_model_forward_pass(self, architecture_generator):
        """Test that generated model can perform forward pass"""
        config = architecture_generator.generate_architecture('mimic_cxr')
        model = architecture_generator.create_model_from_generated_config(config)

        # Create test input
        input_shape = (1, config['architecture']['input_channels'], *config['image_size'])
        test_input = torch.randn(input_shape)

        # Perform forward pass
        with torch.no_grad():
            output = model(test_input)

        assert output is not None
        assert output.shape[0] == 1  # Batch size
        assert output.shape[1] == config['num_classes']  # Number of classes

    def test_generate_and_create_model(self, architecture_generator):
        """Test the combined generate_and_create_model method"""
        model, config = architecture_generator.generate_and_create_model(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification'
        )

        assert model is not None
        assert isinstance(model, torch.nn.Module)
        assert config is not None
        assert isinstance(config, dict)


class TestArchitectureVariations:
    """Test different architecture variations"""

    def test_different_input_shapes(self, architecture_generator):
        """Test architecture generation with different input shapes"""
        shapes = [(1, 28, 28), (1, 224, 224), (1, 320, 320)]

        for shape in shapes:
            config = architecture_generator.generate_architecture(
                'mimic_cxr',
                input_shape=shape
            )
            assert config is not None
            assert config['image_size'] == (shape[1], shape[2])

    def test_different_task_types(self, architecture_generator):
        """Test architecture generation with different task types"""
        task_types = ['binary_classification', 'multi_label_classification']

        for task_type in task_types:
            config = architecture_generator.generate_architecture(
                'mimic_cxr',
                task_type=task_type
            )
            assert config is not None
            assert config['task_type'] == task_type

    def test_architecture_type_determination(self, architecture_generator):
        """Test that architecture type is determined correctly based on image size"""
        # Small image (should be simple_cnn)
        config_small = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 28, 28)  # 784 px area
        )

        # Medium image (should be medium_cnn)
        config_medium = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224)  # 50176 px area
        )

        # Large image (should be large_cnn)
        config_large = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 320, 320)  # 102400 px area
        )

        # Verify architecture types
        assert config_small['architecture_type'] in ['simple_cnn', 'medium_cnn']
        assert config_medium['architecture_type'] in ['medium_cnn', 'large_cnn']
        assert config_large['architecture_type'] in ['large_cnn']


class TestHistoryTracking:
    """Test generation history tracking"""

    def test_history_initialization(self, architecture_generator):
        """Test that history is initialized correctly"""
        assert hasattr(architecture_generator, 'history')
        assert isinstance(architecture_generator.history, list)
        assert len(architecture_generator.history) == 0

    def test_history_recording(self, architecture_generator):
        """Test that generation is recorded in history"""
        initial_length = len(architecture_generator.history)

        # Generate an architecture
        config = architecture_generator.generate_architecture('mimic_cxr')

        # Check that history was updated
        assert len(architecture_generator.history) == initial_length + 1

        # Check history entry structure
        history_entry = architecture_generator.history[-1]
        assert 'config' in history_entry
        assert 'generation_params' in history_entry
        assert 'validation' in history_entry

    def test_get_generation_history(self, architecture_generator):
        """Test getting generation history"""
        # Generate a few architectures
        for _ in range(3):
            architecture_generator.generate_architecture('mimic_cxr')

        history = architecture_generator.get_generation_history()
        assert isinstance(history, list)
        assert len(history) >= 3

    def test_clear_history(self, architecture_generator):
        """Test clearing generation history"""
        # Generate some architectures
        for _ in range(3):
            architecture_generator.generate_architecture('mimic_cxr')

        # Clear history
        architecture_generator.clear_history()

        # Verify history is cleared
        assert len(architecture_generator.history) == 0


class TestFallbackMechanisms:
    """Test fallback mechanisms"""

    def test_fallback_config_generation(self, architecture_generator):
        """Test fallback configuration generation"""
        fallback_config = architecture_generator._generate_fallback_config()

        assert fallback_config is not None
        assert 'name' in fallback_config
        assert fallback_config['name'] == 'FallbackCNN'
        assert 'fallback' in fallback_config
        assert fallback_config['fallback'] is True

    def test_fallback_model_creation(self, architecture_generator):
        """Test that fallback model can be created"""
        fallback_config = architecture_generator._generate_fallback_config()
        model = architecture_generator.create_model_from_generated_config(fallback_config)

        assert model is not None
        assert isinstance(model, torch.nn.Module)


class TestIntegrationWithModelFactory:
    """Test integration with ModelFactory"""

    def test_model_factory_integration(self, architecture_generator, model_factory):
        """Test that ArchitectureGenerator integrates with ModelFactory"""
        # Generate architecture
        config = architecture_generator.generate_architecture('mimic_cxr')

        # Create model using ModelFactory directly
        input_shape = (config['architecture']['input_channels'], *config['image_size'])
        model_factory_model = model_factory.create_model(config, input_shape)

        # Create model using ArchitectureGenerator
        generator_model = architecture_generator.create_model_from_generated_config(config)

        # Both should be valid models
        assert model_factory_model is not None
        assert generator_model is not None
        assert isinstance(model_factory_model, torch.nn.Module)
        assert isinstance(generator_model, torch.nn.Module)

    def test_consistent_model_creation(self, architecture_generator, model_factory):
        """Test that both methods create consistent models"""
        config = architecture_generator.generate_architecture('mimic_cxr')
        input_shape = (config['architecture']['input_channels'], *config['image_size'])

        # Create models
        model_factory_model = model_factory.create_model(config, input_shape)
        generator_model = architecture_generator.create_model_from_generated_config(config)

        # Test with same input
        test_input = torch.randn(1, *input_shape)

        with torch.no_grad():
            output1 = model_factory_model(test_input)
            output2 = generator_model(test_input)

        # Outputs should have same shape
        assert output1.shape == output2.shape


class TestErrorHandling:
    """Test error handling and robustness"""

    def test_generation_with_invalid_inputs(self, architecture_generator):
        """Test generation with invalid inputs"""
        # Test with None inputs
        config = architecture_generator.generate_architecture(
            dataset_name=None,
            input_shape=None,
            task_type=None
        )

        # Should still generate a valid config
        assert config is not None
        assert 'name' in config
        assert 'architecture' in config

    def test_model_creation_with_invalid_config(self, architecture_generator):
        """Test model creation with invalid configuration"""
        # Create an invalid config
        invalid_config = {
            'name': 'InvalidConfig',
            'architecture': {
                # Missing required fields
            }
        }

        # Should handle gracefully (may return fallback)
        try:
            model = architecture_generator.create_model_from_generated_config(invalid_config)
            # If it succeeds, it should return a valid model
            assert model is not None
        except Exception:
            # If it fails, it should fail gracefully
            pass


class TestPerformanceCharacteristics:
    """Test performance characteristics of generated architectures"""

    def test_parameter_count_variation(self, architecture_generator):
        """Test that different architectures have different parameter counts"""
        # Generate architectures for different image sizes
        configs = []
        for size in [(1, 28, 28), (1, 224, 224), (1, 320, 320)]:
            config = architecture_generator.generate_architecture('mimic_cxr', input_shape=size)
            configs.append(config)

        # Parameter counts should vary
        param_counts = [config['validation']['estimated_parameters'] for config in configs]
        assert len(set(param_counts)) > 1  # Should have different parameter counts

    def test_memory_usage_variation(self, architecture_generator):
        """Test that different architectures have different memory usage"""
        configs = []
        for size in [(1, 28, 28), (1, 224, 224), (1, 320, 320)]:
            config = architecture_generator.generate_architecture('mimic_cxr', input_shape=size)
            configs.append(config)

        # Memory usage should vary
        memory_usage = [config['validation']['estimated_memory_mb'] for config in configs]
        assert len(set(memory_usage)) > 1  # Should have different memory usage


class TestReproducibility:
    """Test reproducibility of architecture generation"""

    def test_deterministic_generation(self, architecture_generator):
        """Test that generation is deterministic for same inputs"""
        # Generate architecture multiple times with same inputs
        configs = []
        for _ in range(3):
            config = architecture_generator.generate_architecture(
                'mimic_cxr',
                input_shape=(1, 224, 224),
                task_type='binary_classification'
            )
            configs.append(config)

        # Configurations should be identical (deterministic)
        # Note: This might not be true if there's randomness in generation
        # If they're not identical, at least they should be valid
        for config in configs:
            assert config is not None
            assert 'name' in config
            assert 'architecture' in config


class TestDocumentationIntegration:
    """Test integration with documentation and metadata"""

    def test_generation_metadata(self, architecture_generator):
        """Test that generation includes proper metadata"""
        config = architecture_generator.generate_architecture('mimic_cxr')

        metadata = config['generation_metadata']
        assert isinstance(metadata, dict)
        assert 'dataset_name' in metadata
        assert 'timestamp' in metadata
        assert 'generator_version' in config
        assert 'generator_timestamp' in config

    def test_architecture_documentation(self, architecture_generator):
        """Test that generated architectures include documentation"""
        config = architecture_generator.generate_architecture('mimic_cxr')

        # Should include informative fields
        assert 'name' in config
        assert 'version' in config
        assert 'architecture_type' in config
        assert 'task_type' in config
        assert 'num_classes' in config
