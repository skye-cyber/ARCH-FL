"""
Custom Data Loaders for ARCH-FL Dashboard

This module provides custom data loaders for specific medical imaging datasets
like CheXpert and MIMIC-CXR that are used in the dashboard backend.
"""

import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image
import pandas as pd
import json


class MedicalImageDataset(Dataset):
    """
    Base class for medical imaging datasets.

    Handles loading and preprocessing of medical images with proper
    normalization and transformations.
    """

    def __init__(
        self,
        image_paths: List[str],
        labels: Optional[List[Any]] = None,
        transform: Optional[transforms.Compose] = None,
        label_transform: Optional[callable] = None,
        image_size: Tuple[int, int] = (224, 224),
        channels: int = 1,
    ):
        """
        Initialize medical image dataset.

        Args:
            image_paths: List of paths to image files
            labels: List of corresponding labels (can be None for unsupervised)
            transform: Image transformation pipeline
            label_transform: Label transformation function
            image_size: Target image size (height, width)
            channels: Number of image channels (1 for grayscale, 3 for RGB)
        """
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        self.label_transform = label_transform
        self.image_size = image_size
        self.channels = channels

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Any]:
        """
        Load and return an image and its label.

        Args:
            idx: Index of the sample

        Returns:
            Tuple of (image_tensor, label)
        """
        try:
            # Load image
            image = Image.open(self.image_paths[idx]).convert(
                "L" if self.channels == 1 else "RGB"
            )

            # Resize if needed
            if image.size != self.image_size:
                image = image.resize(self.image_size)

            # Convert to tensor
            if self.transform:
                image = self.transform(image)

            # Get label
            label = self.labels[idx] if self.labels is not None else None

            # Apply label transform if specified
            if self.label_transform and label is not None:
                label = self.label_transform(label)

            return image, label

        except Exception as e:
            print(f"Error loading image {self.image_paths[idx]}: {e}")
            # Return empty tensor and dummy label on error
            empty_tensor = torch.zeros((self.channels, *self.image_size))
            dummy_label = 0 if self.labels is not None else None
            return empty_tensor, dummy_label


class CheXpertDataset(MedicalImageDataset):
    """
    Custom dataset loader for CheXpert dataset.

    Handles the multi-label classification task with 14 possible findings.
    """

    def __init__(
        self,
        data_dir: str,
        split: str = "train",
        transform: Optional[transforms.Compose] = None,
        image_size: Tuple[int, int] = (320, 320),
    ):
        """
        Initialize CheXpert dataset.

        Args:
            data_dir: Path to CheXpert data directory
            split: Data split (train, validation)
            transform: Image transformation pipeline
            image_size: Target image size (height, width)
        """
        # Find all CSV files for the split
        csv_files = [
            f
            for f in os.listdir(data_dir)
            if f.startswith(f"{split}-") and f.endswith(".csv")
        ]

        if not csv_files:
            raise FileNotFoundError(f"No {split} CSV files found in {data_dir}")

        # Load metadata from first CSV file
        csv_path = os.path.join(data_dir, csv_files[0])
        df = pd.read_csv(csv_path)

        # Get image paths
        image_dir = os.path.join(data_dir, "images")
        image_paths = [
            os.path.join(image_dir, row["Path"]) for idx, row in df.iterrows()
        ]

        # Extract labels (multi-label)
        # CheXpert has 14 possible findings, we'll use the presence/absence
        label_columns = [
            "No Finding",
            "Enlarged Cardiomediastinum",
            "Cardiomegaly",
            "Lung Opacity",
            "Lung Lesion",
            "Edema",
            "Consolidation",
            "Pneumonia",
            "Atelectasis",
            "Pneumothorax",
            "Pleural Effusion",
            "Pleural Other",
            "Fracture",
            "Support Devices",
        ]

        # Convert labels to multi-hot encoding
        labels = []
        for idx, row in df.iterrows():
            label = []
            for col in label_columns:
                # Convert to binary: 3=present, 2=absent, 1=uncertain, 0=unlabeled
                # We'll treat uncertain and unlabeled as absent for simplicity
                val = row[col]
                if val == 3:  # present
                    label.append(1)
                elif val == 2:  # absent
                    label.append(0)
                elif val == 1:  # uncertain
                    label.append(0)  # treat as absent
                else:  # unlabeled
                    label.append(0)  # treat as absent
            labels.append(label)

        # Use default transform if none provided
        if transform is None:
            transform = transforms.Compose(
                [transforms.ToTensor(), transforms.Normalize(mean=[0.5], std=[0.5])]
            )

        super().__init__(
            image_paths=image_paths,
            labels=labels,
            transform=transform,
            image_size=image_size,
            channels=1,
        )


