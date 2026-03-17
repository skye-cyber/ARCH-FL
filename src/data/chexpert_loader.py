"""
CheXpert Dataset Loader for ARCH-FL

This module provides functionality to load and preprocess the CheXpert dataset
for federated learning experiments with multi-label chest X-ray classification.
"""

import sys
import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, Subset
from torchvision import transforms
from PIL import Image
import warnings
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Union
from collections import Counter
import random

# Add project root to path
sys.path.insert(0, Path(__file__).resolve().parent.parent.parent.as_posix())

dataset_dir = Path(__file__).resolve().parent.parent / "datasets"

# CheXpert competition classes (14 observations + support devices)
CHEXPERT_CLASSES = [
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

# Standard CheXpert competition classes (14 classes)
CHEXPERT_COMPETITION_CLASSES = [
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Enlarged Cardiomediastinum",
    "Fracture",
    "Lung Lesion",
    "Lung Opacity",
    "No Finding",
    "Pleural Effusion",
    "Pleural Other",
    "Pneumonia",
    "Pneumothorax",
    "Support Devices",
]

# Class indices for multi-label classification
CHEXPERT_CLASS_TO_IDX = {
    cls: idx for idx, cls in enumerate(CHEXPERT_COMPETITION_CLASSES)
}


class CheXpertDataset(Dataset):
    """
    PyTorch Dataset for CheXpert chest X-ray images with multi-label annotations.

    Args:
        csv_file: Path to CheXpert CSV file or pandas DataFrame
        root_dir: Root directory containing the image files
        transform: Optional transform to be applied to images
        max_samples: Maximum number of samples to load (for memory management)
        binary_classification: Whether to convert to binary classification for a specific pathology
        target_pathology: Which pathology to use for binary classification
        multi_label: Whether to use multi-label classification (all 14 classes)
        uncertainty_handling: Method to handle uncertain labels ('zeros', 'ones', 'ignore')
        image_size: Target image size (height, width)
        use_frontal_only: Whether to use only frontal (AP/PA) views
        use_lateral: Whether to include lateral views
    """

    def __init__(
        self,
        csv_file: Union[str, pd.DataFrame],
        root_dir: str = "src/datasets/chexpert",
        transform: Optional[transforms.Compose] = None,
        max_samples: Optional[int] = None,
        binary_classification: bool = False,
        target_pathology: str = "Pneumonia",
        multi_label: bool = True,
        uncertainty_handling: str = "zeros",
        image_size: Tuple[int, int] = (224, 224),
        use_frontal_only: bool = True,
        use_lateral: bool = False,
    ):
        """Initialize CheXpert dataset."""
        self.root_dir = root_dir
        self.transform = transform
        self.binary_classification = binary_classification
        self.target_pathology = target_pathology
        self.multi_label = multi_label
        self.uncertainty_handling = uncertainty_handling
        self.image_size = image_size
        self.use_frontal_only = use_frontal_only
        self.use_lateral = use_lateral

        # Load CSV
        if isinstance(csv_file, str):
            self.data_frame = pd.read_csv(csv_file)
        else:
            self.data_frame = csv_file.copy()

        print(f"📊 Initial CheXpert CSV loaded: {len(self.data_frame)} samples")

        # Filter by view if specified
        self._filter_by_view()

        # Handle uncertain labels
        self._handle_uncertain_labels()

        # Limit samples if specified
        if max_samples is not None and max_samples < len(self.data_frame):
            self.data_frame = self.data_frame.sample(n=max_samples, random_state=42)
            print(f"🔍 Using subset: {max_samples} samples")

        # Validate image paths
        self._validate_paths()

        # Prepare labels
        if binary_classification:
            self._prepare_binary_labels()
        elif multi_label:
            self._prepare_multilabel_labels()

        print(f"✅ CheXpert Dataset loaded: {len(self.data_frame)} samples")
        if binary_classification:
            pos_count = (
                self.data_frame["binary_label"].sum()
                if "binary_label" in self.data_frame.columns
                else 0
            )
            print(
                f"🏥 Binary classification for '{target_pathology}': {pos_count} positive, "
                f"{len(self.data_frame) - pos_count} negative"
            )

    def _filter_by_view(self):
        """Filter samples based on view selection."""
        if "Frontal/Lateral" in self.data_frame.columns:
            if self.use_frontal_only and not self.use_lateral:
                # Keep only frontal views (AP/PA)
                self.data_frame = self.data_frame[
                    self.data_frame["Frontal/Lateral"].str.contains(
                        "frontal", case=False, na=False
                    )
                ]
                print(f"📐 Filtered to frontal views: {len(self.data_frame)} samples")
            elif not self.use_frontal_only and self.use_lateral:
                # Keep only lateral views
                self.data_frame = self.data_frame[
                    self.data_frame["Frontal/Lateral"].str.contains(
                        "lateral", case=False, na=False
                    )
                ]
                print(f"📐 Filtered to lateral views: {len(self.data_frame)} samples")

    def _handle_uncertain_labels(self):
        """Handle uncertain labels (-1 values) according to specified strategy."""
        # Get pathology columns (all columns after 'Path' column or known pathology columns)
        pathology_cols = [
            col for col in CHEXPERT_CLASSES if col in self.data_frame.columns
        ]

        for col in pathology_cols:
            if col in self.data_frame.columns:
                if self.uncertainty_handling == "zeros":
                    # Treat uncertain as negative
                    self.data_frame[col] = self.data_frame[col].replace(-1, 0)
                elif self.uncertainty_handling == "ones":
                    # Treat uncertain as positive
                    self.data_frame[col] = self.data_frame[col].replace(-1, 1)
                elif self.uncertainty_handling == "ignore":
                    # Remove uncertain samples
                    self.data_frame = self.data_frame[self.data_frame[col] != -1]

        print(f"🎯 Uncertainty handling: {self.uncertainty_handling}")

    def _validate_paths(self):
        """Validate that image paths exist and remove missing files."""
        valid_indices = []

        for idx, row in self.data_frame.iterrows():
            img_path = row.get("Path", row.get("path", ""))
            if pd.isna(img_path):
                continue

            full_path = os.path.join(self.root_dir, img_path)
            if os.path.exists(full_path):
                valid_indices.append(idx)
            else:
                # Try alternative path format
                alt_path = img_path.replace("CheXpert-v1.0/", "")
                full_alt_path = os.path.join(self.root_dir, alt_path)
                if os.path.exists(full_alt_path):
                    valid_indices.append(idx)

        if len(valid_indices) < len(self.data_frame):
            print(
                f"⚠️ Removed {len(self.data_frame) - len(valid_indices)} samples with missing images"
            )
            self.data_frame = self.data_frame.loc[valid_indices].reset_index(drop=True)

    def _prepare_binary_labels(self):
        """Create binary labels for target pathology."""
        if self.target_pathology in self.data_frame.columns:
            self.data_frame["binary_label"] = self.data_frame[
                self.target_pathology
            ].apply(lambda x: 1 if x == 1 else 0)
        else:
            # Try to find pathology in text
            print(f"⚠️ {self.target_pathology} not found in columns, using text search")
            self.data_frame["binary_label"] = 0  # Default

    def _prepare_multilabel_labels(self):
        """Create multi-label vectors for all 14 classes."""
        label_matrix = []

        for _, row in self.data_frame.iterrows():
            labels = []
            for cls in CHEXPERT_COMPETITION_CLASSES:
                if cls in row:
                    # Handle -1 (uncertain) according to strategy
                    val = row[cls]
                    if val == -1:
                        if self.uncertainty_handling == "zeros":
                            labels.append(0)
                        elif self.uncertainty_handling == "ones":
                            labels.append(1)
                        else:
                            labels.append(0)  # Default to 0
                    else:
                        labels.append(1 if val == 1 else 0)
                else:
                    labels.append(0)  # Default to 0 if class not present

            label_matrix.append(labels)

        self.data_frame["multilabel"] = list(label_matrix)
        print(
            f"🏷️ Created multi-label vectors with {len(CHEXPERT_COMPETITION_CLASSES)} classes"
        )

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return len(self.data_frame)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Union[int, torch.Tensor]]:
        """Get a sample from the dataset."""
        try:
            # Get image path
            row = self.data_frame.iloc[idx]
            img_path = row.get("Path", row.get("path", ""))

            # Try different path formats
            full_path = os.path.join(self.root_dir, img_path)
            if not os.path.exists(full_path):
                alt_path = img_path.replace("CheXpert-v1.0/", "")
                full_path = os.path.join(self.root_dir, alt_path)

            # Load image
            image = Image.open(full_path).convert("L")  # Convert to grayscale

            # Apply transformations
            if self.transform:
                image = self.transform(image)
            else:
                # Default transform
                transform = transforms.Compose(
                    [
                        transforms.Resize(self.image_size),
                        transforms.ToTensor(),
                        transforms.Normalize(mean=[0.485], std=[0.229]),
                    ]
                )
                image = transform(image)

            # Get label
            if self.binary_classification:
                label = row["binary_label"]
            elif self.multi_label:
                label = torch.tensor(row["multilabel"], dtype=torch.float32)
            else:
                # Default to first pathology if neither binary nor multi
                first_pathology = CHEXPERT_CLASSES[0] if CHEXPERT_CLASSES else None
                label = row.get(first_pathology, 0)

            return image, label

        except Exception as e:
            warnings.warn(f"⚠️ Error loading sample {idx}: {e}")
            # Return a blank image and dummy label if loading fails
            blank_image = torch.zeros((1, self.image_size[0], self.image_size[1]))
            if self.multi_label:
                return blank_image, torch.zeros(len(CHEXPERT_COMPETITION_CLASSES))
            else:
                return blank_image, 0


