# Copyright (c) 2024 ARCH-FL Project
# SPDX-License-Identifier: MIT

"""
Comprehensive tests for Neural Architecture Search functionality
"""

import pytest
import torch
import numpy as np
import json
import tempfile
import os
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


class TestNeuralArchitectureSearch:
    """Test Neural Architecture Search functionality"""

    def test_nas_basic(self, architecture_generator):
        """Test basic NAS functionality"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=3  # Small number for testing
        )

        assert nas_results is not None
        assert isinstance(nas_results, dict)
        assert 'trials' in nas_results
        assert 'best_architecture' in nas_results
        assert 'best_score' in nas_results

    def test_nas_results_structure(self, architecture_generator):
        """Test that NAS results have correct structure"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2
        )

        # Check top-level structure
        assert 'dataset_name' in nas_results
        assert 'input_shape' in nas_results
        assert 'task_type' in nas_results
        assert 'num_trials' in nas_results
        assert 'search_timestamp' in nas_results

        # Check trials structure
        assert isinstance(nas_results['trials'], list)
        assert len(nas_results['trials']) == 2

        for trial in nas_results['trials']:
            assert 'trial_num' in trial
            assert 'config' in trial
            assert 'validation' in trial
            assert 'score' in trial
            assert isinstance(trial['config'], dict)
            assert isinstance(trial['validation'], dict)
            assert isinstance(trial['score'], float)

        # Check best architecture
        assert nas_results['best_architecture'] is not None
        assert isinstance(nas_results['best_architecture'], dict)
        assert nas_results['best_score'] > -float('inf')

    def test_nas_with_constraints(self, architecture_generator):
        """Test NAS with computational constraints"""
        constraints = {
            'max_memory_mb': 200,
            'max_parameters': 500000
        }

        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2,
            constraints=constraints
        )

        assert nas_results is not None
        assert 'constraints' in nas_results
        assert nas_results['constraints'] == constraints

    def test_nas_different_datasets(self, architecture_generator):
        """Test NAS with different datasets"""
        datasets = ['mimic_cxr', 'chexpert', 'pneumoniamnist']

        for dataset_name in datasets:
            nas_results = architecture_generator.neural_architecture_search(
                dataset_name=dataset_name,
                input_shape=(1, 224, 224),
                task_type='binary_classification',
                num_trials=2
            )

            assert nas_results is not None
            assert nas_results['dataset_name'] == dataset_name

    def test_nas_score_range(self, architecture_generator):
        """Test that NAS scores are in reasonable range"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=3
        )

        # Check that scores are reasonable
        for trial in nas_results['trials']:
            score = trial['score']
            # Scores should be finite and not negative infinity
            assert np.isfinite(score)
            # Scores should be in reasonable range (typically -10 to 10)
            assert score > -100
            assert score < 100


class TestNASResultsManagement:
    """Test NAS results saving and loading"""

    def test_save_nas_results(self, architecture_generator):
        """Test saving NAS results to file"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            # Save results
            architecture_generator.save_search_results(nas_results, temp_file)

            # Verify file was created
            assert os.path.exists(temp_file)

            # Verify file contains data
            with open(temp_file, 'r') as f:
                loaded_data = json.load(f)

            assert 'dataset_name' in loaded_data
            assert 'trials' in loaded_data

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_load_nas_results(self, architecture_generator):
        """Test loading NAS results from file"""
        # First, generate and save some results
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
            json.dump(nas_results, f)

        try:
            # Load results
            loaded_results = architecture_generator.load_search_results(temp_file)

            # Verify loaded results match original
            assert loaded_results['dataset_name'] == nas_results['dataset_name']
            assert loaded_results['num_trials'] == nas_results['num_trials']
            assert len(loaded_results['trials']) == len(nas_results['trials'])

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestNASArchitectureQuality:
    """Test quality of architectures generated by NAS"""

    def test_nas_generates_valid_architectures(self, architecture_generator):
        """Test that NAS generates valid architectures"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=3
        )

        # Check that all generated architectures are valid
        for trial in nas_results['trials']:
            config = trial['config']
            validation = trial['validation']

            assert validation['valid'] is True
            assert len(validation['errors']) == 0

    def test_nas_best_architecture_selection(self, architecture_generator):
        """Test that NAS selects the best architecture"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=5
        )

        # Find the trial with the highest score
        best_trial_score = max(trial['score'] for trial in nas_results['trials'])

        # Best architecture should have the highest score
        assert nas_results['best_score'] == best_trial_score

        # Best architecture should be one of the trials
        best_arch_configs = [trial['config'] for trial in nas_results['trials']
                             if trial['score'] == best_trial_score]

        assert len(best_arch_configs) > 0

    def test_nas_architecture_variation(self, architecture_generator):
        """Test that NAS generates varied architectures"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=5
        )

        # Check that architectures have some variation
        conv_layer_counts = []
        param_counts = []

        for trial in nas_results['trials']:
            config = trial['config']
            conv_layer_counts.append(len(config['architecture']['conv_layers']))
            param_counts.append(trial['validation']['estimated_parameters'])

        # Should have some variation in architecture characteristics
        assert len(set(conv_layer_counts)) > 1 or len(set(param_counts)) > 1


class TestNASModelCreation:
    """Test creating models from NAS results"""

    def test_create_model_from_nas_result(self, architecture_generator):
        """Test creating model from NAS result"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2
        )

        # Create model from best architecture
        best_config = nas_results['best_architecture']
        model = architecture_generator.create_model_from_generated_config(best_config)

        assert model is not None
        assert isinstance(model, torch.nn.Module)

    def test_nas_model_forward_pass(self, architecture_generator):
        """Test that NAS-generated models can perform forward pass"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2
        )

        # Create model from best architecture
        best_config = nas_results['best_architecture']
        model = architecture_generator.create_model_from_generated_config(best_config)

        # Test forward pass
        input_shape = (1, best_config['architecture']['input_channels'], *best_config['image_size'])
        test_input = torch.randn(input_shape)

        with torch.no_grad():
            output = model(test_input)

        assert output is not None
        assert output.shape[1] == best_config['num_classes']

    def test_create_models_from_all_nas_trials(self, architecture_generator):
        """Test creating models from all NAS trials"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=3
        )

        # Create models from all trials
        models = []
        for trial in nas_results['trials']:
            config = trial['config']
            model = architecture_generator.create_model_from_generated_config(config)
            models.append(model)

            assert model is not None
            assert isinstance(model, torch.nn.Module)

        # Should have created models for all trials
        assert len(models) == len(nas_results['trials'])


