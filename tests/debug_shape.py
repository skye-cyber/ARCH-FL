#!/usr/bin/env python3

import sys
import os
import torch

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

print("🐛 Debugging shape issue...")

try:
    from src.models.architectures import MediumCNN
    from src.data.mimic_cxr_loader import create_mimic_cxr_data_loaders

    # Create a small data loader
    print("Creating data loader...")
    client_loaders, test_loader = create_mimic_cxr_data_loaders(
        num_clients=1,
        max_samples=10,
        batch_size=2,
        iid=True
    )

    # Get one batch to check shape
    for batch_data, batch_labels in client_loaders[0]:
        print(f"Batch data shape: {batch_data.shape}")
        print(f"Batch labels shape: {batch_labels.shape}")

        # Test with MediumCNN
        model = MediumCNN(num_classes=2)
        print("Model input expected: 1x224x224")
        print(f"Model actually getting: {batch_data.shape[1:]}")

        # Try forward pass
        try:
            output = model(batch_data)
            print(f"✅ Model output shape: {output.shape}")
        except Exception as e:
            print(f"❌ Model forward failed: {e}")

            # Debug layer by layer
            print("\n🔍 Debugging layer by layer:")
            x = batch_data
            print(f"Input: {x.shape}")

            x = torch.relu(model.conv1(x))
            print(f"After conv1: {x.shape}")
            x = torch.nn.functional.max_pool2d(x, 2)
            print(f"After pool1: {x.shape}")

            x = torch.relu(model.conv2(x))
            print(f"After conv2: {x.shape}")
            x = torch.nn.functional.max_pool2d(x, 2)
            print(f"After pool2: {x.shape}")

            x = torch.relu(model.conv3(x))
            print(f"After conv3: {x.shape}")
            x = torch.nn.functional.max_pool2d(x, 2)
            print(f"After pool3: {x.shape}")

            x = torch.flatten(x, 1)
            print(f"Flattened: {x.shape}")
            print(f"Expected by fc1: {model.fc1.weight.shape}")

        break

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
