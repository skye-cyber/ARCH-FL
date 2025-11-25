#!/usr/bin/env python3

import sys
import importlib
import torch
import yaml
from pathlib import Path


def check_imports():
    """Check if all required packages are installed"""
    required = [
        'torch', 'torchvision', 'opacus', 'numpy', 'pandas',
        'sklearn', 'matplotlib', 'streamlit', 'yaml'
    ]

    missing = []
    for package in required:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Missing packages: {missing}")
        return False
    print("✓ All packages installed")
    return True


def check_paths():
    """Check if necessary directories exist"""
    required_dirs = ['data', 'config', 'src', 'experiments']
    missing_dirs = []

    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"Missing directories: {missing_dirs}")
        return False
    print("✓ All directories present")
    return True


def check_configs():
    """Validate configuration files"""
    config_files = [
        'config/base.yaml',
        'config/experiment/iid_baseline.yaml',
        'config/model/simple_cnn.yaml'
    ]

    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                yaml.safe_load(f)
        except Exception as e:
            print(f"Error in {config_file}: {e}")
            return False

    print("✓ All config files valid")
    return True


def check_gpu():
    """Check GPU availability"""
    if torch.cuda.is_available():
        print(f"✓ GPU available: {torch.cuda.get_device_name()}")
        return True
    else:
        print("✓ Using CPU")
        return True


if __name__ == "__main__":
    print("Validating ARCH-FL setup...")

    checks = [
        check_imports(),
        check_paths(),
        check_configs(),
        check_gpu()
    ]

    if all(checks):
        print("\n✓ Setup validation passed!")
        sys.exit(0)
    else:
        print("\n✗ Setup validation failed!")
        sys.exit(1)