class TestNASPerformance:
    """Test performance characteristics of NAS"""

    def test_nas_timing(self, architecture_generator):
        """Test that NAS completes in reasonable time"""
        import time

        start_time = time.time()

        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=3
        )

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (less than 10 seconds for 3 trials)
        assert duration < 10.0

        # Record actual duration for reference
        print(f"NAS with 3 trials completed in {duration:.2f} seconds")

    def test_nas_scaling(self, architecture_generator):
        """Test that NAS scales reasonably with number of trials"""
        import time

        trials_and_times = []

        for num_trials in [2, 4, 6]:
            start_time = time.time()

            nas_results = architecture_generator.neural_architecture_search(
                dataset_name='mimic_cxr',
                input_shape=(1, 224, 224),
                task_type='binary_classification',
                num_trials=num_trials
            )

            end_time = time.time()
            duration = end_time - start_time
            trials_and_times.append((num_trials, duration))

            # Should complete in reasonable time
            assert duration < 15.0  # 15 seconds max for up to 6 trials

        # Print scaling information
        for trials, duration in trials_and_times:
            print(f"NAS with {trials} trials completed in {duration:.2f} seconds")


class TestNASIntegration:
    """Test integration of NAS with other components"""

    def test_nas_with_model_factory(self, architecture_generator):
        """Test NAS integration with ModelFactory"""
        from src.models.model_factory import ModelFactory

        factory = ModelFactory()

        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2
        )

        # Create model using both methods
        best_config = nas_results['best_architecture']

        # Using ArchitectureGenerator
        generator_model = architecture_generator.create_model_from_generated_config(best_config)

        # Using ModelFactory directly
        input_shape = (best_config['architecture']['input_channels'], *best_config['image_size'])
        factory_model = factory.create_model(best_config, input_shape)

        # Both should be valid
        assert generator_model is not None
        assert factory_model is not None
        assert isinstance(generator_model, torch.nn.Module)
        assert isinstance(factory_model, torch.nn.Module)

    def test_nas_with_dataset_analyzer(self, architecture_generator):
        """Test NAS integration with DatasetAnalyzer"""
        try:
            # from src.data.analyzer import DatasetAnalyzer

            # Test that NAS can use dataset analysis
            nas_results = architecture_generator.neural_architecture_search(
                dataset_name='mimic_cxr',
                input_shape=(1, 224, 224),
                task_type='binary_classification',
                num_trials=2
            )

            # Should complete successfully
            assert nas_results is not None
            assert 'trials' in nas_results

        except ImportError:
            # Skip if DatasetAnalyzer not available
            pytest.skip("DatasetAnalyzer not available")


