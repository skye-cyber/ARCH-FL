import yaml
import os
from typing import Any, Dict


class Config:
    def __init__(self, config_path: str):
        self.data = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Handle inheritance
        if 'extends' in config:
            base_path = os.path.join(os.path.dirname(config_path), config['extends'])
            base_config = self._load_config(base_path)
            base_config.update(config)
            return base_config
        return config

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
