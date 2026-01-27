# Copyright (c) 2024 ARCH-FL Project
# SPDX-License-Identifier: MIT

"""
Comprehensive tests for constraint-based optimization functionality
"""

import pytest
import torch
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, Path(__file__).resolve().parent.parent.as_posix())

try:
    from src.models.architecture_generator import ArchitectureGenerator
except ImportError as e:
    print(f"Import error: {e}")
    raise


@pytest.fixture
def architecture_generator():
    """Create an ArchitectureGenerator instance"""
    return ArchitectureGenerator()


class TestConstraintBasedOptimization:
    """Test constraint-based architecture optimization"""

    def test_memory_constraint_basic(self, architecture_generator):
        """Test basic memory constraint application"""
        constraints = {'max_memory_mb': 100}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        assert config is not None
        assert 'constraints_applied' in config
        assert config['constraints_applied'] == constraints

    def test_parameter_constraint_basic(self, architecture_generator):
        """Test basic parameter constraint application"""
        constraints = {'max_parameters': 300000}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        assert config is not None
        assert 'constraints_applied' in config
        assert config['constraints_applied'] == constraints

    def test_training_time_constraint_basic(self, architecture_generator):
        """Test basic training time constraint application"""
        constraints = {'max_training_time': 5}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        assert config is not None
        assert 'constraints_applied' in config
        assert config['constraints_applied'] == constraints

    def test_multiple_constraints(self, architecture_generator):
        """Test multiple constraints applied together"""
        constraints = {
            'max_memory_mb': 150,
            'max_parameters': 400000,
            'max_training_time': 8
        }

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        assert config is not None
        assert 'constraints_applied' in config
        assert config['constraints_applied'] == constraints


class TestMemoryOptimization:
    """Test memory constraint optimization"""

    def test_memory_reduction(self, architecture_generator):
        """Test that memory constraints reduce architecture size"""
        # Generate without constraints
        config_no_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224)
        )

        # Generate with memory constraint
        constraints = {'max_memory_mb': 50}
        config_with_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Constrained version should have lower memory estimate
        mem_no_constraint = config_no_constraint['validation']['estimated_memory_mb']
        mem_with_constraint = config_with_constraint['validation']['estimated_memory_mb']

        assert mem_with_constraint <= mem_no_constraint

    def test_memory_constraint_satisfaction(self, architecture_generator):
        """Test that memory constraints are satisfied"""
        max_memory = 100
        constraints = {'max_memory_mb': max_memory}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        estimated_memory = config['validation']['estimated_memory_mb']

        # Should satisfy the constraint (with some tolerance)
        assert estimated_memory <= max_memory * 1.2  # Allow 20% tolerance

    def test_memory_optimization_preserves_validity(self, architecture_generator):
        """Test that memory optimization preserves architecture validity"""
        constraints = {'max_memory_mb': 50}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        validation = config['validation']

        assert validation['valid'] == True
        assert len(validation['errors']) == 0


class TestParameterOptimization:
    """Test parameter count constraint optimization"""

    def test_parameter_reduction(self, architecture_generator):
        """Test that parameter constraints reduce parameter count"""
        # Generate without constraints
        config_no_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224)
        )

        # Generate with parameter constraint
        constraints = {'max_parameters': 200000}
        config_with_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Constrained version should have lower parameter count
        params_no_constraint = config_no_constraint['validation']['estimated_parameters']
        params_with_constraint = config_with_constraint['validation']['estimated_parameters']

        assert params_with_constraint <= params_no_constraint

    def test_parameter_constraint_satisfaction(self, architecture_generator):
        """Test that parameter constraints are satisfied"""
        max_params = 300000
        constraints = {'max_parameters': max_params}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        estimated_params = config['validation']['estimated_parameters']

        # Should satisfy the constraint (with some tolerance)
        assert estimated_params <= max_params * 1.2  # Allow 20% tolerance

    def test_parameter_optimization_preserves_validity(self, architecture_generator):
        """Test that parameter optimization preserves architecture validity"""
        constraints = {'max_parameters': 100000}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        validation = config['validation']

        assert validation['valid'] == True
        assert len(validation['errors']) == 0