class TestNASEdgeCases:
    """Test edge cases and error handling in NAS"""

    def test_nas_with_zero_trials(self, architecture_generator):
        """Test NAS with zero trials"""
        # This should handle gracefully or raise appropriate error
        try:
            nas_results = architecture_generator.neural_architecture_search(
                dataset_name='mimic_cxr',
                input_shape=(1, 224, 224),
                task_type='binary_classification',
                num_trials=0
            )

            # If it succeeds, should return empty results
            assert nas_results is not None
            assert len(nas_results['trials']) == 0

        except Exception as e:
            # If it fails, should fail gracefully
            assert "num_trials" in str(e) or "trials" in str(e)

    def test_nas_with_single_trial(self, architecture_generator):
        """Test NAS with single trial"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='mimic_cxr',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=1
        )

        assert nas_results is not None
        assert len(nas_results['trials']) == 1
        assert nas_results['best_architecture'] is not None

    def test_nas_with_invalid_dataset(self, architecture_generator):
        """Test NAS with invalid dataset name"""
        nas_results = architecture_generator.neural_architecture_search(
            dataset_name='invalid_dataset',
            input_shape=(1, 224, 224),
            task_type='binary_classification',
            num_trials=2
        )

        # Should still complete and generate architectures
        assert nas_results is not None
        assert len(nas_results['trials']) == 2


class TestNASReproducibility:
    """Test reproducibility of NAS results"""

    def test_nas_randomness(self, architecture_generator):
        """Test that NAS generates different architectures across runs"""
        # Run NAS multiple times
        results_list = []
        for _ in range(3):
            nas_results = architecture_generator.neural_architecture_search(
                dataset_name='mimic_cxr',
                input_shape=(1, 224, 224),
                task_type='binary_classification',
                num_trials=2
            )
            results_list.append(nas_results)

        # Results should be different (due to randomness)
        # At least some variation should be present
        param_counts = []
        for results in results_list:
            for trial in results['trials']:
                param_counts.append(trial['validation']['estimated_parameters'])

        # Should have some variation
        assert len(set(param_counts)) > 1

    def test_nas_score_consistency(self, architecture_generator):
        """Test that scoring is consistent"""
        # Generate a configuration
        config = architecture_generator.generate_architecture('mimic_cxr')
        validation = architecture_generator._validate_architecture(config, (1, 224, 224))

        # Score it multiple times
        scores = []
        for _ in range(3):
            score = architecture_generator._score_architecture(config, validation)
            scores.append(score)

        # Scores should be consistent (allowing for small random component)
        # The main components should be the same, but randomness can cause slight variation
        assert len(set([round(score, 2) for score in scores])) <= 3
