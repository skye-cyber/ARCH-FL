#!/bin/bash

echo "Setting up ARCH-FL environment..."

# Create conda environment
conda create -n arch-fl python=3.9 -y

# Activate environment
conda activate arch-fl

# Install core dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install project dependencies
pip install -r requirements.txt

# Install project in development mode
pip install -e .

# Create necessary directories
mkdir -p data results/checkpoints results/figures results/logs

echo "Environment setup complete."
echo "Activate with: conda activate arch-fl"
