"""
Architecture Generator for ARCH-FL

AutoML system for automatically generating and optimizing model architectures
based on dataset characteristics, performance requirements, and computational constraints.
"""

import os
import sys
import json
import yaml
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import warnings
import random
from copy import deepcopy
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.data.analyzer import DatasetAnalyzer
    from src.models.model_factory import ModelFactory
    from src.data.registry import DatasetRegistry
    DATASET_ANALYZER_AVAILABLE = True
except ImportError:
    DATASET_ANALYZER_AVAILABLE = False
    warnings.warn("DatasetAnalyzer not available, some features will be limited")


class ArchitectureGenerator:
    """
    AutoML Architecture Generator for ARCH-FL.

    This class implements neural architecture search and hyperparameter optimization
    to automatically generate optimal model architectures for given datasets and constraints.
    """

    def __init__(
        self,
        config_dir: str = (Path(__file__).resolve().parent.parent.parent / "config/model")
    ):
        """
        Initialize ArchitectureGenerator.

        Args:
            config_dir: Directory containing architecture configuration files
        """
        self.config_dir = config_dir
        self.factory = ModelFactory()
        self.registry = DatasetRegistry()
        self._load_architecture_rules()
        self.search_space = self._define_search_space()
        self.history = []

    def _load_architecture_rules(self) -> None:
        """Load architecture generation rules from YAML file."""
        rules_file = os.path.join(self.config_dir, "architecture_rules.yaml")

        if os.path.exists(rules_file):
            with open(rules_file, 'r') as f:
                self.rules = yaml.safe_load(f)
        else:
            # Fallback to default rules
            self.rules = self._get_default_rules()
            warnings.warn(f"Architecture rules file not found, using defaults: {rules_file}")

    def _get_default_rules(self) -> Dict[str, Any]:
        """Get default architecture generation rules."""
        return {
            'size_categories': {
                'small': {'max_area': 10000, 'recommended_architecture': 'simple_cnn'},
                'medium': {'min_area': 10000, 'max_area': 100000, 'recommended_architecture': 'medium_cnn'},
                'large': {'min_area': 100000, 'recommended_architecture': 'large_cnn'}
            },
            'architecture_templates': {
                'simple_cnn': {'conv_layers': 2, 'conv_depth': [32, 64], 'fc_layers': 2, 'fc_depth': [128, 'num_classes']},
                'medium_cnn': {'conv_layers': 3, 'conv_depth': [32, 64, 128], 'fc_layers': 2, 'fc_depth': [256, 'num_classes']},
                'large_cnn': {'conv_layers': 4, 'conv_depth': [32, 64, 128, 256], 'fc_layers': 2, 'fc_depth': [512, 'num_classes']}
            },
            'task_complexity': {
                'binary_classification': 1.0,
                'multi_label_classification': 1.5
            }
        }

    def _define_search_space(self) -> Dict[str, Any]:
        """Define the search space for neural architecture search."""
        return {
            'conv_layers': {
                'min': 2,
                'max': 6,
                'step': 1
            },
            'conv_channels': {
                'min': 16,
                'max': 512,
                'step': 16,
                'growth_factor': 2.0
            },
            'fc_layers': {
                'min': 1,
                'max': 3,
                'step': 1
            },
            'fc_units': {
                'min': 64,
                'max': 1024,
                'step': 64
            },
            'stride': [1, 2],
            'kernel_size': [3, 5],
            'padding': [0, 1],
            'activation': ['ReLU', 'LeakyReLU', 'ELU'],
            'pooling': ['MaxPool2d', 'AvgPool2d'],
            'pool_kernel': [2, 3],
            'dropout': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
        }

    def generate_architecture(self, dataset_name: str,
                              input_shape: Optional[tuple] = None,
                              task_type: Optional[str] = None,
                              constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate optimal architecture for a given dataset.

        Args:
            dataset_name: Name of the dataset
            input_shape: Input tensor shape (C, H, W)
            task_type: Type of task (binary_classification, multi_label_classification)
            constraints: Computational constraints (memory, training_time, etc.)

        Returns:
            Dictionary with generated architecture configuration
        """
        # Record generation parameters
        generation_params = {
            'dataset_name': dataset_name,
            'input_shape': input_shape,
            'task_type': task_type,
            'constraints': constraints,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Analyze dataset if DatasetAnalyzer is available
            if DATASET_ANALYZER_AVAILABLE and dataset_name:
                analyzer = DatasetAnalyzer(dataset_name=dataset_name)
                metadata = analyzer.analyze()
                properties = metadata['properties']

                # Use dataset properties to inform architecture generation
                image_size = properties.get('image_size', (224, 224))
                channels = properties.get('channels', 1)
                num_classes = properties.get('num_classes', 2)
                task_type = task_type or properties.get('task_type', 'binary_classification')

                if input_shape is None:
                    input_shape = (channels, image_size[1], image_size[0])

                generation_params.update({
                    'analyzed_image_size': image_size,
                    'analyzed_channels': channels,
                    'analyzed_num_classes': num_classes,
                    'analyzed_task_type': task_type
                })
            else:
                # Use provided parameters or defaults
                if input_shape is None:
                    input_shape = (1, 224, 224)  # Default: 1 channel, 224x224
                if task_type is None:
                    task_type = 'binary_classification'

                # Estimate num_classes based on task type
                num_classes = 2 if task_type == 'binary_classification' else 14

                generation_params.update({
                    'using_defaults': True,
                    'default_input_shape': input_shape,
                    'default_task_type': task_type,
                    'default_num_classes': num_classes
                })

            # Generate architecture based on dataset characteristics
            if input_shape:
                image_area = input_shape[1] * input_shape[2]
                arch_type = self._determine_architecture_type(image_area)
                config = self._generate_from_template(arch_type, input_shape, task_type, num_classes)
            else:
                # Fallback to medium_cnn if no input shape
                config = self._generate_from_template('medium_cnn', (1, 224, 224), task_type, num_classes)

            # Apply constraints if provided
            if constraints:
                config = self._apply_constraints(config, constraints)

            # Validate the generated architecture
            validation_result = self._validate_architecture(config, input_shape)
            config['validation'] = validation_result

            # Add generation metadata
            config['generation_metadata'] = generation_params
            config['generator_version'] = '1.0'
            config['generator_timestamp'] = datetime.now().isoformat()

            # Record in history
            self.history.append({
                'config': config,
                'generation_params': generation_params,
                'validation': validation_result
            })

            return config

        except Exception as e:
            # Fallback to simple architecture if generation fails
            warnings.warn(f"Architecture generation failed: {e}, using fallback")
            fallback_config = self._generate_fallback_config(input_shape, task_type)
            fallback_config['generation_error'] = str(e)
            return fallback_config

    def _determine_architecture_type(self, image_area: int) -> str:
        """Determine architecture type based on image area."""
        size_categories = self.rules.get('size_categories', {})

        if image_area < size_categories.get('small', {}).get('max_area', 10000):
            return 'simple_cnn'
        elif image_area < size_categories.get('medium', {}).get('max_area', 100000):
            return 'medium_cnn'
        else:
            return 'large_cnn'

    def _generate_from_template(self, arch_type: str, input_shape: tuple,
                                task_type: str, num_classes: int) -> Dict[str, Any]:
        """Generate architecture from template."""
        templates = self.rules.get('architecture_templates', {})
        template = templates.get(arch_type, templates.get('medium_cnn'))

        if not template:
            raise ValueError(f"Unknown architecture type: {arch_type}")

        # Get task complexity multiplier
        task_complexity = self.rules.get('task_complexity', {}).get(task_type, 1.0)

        # Generate configuration based on template
        config = {
            'name': f"AutoGenerated{arch_type.title()}",
            'version': '1.0',
            'architecture_type': arch_type,
            'task_type': task_type,
            'num_classes': num_classes,
            'input_channels': input_shape[0],
            'image_size': (input_shape[1], input_shape[2]),
            'task_complexity': task_complexity,
            'architecture': {
                'input_channels': input_shape[0],
                'activation': 'ReLU',
                'pooling': 'MaxPool2d',
                'pool_kernel': 2,
                'dropout': 0.5
            }
        }

        # Generate convolutional layers
        conv_layers_config = []
        num_conv_layers = template.get('conv_layers', 3)
        conv_depths = template.get('conv_depth', [32, 64, 128])

        # Adjust depth based on task complexity
        adjusted_depths = [int(depth * task_complexity) for depth in conv_depths]

        for i in range(num_conv_layers):
            if i < len(adjusted_depths):
                out_channels = adjusted_depths[i]
            else:
                # Extend depth pattern if more layers than template
                out_channels = adjusted_depths[-1] * (2 ** (i - len(adjusted_depths) + 1))

            conv_layers_config.append({
                'out_channels': out_channels,
                'kernel_size': 3,
                'stride': 2 if i < num_conv_layers - 1 else 1,  # Reduce stride for last layer
                'padding': 1
            })

        config['architecture']['conv_layers'] = conv_layers_config

        # Generate fully connected layers
        fc_layers_config = []
        num_fc_layers = template.get('fc_layers', 2)
        fc_depths = template.get('fc_depth', [256, 'num_classes'])

        for i in range(num_fc_layers):
            if i < len(fc_depths):
                if fc_depths[i] == 'num_classes':
                    out_features = num_classes
                else:
                    out_features = int(fc_depths[i] * task_complexity)
            else:
                out_features = num_classes if i == num_fc_layers - 1 else 256

            fc_layers_config.append({
                'out_features': out_features
            })

        config['architecture']['fc_layers'] = fc_layers_config

        return config

    def _apply_constraints(self, config: Dict[str, Any],
                           constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Apply computational constraints to architecture."""
        # Make a deep copy to avoid modifying original
        constrained_config = deepcopy(config)

        # Apply memory constraints
        if 'max_memory_mb' in constraints:
            constrained_config = self._apply_memory_constraint(constrained_config, constraints['max_memory_mb'])

        # Apply training time constraints
        if 'max_training_time' in constraints:
            constrained_config = self._apply_training_time_constraint(constrained_config, constraints['max_training_time'])

        # Apply parameter count constraints
        if 'max_parameters' in constraints:
            constrained_config = self._apply_parameter_constraint(constrained_config, constraints['max_parameters'])

        constrained_config['constraints_applied'] = constraints
        return constrained_config

    def _apply_memory_constraint(self, config: Dict[str, Any], max_memory_mb: float) -> Dict[str, Any]:
        """Adjust architecture to fit memory constraints."""
        # Estimate current memory usage
        current_memory = self._estimate_memory_usage(config)

        if current_memory > max_memory_mb:
            # Reduce architecture complexity
            reduction_factor = max_memory_mb / current_memory

            # Reduce convolutional layers
            conv_layers = config['architecture']['conv_layers']
            if len(conv_layers) > 2:
                # Remove some layers
                new_conv_layers = conv_layers[:max(2, int(len(conv_layers) * reduction_factor))]
                config['architecture']['conv_layers'] = new_conv_layers

            # Reduce channel counts
            for layer in config['architecture']['conv_layers']:
                layer['out_channels'] = max(16, int(layer['out_channels'] * reduction_factor))

            # Reduce FC layer sizes
            fc_layers = config['architecture']['fc_layers']
            for i, layer in enumerate(fc_layers[:-1]):  # Don't reduce final layer
                layer['out_features'] = max(64, int(layer['out_features'] * reduction_factor))

        return config

    def _apply_training_time_constraint(self, config: Dict[str, Any],
                                        max_training_time: float) -> Dict[str, Any]:
        """Adjust architecture to fit training time constraints."""
        # Estimate current training time
        current_time = self._estimate_training_time(config)

        if current_time > max_training_time:
            reduction_factor = max_training_time / current_time

            # Reduce number of layers
            conv_layers = config['architecture']['conv_layers']
            if len(conv_layers) > 2:
                new_conv_layers = conv_layers[:max(2, int(len(conv_layers) * reduction_factor))]
                config['architecture']['conv_layers'] = new_conv_layers

            # Reduce channel counts
            for layer in config['architecture']['conv_layers']:
                layer['out_channels'] = max(16, int(layer['out_channels'] * reduction_factor))

        return config

    def _apply_parameter_constraint(self, config: Dict[str, Any],
                                    max_parameters: int) -> Dict[str, Any]:
        """Adjust architecture to fit parameter count constraints."""
        # Estimate current parameter count
        current_params = self._estimate_parameter_count(config)

        if current_params > max_parameters:
            reduction_factor = max_parameters / current_params

            # Reduce convolutional layers
            conv_layers = config['architecture']['conv_layers']
            if len(conv_layers) > 2:
                new_conv_layers = conv_layers[:max(2, int(len(conv_layers) * reduction_factor))]
                config['architecture']['conv_layers'] = new_conv_layers

            # Reduce channel counts
            for layer in config['architecture']['conv_layers']:
                layer['out_channels'] = max(16, int(layer['out_channels'] * reduction_factor))

            # Reduce FC layer sizes
            fc_layers = config['architecture']['fc_layers']
            for i, layer in enumerate(fc_layers[:-1]):  # Don't reduce final layer
                layer['out_features'] = max(64, int(layer['out_features'] * reduction_factor))

        return config

    def _estimate_memory_usage(self, config: Dict[str, Any]) -> float:
        """Estimate memory usage of architecture in MB."""
        # Simple heuristic-based estimation
        conv_layers = config['architecture']['conv_layers']
        fc_layers = config['architecture']['fc_layers']

        # Estimate conv layer memory
        conv_memory = 0
        for layer in conv_layers:
            # Rough estimate: channels * kernel_size^2 * 4 bytes per float
            conv_memory += layer['out_channels'] * (layer['kernel_size'] ** 2) * 4

        # Estimate FC layer memory
        fc_memory = 0
        for layer in fc_layers:
            # Rough estimate: input_features * output_features * 4 bytes
            fc_memory += layer['out_features'] * 256 * 4  # Assume 256 input features

        # Convert to MB and add overhead
        total_memory = (conv_memory + fc_memory) / (1024 * 1024)
        return total_memory * 1.5  # Add 50% overhead

    def _estimate_training_time(self, config: Dict[str, Any]) -> float:
        """Estimate training time per epoch in seconds."""
        # Simple heuristic-based estimation
        conv_layers = config['architecture']['conv_layers']

        # Base time based on number of conv layers
        base_time = len(conv_layers) * 5.0  # 5 seconds per conv layer

        # Adjust for channel counts
        avg_channels = np.mean([layer['out_channels'] for layer in conv_layers])
        channel_factor = avg_channels / 64.0  # Normalize to 64 channels

        estimated_time = base_time * channel_factor
        return estimated_time

    def _estimate_parameter_count(self, config: Dict[str, Any]) -> int:
        """Estimate total parameter count of architecture."""
        conv_layers = config['architecture']['conv_layers']
        fc_layers = config['architecture']['fc_layers']
        input_channels = config['architecture']['input_channels']

        # Estimate conv layer parameters
        conv_params = 0
        current_channels = input_channels

        for layer in conv_layers:
            kernel_size = layer['kernel_size']
            out_channels = layer['out_channels']

            # Conv layer parameters: out_channels * (in_channels * kernel_size^2 + bias)
            conv_params += out_channels * (current_channels * kernel_size * kernel_size + 1)
            current_channels = out_channels

        # Estimate FC layer parameters
        fc_params = 0
        # Assume flattened size of 1024 for estimation
        flattened_size = 1024

        for i, layer in enumerate(fc_layers):
            out_features = layer['out_features']
            fc_params += out_features * (flattened_size + 1)  # +1 for bias
            flattened_size = out_features

        return conv_params + fc_params

    def _validate_architecture(self, config: Dict[str, Any],
                               input_shape: tuple) -> Dict[str, Any]:
        """Validate generated architecture."""
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'estimated_parameters': 0,
            'estimated_memory_mb': 0,
            'estimated_training_time': 0
        }

        try:
            # Check basic structure
            if 'architecture' not in config:
                validation_result['errors'].append('Missing architecture section')
                validation_result['valid'] = False

            arch = config['architecture']

            # Check required fields
            required_fields = ['conv_layers', 'fc_layers', 'input_channels']
            for field in required_fields:
                if field not in arch:
                    validation_result['errors'].append(f'Missing required field: {field}')
                    validation_result['valid'] = False

            # Check conv layers
            conv_layers = arch['conv_layers']
            if not conv_layers or len(conv_layers) < 1:
                validation_result['errors'].append('At least one conv layer required')
                validation_result['valid'] = False
            else:
                for i, layer in enumerate(conv_layers):
                    if 'out_channels' not in layer:
                        validation_result['errors'].append(f'Conv layer {i} missing out_channels')
                        validation_result['valid'] = False
                    if layer['out_channels'] < 8:
                        validation_result['warnings'].append(f'Conv layer {i} has very few channels: {layer["out_channels"]}')

            # Check FC layers
            fc_layers = arch['fc_layers']
            if not fc_layers or len(fc_layers) < 1:
                validation_result['errors'].append('At least one FC layer required')
                validation_result['valid'] = False
            else:
                # Check final layer matches num_classes
                final_layer = fc_layers[-1]
                expected_classes = config.get('num_classes', 2)
                if final_layer['out_features'] != expected_classes:
                    validation_result['warnings'].append(
                        f'Final layer output ({final_layer["out_features"]}) '
                        + f'does not match num_classes ({expected_classes})'
                    )

            # Estimate architecture metrics
            validation_result['estimated_parameters'] = self._estimate_parameter_count(config)
            validation_result['estimated_memory_mb'] = self._estimate_memory_usage(config)
            validation_result['estimated_training_time'] = self._estimate_training_time(config)

            # Add informational messages
            validation_result['info'] = {
                'architecture_type': config.get('architecture_type', 'unknown'),
                'task_type': config.get('task_type', 'unknown'),
                'image_size': config.get('image_size', 'unknown'),
                'num_classes': config.get('num_classes', 'unknown')
            }

        except Exception as e:
            validation_result['errors'].append(f'Validation error: {str(e)}')
            validation_result['valid'] = False

        return validation_result

    def _generate_fallback_config(self, input_shape: Optional[tuple] = None,
                                  task_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate fallback configuration if generation fails."""
        if input_shape is None:
            input_shape = (1, 224, 224)
        if task_type is None:
            task_type = 'binary_classification'

        num_classes = 2 if task_type == 'binary_classification' else 14

        return {
            'name': 'FallbackCNN',
            'version': '1.0',
            'architecture_type': 'medium_cnn',
            'task_type': task_type,
            'num_classes': num_classes,
            'input_channels': input_shape[0],
            'image_size': (input_shape[1], input_shape[2]),
            'architecture': {
                'input_channels': input_shape[0],
                'conv_layers': [
                    {'out_channels': 32, 'kernel_size': 3, 'stride': 2, 'padding': 1},
                    {'out_channels': 64, 'kernel_size': 3, 'stride': 2, 'padding': 1},
                    {'out_channels': 128, 'kernel_size': 3, 'stride': 1, 'padding': 1}
                ],
                'fc_layers': [
                    {'out_features': 256},
                    {'out_features': num_classes}
                ],
                'activation': 'ReLU',
                'pooling': 'MaxPool2d',
                'pool_kernel': 2,
                'dropout': 0.5
            },
            'fallback': True,
            'generation_timestamp': datetime.now().isoformat()
        }

    def create_model_from_generated_config(self, config: Dict[str, Any]) -> nn.Module:
        """
        Create PyTorch model from generated configuration.

        Args:
            config: Generated architecture configuration

        Returns:
            PyTorch model instance
        """
        try:
            # Extract input shape from config
            input_channels = config['architecture']['input_channels']
            image_size = config.get('image_size', (224, 224))
            input_shape = (input_channels, image_size[0], image_size[1])

            # Create model using ModelFactory
            model = self.factory.create_model(config, input_shape)

            return model

        except Exception as e:
            warnings.warn(f"Failed to create model from generated config: {e}")
            # Try fallback
            fallback_config = self._generate_fallback_config()
            return self.factory.create_model(fallback_config, (1, 224, 224))

    def generate_and_create_model(self, dataset_name: str,
                                  input_shape: Optional[tuple] = None,
                                  task_type: Optional[str] = None,
                                  constraints: Optional[Dict[str, Any]] = None) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        Generate architecture and create model in one step.

        Args:
            dataset_name: Name of the dataset
            input_shape: Input tensor shape
            task_type: Task type
            constraints: Computational constraints

        Returns:
            Tuple of (model, config)
        """
        # Generate architecture
        config = self.generate_architecture(dataset_name, input_shape, task_type, constraints)

        # Create model
        model = self.create_model_from_generated_config(config)

        return model, config

    def neural_architecture_search(self, dataset_name: str,
                                   input_shape: tuple,
                                   task_type: str,
                                   num_trials: int = 10,
                                   constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform neural architecture search to find optimal architecture.

        Args:
            dataset_name: Name of the dataset
            input_shape: Input tensor shape
            task_type: Task type
            num_trials: Number of architectures to try
            constraints: Computational constraints

        Returns:
            Dictionary with best architecture and search results
        """
        search_results = {
            'dataset_name': dataset_name,
            'input_shape': input_shape,
            'task_type': task_type,
            'num_trials': num_trials,
            'constraints': constraints,
            'trials': [],
            'best_architecture': None,
            'best_score': -float('inf'),
            'search_timestamp': datetime.now().isoformat()
        }

        for trial_num in range(num_trials):
            # Generate random architecture variations
            config = self._generate_random_architecture_variation(dataset_name, input_shape, task_type, constraints)

            # Validate architecture
            validation = self._validate_architecture(config, input_shape)

            # Score architecture (simple heuristic for now)
            score = self._score_architecture(config, validation)

            # Record trial
            trial_result = {
                'trial_num': trial_num,
                'config': config,
                'validation': validation,
                'score': score
            }
            search_results['trials'].append(trial_result)

            # Update best architecture
            if score > search_results['best_score']:
                search_results['best_score'] = score
                search_results['best_architecture'] = config

            print(f"NAS Trial {trial_num + 1}/{num_trials}: Score = {score:.2f}")

        return search_results

    def _generate_random_architecture_variation(self, dataset_name: str,
                                                input_shape: tuple,
                                                task_type: str,
                                                constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate random architecture variation for NAS."""
        # Start with base architecture
        base_config = self.generate_architecture(dataset_name, input_shape, task_type, constraints)

        # Create a copy to modify
        config = deepcopy(base_config)

        # Randomly vary architecture parameters
        arch = config['architecture']

        # Vary number of conv layers (±1)
        num_conv_layers = len(arch['conv_layers'])
        new_num_conv = max(2, min(6, num_conv_layers + random.choice([-1, 0, 1])))

        if new_num_conv != num_conv_layers:
            # Add or remove layers
            if new_num_conv > num_conv_layers:
                # Add layers
                last_layer = arch['conv_layers'][-1]
                for _ in range(new_num_conv - num_conv_layers):
                    new_layer = {
                        'out_channels': min(512, last_layer['out_channels'] * 2),
                        'kernel_size': random.choice([3, 5]),
                        'stride': 1,
                        'padding': 1
                    }
                    arch['conv_layers'].append(new_layer)
            else:
                # Remove layers
                arch['conv_layers'] = arch['conv_layers'][:new_num_conv]

        # Vary channel counts (±20%)
        for layer in arch['conv_layers']:
            layer['out_channels'] = max(16, int(layer['out_channels'] * random.uniform(0.8, 1.2)))

        # Vary FC layer sizes (±20%)
        for i, layer in enumerate(arch['fc_layers'][:-1]):  # Don't vary final layer
            layer['out_features'] = max(64, int(layer['out_features'] * random.uniform(0.8, 1.2)))

        # Randomly change activation
        arch['activation'] = random.choice(['ReLU', 'LeakyReLU', 'ELU'])

        # Randomly change dropout
        arch['dropout'] = random.choice([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])

        return config

    def _score_architecture(self, config: Dict[str, Any],
                            validation: Dict[str, Any]) -> float:
        """Score architecture based on multiple factors."""
        # Base score from validation
        score = 0.0

        # Penalize invalid architectures
        if not validation.get('valid', True):
            return -float('inf')

        # Favor architectures with reasonable parameter counts
        params = validation.get('estimated_parameters', 0)
        if params > 0:
            # Optimal around 500K parameters
            param_score = 1.0 - abs(np.log10(params) - np.log10(500000)) / 3.0
            score += param_score * 0.4

        # Favor architectures with reasonable memory usage
        memory = validation.get('estimated_memory_mb', 0)
        if memory > 0:
            # Optimal around 200 MB
            memory_score = 1.0 - abs(np.log10(memory) - np.log10(200)) / 2.0
            score += memory_score * 0.3

        # Favor architectures with reasonable training time
        time = validation.get('estimated_training_time', 0)
        if time > 0:
            # Optimal around 10 seconds per epoch
            time_score = 1.0 - abs(np.log10(time) - np.log10(10)) / 1.5
            score += time_score * 0.3

        # Add small random component for exploration
        score += random.uniform(0, 0.1)

        return score

    def save_search_results(self, search_results: Dict[str, Any],
                            output_file: str) -> None:
        """Save neural architecture search results to file."""
        with open(output_file, 'w') as f:
            json.dump(search_results, f, indent=2)

        print(f"💾 NAS results saved to: {output_file}")

    def load_search_results(self, input_file: str) -> Dict[str, Any]:
        """Load neural architecture search results from file."""
        with open(input_file, 'r') as f:
            search_results = json.load(f)

        print(f"📊 NAS results loaded from: {input_file}")
        return search_results

    def get_generation_history(self) -> List[Dict[str, Any]]:
        """Get history of generated architectures."""
        return self.history

    def clear_history(self) -> None:
        """Clear generation history."""
        self.history = []


def get_architecture_generator() -> ArchitectureGenerator:
    """Get singleton instance of ArchitectureGenerator."""
    return ArchitectureGenerator()


# Test the ArchitectureGenerator
if __name__ == "__main__":
    print("🧪 Testing ArchitectureGenerator...")

    generator = ArchitectureGenerator()

    # Test architecture generation for different datasets
    datasets_to_test = ['mimic_cxr', 'chexpert', 'pneumoniamnist']

    for dataset_name in datasets_to_test:
        print(f"\n🔍 Generating architecture for {dataset_name}...")

        # Generate architecture
        config = generator.generate_architecture(dataset_name)

        print(f"✅ Generated: {config['name']}")
        print(f"   Type: {config['architecture_type']}")
        print(f"   Conv Layers: {len(config['architecture']['conv_layers'])}")
        print(f"   FC Layers: {len(config['architecture']['fc_layers'])}")
        print(f"   Parameters: ~{config['validation']['estimated_parameters']:,}")
        print(f"   Memory: ~{config['validation']['estimated_memory_mb']:.1f} MB")

        # Create model from generated config
        try:
            model = generator.create_model_from_generated_config(config)
            test_input = torch.randn(1, *config['architecture']['input_channels'],
                                     *config['image_size'])
            output = model(test_input)
            print(f"   ✅ Model created: {test_input.shape} -> {output.shape}")
        except Exception as e:
            print(f"   ❌ Model creation failed: {e}")

    # Test neural architecture search (small scale)
    print("\n🔬 Testing Neural Architecture Search (3 trials)...")
    nas_results = generator.neural_architecture_search(
        dataset_name='mimic_cxr',
        input_shape=(1, 224, 224),
        task_type='binary_classification',
        num_trials=3
    )

    print("✅ NAS completed")
    print(f"   Best score: {nas_results['best_score']:.2f}")
    print(f"   Best architecture: {nas_results['best_architecture']['name']}")

    # Save NAS results
    generator.save_search_results(nas_results, 'docs/analysis/nas_results_example.json')

    print("\n🎉 ArchitectureGenerator tests completed!")
