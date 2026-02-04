import yaml
from pathlib import Path


class Config:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.data = yaml.safe_load(f)

    def get(self, key, default=None):
        keys = key.split('.')
        value = self.data
        for k in keys:
            value = value.get(k, {})
        return value if value != {} else default


# Usage
config_file = Path(__file__).resolve().parent.parent.parent / 'config/experiment/non_iid_dp.yaml'
config = Config(config_file.as_posix())
epsilon = config.get('privacy.epsilon')  # 2.0
batch_size = config.get('training.batch_size')  # 32