class TestTrainingTimeOptimization:
    """Test training time constraint optimization"""

    def test_training_time_reduction(self, architecture_generator):
        """Test that training time constraints reduce architecture complexity"""
        # Generate without constraints
        config_no_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224)
        )

        # Generate with training time constraint
        constraints = {'max_training_time': 3}
        config_with_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Constrained version should have lower training time estimate
        time_no_constraint = config_no_constraint['validation']['estimated_training_time']
        time_with_constraint = config_with_constraint['validation']['estimated_training_time']

        assert time_with_constraint <= time_no_constraint

    def test_training_time_constraint_satisfaction(self, architecture_generator):
        """Test that training time constraints are satisfied"""
        max_time = 5
        constraints = {'max_training_time': max_time}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        estimated_time = config['validation']['estimated_training_time']

        # Should satisfy the constraint (with some tolerance)
        assert estimated_time <= max_time * 1.2  # Allow 20% tolerance

    def test_training_time_optimization_preserves_validity(self, architecture_generator):
        """Test that training time optimization preserves architecture validity"""
        constraints = {'max_training_time': 2}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        validation = config['validation']

        assert validation['valid'] is True
        assert len(validation['errors']) == 0


class TestConstraintImpactOnArchitecture:
    """Test how constraints impact architecture characteristics"""

    def test_constraints_reduce_layer_count(self, architecture_generator):
        """Test that constraints can reduce number of layers"""
        # Generate without constraints
        config_no_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224)
        )

        # Generate with strict constraints
        constraints = {
            'max_memory_mb': 30,
            'max_parameters': 50000,
            'max_training_time': 2
        }
        config_with_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Constrained version should have fewer layers
        layers_no_constraint = len(config_no_constraint['architecture']['conv_layers'])
        layers_with_constraint = len(config_with_constraint['architecture']['conv_layers'])

        assert layers_with_constraint <= layers_no_constraint

    def test_constraints_reduce_channel_depth(self, architecture_generator):
        """Test that constraints can reduce channel depth"""
        # Generate without constraints
        config_no_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224)
        )

        # Generate with strict constraints
        constraints = {'max_memory_mb': 40}
        config_with_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Constrained version should have smaller channels
        if len(config_no_constraint['architecture']['conv_layers']) > 0:
            max_channels_no_constraint = max(
                layer['out_channels']
                for layer in config_no_constraint['architecture']['conv_layers']
            )
            max_channels_with_constraint = max(
                layer['out_channels']
                for layer in config_with_constraint['architecture']['conv_layers']
            )

            assert max_channels_with_constraint <= max_channels_no_constraint

    def test_constraints_preserve_final_layer(self, architecture_generator):
        """Test that constraints preserve final layer structure"""
        constraints = {
            'max_memory_mb': 50,
            'max_parameters': 100000
        }

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            constraints=constraints
        )

        # Final layer should still match num_classes
        fc_layers = config['architecture']['fc_layers']
        final_layer = fc_layers[-1]

        assert final_layer['out_features'] == config['num_classes']


class TestConstraintEdgeCases:
    """Test edge cases in constraint handling"""

    def test_very_strict_constraints(self, architecture_generator):
        """Test with very strict constraints"""
        constraints = {
            'max_memory_mb': 10,
            'max_parameters': 10000,
            'max_training_time': 0.5
        }

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Should still generate a valid architecture
        assert config is not None
        assert config['validation']['valid'] == True

    def test_very_loose_constraints(self, architecture_generator):
        """Test with very loose constraints"""
        constraints = {
            'max_memory_mb': 1000,
            'max_parameters': 10000000,
            'max_training_time': 100
        }

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Should generate architecture similar to unconstrained
        assert config is not None
        assert config['validation']['valid'] == True

    def test_empty_constraints(self, architecture_generator):
        """Test with empty constraints dict"""
        constraints = {}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Should work like no constraints
        assert config is not None
        assert config['validation']['valid'] == True

    def test_none_constraints(self, architecture_generator):
        """Test with None constraints"""
        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=None
        )

        # Should work like no constraints
        assert config is not None
        assert config['validation']['valid'] == True