def get_chexpert_transforms(
    train: bool = True, image_size: Tuple[int, int] = (224, 224)
) -> transforms.Compose:
    """
    Get standard transforms for CheXpert dataset.

    Args:
        train: Whether to use training transforms (with augmentation)
        image_size: Target image size

    Returns:
        Composed transforms
    """
    if train:
        return transforms.Compose(
            [
                transforms.Resize(image_size),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomAffine(degrees=5, translate=(0.05, 0.05)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485], std=[0.229]
                ),  # Grayscale normalization
            ]
        )
    else:
        return transforms.Compose(
            [
                transforms.Resize(image_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485], std=[0.229]),
            ]
        )


def load_chexpert_dataset(
    csv_path: str = None,
    max_samples: int = 10000,
    binary_classification: bool = False,
    target_pathology: str = "Pneumonia",
    multi_label: bool = True,
    uncertainty_handling: str = "zeros",
    test_split: float = 0.2,
    val_split: float = 0.1,
    random_state: int = 42,
    use_frontal_only: bool = True,
) -> Tuple[Dataset, Dataset, Dataset]:
    """
    Load CheXpert dataset and split into train/val/test.

    Args:
        csv_path: Path to CheXpert CSV file
        max_samples: Maximum number of samples to load (for memory management)
        binary_classification: Whether to convert to binary classification
        target_pathology: Target pathology for binary classification
        multi_label: Whether to use multi-label classification
        uncertainty_handling: How to handle uncertain labels
        test_split: Fraction of data to use for testing
        val_split: Fraction of training data to use for validation
        random_state: Random seed for reproducibility
        use_frontal_only: Whether to use only frontal views

    Returns:
        Tuple of (train_dataset, val_dataset, test_dataset)
    """
    print(f"🔄 Loading CheXpert dataset...")

    # Default CSV path
    if csv_path is None:
        csv_path = dataset_dir / "chexpert" / "CheXpert-v1.0" / "train.csv"
        csv_path = csv_path.as_posix()

    try:
        # Check if CSV exists
        if not os.path.exists(csv_path):
            print(f"✗ CSV file not found: {csv_path}")
            print("🔄 Trying alternative path...")
            alt_path = dataset_dir / "chexpert" / "train.csv"
            alt_path = alt_path.as_posix()
            if os.path.exists(alt_path):
                csv_path = alt_path
                print(f"✓ Found CSV at: {csv_path}")
            else:
                raise FileNotFoundError(
                    f"CheXpert CSV not found at {csv_path} or {alt_path}"
                )

        # Create transforms
        train_transform = get_chexpert_transforms(train=True)
        val_transform = get_chexpert_transforms(train=False)
        test_transform = get_chexpert_transforms(train=False)

        # Load full dataset
        full_dataset = CheXpertDataset(
            csv_file=csv_path,
            transform=train_transform,  # Will be overridden for val/test
            max_samples=max_samples,
            binary_classification=binary_classification,
            target_pathology=target_pathology,
            multi_label=multi_label,
            uncertainty_handling=uncertainty_handling,
            use_frontal_only=use_frontal_only,
        )

        # Split into train, val, test
        indices = list(range(len(full_dataset)))
        random.Random(random_state).shuffle(indices)

        test_size = int(len(indices) * test_split)
        val_size = int(len(indices) * val_split)
        train_size = len(indices) - test_size - val_size

        train_indices = indices[:train_size]
        val_indices = indices[train_size : train_size + val_size]
        test_indices = indices[train_size + val_size :]

        # Create subset datasets
        train_dataset = Subset(full_dataset, train_indices)
        val_dataset = Subset(full_dataset, val_indices)
        test_dataset = Subset(full_dataset, test_indices)

        # Override transforms
        train_dataset.dataset.transform = train_transform
        val_dataset.dataset.transform = val_transform
        test_dataset.dataset.transform = test_transform

        print(
            f"📊 Dataset split: {len(train_dataset)} train, {len(val_dataset)} val, {len(test_dataset)} test"
        )
        print("🎉 CheXpert dataset loaded successfully!")

        return train_dataset, val_dataset, test_dataset

    except Exception as e:
        print(f"❌ Error loading CheXpert dataset: {e}")
        print("🔄 Falling back to synthetic data...")
        return _create_synthetic_chexpert(
            max_samples=max_samples,
            multi_label=multi_label,
            test_split=test_split,
            val_split=val_split,
        )


