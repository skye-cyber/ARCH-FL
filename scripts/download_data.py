#!/usr/bin/env python3

import os
import requests
import tarfile
from pathlib import Path


def download_medmnist():
    """Download MedMNIST datasets"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    datasets = {
        "pneumoniamnist": "https://zenodo.org/record/5208230/files/pneumoniamnist.npz?download=1",
        "chestmnist": "https://zenodo.org/record/5208230/files/chestmnist.npz?download=1"
    }

    for name, url in datasets.items():
        print(f"Downloading {name}...")
        response = requests.get(url, stream=True)
        file_path = data_dir / f"{name}.npz"

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded {file_path}")


if __name__ == "__main__":
    download_medmnist()
