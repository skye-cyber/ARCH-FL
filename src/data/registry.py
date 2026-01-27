"""
Dataset Registry for ARCH-FL

Maintains a registry of supported datasets and their characteristics.
This enables the framework to recognize and adapt to different medical imaging datasets.
"""

from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path


class DatasetRegistry:
    """
    Registry of supported medical imaging datasets.

    This class maintains information about known datasets and provides
    methods to register new datasets, retrieve dataset information, and
    manage dataset configurations.
    """

    def __init__(self):
        """Initialize dataset registry."""
        self.datasets = {}
        self._load_builtin_datasets()
        self._registry_file = (Path(__file__).resolve().parent.parent.parent / "config/dataset_registry.json").as_posix()
        self._ensure_registry_file()

    def _load_builtin_datasets(self) -> None:
        """Load information about built-in datasets."""
        self.datasets = {
            'mimic_cxr': {
                'name': 'MIMIC-CXR',
                'description': 'MIMIC-CXR Chest X-ray Dataset',
                'data_type': 'chest_xray',
                'image_format': 'grayscale',
                'default_size': (224, 224),
                'channels': 1,
                'task_types': ['binary_classification', 'multi_label_classification'],
                'path': 'src/datasets/mimic_cxr',
                'supported': True,
                'metadata_file': 'src/datasets/mimic_cxr/datasetinfo.md'
            },
            'chexpert': {
                'name': 'CheXpert',
                'description': 'Stanford CheXpert Chest X-ray Dataset',
                'data_type': 'chest_xray',
                'image_format': 'grayscale',
                'default_size': (320, 320),
                'channels': 1,
                'task_types': ['multi_label_classification'],
                'path': 'src/datasets/chexpert',
                'supported': True,
                'metadata_file': 'src/datasets/chexpert/datasetinfo.md'
            },
            'pneumoniamnist': {
                'name': 'PneumoniaMNIST',
                'description': 'Pneumonia MNIST Dataset',
                'data_type': 'chest_xray',
                'image_format': 'grayscale',
                'default_size': (28, 28),
                'channels': 1,
                'task_types': ['binary_classification'],
                'path': None,  # Loaded via torchvision/medmnist
                'supported': True,
                'metadata_file': None
            }
        }

    def _ensure_registry_file(self) -> None:
        """Ensure registry file exists."""
        registry_path = Path(self._registry_file)
        if not registry_path.exists():
            # Create registry file with built-in datasets
            self._save_registry()

    def register_dataset(self, dataset_name: str, dataset_info: Dict[str, Any]) -> None:
        """
        Register a new dataset in the registry.

        Args:
            dataset_name: Name/key for the dataset
            dataset_info: Dictionary containing dataset information
        """
        dataset_name = dataset_name.lower()
        self.datasets[dataset_name] = dataset_info
        self._save_registry()
        print(f"📊 Registered dataset: {dataset_name}")

    def get_dataset_info(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dictionary with dataset information, or None if not found
        """
        dataset_name = dataset_name.lower()
        return self.datasets.get(dataset_name)

    def list_datasets(self) -> List[str]:
        """List all registered datasets."""
        return list(self.datasets.keys())

    def is_supported(self, dataset_name: str) -> bool:
        """Check if a dataset is supported."""
        dataset_name = dataset_name.lower()
        dataset_info = self.datasets.get(dataset_name)
        return dataset_info is not None and dataset_info.get('supported', False)

    def get_dataset_path(self, dataset_name: str) -> Optional[str]:
        """Get the path to a dataset."""
        dataset_name = dataset_name.lower()
        dataset_info = self.datasets.get(dataset_name)
        return dataset_info.get('path') if dataset_info else None

    def get_dataset_metadata(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a dataset."""
        dataset_name = dataset_name.lower()
        dataset_info = self.datasets.get(dataset_name)

        if not dataset_info:
            return None

        metadata_file = dataset_info.get('metadata_file')
        if metadata_file and os.path.exists(metadata_file):
            try:
                # Try to parse datasetinfo.md if it exists
                if metadata_file.endswith('.md'):
                    return self._parse_datasetinfo_md(metadata_file)
                elif metadata_file.endswith('.json'):
                    return self._load_json_metadata(metadata_file)
            except Exception as e:
                print(f"⚠️ Could not load metadata from {metadata_file}: {e}")

        # Return basic info from registry
        return {
            'dataset_name': dataset_name,
            'properties': {
                'image_size': dataset_info.get('default_size'),
                'channels': dataset_info.get('channels'),
                'data_type': dataset_info.get('data_type'),
                'image_format': dataset_info.get('image_format')
            }
        }

    def _parse_datasetinfo_md(self, metadata_file: str) -> Dict[str, Any]:
        """Parse datasetinfo.md file to extract metadata."""
        import re

        metadata = {
            'dataset_name': os.path.basename(os.path.dirname(metadata_file)),
            'properties': {}
        }

        try:
            with open(metadata_file, 'r') as f:
                content = f.read()

                # Extract image size if available
                size_match = re.search(r'image_size:\s*\((\d+),\s*(\d+)\)', content)
                if size_match:
                    metadata['properties']['image_size'] = (int(size_match.group(1)), int(size_match.group(2)))

                # Extract channels
                channels_match = re.search(r'channels:\s*(\d+)', content)
                if channels_match:
                    metadata['properties']['channels'] = int(channels_match.group(1))

                # Extract data type
                data_type_match = re.search(r'data_type:\s*([^\n]+)', content)
                if data_type_match:
                    metadata['properties']['data_type'] = data_type_match.group(1).strip()

                # Extract image format
                format_match = re.search(r'image_format:\s*([^\n]+)', content)
                if format_match:
                    metadata['properties']['image_format'] = format_match.group(1).strip()

        except Exception as e:
            print(f"⚠️ Error parsing {metadata_file}: {e}")

        return metadata

    def _load_json_metadata(self, metadata_file: str) -> Dict[str, Any]:
        """Load metadata from JSON file."""
        with open(metadata_file, 'r') as f:
            return json.load(f)

    def _save_registry(self) -> None:
        """Save registry to file."""
        registry_data = {
            'datasets': self.datasets,
            'version': '1.0',
            'description': 'ARCH-FL Dataset Registry'
        }

        with open(self._registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2)

    def _load_registry(self) -> None:
        """Load registry from file."""
        if os.path.exists(self._registry_file):
            with open(self._registry_file, 'r') as f:
                registry_data = json.load(f)
                self.datasets.update(registry_data.get('datasets', {}))


def get_dataset_registry() -> DatasetRegistry:
    """Get singleton instance of DatasetRegistry."""
    return DatasetRegistry()


# Test the registry
if __name__ == "__main__":
    print("🧪 Testing DatasetRegistry...")

    registry = DatasetRegistry()

    # List all datasets
    print(f"\n📚 Registered datasets: {registry.list_datasets()}")

    # Get info for each dataset
    for dataset_name in registry.list_datasets():
        info = registry.get_dataset_info(dataset_name)
        print(f"\n📊 {dataset_name}:")
        print(f"   Name: {info['name']}")
        print(f"   Description: {info['description']}")
        print(f"   Data Type: {info['data_type']}")
        print(f"   Image Format: {info['image_format']}")
        print(f"   Supported: {info['supported']}")

        # Get metadata
        metadata = registry.get_dataset_metadata(dataset_name)
        if metadata:
            props = metadata.get('properties', {})
            print(f"   Image Size: {props.get('image_size', 'Unknown')}")
            print(f"   Channels: {props.get('channels', 'Unknown')}")

    print("\n🎉 DatasetRegistry tests completed!")