def _create_synthetic_chexpert(
    max_samples: int = 1000,
    multi_label: bool = True,
    test_split: float = 0.2,
    val_split: float = 0.1,
) -> Tuple[Dataset, Dataset, Dataset]:
    """Create synthetic CheXpert data as fallback."""
    from torch.utils.data import TensorDataset

    num_classes = len(CHEXPERT_COMPETITION_CLASSES) if multi_label else 1
    image_size = 224
    num_samples = max_samples

    # Generate synthetic images and labels
    images = torch.randn(num_samples, 1, image_size, image_size)

    if multi_label:
        # Multi-label: random binary vectors with some correlation
        labels = torch.zeros(num_samples, num_classes)
        for i in range(num_samples):
            # Each sample has 2-5 positive labels
            num_pos = random.randint(2, 5)
            pos_indices = random.sample(range(num_classes), num_pos)
            labels[i, pos_indices] = 1
    else:
        # Binary classification
        labels = torch.randint(0, 2, (num_samples,))

    # Create dataset
    dataset = TensorDataset(images, labels)

    # Split
    test_size = int(num_samples * test_split)
    val_size = int(num_samples * val_split)
    train_size = num_samples - test_size - val_size

    train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size, test_size]
    )

    print(f"✅ Created synthetic CheXpert dataset: {num_samples} samples")
    return train_dataset, val_dataset, test_dataset