class TestConstraintModelCreation:
    """Test creating models from constrained architectures"""

    def test_create_model_from_constrained_config(self, architecture_generator):
        """Test creating model from constrained configuration"""
        constraints = {
            'max_memory_mb': 100,
            'max_parameters': 300000
        }

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        model = architecture_generator.create_model_from_generated_config(config)

        assert model is not None
        assert isinstance(model, torch.nn.Module)

    def test_constrained_model_forward_pass(self, architecture_generator):
        """Test that constrained models can perform forward pass"""
        constraints = {'max_memory_mb': 80}

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        model = architecture_generator.create_model_from_generated_config(config)

        # Test forward pass
        input_shape = (1, config['architecture']['input_channels'], *config['image_size'])
        test_input = torch.randn(input_shape)

        with torch.no_grad():
            output = model(test_input)

        assert output is not None
        assert output.shape[1] == config['num_classes']

    def test_constraints_preserve_model_functionality(self, architecture_generator):
        """Test that constraints preserve model functionality"""
        # Generate with and without constraints
        config_no_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224)
        )

        constraints = {'max_memory_mb': 150}
        config_with_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Create models
        model_no_constraint = architecture_generator.create_model_from_generated_config(config_no_constraint)
        model_with_constraint = architecture_generator.create_model_from_generated_config(config_with_constraint)

        # Test with same input
        input_shape = (1, 1, 224, 224)
        test_input = torch.randn(input_shape)

        with torch.no_grad():
            output_no_constraint = model_no_constraint(test_input)
            output_with_constraint = model_with_constraint(test_input)

        # Both should produce valid outputs
        assert output_no_constraint is not None
        assert output_with_constraint is not None
        assert output_no_constraint.shape == output_with_constraint.shape


class TestConstraintPerformanceImpact:
    """Test performance impact of constraints"""

    def test_constraints_reduce_resource_usage(self, architecture_generator):
        """Test that constraints reduce overall resource usage"""
        # Generate without constraints
        config_no_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224)
        )

        # Generate with constraints
        constraints = {
            'max_memory_mb': 100,
            'max_parameters': 300000,
            'max_training_time': 5
        }
        config_with_constraint = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        # Constrained version should use fewer resources
        val_no_constraint = config_no_constraint['validation']
        val_with_constraint = config_with_constraint['validation']

        assert val_with_constraint['estimated_memory_mb'] <= val_no_constraint['estimated_memory_mb']
        assert val_with_constraint['estimated_parameters'] <= val_no_constraint['estimated_parameters']
        assert val_with_constraint['estimated_training_time'] <= val_no_constraint['estimated_training_time']

    def test_constraints_maintain_reasonable_performance(self, architecture_generator):
        """Test that constraints maintain reasonable performance characteristics"""
        constraints = {
            'max_memory_mb': 150,
            'max_parameters': 500000
        }

        config = architecture_generator.generate_architecture(
            'mimic_cxr',
            input_shape=(1, 224, 224),
            constraints=constraints
        )

        validation = config['validation']

        # Should still have reasonable performance characteristics
        assert validation['estimated_parameters'] > 10000  # More than trivial
        assert validation['estimated_memory_mb'] > 0.1  # More than trivial (can be very small with constraints)
        assert validation['estimated_training_time'] > 0.1  # More than trivial


class TestConstraintIntegration:
    """Test constraint integration with other components"""

    def test_constraints_with_nas(self, architecture_generator):
        """Test constraints with neural architecture search"""
        constraints = {
            'max_memory_mb': 100,
            'max_parameters': 300000
        }

        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2,
            constraints=constraints
        )

        # All trials should respect constraints
        for trial in nas_results['trials']:
            config = trial['config']
            validation = trial['validation']

            assert validation['estimated_memory_mb'] <= constraints['max_memory_mb'] * 1.2
            assert validation['estimated_parameters'] <= constraints['max_parameters'] * 1.2

    def test_constraints_with_different_datasets(self, architecture_generator):
        """Test constraints with different datasets"""
        datasets = ['mimic_cxr', 'chexpert', 'pneumoniamnist']
        constraints = {'max_memory_mb': 100}

        for dataset_name in datasets:
            config = architecture_generator.generate_architecture(
                dataset_name,
                input_shape=(1, 224, 224),
                constraints=constraints
            )

            # Should work for all datasets
            assert config is not None
            assert config['validation']['valid'] == True

    def test_constraints_with_different_task_types(self, architecture_generator):
        """Test constraints with different task types"""
        task_types = ['binary_classification', 'multi_label_classification']
        constraints = {'max_memory_mb': 100}

        for task_type in task_types:
            config = architecture_generator.generate_architecture(
                'mimic_cxr',
                input_shape=(1, 224, 224),
                task_type=task_type,
                constraints=constraints
            )

            # Should work for all task types
            assert config is not None
            assert config['validation']['valid'] == True
