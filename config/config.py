from typing import Dict, Any, Optional
import os
import json
from dataclasses import dataclass, field, FrozenInstanceError
from datetime import datetime

@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration class for database connection settings"""
    username: str
    password: str
    host: str
    name: str

    def __post_init__(self):
        """Validate that all database configuration fields are non-empty"""
        for field_name, field_value in self.__dict__.items():
            if not field_value:
                raise ValueError(f"Database {field_name} cannot be empty")

@dataclass(frozen=True)
class CommunicationConfig:
    """Configuration class for communication protocol settings"""
    protocol_type: str
    host: str
    port: int

    def __post_init__(self):
        """Validate communication protocol settings including protocol type, port range, and host"""
        if self.protocol_type not in ['json', 'wire', 'grpc']:
            raise ValueError("Protocol type must be 'json', 'wire', or 'grpc'")
        if not isinstance(self.port, int) or not (1024 <= self.port <= 65535):
            raise ValueError("Port must be an integer between 1024 and 65535")
        if not self.host:
            raise ValueError("Host cannot be empty")

@dataclass(frozen=True)
class AppConfig:
    """Main application configuration class combining database and communication settings"""
    database: Optional[DatabaseConfig]
    communication: CommunicationConfig
    env: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate environment setting"""
        if self.env not in ['production', 'debug']:
            raise ValueError("Environment must be 'production' or 'debug'")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create AppConfig instance from dictionary data
        
        Args:
            data: Dictionary containing configuration data
            
        Returns:
            AppConfig instance
            
        Raises:
            ValueError: If configuration format is invalid
        """
        try:
            return cls(
                database=DatabaseConfig(**data['database']) if 'database' in data else None,
                communication=CommunicationConfig(**data['communication']),
                env=data['env']
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid configuration format: {str(e)}")

class Config:
    """Singleton configuration manager class"""

    _instance: Optional['Config'] = None
    _config: Optional[AppConfig] = None

    def __init__(self, config_path: str = None):
        """Initialize Config instance with optional config file path
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or os.getenv('APP_CONFIG_PATH')
        self.load_config()

    @classmethod
    def get_instance(cls, config_path: str = None) -> 'Config':
        """Get or create singleton Config instance
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            Config singleton instance
        """
        if cls._instance is None:
            cls._instance = Config(config_path)
        return cls._instance

    def load_config(self) -> None:
        """Load configuration from config file with fallback mechanisms"""
        config_data = self._load_config_file()
        if not config_data:
            raise ValueError("No valid configuration found")
        self._config = AppConfig.from_dict(config_data)

    def _load_config_file(self) -> Dict[str, Any]:
        """Try loading config from various locations"""
        paths = [
            self.config_path,
            os.path.join(os.path.dirname(__file__), 'config.json'),
            os.path.join(os.path.dirname(__file__), '../config.json')
        ]

        for path in paths:
            if path and os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error parsing config file {path}: {e}")
                except Exception as e:
                    print(f"Error reading config file {path}: {e}")
        return {}

    def get(self, *keys: str) -> Any:
        """Get a configuration value using dot notation"""
        if not self._config:
            raise ValueError("Configuration not loaded")

        value = self._config
        for key in keys:
            try:
                value = getattr(value, key)
            except AttributeError:
                return None
        return value