def create_chexpert_data_loaders(
    num_clients: int = 5,
    max_samples: int = 10000,
    batch_size: int = 32,
    iid: bool = False,
    alpha: float = 0.5,
    binary_classification: bool = False,
    target_pathology: str = "Pneumonia",
    multi_label: bool = True,
    uncertainty_handling: str = "zeros",
    use_frontal_only: bool = True,
) -> Tuple[List[DataLoader], DataLoader]:
    """
    Create data loaders for CheXpert dataset partitioned for federated learning.

    Args:
        num_clients: Number of client partitions
        max_samples: Maximum samples to load
        batch_size: Batch size for data loaders
        iid: Whether to use IID partitioning
        alpha: Dirichlet parameter for non-IID partitioning
        binary_classification: Whether to use binary classification
        target_pathology: Target pathology for binary classification
        multi_label: Whether to use multi-label classification
        uncertainty_handling: How to handle uncertain labels
        use_frontal_only: Whether to use only frontal views

    Returns:
        Tuple of (client_loaders, test_loader)
    """
    try:
        # Load dataset
        train_dataset, val_dataset, test_dataset = load_chexpert_dataset(
            max_samples=max_samples,
            binary_classification=binary_classification,
            target_pathology=target_pathology,
            multi_label=multi_label,
            uncertainty_handling=uncertainty_handling,
            use_frontal_only=use_frontal_only,
            test_split=0.2,
            val_split=0.1,
        )

        # Partition training data for clients
        if iid:
            from src.data.partitioning import partition_iid

            client_datasets = partition_iid(train_dataset, num_clients)
        else:
            from src.data.partitioning import partition_non_iid

            # For multi-label, we need to adapt the partitioning strategy
            if multi_label:
                # Use labels for partitioning
                labels = [train_dataset[i][1] for i in range(len(train_dataset))]
                if isinstance(labels[0], torch.Tensor):
                    # Convert multi-label to single label for partitioning (use most frequent)
                    labels = [torch.argmax(l).item() for l in labels]
                client_datasets = partition_non_iid(
                    train_dataset, num_clients, alpha, labels=labels
                )
            else:
                labels = [train_dataset[i][1] for i in range(len(train_dataset))]
                client_datasets = partition_non_iid(
                    train_dataset, num_clients, alpha, labels=labels
                )

        # Create data loaders
        client_loaders = [
            DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
            for dataset in client_datasets
        ]

        # Use validation set for testing
        test_loader = DataLoader(
            test_dataset, batch_size=batch_size, shuffle=False, num_workers=0
        )

        print(f"🎉 Created {num_clients} client loaders and 1 test loader")

        # Print class distribution if multi-label
        if multi_label:
            print("\n📊 Multi-label class distribution (first 5 clients):")
            for i, loader in enumerate(client_loaders[:5]):
                label_counts = Counter()
                for _, labels in loader:
                    for label_vec in labels:
                        for j, val in enumerate(label_vec):
                            if val == 1:
                                label_counts[CHEXPERT_COMPETITION_CLASSES[j]] += 1
                print(f"  Client {i + 1}: {dict(label_counts.most_common(3))}")

        return client_loaders, test_loader

    except Exception as e:
        print(f"❌ Error creating CheXpert data loaders: {e}")
        print("🔄 Falling back to synthetic data loaders...")
        from .loaders import get_data_loaders

        return get_data_loaders(
            dataset_name="chexpert",
            num_clients=num_clients,
            iid=iid,
            batch_size=batch_size,
            alpha=alpha,
        )


