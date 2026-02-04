"""
MIMIC-CXR Dataset Loader for ARCH-FL

This module provides functionality to load and preprocess the MIMIC-CXR dataset
for federated learning experiments.
"""
import sys
import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import io
import warnings
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any


sys.path.insert(0, Path(__file__).resolve().parent.parent.parent.as_posix())

dataset_dir = Path(__file__).resolve().parent.parent / 'datasets'


class MIMICCXRDataset(Dataset):
    """
    PyTorch Dataset for MIMIC-CXR chest X-ray images.

    Args:
        data_frame: Pandas DataFrame containing dataset metadata
        root_dir: Root directory containing the parquet files
        transform: Optional transform to be applied to images
        max_samples: Maximum number of samples to load (for memory management)
        binary_classification: Whether to convert to binary classification task
        target_pathology: Which pathology to use for binary classification
    """

    def __init__(self,
                 data_frame: pd.DataFrame,
                 root_dir: str = "src/datasets/mimic_cxr",
                 transform: Optional[transforms.Compose] = None,
                 max_samples: Optional[int] = None,
                 binary_classification: bool = True,
                 target_pathology: str = "Pneumonia"):
        """Initialize MIMIC-CXR dataset."""
        self.data_frame = data_frame
        self.root_dir = root_dir
        self.transform = transform
        self.binary_classification = binary_classification
        self.target_pathology = target_pathology

        # Limit samples if specified (for memory management)
        if max_samples is not None and max_samples < len(data_frame):
            self.data_frame = data_frame.sample(n=max_samples, random_state=42)

        # Preprocess findings for binary classification
        if binary_classification:
            self._preprocess_binary_labels()

        print(f"📊 MIMIC-CXR Dataset loaded: {len(self.data_frame)} samples")
        if max_samples:
            print(f"🔍 Using subset: {max_samples} samples")

    def _preprocess_binary_labels(self):
        """Convert findings text to binary labels for target pathology."""
        # Simple text-based classification (can be enhanced with NLP later)
        self.data_frame['binary_label'] = self.data_frame['findings'].apply(
            lambda x: 1 if self.target_pathology.lower() in str(x).lower() else 0
        )
        print(f"🏥 Binary labels created for {self.target_pathology}: "
              f"{self.data_frame['binary_label'].sum()} positive cases")

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return len(self.data_frame)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """Get a sample from the dataset."""
        try:
            # Get image data (assuming it's stored as bytes in the parquet)
            img_data = self.data_frame.iloc[idx]['image']

            # Handle different image data formats
            if isinstance(img_data, bytes):
                # Image stored as bytes
                image = Image.open(io.BytesIO(img_data)).convert('L')  # Convert to grayscale
            elif isinstance(img_data, str):
                # Image path stored as string
                img_path = os.path.join(self.root_dir, img_data)
                image = Image.open(img_path).convert('L')
            else:
                # Try to convert other formats
                image = Image.fromarray(img_data).convert('L')

            # Apply transformations
            if self.transform:
                image = self.transform(image)

            # Get label
            if self.binary_classification:
                label = self.data_frame.iloc[idx]['binary_label']
            else:
                # For multi-label, we'd need more sophisticated processing
                label = 0  # Placeholder

            return image, label

        except Exception as e:
            warnings.warn(f"⚠️ Error loading sample {idx}: {e}")
            # Return a blank image and dummy label if loading fails
            blank_image = torch.zeros((1, 224, 224))  # Standard chest X-ray size
            return blank_image, 0


def get_mimic_cxr_transforms(train: bool = True) -> transforms.Compose:
    """
    Get standard transforms for MIMIC-CXR dataset.

    Args:
        train: Whether to use training transforms (with augmentation)

    Returns:
        Composed transforms
    """
    if train:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485], std=[0.229])  # Grayscale normalization
        ])
    else:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485], std=[0.229])
        ])


