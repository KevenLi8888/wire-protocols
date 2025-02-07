import os
import json
from typing import Dict, Any

class Config:
    _instance = None
    _config: Dict[str, Any] = {
        'database': {
            'username': 'your_username',
            'password': 'your_password',
            'host': 'localhost',
            'name': 'your_database'
        },
        'communication': {
            'protocol': 'json',
            'host': 'localhost',
            'port': 12345
        }
    }

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.getenv('APP_CONFIG_PATH')
        self.load_config()

    @classmethod
    def get_instance(cls, config_path: str = None):
        if cls._instance is None:
            cls._instance = Config(config_path)
        return cls._instance

    def load_config(self):
        """Load configuration from config file if it exists"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self._config.update(json.load(f))
            except Exception as e:
                print(f"Error loading config file: {e}")
        else:
            # Fallback to default location
            default_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(default_path):
                with open(default_path, 'r') as f:
                    self._config.update(json.load(f))

    def get(self, *keys):
        """Get a configuration value using dot notation"""
        value = self._config
        for key in keys:
            value = value[key]
        return value