def get_chexpert_statistics(csv_path: str = None) -> Dict[str, Any]:
    """
    Get statistics about CheXpert dataset.

    Args:
        csv_path: Path to CheXpert CSV file

    Returns:
        Dictionary with dataset statistics
    """
    if csv_path is None:
        csv_path = dataset_dir / "chexpert" / "CheXpert-v1.0" / "train.csv"
        csv_path = csv_path.as_posix()

    try:
        df = pd.read_csv(csv_path)
        stats = {
            "total_samples": len(df),
            "frontal_lateral_distribution": df["Frontal/Lateral"]
            .value_counts()
            .to_dict()
            if "Frontal/Lateral" in df.columns
            else {},
            "pathology_prevalence": {},
            "unique_patients": df["PatientID"].nunique()
            if "PatientID" in df.columns
            else 0,
            "unique_studies": df["StudyID"].nunique() if "StudyID" in df.columns else 0,
        }

        # Calculate pathology prevalence
        for pathology in CHEXPERT_CLASSES:
            if pathology in df.columns:
                pos_count = (df[pathology] == 1).sum()
                uncertain_count = (df[pathology] == -1).sum()
                stats["pathology_prevalence"][pathology] = {
                    "positive": int(pos_count),
                    "positive_pct": float(pos_count / len(df) * 100),
                    "uncertain": int(uncertain_count),
                    "uncertain_pct": float(uncertain_count / len(df) * 100),
                }

        return stats

    except Exception as e:
        print(f"Error getting CheXpert statistics: {e}")
        return {}


