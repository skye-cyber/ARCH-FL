"""
Dataset Analyzer for ARCH-FL

Automatically characterizes medical imaging datasets to enable adaptive architecture generation.
This module analyzes dataset properties such as image dimensions, channels, classes, and distribution
to inform optimal model architecture selection.
"""

import os
import sys
import numpy as np
import pandas as pd
import torch
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
import warnings
from PIL import Image
import io


class DatasetAnalyzer:
    """
    Analyzes medical imaging datasets to extract characteristics for adaptive architecture.

    This class provides the foundation for the adaptive architecture by understanding
    the properties of any given dataset.
    """

    def __init__(self, dataset_name: Optional[str] = None, dataset_path: Optional[str] = None):
        """
        Initialize DatasetAnalyzer.

        Args:
            dataset_name: Name of the dataset (e.g., 'mimic_cxr', 'chexpert')
            dataset_path: Path to dataset files
        """
        self.dataset_name = dataset_name
        self.dataset_path = dataset_path
        self.metadata = {}
        self._supported_datasets = ['mimic_cxr', 'chexpert', 'pneumoniamnist']

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the dataset and return metadata.

        Returns:
            Dictionary containing dataset metadata and characteristics
        """
        if not self.dataset_name and not self.dataset_path:
            raise ValueError("Either dataset_name or dataset_path must be provided")

        self.metadata = {
            'dataset_name': self.dataset_name,
            'dataset_path': self.dataset_path,
            'analysis_timestamp': pd.Timestamp.now().isoformat(),
            'properties': {}
        }

        # Analyze based on what's available
        if self.dataset_name:
            if self.dataset_name.lower() in self._supported_datasets:
                self._analyze_known_dataset()
            else:
                self._analyze_generic_dataset()
        else:
            self._analyze_generic_dataset()

        return self.metadata

    def _analyze_known_dataset(self) -> None:
        """Analyze known supported datasets."""
        dataset_name = self.dataset_name.lower()

        if dataset_name == 'mimic_cxr':
            self._analyze_mimic_cxr()
        elif dataset_name == 'chexpert':
            self._analyze_chexpert()
        elif dataset_name == 'pneumoniamnist':
            self._analyze_pneumoniamnist()

    def _analyze_mimic_cxr(self) -> None:
        """Analyze MIMIC-CXR dataset characteristics."""
        properties = {
            'image_size': (224, 224),
            'channels': 1,  # Grayscale
            'num_classes': 2,  # Binary classification (pneumonia vs normal)
            'image_format': 'grayscale',
            'task_type': 'binary_classification',
            'data_type': 'chest_xray',
            'expected_input_shape': (1, 224, 224),
            'dataset_size': 'large',  # 30K+ images
            'recommended_architecture': 'medium_cnn',
            'normalization': {'mean': [0.485], 'std': [0.229]},
            'class_distribution': 'imbalanced',  # Typical for medical data
            'metadata_available': True
        }

        # Try to get actual statistics if data is available
        try:
            if self.dataset_path:
                actual_stats = self._get_mimic_cxr_statistics()
                properties.update(actual_stats)
        except Exception as e:
            warnings.warn(f"Could not get MIMIC-CXR statistics: {e}")

        self.metadata['properties'] = properties

    def _get_mimic_cxr_statistics(self) -> Dict[str, Any]:
        """Get actual statistics from MIMIC-CXR data if available."""
        stats = {}

        # Check if parquet files exist
        if self.dataset_path:
            data_dir = Path(self.dataset_path) / 'data'
            if data_dir.exists():
                parquet_files = list(data_dir.glob('train-*.parquet'))
                if parquet_files:
                    try:
                        import pyarrow.parquet as pq

                        # Sample a few images to verify characteristics
                        sample_file = parquet_files[0]
                        table = pq.read_table(sample_file, columns=['image', 'findings'])
                        df = table.to_pandas()

                        # Sample up to 10 images for analysis
                        sample_size = min(10, len(df))
                        sample_df = df.sample(n=sample_size, random_state=42)

                        # Analyze sample images
                        image_sizes = []
                        channels = []
                        pneumonia_count = 0

                        for idx, row in sample_df.iterrows():
                            try:
                                img_data = row['image']
                                if isinstance(img_data, bytes):
                                    image = Image.open(io.BytesIO(img_data))
                                    image_sizes.append(image.size)
                                    channels.append(1 if image.mode == 'L' else len(image.getbands()))

                                    # Check for pneumonia in findings
                                    if isinstance(row['findings'], str) and 'pneumonia' in row['findings'].lower():
                                        pneumonia_count += 1
                            except Exception as e:
                                warnings.warn(f"Error analyzing image {idx}: {e}")
                                continue

                        if image_sizes:
                            # Calculate average image size
                            avg_width = np.mean([s[0] for s in image_sizes])
                            avg_height = np.mean([s[1] for s in image_sizes])
                            stats['actual_image_size'] = (int(avg_width), int(avg_height))

                            # Determine if images are consistently grayscale
                            if all(c == 1 for c in channels):
                                stats['actual_channels'] = 1
                                stats['actual_image_format'] = 'grayscale'
                            else:
                                stats['actual_channels'] = max(channels)
                                stats['actual_image_format'] = 'rgb'

                        # Class distribution
                        if len(sample_df) > 0:
                            pneumonia_ratio = pneumonia_count / len(sample_df)
                            stats['pneumonia_ratio'] = pneumonia_ratio
                            stats['class_balance'] = 'balanced' if 0.3 < pneumonia_ratio < 0.7 else 'imbalanced'

                    except Exception as e:
                        warnings.warn(f"Error reading MIMIC-CXR parquet: {e}")

        return stats

    def _analyze_chexpert(self) -> None:
        """Analyze CheXpert dataset characteristics."""
        properties = {
            'image_size': (320, 320),  # CheXpert uses 320x320
            'channels': 1,  # Grayscale
            'num_classes': 14,  # Multi-label classification
            'image_format': 'grayscale',
            'task_type': 'multi_label_classification',
            'data_type': 'chest_xray',
            'expected_input_shape': (1, 320, 320),
            'dataset_size': 'very_large',  # 220K+ images
            'recommended_architecture': 'large_cnn',
            'normalization': {'mean': [0.485], 'std': [0.229]},
            'class_distribution': 'multi_label_imbalanced',
            'metadata_available': True,
            'labels': [
                'No Finding', 'Enlarged Cardiomediastinum', 'Cardiomegaly',
                'Lung Opacity', 'Lung Lesion', 'Edema', 'Consolidation',
                'Pneumonia', 'Atelectasis', 'Pneumothorax', 'Pleural Effusion',
                'Pleural Other', 'Fracture', 'Support Devices'
            ]
        }

        # Try to get actual statistics if data is available
        try:
            if self.dataset_path:
                actual_stats = self._get_chexpert_statistics()
                properties.update(actual_stats)
        except Exception as e:
            warnings.warn(f"Could not get CheXpert statistics: {e}")

        self.metadata['properties'] = properties

    def _get_chexpert_statistics(self) -> Dict[str, Any]:
        """Get actual statistics from CheXpert data if available."""
        stats = {}

        # Check if parquet files exist
        if self.dataset_path:
            data_dir = Path(self.dataset_path) / 'data'
            if data_dir.exists():
                parquet_files = list(data_dir.glob('train-*.parquet'))
                if parquet_files:
                    try:
                        import pyarrow.parquet as pq

                        # Sample a few images to verify characteristics
                        sample_file = parquet_files[0]
                        table = pq.read_table(sample_file, columns=['image', 'Path'])
                        df = table.to_pandas()

                        # Sample up to 5 images for analysis
                        sample_size = min(5, len(df))
                        sample_df = df.sample(n=sample_size, random_state=42)

                        # Analyze sample images
                        image_sizes = []
                        channels = []

                        for idx, row in sample_df.iterrows():
                            try:
                                img_data = row['image']
                                if isinstance(img_data, bytes):
                                    image = Image.open(io.BytesIO(img_data))
                                    image_sizes.append(image.size)
                                    channels.append(1 if image.mode == 'L' else len(image.getbands()))
                            except Exception as e:
                                warnings.warn(f"Error analyzing CheXpert image {idx}: {e}")
                                continue

                        if image_sizes:
                            # Calculate average image size
                            avg_width = np.mean([s[0] for s in image_sizes])
                            avg_height = np.mean([s[1] for s in image_sizes])
                            stats['actual_image_size'] = (int(avg_width), int(avg_height))

                            # Determine if images are consistently grayscale
                            if all(c == 1 for c in channels):
                                stats['actual_channels'] = 1
                                stats['actual_image_format'] = 'grayscale'
                            else:
                                stats['actual_channels'] = max(channels)
                                stats['actual_image_format'] = 'rgb'

                    except Exception as e:
                        warnings.warn(f"Error reading CheXpert parquet: {e}")

        return stats

    def _analyze_pneumoniamnist(self) -> None:
        """Analyze PneumoniaMNIST dataset characteristics."""
        properties = {
            'image_size': (28, 28),
            'channels': 1,  # Grayscale
            'num_classes': 2,  # Binary classification
            'image_format': 'grayscale',
            'task_type': 'binary_classification',
            'data_type': 'chest_xray',
            'expected_input_shape': (1, 28, 28),
            'dataset_size': 'small',  # ~5K images
            'recommended_architecture': 'simple_cnn',
            'normalization': {'mean': [0.5], 'std': [0.5]},
            'class_distribution': 'balanced',
            'metadata_available': True
        }

        self.metadata['properties'] = properties

    def _analyze_generic_dataset(self, mean: float = 0.5, std: float = 0.5) -> None:
        """
        Analyze generic/unknown datasets.
        mean: normalization mean\n
        std: normalization std
        """
        properties = {
            'image_size': None,
            'channels': None,
            'num_classes': None,
            'image_format': 'unknown',
            'task_type': 'unknown',
            'data_type': 'unknown',
            'expected_input_shape': None,
            'dataset_size': 'unknown',
            'recommended_architecture': 'auto',
            'normalization': {'mean': [mean], 'std': [std]},  # Default normalization
            'class_distribution': 'unknown',
            'metadata_available': False
        }

        # Try to infer properties from dataset path
        if self.dataset_path:
            try:
                inferred_properties = self._infer_dataset_properties()
                properties.update(inferred_properties)
            except Exception as e:
                warnings.warn(f"Could not infer dataset properties: {e}")

        self.metadata['properties'] = properties

    def _infer_dataset_properties(self) -> Dict[str, Any]:
        """Infer dataset properties from files."""
        inferred = {}

        # Check if it's a directory with image files
        dataset_path = Path(self.dataset_path)
        if dataset_path.is_dir():
            # Count image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.dcm', '.nii', '.nii.gz']
            image_files = []

            for ext in image_extensions:
                image_files.extend(dataset_path.rglob(f'*{ext}'))

            if image_files:
                inferred['dataset_size'] = self._categorize_dataset_size(len(image_files))

                # Sample a few images to get characteristics
                sample_size = min(10, len(image_files))
                sample_files = np.random.choice(image_files, sample_size, replace=False)

                image_sizes = []
                channels = []

                for file_path in sample_files:
                    try:
                        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                            image = Image.open(file_path)
                            image_sizes.append(image.size)
                            channels.append(1 if image.mode == 'L' else len(image.getbands()))
                        elif file_path.suffix.lower() in ['.dcm']:
                            # DICOM file - would need pydicom to read
                            inferred['data_type'] = 'dicom'
                            inferred['image_format'] = 'dicom'
                        elif file_path.suffix.lower() in ['.nii', '.nii.gz']:
                            # NIfTI file - would need nibabel to read
                            inferred['data_type'] = 'nifti'
                            inferred['image_format'] = '3d_medical'
                    except Exception as e:
                        warnings.warn(f"Error reading {file_path}: {e}")
                        continue

                if image_sizes:
                    # Calculate average image size
                    avg_width = np.mean([s[0] for s in image_sizes])
                    avg_height = np.mean([s[1] for s in image_sizes])
                    inferred['image_size'] = (int(avg_width), int(avg_height))

                    # Determine channels
                    if all(c == 1 for c in channels):
                        inferred['channels'] = 1
                        inferred['image_format'] = 'grayscale'
                    else:
                        inferred['channels'] = max(channels)
                        inferred['image_format'] = 'rgb'

                    # Set expected input shape
                    inferred['expected_input_shape'] = (inferred['channels'], avg_height, avg_width)

                    # Recommend architecture based on image size
                    image_area = avg_width * avg_height
                    if image_area < 10000:  # < 100x100
                        inferred['recommended_architecture'] = 'simple_cnn'
                    elif image_area < 100000:  # < 300x300
                        inferred['recommended_architecture'] = 'medium_cnn'
                    else:
                        inferred['recommended_architecture'] = 'large_cnn'

        return inferred

    def _categorize_dataset_size(self, num_samples: int) -> str:
        """Categorize dataset size based on number of samples."""
        if num_samples < 1_000:
            return 'tiny'
        elif num_samples < 10_000:
            return 'small'
        elif num_samples < 100_000:
            return 'medium'
        elif num_samples < 1_000_000:
            return 'large'
        else:
            return 'very_large'

    def get_recommended_architecture_config(self) -> Dict[str, Any]:
        """
        Get recommended architecture configuration based on dataset analysis.

        Returns:
            Dictionary with recommended model configuration
        """
        if not self.metadata or not self.metadata.get('properties'):
            raise ValueError("Dataset not analyzed yet. Call analyze() first.")

        properties = self.metadata['properties']
        recommended_arch = properties.get('recommended_architecture', 'simple_cnn')

        # Generate configuration based on recommendation
        config = self._generate_architecture_config(recommended_arch, properties)
        return config

    def _generate_architecture_config(self, arch_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Generate model configuration based on architecture type and dataset properties."""
        base_config = {
            'name': 'ConfigurableCNN',
            'num_classes': properties.get('num_classes', 2),
            'input_channels': properties.get('channels', 1),
            'task_type': properties.get('task_type', 'binary_classification'),
            'architecture': {
                'input_channels': properties.get('channels', 1),
                'activation': 'ReLU',
                'pooling': 'MaxPool2d',
                'pool_kernel': 2,
                'dropout': 0.5
            }
        }

        # Set architecture based on type
        if arch_type == 'simple_cnn':
            base_config['architecture']['conv_layers'] = [
                {'out_channels': 32, 'kernel_size': 3, 'stride': 1, 'padding': 1},
                {'out_channels': 64, 'kernel_size': 3, 'stride': 1, 'padding': 1}
            ]
            base_config['architecture']['fc_layers'] = [
                {'out_features': 128},
                {'out_features': base_config['num_classes']}
            ]

        elif arch_type == 'medium_cnn':
            base_config['architecture']['conv_layers'] = [
                {'out_channels': 32, 'kernel_size': 3, 'stride': 2, 'padding': 1},
                {'out_channels': 64, 'kernel_size': 3, 'stride': 2, 'padding': 1},
                {'out_channels': 128, 'kernel_size': 3, 'stride': 2, 'padding': 1}
            ]
            base_config['architecture']['fc_layers'] = [
                {'out_features': 256},
                {'out_features': base_config['num_classes']}
            ]

        elif arch_type == 'large_cnn':
            base_config['architecture']['conv_layers'] = [
                {'out_channels': 32, 'kernel_size': 3, 'stride': 2, 'padding': 1},
                {'out_channels': 64, 'kernel_size': 3, 'stride': 2, 'padding': 1},
                {'out_channels': 128, 'kernel_size': 3, 'stride': 2, 'padding': 1},
                {'out_channels': 256, 'kernel_size': 3, 'stride': 2, 'padding': 1}
            ]
            base_config['architecture']['fc_layers'] = [
                {'out_features': 512},
                {'out_features': base_config['num_classes']}
            ]

        else:  # auto or unknown
            # Base on image size if available
            image_size = properties.get('image_size')
            if image_size:
                image_area = image_size[0] * image_size[1]
                if image_area < 10000:
                    return self._generate_architecture_config('simple_cnn', properties)
                elif image_area < 100000:
                    return self._generate_architecture_config('medium_cnn', properties)
                else:
                    return self._generate_architecture_config('large_cnn', properties)
            else:
                # Default to medium_cnn
                return self._generate_architecture_config('medium_cnn', properties)

        return base_config

    def save_metadata(self, output_path: str) -> None:
        """Save dataset metadata to JSON file."""
        import json

        if not self.metadata:
            raise ValueError("No metadata to save. Call analyze() first.")

        with open(output_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        print(f"💾 Dataset metadata saved to: {output_path}")

    def load_metadata(self, input_path: str) -> None:
        """Load dataset metadata from JSON file."""
        import json

        with open(input_path, 'r') as f:
            self.metadata = json.load(f)

        print(f"📊 Dataset metadata loaded from: {input_path}")


def get_dataset_analyzer(dataset_name: Optional[str] = None, dataset_path: Optional[str] = None) -> DatasetAnalyzer:
    """Get DatasetAnalyzer instance."""
    return DatasetAnalyzer(dataset_name, dataset_path)


# Test the analyzer
if __name__ == "__main__":
    print("🧪 Testing DatasetAnalyzer...")

    # Test with known datasets
    for dataset_name in ['mimic_cxr', 'chexpert', 'pneumoniamnist']:
        print(f"\n🔍 Analyzing {dataset_name}...")
        analyzer = DatasetAnalyzer(dataset_name=dataset_name)
        metadata = analyzer.analyze()

        print(f"✅ Dataset: {metadata['dataset_name']}")
        print(f"   Image Size: {metadata['properties'].get('image_size', 'Unknown')}")
        print(f"   Channels: {metadata['properties'].get('channels', 'Unknown')}")
        print(f"   Classes: {metadata['properties'].get('num_classes', 'Unknown')}")
        print(f"   Recommended Architecture: {metadata['properties'].get('recommended_architecture', 'Unknown')}")

        # Get recommended config
        config = analyzer.get_recommended_architecture_config()
        print(f"   Recommended Config Type: {config['name']}")

        # Save metadata
        analyzer.save_metadata(f"docs/analysis/{dataset_name}_metadata.json")

    print("\n🎉 DatasetAnalyzer tests completed!")
