from setuptools import setup, find_packages

setup(
    name="arch-fl",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "opacus>=1.0.0",
        "pytorch-lightning>=2.0.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.11",
)