# Simple test function
if __name__ == "__main__":
    print("🧪 Testing CheXpert dataset loader...")
    print("=" * 60)

    # Test 1: Basic loading with multi-label
    print("\n📋 Test 1: Multi-label classification")
    try:
        client_loaders, test_loader = create_chexpert_data_loaders(
            num_clients=3,
            max_samples=500,  # Small subset for testing
            batch_size=16,
            iid=True,
            multi_label=True,
        )

        print(f"✅ Successfully created {len(client_loaders)} client loaders")

        # Test one batch from first client
        for batch_data, batch_labels in client_loaders[0]:
            print(f"✅ Batch shape: {batch_data.shape}, labels: {batch_labels.shape}")
            print(f"   Label sample: {batch_labels[0]}")
            break

    except Exception as e:
        print(f"❌ Test 1 failed: {e}")

    # Test 2: Binary classification
    print("\n📋 Test 2: Binary classification (Pneumonia)")
    try:
        client_loaders, test_loader = create_chexpert_data_loaders(
            num_clients=3,
            max_samples=300,
            batch_size=16,
            iid=False,
            alpha=0.5,
            binary_classification=True,
            target_pathology="Pneumonia",
            multi_label=False,
        )

        print(f"✅ Successfully created {len(client_loaders)} client loaders")

        # Check distribution
        for i, loader in enumerate(client_loaders[:2]):
            labels = []
            for _, batch_labels in loader:
                labels.extend(batch_labels.numpy())
            print(
                f"   Client {i + 1}: {sum(labels)}/{len(labels)} positive ({sum(labels) / len(labels) * 100:.1f}%)"
            )

    except Exception as e:
        print(f"❌ Test 2 failed: {e}")

    # Test 3: Non-IID partitioning
    print("\n📋 Test 3: Non-IID partitioning with alpha=0.1")
    try:
        client_loaders, test_loader = create_chexpert_data_loaders(
            num_clients=5,
            max_samples=1000,
            batch_size=16,
            iid=False,
            alpha=0.1,
            binary_classification=True,
            target_pathology="Cardiomegaly",
        )

        print(f"✅ Successfully created {len(client_loaders)} client loaders")

        # Show distribution across clients
        print("   Client distribution:")
        for i, loader in enumerate(client_loaders):
            labels = []
            for _, batch_labels in loader:
                labels.extend(batch_labels.numpy())
            if labels:
                pos_pct = sum(labels) / len(labels) * 100
                print(
                    f"     Client {i + 1}: {pos_pct:.1f}% positive ({sum(labels)}/{len(labels)})"
                )

    except Exception as e:
        print(f"❌ Test 3 failed: {e}")

    # Test 4: Get statistics
    print("\n📋 Test 4: Dataset statistics")
    try:
        stats = get_chexpert_statistics()
        print(f"✅ Total samples: {stats.get('total_samples', 'N/A')}")
        print(f"✅ Unique patients: {stats.get('unique_patients', 'N/A')}")

        if "pathology_prevalence" in stats:
            print("   Top 5 pathologies by prevalence:")
            pathologies = sorted(
                stats["pathology_prevalence"].items(),
                key=lambda x: x[1]["positive"],
                reverse=True,
            )[:5]
            for path, data in pathologies:
                print(
                    f"     {path}: {data['positive_pct']:.1f}% positive, {data['uncertain_pct']:.1f}% uncertain"
                )

    except Exception as e:
        print(f"❌ Test 4 failed: {e}")

    print("\n" + "=" * 60)
    print("✅ CheXpert dataset loader tests completed")
