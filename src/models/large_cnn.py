"""
Large CNN model for handling 224x224 medical images (MIMIC-CXR, CheXpert)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class LargeCNN(nn.Module):
    """
    CNN model for 224x224 grayscale medical images.

    Architecture:
    - Input: 1x224x224 (grayscale)
    - Conv1: 1x224x224 -> 32x112x112 (kernel=3, stride=2)
    - Conv2: 32x112x112 -> 64x56x56 (kernel=3, stride=2)
    - Conv3: 64x56x56 -> 128x28x28 (kernel=3, stride=2)
    - Conv4: 128x28x28 -> 256x14x14 (kernel=3, stride=2)
    - FC1: 256x14x14 -> 512
    - FC2: 512 -> num_classes
    """

    def __init__(self, num_classes: int = 2):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=2, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1)

        self.dropout = nn.Dropout(0.5)

        # Calculate the flattened size after conv layers
        # 224 -> 112 -> 56 -> 28 -> 14
        self.fc1 = nn.Linear(256 * 14 * 14, 512)
        self.fc2 = nn.Linear(512, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Conv layers with ReLU and max pooling
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2)

        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2)

        x = F.relu(self.conv3(x))
        x = F.max_pool2d(x, 2)

        x = F.relu(self.conv4(x))
        x = F.max_pool2d(x, 2)

        # Flatten and fully connected layers
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)


class MediumCNN(nn.Module):
    """
    Medium-sized CNN model for 224x224 images (balanced performance).

    Architecture:
    - Input: 1x224x224 (grayscale)
    - Conv1: 1x224x224 -> 32x112x112
    - Conv2: 32x112x112 -> 64x56x56
    - Conv3: 64x56x56 -> 128x28x28
    - FC1: 128x28x28 -> 256
    - FC2: 256 -> num_classes
    """

    def __init__(self, num_classes: int = 2):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=2, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)

        self.dropout = nn.Dropout(0.5)

        # 224 -> 112 -> 56 -> 28
        self.fc1 = nn.Linear(128 * 28 * 28, 256)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2)

        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2)

        x = F.relu(self.conv3(x))
        x = F.max_pool2d(x, 2)

        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)


# Test the models
if __name__ == "__main__":
    print("🧪 Testing LargeCNN and MediumCNN models...")

    # Test LargeCNN
    large_model = LargeCNN(num_classes=2)
    test_input = torch.randn(1, 1, 224, 224)
    output = large_model(test_input)
    print(f"✅ LargeCNN output shape: {output.shape}")

    # Test MediumCNN
    medium_model = MediumCNN(num_classes=2)
    output = medium_model(test_input)
    print(f"✅ MediumCNN output shape: {output.shape}")

    print("🎉 Model tests passed!")