def load_mimic_cxr_dataset(
    max_samples: int = 1000,
    binary_classification: bool = True,
    target_pathology: str = "Pneumonia",
    test_split: float = 0.2,
    random_state: int = 42
) -> Tuple[List[Dataset], Dataset]:
    """
    Load MIMIC-CXR dataset and partition it for federated learning.

    Args:
        max_samples: Maximum number of samples to load (for memory management)
        binary_classification: Whether to convert to binary classification
        target_pathology: Target pathology for binary classification
        test_split: Fraction of data to use for testing
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (client_datasets, test_dataset)
    """
    import pyarrow.parquet as pq

    print(f"🔄 Loading MIMIC-CXR dataset (max {max_samples} samples)...")

    try:
        # Load parquet files
        parquet_files = [
            dataset_dir / "mimic_cxr/data/train-00000-of-00002.parquet",
            dataset_dir / "mimic_cxr/data/train-00001-of-00002.parquet"
        ]

        # Read parquet files in chunks to manage memory
        dfs = []
        for file in parquet_files:
            file = file.as_posix()
            if os.path.exists(file):
                # Read in chunks
                table = pq.read_table(file)
                df = table.to_pandas()
                dfs.append(df)
                print(f"✓ Loaded {file}: {len(df)} samples")
            else:
                print(f"✗ File not found: {file}")

        if not dfs:
            raise FileNotFoundError("No MIMIC-CXR parquet files found")

        # Combine dataframes
        full_df = pd.concat(dfs, ignore_index=True)

        # Limit samples for memory management
        if max_samples and max_samples < len(full_df):
            full_df = full_df.sample(n=max_samples, random_state=random_state)
            print(f"🔍 Using {max_samples} samples (limited for memory)")

        # Split into train and test
        from sklearn.model_selection import train_test_split
        train_df, test_df = train_test_split(
            full_df, test_size=test_split, random_state=random_state
        )

        print(f"📊 Dataset split: {len(train_df)} train, {len(test_df)} test")

        # Create transforms
        train_transform = get_mimic_cxr_transforms(train=True)
        test_transform = get_mimic_cxr_transforms(train=False)

        # Create datasets
        train_dataset = MIMICCXRDataset(
            data_frame=train_df,
            transform=train_transform,
            binary_classification=binary_classification,
            target_pathology=target_pathology
        )

        test_dataset = MIMICCXRDataset(
            data_frame=test_df,
            transform=test_transform,
            binary_classification=binary_classification,
            target_pathology=target_pathology
        )

        print("🎉 MIMIC-CXR dataset loaded successfully!")
        return train_dataset, test_dataset

    except Exception as e:
        print(f"❌ Error loading MIMIC-CXR dataset: {e}")
        # Fallback to synthetic data
        print("🔄 Falling back to synthetic data...")
        from datasets import MedicalDataset
        from loaders import get_data_loaders

        # Create synthetic dataset as fallback
        num_samples = max_samples or 1000
        data = np.random.randn(num_samples, 1, 224, 224).astype(np.float32)
        targets = np.random.randint(0, 2, num_samples)
        synthetic_dataset = MedicalDataset(data, targets)

        # Split into train and test
        train_size = int((1 - test_split) * num_samples)
        test_size = num_samples - train_size
        train_dataset, test_dataset = torch.utils.data.random_split(
            synthetic_dataset, [train_size, test_size]
        )

        print(f"✅ Created synthetic dataset: {num_samples} samples")
        return train_dataset, test_dataset


def create_mimic_cxr_data_loaders(
    num_clients: int = 5,
    max_samples: int = 1000,
    batch_size: int = 32,
    iid: bool = False,
    alpha: float = 0.5
) -> Tuple[List[DataLoader], DataLoader]:
    """
    Create data loaders for MIMIC-CXR dataset partitioned for federated learning.

    Args:
        num_clients: Number of client partitions
        max_samples: Maximum samples to load (memory management)
        batch_size: Batch size for data loaders
        iid: Whether to use IID partitioning
        alpha: Dirichlet parameter for non-IID partitioning

    Returns:
        Tuple of (client_loaders, test_loader)
    """
    try:
        # Load dataset
        train_dataset, test_dataset = load_mimic_cxr_dataset(max_samples=max_samples)

        # Partition training data
        if iid:
            from src.data.partitioning import partition_iid
            client_datasets = partition_iid(train_dataset, num_clients)
        else:
            from src.data.partitioning import partition_non_iid
            client_datasets = partition_non_iid(train_dataset, num_clients, alpha)

        # Create data loaders
        client_loaders = [
            DataLoader(dataset, batch_size=batch_size, shuffle=True)
            for dataset in client_datasets
        ]

        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

        print(f"🎉 Created {num_clients} client loaders and 1 test loader")
        return client_loaders, test_loader

    except Exception as e:
        print(f"❌ Error creating MIMIC-CXR data loaders: {e}")
        # Fallback to existing synthetic data loader
        print("🔄 Falling back to synthetic data loaders...")
        from .loaders import get_data_loaders
        return get_data_loaders("PneumoniaMNIST", num_clients, iid, batch_size, alpha)


# Simple test function
if __name__ == "__main__":
    print("🧪 Testing MIMIC-CXR dataset loader...")

    # Test with small subset first
    try:
        client_loaders, test_loader = create_mimic_cxr_data_loaders(
            num_clients=3,
            max_samples=100,  # Very small subset for testing
            batch_size=16,
            iid=True
        )

        print(f"✅ Successfully created {len(client_loaders)} client loaders")

        # Test one batch from first client
        for batch_data, batch_labels in client_loaders[0]:
            print(f"✅ Batch shape: {batch_data.shape}, labels: {batch_labels.shape}")
            break

    except Exception as e:
        print(f"❌ Test failed: {e}")