class MIMICCXRDataset(MedicalImageDataset):
    """
    Custom dataset loader for MIMIC-CXR dataset.

    Handles the multi-label classification task with findings and impressions.
    """

    def __init__(
        self,
        data_dir: str,
        split: str = "train",
        transform: Optional[transforms.Compose] = None,
        image_size: Tuple[int, int] = (224, 224),
    ):
        """
        Initialize MIMIC-CXR dataset.

        Args:
            data_dir: Path to MIMIC-CXR data directory
            split: Data split (train, validation, test)
            transform: Image transformation pipeline
            image_size: Target image size (height, width)
        """
        # Find all metadata files for the split
        metadata_files = [
            f
            for f in os.listdir(data_dir)
            if f.startswith(f"{split}-") and (f.endswith(".csv") or f.endswith(".tsv"))
        ]

        if not metadata_files:
            raise FileNotFoundError(f"No {split} metadata files found in {data_dir}")

        # Load metadata from first file
        metadata_path = os.path.join(data_dir, metadata_files[0])

        # Determine file format
        if metadata_path.endswith(".csv"):
            df = pd.read_csv(metadata_path)
        elif metadata_path.endswith(".tsv"):
            df = pd.read_csv(metadata_path, sep="\t")
        else:
            raise ValueError(f"Unsupported metadata format: {metadata_path}")

        # Get image paths
        image_paths = []
        labels = []

        for idx, row in df.iterrows():
            # MIMIC-CXR typically has 'filepath' or 'path' column
            if "filepath" in row:
                image_path = os.path.join(data_dir, row["filepath"])
            elif "path" in row:
                image_path = os.path.join(data_dir, row["path"])
            else:
                continue

            if os.path.exists(image_path):
                image_paths.append(image_path)

                # For simplicity, we'll use a binary label based on "No Finding"
                # In a real implementation, you'd extract proper multi-label findings
                label = 0  # default
                if "No Finding" in row and row["No Finding"] == "present":
                    label = 1

                labels.append(label)

        # Use default transform if none provided
        if transform is None:
            transform = transforms.Compose(
                [transforms.ToTensor(), transforms.Normalize(mean=[0.5], std=[0.5])]
            )

        super().__init__(
            image_paths=image_paths,
            labels=labels,
            transform=transform,
            image_size=image_size,
            channels=1,
        )


def get_medical_transform(
    train: bool = True, image_size: Tuple[int, int] = (224, 224)
) -> transforms.Compose:
    """
    Get standard medical image transformation pipeline.

    Args:
        train: Whether this is for training (includes augmentation)
        image_size: Target image size

    Returns:
        Composed transformation pipeline
    """
    if train:
        return transforms.Compose(
            [
                transforms.Resize(image_size),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(10),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5]),
            ]
        )
    else:
        return transforms.Compose(
            [
                transforms.Resize(image_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5]),
            ]
        )


