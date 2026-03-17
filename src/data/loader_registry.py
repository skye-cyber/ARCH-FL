"""
Data Loader Registry for ARCH-FL

Class-based registry system for managing and creating data loaders.
This system allows registration of custom data loaders and integrates with the dataset registry.
"""

import sys
import os
from typing import Dict, Any, Optional, List, Callable, Tuple
from torch.utils.data import DataLoader
import numpy as np

# Handle both direct execution and module import
if __name__ == "__main__":
    # When running directly, add src to path and use absolute imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from datasets import MedicalDataset, get_transform
    from partitioning import partition_iid, partition_non_iid
    from registry import DatasetRegistry
else:
    # When imported as module, use relative imports
    from .datasets import MedicalDataset, get_transform
    from .partitioning import partition_iid, partition_non_iid
    from .registry import DatasetRegistry


class DataLoaderRegistry:
    """
    Registry for managing data loader implementations.

    This class maintains a collection of data loader factories and provides
    methods to register new loaders, retrieve loaders, and create data loaders
    for federated learning scenarios.
    """

    def __init__(self):
        """Initialize data loader registry."""
        self.loaders = {}
        self.dataset_registry = DatasetRegistry()
        self._register_builtin_loaders()

    def _register_builtin_loaders(self) -> None:
        """Register built-in data loader implementations."""
        # Register synthetic data loader (current implementation)
        self.register_loader(
            "synthetic",
            self._create_synthetic_loader,
            description="Synthetic data loader for testing and development",
        )

        # Register MedMNIST loader
        # self.register_loader(
        #     "medmnist",
        #     self._create_medmnist_loader,
        #     description="MedMNIST data loader for medical imaging datasets",
        # )

        # Register CheXpert loader
        self.register_loader(
            "chexpert",
            self._create_CheXpert_loader,
            description="CheXpert chest X-ray dataset loader",
            supported_datasets=["chexpert"],
        )

        # Register MIMIC-CXR loader
        self.register_loader(
            "mimic_cxr",
            self._create_mimic_cxr_loader,
            description="MIMIC-CXR chest X-ray dataset loader",
            supported_datasets=["mimic_cxr"],
        )

    def register_loader(
        self,
        loader_name: str,
        loader_factory: Callable,
        description: str = "",
        supported_datasets: Optional[List[str]] = None,
    ) -> None:
        """
        Register a new data loader in the registry.

        Args:
            loader_name: Name/key for the loader
            loader_factory: Function that creates the data loader
            description: Description of the loader
            supported_datasets: List of datasets this loader supports
        """
        loader_name = loader_name.lower()
        self.loaders[loader_name] = {
            "factory": loader_factory,
            "description": description,
            "supported_datasets": supported_datasets or [],
        }
        print(f"Registered data loader: {loader_name}")

    def get_loader_info(self, loader_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered data loader.

        Args:
            loader_name: Name of the data loader

        Returns:
            Dictionary with loader information, or None if not found
        """
        loader_name = loader_name.lower()
        return self.loaders.get(loader_name)

    def list_loaders(self) -> List[str]:
        """List all registered data loaders."""
        return list(self.loaders.keys())

    def is_supported(self, loader_name: str) -> bool:
        """Check if a data loader is supported."""
        loader_name = loader_name.lower()
        return loader_name in self.loaders

    def get_supported_loaders_for_dataset(self, dataset_name: str) -> List[str]:
        """
        Get data loaders that support a specific dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            List of loader names that support the dataset
        """
        dataset_name = dataset_name.lower()
        supported_loaders = []

        for loader_name, loader_info in self.loaders.items():
            # Check if this loader supports the dataset
            if (
                not loader_info["supported_datasets"]
                or dataset_name in loader_info["supported_datasets"]
            ):
                supported_loaders.append(loader_name)

        return supported_loaders

    def create_data_loaders(
        self,
        dataset_name: str,
        num_clients: int,
        iid: bool = True,
        batch_size: int = 32,
        alpha: float = 0.5,
        loader_type: Optional[str] = None,
    ) -> Tuple[List[DataLoader], DataLoader]:
        """
        Create data loaders for federated learning.

        Args:
            dataset_name: Name of the dataset
            num_clients: Number of client data loaders to create
            iid: Whether to use IID partitioning
            batch_size: Batch size for data loaders
            alpha: Alpha parameter for non-IID partitioning
            loader_type: Specific loader type to use (None for auto-selection)

        Returns:
            Tuple of (client_loaders, test_loader)
        """
        dataset_name = dataset_name.lower()

        # Check if dataset is registered
        if not self.dataset_registry.is_supported(dataset_name):
            raise ValueError(f"Dataset '{dataset_name}' is not registered or supported")

        # Auto-select loader if not specified
        if loader_type is None:
            loader_type = self._auto_select_loader(dataset_name)

        # Get the loader factory
        loader_info = self.get_loader_info(loader_type)
        if not loader_info:
            raise ValueError(f"Data loader '{loader_type}' not found")

        # Create data loaders using the factory
        client_loaders, test_loader = loader_info["factory"](
            dataset_name, num_clients, iid, batch_size, alpha
        )

        return client_loaders, test_loader

    def _auto_select_loader(self, dataset_name: str) -> str:
        """
        Automatically select the best loader for a dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Name of the selected loader
        """
        dataset_name = dataset_name.lower()

        # Use specific loaders for known datasets
        if dataset_name == "chexpert":
            return "chexpert"
        elif dataset_name == "mimic_cxr":
            return "mimic_cxr"

        # For other datasets, use synthetic loader as default
        return "synthetic"

    def _create_synthetic_loader(
        self,
        dataset_name: str,
        num_clients: int,
        iid: bool = True,
        batch_size: int = 32,
        alpha: float = 0.5,
    ) -> Tuple[List[DataLoader], DataLoader]:
        """
        Create synthetic data loader (current implementation).

        This is the existing implementation that will be replaced with real datasets.
        """
        # Get dataset info to determine appropriate synthetic data characteristics
        dataset_info = self.dataset_registry.get_dataset_info(dataset_name)

        if dataset_info:
            # Use dataset characteristics for synthetic data
            image_size = dataset_info.get("default_size", (28, 28))
            channels = dataset_info.get("channels", 1)
            num_classes = 2  # Default for binary classification

            # For specific datasets, use appropriate class counts
            if dataset_name == "chexpert":
                num_classes = 14  # CheXpert has 14 classes
        else:
            # Fallback defaults
            image_size = (28, 28)
            channels = 1
            num_classes = 2

        # Create synthetic data
        num_samples = 1000
        data = np.random.randn(num_samples, channels, *image_size).astype(np.float32)
        targets = np.random.randint(0, num_classes, num_samples)

        dataset = MedicalDataset(data, targets, transform=get_transform())

        # Partition data
        if iid:
            client_datasets = partition_iid(dataset, num_clients)
        else:
            client_datasets = partition_non_iid(dataset, num_clients, alpha)

        # Create client loaders
        client_loaders = []
        for client_dataset in client_datasets:
            loader = DataLoader(client_dataset, batch_size=batch_size, shuffle=True)
            client_loaders.append(loader)

        # Create test loader (20% of data)
        from torch.utils.data import random_split

        train_size = int(0.8 * len(dataset))
        test_size = len(dataset) - train_size
        train_dataset, test_dataset = random_split(dataset, [train_size, test_size])
        test_loader = DataLoader(test_dataset, batch_size=batch_size)

        return client_loaders, test_loader

    def _create_medmnist_loader(
        self,
        dataset_name: str,
        num_clients: int,
        iid: bool = True,
        batch_size: int = 32,
        alpha: float = 0.5,
    ) -> Tuple[List[DataLoader], DataLoader]:
        """
        Create MedMNIST data loader.

        This will be implemented to load real MedMNIST datasets.
        """
        try:
            # This is a placeholder for the actual MedMNIST implementation
            # For now, fall back to synthetic data
            print(
                f"MedMNIST loader for {dataset_name} not yet implemented, using synthetic data"
            )
            return self._create_synthetic_loader(
                dataset_name, num_clients, iid, batch_size, alpha
            )
        except Exception as e:
            print(f"Error creating MedMNIST loader: {e}")
            return self._create_synthetic_loader(
                dataset_name, num_clients, iid, batch_size, alpha
            )

    def _create_chexpert_loader(
        self,
        dataset_name: str,
        num_clients: int,
        iid: bool = True,
        batch_size: int = 32,
        alpha: float = 0.5,
    ) -> Tuple[List[DataLoader], DataLoader]:
        """
        Create CheXpert data loader.

        This loads the real CheXpert dataset for federated learning.
        """
        try:
            # Get dataset path from registry
            dataset_info = self.dataset_registry.get_dataset_info(dataset_name)
            if not dataset_info:
                raise ValueError(f"Dataset '{dataset_name}' not found in registry")

            data_dir = dataset_info.get("path")
            if not data_dir or not os.path.exists(data_dir):
                raise ValueError(f"Dataset path '{data_dir}' does not exist")

            # Import custom loader from dashboard backend
            from src.data.mimi import create_chexpert_loaders

            # Create loaders
            client_loaders, test_loader = create_chexpert_loaders(
                data_dir=data_dir,
                num_clients=num_clients,
                iid=iid,
                batch_size=batch_size,
                alpha=alpha,
            )

            return client_loaders, test_loader

        except ImportError as e:
            print(f"Custom CheXpert loader not available: {e}")
            print("Falling back to synthetic data")
            return self._create_synthetic_loader(
                dataset_name, num_clients, iid, batch_size, alpha
            )
        except Exception as e:
            print(f"Error creating CheXpert loader: {e}")
            return self._create_synthetic_loader(
                dataset_name, num_clients, iid, batch_size, alpha
            )

    def _create_mimic_cxr_loader(
        self,
        dataset_name: str,
        num_clients: int,
        iid: bool = True,
        batch_size: int = 32,
        alpha: float = 0.5,
    ) -> Tuple[List[DataLoader], DataLoader]:
        """
        Create MIMIC-CXR data loader.

        This loads the real MIMIC-CXR dataset for federated learning.
        """
        try:
            # Get dataset path from registry
            dataset_info = self.dataset_registry.get_dataset_info(dataset_name)
            if not dataset_info:
                raise ValueError(f"Dataset '{dataset_name}' not found in registry")

            data_dir = dataset_info.get("path")
            if not data_dir or not os.path.exists(data_dir):
                raise ValueError(f"Dataset path '{data_dir}' does not exist")

            # Import custom loader from dashboard backend
            from src.data.mimic_cxr_loader import create_mimic_cxr_data_loaders

            # Create loaders
            client_loaders, test_loader = create_mimic_cxr_data_loaders(
                # data_dir=data_dir,
                num_clients=num_clients,
                iid=iid,
                batch_size=batch_size,
                alpha=alpha,
            )

            return client_loaders, test_loader

        except ImportError as e:
            print(f"Custom MIMIC-CXR loader not available: {e}")
            print("Falling back to synthetic data")
            return self._create_synthetic_loader(
                dataset_name, num_clients, iid, batch_size, alpha
            )
        except Exception as e:
            print(f"Error creating MIMIC-CXR loader: {e}")
            return self._create_synthetic_loader(
                dataset_name, num_clients, iid, batch_size, alpha
            )

    def _create_CheXpert_loader(
        self,
        dataset_name: str,
        num_clients: int,
        iid: bool = True,
        batch_size: int = 32,
        alpha: float = 0.5,
    ) -> Tuple[List[DataLoader], DataLoader]:
        """
        Create CheXpert data loader.

        This loads the real CheXpert dataset for federated learning.
        """
        try:
            # Get dataset path from registry
            dataset_info = self.dataset_registry.get_dataset_info(dataset_name)
            if not dataset_info:
                raise ValueError(f"Dataset '{dataset_name}' not found in registry")

            data_dir = dataset_info.get("path")
            if not data_dir or not os.path.exists(data_dir):
                raise ValueError(f"Dataset path '{data_dir}' does not exist")

            # Import custom loader from dashboard backend
            from src.data.chexpert_loader import create_chexpert_data_loaders

            # Create loaders
            client_loaders, test_loader = create_chexpert_data_loaders(
                num_clients=num_clients,
                iid=iid,
                batch_size=batch_size,
                alpha=alpha,
            )

            return client_loaders, test_loader

        except ImportError as e:
            print(f"Custom CheXpert loader not available: {e}")
            print("Falling back to synthetic data")
            return self._create_synthetic_loader(
                dataset_name, num_clients, iid, batch_size, alpha
            )
        except Exception as e:
            print(f"Error creating CheXpert loader: {e}")
            return self._create_synthetic_loader(
                dataset_name, num_clients, iid, batch_size, alpha
            )


def get_data_loader_registry() -> DataLoaderRegistry:
    """Get singleton instance of DataLoaderRegistry."""
    return DataLoaderRegistry()


# Backward compatibility function
# This maintains the original get_data_loaders function signature
def get_data_loaders(
    dataset_name: str,
    num_clients: int,
    iid: bool = True,
    batch_size: int = 32,
    alpha: float = 0.5,
) -> tuple:
    """
    Create data loaders for federated learning (backward compatibility).

    This function maintains the original API but uses the new registry system.
    """
    registry = get_data_loader_registry()
    return registry.create_data_loaders(
        dataset_name, num_clients, iid, batch_size, alpha
    )


# Test the registry
if __name__ == "__main__":
    print("🧪 Testing DataLoaderRegistry...")

    registry = DataLoaderRegistry()

    # List all loaders
    print(f"\n📋 Registered data loaders: {registry.list_loaders()}")

    # Get info for each loader
    for loader_name in registry.list_loaders():
        info = registry.get_loader_info(loader_name)
        print(f"\n📦 {loader_name}:")
        print(f"   Description: {info['description']}")
        print(f"   Supported datasets: {info['supported_datasets']}")

    # Test creating data loaders
    print("\n🔧 Testing data loader creation...")

    try:
        client_loaders, test_loader = registry.create_data_loaders(
            "PneumoniaMNIST", num_clients=3, iid=True, batch_size=32
        )
        print(f"✅ Created {len(client_loaders)} client loaders and 1 test loader")
        print(f"   Test loader batch size: {test_loader.batch_size}")

        # Test with non-IID
        client_loaders_non_iid, test_loader_non_iid = registry.create_data_loaders(
            "PneumoniaMNIST", num_clients=3, iid=False, batch_size=32, alpha=0.5
        )
        print("✅ Created non-IID loaders with alpha=0.5")

    except Exception as e:
        print(f"❌ Error creating data loaders: {e}")

    # Test backward compatibility
    print("\n🔄 Testing backward compatibility...")
    try:
        client_loaders_old, test_loader_old = get_data_loaders(
            "PneumoniaMNIST", 3, True, 32, 0.5
        )
        print("✅ Backward compatibility function works")
    except Exception as e:
        print(f"❌ Backward compatibility failed: {e}")

    print("\n🎉 DataLoaderRegistry tests completed!")
