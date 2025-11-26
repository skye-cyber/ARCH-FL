#!/usr/bin/env python3

import subprocess
from pathlib import Path


def generate_diagrams():
    """Generate PNG diagrams from DOT files"""
    diagrams_dir = Path(__file__).parent

    for dot_file in diagrams_dir.glob("*.dot"):
        png_file = dot_file.with_suffix('.png')
        try:
            subprocess.run([
                'dot', '-Tpng', str(dot_file),
                '-o', str(png_file),
                '-Gdpi=600'
            ], check=True)
            print(f"Generated: {png_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating {png_file}: {e}")
        except FileNotFoundError:
            print("Graphviz 'dot' command not found. Install with: sudo apt-get install graphviz")


"""
dot -Tpng architecture.dot -o architecture.png -Gdpi=300
dot -Tpng data_flow.dot -o data_flow.png -Gdpi=300
dot -Tpng privacy_flow.dot -o privacy_flow.png -Gdpi=300
"""


if __name__ == "__main__":
    generate_diagrams()