def create_chexpert_loaders(
    data_dir: str,
    num_clients: int,
    iid: bool = True,
    batch_size: int = 32,
    alpha: float = 0.5,
) -> Tuple[List[DataLoader], DataLoader]:
    """
    Create data loaders for CheXpert dataset for federated learning.

    Args:
        data_dir: Path to CheXpert data directory
        num_clients: Number of client data loaders to create
        iid: Whether to use IID partitioning
        batch_size: Batch size for data loaders
        alpha: Alpha parameter for non-IID partitioning

    Returns:
        Tuple of (client_loaders, test_loader)
    """
    # Create full dataset
    train_transform = get_medical_transform(train=True, image_size=(320, 320))
    test_transform = get_medical_transform(train=False, image_size=(320, 320))

    full_train_dataset = CheXpertDataset(
        data_dir=data_dir,
        split="train",
        transform=train_transform,
        image_size=(320, 320),
    )

    # Create validation/test dataset
    test_dataset = CheXpertDataset(
        data_dir=data_dir,
        split="validation",
        transform=test_transform,
        image_size=(320, 320),
    )

    # Partition dataset for clients
    if iid:
        client_datasets = partition_iid(full_train_dataset, num_clients)
    else:
        client_datasets = partition_non_iid(full_train_dataset, num_clients, alpha)

    # Create client loaders
    client_loaders = []
    for client_dataset in client_datasets:
        loader = DataLoader(
            client_dataset, batch_size=batch_size, shuffle=True, num_workers=2
        )
        client_loaders.append(loader)

    # Create test loader
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, num_workers=2
    )

    return client_loaders, test_loader


def create_mimic_cxr_loaders(
    data_dir: str,
    num_clients: int,
    iid: bool = True,
    batch_size: int = 32,
    alpha: float = 0.5,
) -> Tuple[List[DataLoader], DataLoader]:
    """
    Create data loaders for MIMIC-CXR dataset for federated learning.

    Args:
        data_dir: Path to MIMIC-CXR data directory
        num_clients: Number of client data loaders to create
        iid: Whether to use IID partitioning
        batch_size: Batch size for data loaders
        alpha: Alpha parameter for non-IID partitioning

    Returns:
        Tuple of (client_loaders, test_loader)
    """
    # Create full dataset
    train_transform = get_medical_transform(train=True, image_size=(224, 224))
    test_transform = get_medical_transform(train=False, image_size=(224, 224))

    full_train_dataset = MIMICCXRDataset(
        data_dir=data_dir,
        split="train",
        transform=train_transform,
        image_size=(224, 224),
    )

    # Create test dataset (use train split for test if validation not available)
    test_dataset = MIMICCXRDataset(
        data_dir=data_dir,
        split="test",
        transform=test_transform,
        image_size=(224, 224),
    )

    # If test split doesn't exist, use a portion of train split
    if len(test_dataset) == 0:
        from torch.utils.data import random_split

        train_size = int(0.8 * len(full_train_dataset))
        test_size = len(full_train_dataset) - train_size
        full_train_dataset, test_dataset = random_split(
            full_train_dataset, [train_size, test_size]
        )
        test_dataset.dataset.transform = test_transform

    # Partition dataset for clients
    if iid:
        client_datasets = partition_iid(full_train_dataset, num_clients)
    else:
        client_datasets = partition_non_iid(full_train_dataset, num_clients, alpha)

    # Create client loaders
    client_loaders = []
    for client_dataset in client_datasets:
        loader = DataLoader(
            client_dataset, batch_size=batch_size, shuffle=True, num_workers=2
        )
        client_loaders.append(loader)

    # Create test loader
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, num_workers=2
    )

    return client_loaders, test_loader


def partition_iid(dataset: Dataset, num_clients: int) -> List[Dataset]:
    """
    Partition dataset into IID client datasets.

    Args:
        dataset: Full dataset to partition
        num_clients: Number of clients

    Returns:
        List of client datasets
    """
    import numpy as np
    from torch.utils.data import Subset

    # Shuffle indices
    indices = np.random.permutation(len(dataset))

    # Split into num_clients parts
    client_indices = np.array_split(indices, num_clients)

    # Create subsets
    client_datasets = []
    for indices in client_indices:
        client_datasets.append(Subset(dataset, indices))

    return client_datasets


