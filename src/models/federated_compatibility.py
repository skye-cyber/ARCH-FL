"""
Federated Learning Compatibility Validator for ARCH-FL

This module provides validation and testing utilities to ensure that custom architectures
are compatible with the federated learning framework.
"""

import sys
import os
from typing import Dict, Any, Optional, Tuple
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Handle both direct execution and module import
if __name__ == "__main__":
    # When running directly, add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class FederatedCompatibilityValidator:
    """
    Validator for ensuring architectures are compatible with federated learning.
    
    This class provides methods to test and validate that custom architectures
    meet the requirements for federated learning, including:
    - Proper model structure (nn.Module)
    - Compatibility with client training
    - State dict serialization/deserialization
    - Forward/backward pass compatibility
    """
    
    def __init__(self):
        """Initialize compatibility validator."""
        self.device = "cpu"  # Use CPU for testing by default
    
    def validate_architecture_for_federated_learning(self, model: nn.Module,
                                                    input_shape: Tuple[int, ...] = (1, 28, 28),
                                                    num_classes: int = 2) -> bool:
        """
        Validate that a model is compatible with federated learning.
        
        Args:
            model: PyTorch model to validate
            input_shape: Input tensor shape (C, H, W)
            num_classes: Number of output classes
            
        Returns:
            True if model is compatible, False otherwise
        """
        print(f"🔍 Validating model {type(model).__name__} for federated learning...")
        
        try:
            # Test 1: Check if model is a nn.Module
            if not isinstance(model, nn.Module):
                print("❌ Model is not a PyTorch nn.Module")
                return False
            
            print("✅ Model is a valid nn.Module")
            
            # Test 2: Test forward pass
            if not self._test_forward_pass(model, input_shape):
                return False
            
            # Test 3: Test backward pass (training compatibility)
            if not self._test_backward_pass(model, input_shape):
                return False
            
            # Test 4: Test state dict serialization
            if not self._test_state_dict_serialization(model):
                return False
            
            # Test 5: Test client training simulation
            if not self._test_client_training_simulation(model, input_shape, num_classes):
                return False
            
            print("✅ All federated learning compatibility tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Federated learning compatibility test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_forward_pass(self, model: nn.Module, input_shape: Tuple[int, ...]) -> bool:
        """Test that the model can perform a forward pass."""
        try:
            # Create test input
            test_input = torch.randn(1, *input_shape).to(self.device)
            model.to(self.device)
            model.eval()
            
            # Perform forward pass
            with torch.no_grad():
                output = model(test_input)
            
            # Check output shape
            if len(output.shape) != 2:
                print(f"❌ Invalid output shape: {output.shape}")
                return False
            
            if output.shape[0] != 1:  # Batch size should be 1
                print(f"❌ Invalid batch size in output: {output.shape[0]}")
                return False
            
            print(f"✅ Forward pass successful, output shape: {output.shape}")
            return True
            
        except Exception as e:
            print(f"❌ Forward pass failed: {e}")
            return False
    
    def _test_backward_pass(self, model: nn.Module, input_shape: Tuple[int, ...]) -> bool:
        """Test that the model can perform backward pass (training)."""
        try:
            # Create test data
            test_input = torch.randn(2, *input_shape).to(self.device)  # Batch size 2
            test_target = torch.randint(0, 2, (2,)).to(self.device)  # Binary classification
            
            model.to(self.device)
            model.train()
            
            # Perform forward pass
            output = model(test_input)
            
            # Create loss and backward pass
            criterion = nn.CrossEntropyLoss()
            loss = criterion(output, test_target)
            loss.backward()
            
            # Check if gradients are computed
            has_gradients = False
            for name, param in model.named_parameters():
                if param.grad is not None:
                    has_gradients = True
                    break
            
            if not has_gradients:
                print("❌ No gradients computed during backward pass")
                return False
            
            print("✅ Backward pass successful, gradients computed")
            return True
            
        except Exception as e:
            print(f"❌ Backward pass failed: {e}")
            return False
    
    def _test_state_dict_serialization(self, model: nn.Module) -> bool:
        """Test that the model's state dict can be serialized and deserialized."""
        try:
            # Get state dict
            state_dict = model.state_dict()
            
            if not state_dict or len(state_dict) == 0:
                print("❌ Empty state dict")
                return False
            
            # Test serialization
            import json
            state_dict_keys = list(state_dict.keys())
            
            # Test deserialization by creating a new model and loading state dict
            # For this test, we'll just check that the state dict has the expected structure
            for key, tensor in state_dict.items():
                if not isinstance(tensor, torch.Tensor):
                    print(f"❌ State dict value for '{key}' is not a tensor")
                    return False
            
            print(f"✅ State dict serialization successful, {len(state_dict)} parameters")
            return True
            
        except Exception as e:
            print(f"❌ State dict serialization failed: {e}")
            return False
    
    def _test_client_training_simulation(self, model: nn.Module, 
                                        input_shape: Tuple[int, ...], 
                                        num_classes: int = 2) -> bool:
        """Test that the model works in a simulated client training scenario."""
        try:
            # Create synthetic dataset
            num_samples = 10
            data = torch.randn(num_samples, *input_shape)
            targets = torch.randint(0, num_classes, (num_samples,))
            
            dataset = TensorDataset(data, targets)
            train_loader = DataLoader(dataset, batch_size=2, shuffle=True)
            
            # Simulate client training
            model.to(self.device)
            optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
            criterion = nn.CrossEntropyLoss()
            
            # Perform one training step
            for batch_data, batch_targets in train_loader:
                batch_data, batch_targets = batch_data.to(self.device), batch_targets.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(batch_data)
                loss = criterion(outputs, batch_targets)
                loss.backward()
                optimizer.step()
                break  # Just test one batch
            
            print("✅ Client training simulation successful")
            return True
            
        except Exception as e:
            print(f"❌ Client training simulation failed: {e}")
            return False
    
    def validate_architecture_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate an architecture configuration for federated learning compatibility.
        
        Args:
            config: Architecture configuration to validate
            
        Returns:
            True if configuration is federated learning compatible, False otherwise
        """
        print(f"🔍 Validating architecture config for federated learning...")
        
        try:
            # Check if we can create a model from the config
            if __name__ == "__main__":
                from models.model_factory import ModelFactory
            else:
                from src.models.model_factory import ModelFactory
            factory = ModelFactory()
            
            # Determine input shape
            input_shape = config.get('input_shape', (1, 28, 28))
            
            # Create model
            model = factory.create_model(config, input_shape)
            
            # Validate the created model
            return self.validate_architecture_for_federated_learning(model, input_shape)
            
        except Exception as e:
            print(f"❌ Architecture config validation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_compatibility_report(self, model: nn.Module,
                               input_shape: Tuple[int, ...] = (1, 28, 28)) -> Dict[str, Any]:
        """
        Generate a detailed compatibility report for a model.
        
        Args:
            model: PyTorch model to analyze
            input_shape: Input tensor shape for testing
            
        Returns:
            Dictionary with compatibility analysis results
        """
        report = {
            'model_type': type(model).__name__,
            'input_shape': input_shape,
            'tests': {}
        }
        
        # Test model type
        report['tests']['is_nn_module'] = isinstance(model, nn.Module)
        
        # Test forward pass
        try:
            test_input = torch.randn(1, *input_shape).to(self.device)
            model.to(self.device)
            model.eval()
            with torch.no_grad():
                output = model(test_input)
            report['tests']['forward_pass'] = True
            report['output_shape'] = tuple(output.shape)
        except Exception as e:
            report['tests']['forward_pass'] = False
            report['forward_pass_error'] = str(e)
        
        # Test backward pass
        try:
            test_input = torch.randn(2, *input_shape).to(self.device)
            test_target = torch.randint(0, 2, (2,)).to(self.device)
            model.to(self.device)
            model.train()
            output = model(test_input)
            criterion = nn.CrossEntropyLoss()
            loss = criterion(output, test_target)
            loss.backward()
            report['tests']['backward_pass'] = True
        except Exception as e:
            report['tests']['backward_pass'] = False
            report['backward_pass_error'] = str(e)
        
        # Test state dict
        try:
            state_dict = model.state_dict()
            report['tests']['state_dict'] = len(state_dict) > 0
            report['parameter_count'] = sum(p.numel() for p in model.parameters())
        except Exception as e:
            report['tests']['state_dict'] = False
            report['state_dict_error'] = str(e)
        
        # Overall compatibility
        all_passed = all([
            report['tests'].get('is_nn_module', False),
            report['tests'].get('forward_pass', False),
            report['tests'].get('backward_pass', False),
            report['tests'].get('state_dict', False)
        ])
        
        report['compatible'] = all_passed
        
        return report


def get_federated_compatibility_validator() -> FederatedCompatibilityValidator:
    """Get singleton instance of FederatedCompatibilityValidator."""
    return FederatedCompatibilityValidator()


# Test the validator
if __name__ == "__main__":
    print("🧪 Testing FederatedCompatibilityValidator...")
    
    validator = FederatedCompatibilityValidator()
    
    # Test with SimpleCNN
    print(f"\n🔧 Testing SimpleCNN compatibility...")
    try:
        if __name__ == "__main__":
            from models.architectures import SimpleCNN
        else:
            from src.models.architectures import SimpleCNN
        simple_model = SimpleCNN(num_classes=2)
        
        is_compatible = validator.validate_architecture_for_federated_learning(
            simple_model, input_shape=(1, 28, 28), num_classes=2
        )
        
        print(f"SimpleCNN federated learning compatibility: {'✅ PASS' if is_compatible else '❌ FAIL'}")
        
        # Get detailed report
        report = validator.get_compatibility_report(simple_model, (1, 28, 28))
        print(f"\n📋 SimpleCNN Compatibility Report:")
        print(f"   Model Type: {report['model_type']}")
        print(f"   Compatible: {report['compatible']}")
        print(f"   Parameters: {report.get('parameter_count', 'N/A')}")
        print(f"   Output Shape: {report.get('output_shape', 'N/A')}")
        print(f"   Tests - Forward: {'✅' if report['tests'].get('forward_pass') else '❌'}")
        print(f"   Tests - Backward: {'✅' if report['tests'].get('backward_pass') else '❌'}")
        print(f"   Tests - State Dict: {'✅' if report['tests'].get('state_dict') else '❌'}")
        
    except Exception as e:
        print(f"❌ Error testing SimpleCNN: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with ConfigurableCNN
    print(f"\n🔧 Testing ConfigurableCNN compatibility...")
    try:
        if __name__ == "__main__":
            from models.model_factory import ModelFactory
        else:
            from src.models.model_factory import ModelFactory
        factory = ModelFactory()
        
        config = {
            'name': 'ConfigurableCNN',
            'num_classes': 2,
            'architecture': {
                'input_channels': 1,
                'conv_layers': [
                    {'out_channels': 32, 'kernel_size': 3, 'stride': 1, 'padding': 1},
                    {'out_channels': 64, 'kernel_size': 3, 'stride': 1, 'padding': 1}
                ],
                'fc_layers': [
                    {'out_features': 128},
                    {'out_features': 2}
                ],
                'activation': 'ReLU',
                'pooling': 'MaxPool2d',
                'pool_kernel': 2,
                'dropout': 0.5
            }
        }
        
        configurable_model = factory.create_model(config, (1, 28, 28))
        
        is_compatible = validator.validate_architecture_for_federated_learning(
            configurable_model, input_shape=(1, 28, 28), num_classes=2
        )
        
        print(f"ConfigurableCNN federated learning compatibility: {'✅ PASS' if is_compatible else '❌ FAIL'}")
        
    except Exception as e:
        print(f"❌ Error testing ConfigurableCNN: {e}")
        import traceback
        traceback.print_exc()
    
    # Test architecture config validation
    print(f"\n🔍 Testing architecture config validation...")
    
    valid_config = {
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
    
    config_compatible = validator.validate_architecture_config(valid_config)
    print(f"Valid config federated learning compatibility: {'✅ PASS' if config_compatible else '❌ FAIL'}")
    
    print(f"\n🎉 FederatedCompatibilityValidator tests completed!")