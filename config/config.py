from typing import Dict, Any, Optional
import os
import json
import socket
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
class RegistryConfig:
    """Configuration class for registry connection settings"""
    username: str
    password: str
    host: str
    name: str

    def __post_init__(self):
        """Validate registry configuration fields"""
        for field_name, field_value in self.__dict__.items():
            if not field_value:
                raise ValueError(f"Registry {field_name} cannot be empty")

@dataclass(frozen=True)
class ServerConfig:
    """Configuration class for server settings"""
    id: str
    protocol_type: str
    host: Optional[str]
    port: int

    def __post_init__(self):
        """Validate server configuration settings"""
        if self.protocol_type not in ['json', 'wire', 'grpc']:
            raise ValueError("Protocol type must be 'json', 'wire', or 'grpc'")
        if not isinstance(self.port, int) or not (1024 <= self.port <= 65535):
            raise ValueError("Port must be an integer between 1024 and 65535")
        # Note: host can be empty; will use local IP in that case

@dataclass(frozen=True)
class ClientConfig:
    """Configuration class for client settings"""
    protocol_type: str

    def __post_init__(self):
        """Validate client configuration settings"""
        if self.protocol_type not in ['json', 'wire', 'grpc']:
            raise ValueError("Protocol type must be 'json', 'wire', or 'grpc'")

@dataclass(frozen=True)
class ServerAppConfig:
    """Server application configuration class"""
    database: DatabaseConfig
    registry: RegistryConfig
    server: ServerConfig
    env: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate environment setting"""
        if self.env not in ['production', 'debug']:
            raise ValueError("Environment must be 'production' or 'debug'")

@dataclass(frozen=True)
class ClientAppConfig:
    """Client application configuration class"""
    registry: RegistryConfig
    client: ClientConfig
    env: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate environment setting"""
        if self.env not in ['production', 'debug']:
            raise ValueError("Environment must be 'production' or 'debug'")

class Config:
    """Singleton configuration manager class"""

    _instance: Optional['Config'] = None
    _config: Optional[Any] = None
    _is_server: bool = False

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
        
        # Determine whether this is a server or client config
        self._is_server = 'server' in config_data
        
        if self._is_server:
            # Replace empty host with local IP
            if 'server' in config_data and 'host' in config_data['server'] and not config_data['server']['host']:
                config_data['server']['host'] = self._get_local_ip()
            self._config = self._create_server_config(config_data)
        else:
            self._config = self._create_client_config(config_data)

    def _create_server_config(self, data: Dict[str, Any]) -> ServerAppConfig:
        """Create ServerAppConfig from dictionary data"""
        try:
            return ServerAppConfig(
                database=DatabaseConfig(**data['database']),
                registry=RegistryConfig(**data['registry']),
                server=ServerConfig(**data['server']),
                env=data['env']
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid server configuration format: {str(e)}")

    def _create_client_config(self, data: Dict[str, Any]) -> ClientAppConfig:
        """Create ClientAppConfig from dictionary data"""
        try:
            return ClientAppConfig(
                registry=RegistryConfig(**data['registry']),
                client=ClientConfig(**data['client']),
                env=data['env']
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid client configuration format: {str(e)}")

    def _get_local_ip(self) -> str:
        """Get the local IP address of the machine"""
        try:
            # Create a temporary socket to determine the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Connect to a public IP
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            # Fall back to localhost if unable to determine IP
            return '127.0.0.1'

    def _load_config_file(self) -> Dict[str, Any]:
        """Try loading config from various locations"""
        paths = [
            self.config_path,
            os.path.join(os.path.dirname(__file__), '../config-server.json'),
            os.path.join(os.path.dirname(__file__), '../config-client.json'),
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