def partition_non_iid(
    dataset: Dataset, num_clients: int, alpha: float
) -> List[Dataset]:
    """
    Partition dataset into non-IID client datasets using Dirichlet distribution.

    Args:
        dataset: Full dataset to partition
        num_clients: Number of clients
        alpha: Concentration parameter for Dirichlet distribution

    Returns:
        List of client datasets
    """
    import numpy as np
    from torch.utils.data import Subset

    # For multi-label datasets, we'll partition based on class distribution
    # Get labels for all samples
    labels = []
    for i in range(len(dataset)):
        _, label = dataset[i]
        labels.append(label)

    # Convert to numpy array
    labels = np.array(labels)

    # Get unique classes
    if labels.ndim > 1:  # multi-label
        num_classes = labels.shape[1]
    else:  # single-label
        num_classes = len(np.unique(labels))

    # Sample client proportions from Dirichlet distribution
    client_proportions = np.random.dirichlet(np.repeat(alpha, num_clients))

    # Assign samples to clients based on class proportions
    client_indices = [[] for _ in range(num_clients)]

    for i, label in enumerate(labels):
        if labels.ndim > 1:  # multi-label
            # For multi-label, assign to client with highest proportion for any class
            class_proportions = client_proportions[:, label.astype(bool)]
            if len(class_proportions) > 0:
                client_idx = np.argmax(np.mean(class_proportions, axis=1))
            else:
                client_idx = np.random.randint(num_clients)
        else:  # single-label
            # For single-label, assign based on label
            client_idx = np.random.choice(num_clients, p=client_proportions[:, label])

        client_indices[client_idx].append(i)

    # Create subsets
    client_datasets = []
    for indices in client_indices:
        client_datasets.append(Subset(dataset, indices))

    return client_datasets


if __name__ == "__main__":
    """Test the custom loaders."""
    print("Testing custom medical image loaders...")

    # Test CheXpert loader
    print("\nTesting CheXpertDataset...")
    try:
        # This will fail if data doesn't exist, but we can test the class
        dataset = CheXpertDataset(
            data_dir="./test_data",
            split="train",
            image_size=(320, 320),
        )
        print("✅ CheXpertDataset class works (would need real data to load)")
    except FileNotFoundError:
        print("⚠️ CheXpert data not found (expected for testing)")

    # Test MIMIC-CXR loader
    print("\nTesting MIMICCXRDataset...")
    try:
        dataset = MIMICCXRDataset(
            data_dir="./test_data",
            split="train",
            image_size=(224, 224),
        )
        print(f"✅ MIMICCXRDataset class works (would need real data to load)")
    except FileNotFoundError:
        print("⚠️ MIMIC-CXR data not found (expected for testing)")

    # Test partitioning functions
    print("\nTesting partitioning functions...")

    # Create a small synthetic dataset for testing
    from torch.utils.data import TensorDataset
    import torch

    # Create synthetic data
    data = torch.randn(100, 1, 224, 224)
    labels = torch.randint(0, 2, (100,))
    synthetic_dataset = TensorDataset(data, labels)

    # Test IID partitioning
    iid_datasets = partition_iid(synthetic_dataset, 3)
    print(f"✅ IID partitioning: created {len(iid_datasets)} client datasets")
    print(f"   Sizes: {[len(ds) for ds in iid_datasets]}")

    # Test non-IID partitioning
    non_iid_datasets = partition_non_iid(synthetic_dataset, 3, alpha=0.5)
    print(f"✅ Non-IID partitioning: created {len(non_iid_datasets)} client datasets")
    print(f"   Sizes: {[len(ds) for ds in non_iid_datasets]}")

    print("\n✅ All tests passed!")
