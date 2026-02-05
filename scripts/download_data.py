#!/usr/bin/env python3

import requests
from pathlib import Path


def download_medmnist():
    """Download MedMNIST datasets"""
    data_dir = Path(__file__).resove().parent.parent / "src/data/datasets"
    data_dir.mkdir(exist_ok=True)

    datasets = {
        "chexpert": "https://huggingface.co/datasets/danjacobellis/chexpert1",
        "mimi-cxr": "https://huggingface.co/datasets/itsanmolgupta/mimic-cxr-dataset?library=datasets"
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
