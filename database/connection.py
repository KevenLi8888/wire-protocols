# Requires: python -m pip install "pymongo[srv]"

from pymongo import MongoClient
from urllib.parse import quote_plus
from typing import Optional, Dict
from pymongo.database import Database
from config.config import Config

class DatabaseManager:
    """Class to manage MongoDB database connections
    
    This class manages multiple database connections. It handles
    connection establishment, credential management, and database operations.
    """
    _instances: Dict[str, 'DatabaseManager'] = {}  # Dictionary to store instances by type

    def __init__(self, db_type: str):
        """Initialize database manager with configuration settings
        
        Args:
            db_type: Type of database to connect to ('database' or 'registry')
        
        Retrieves database configuration from the Config singleton and sets up
        connection parameters with proper URL encoding for special characters
        in credentials.
        """
        config = Config.get_instance()
        
        # Use the appropriate configuration based on db_type
        if db_type not in ['database', 'registry']:
            raise ValueError(f"Invalid database type: {db_type}. Must be 'database' or 'registry'")
            
        # Store the database type
        self.db_type = db_type
        
        # Get configuration for the specified database type
        db_config = config.get(db_type)
        
        self.username = quote_plus(db_config.username)
        self.password = quote_plus(db_config.password)
        self.host = db_config.host
        self.database_name = db_config.name
        self._db: Optional[Database] = None

    @classmethod
    def get_instance(cls, db_type: str = 'database') -> 'DatabaseManager':
        """Get or create instance of DatabaseManager for the specified database type
        
        Args:
            db_type: Type of database to connect to ('database' or 'registry')
            
        Returns:
            DatabaseManager: The instance for the specified database type
        """
        if db_type not in cls._instances:
            cls._instances[db_type] = DatabaseManager(db_type)
        return cls._instances[db_type]

    @classmethod
    def reset_instances(cls):
        """Reset all database manager instances
        
        This method is primarily used for testing purposes.
        """
        cls._instances = {}

    @property
    def db(self) -> Optional[Database]:
        """Get the database connection, creating it if it doesn't exist
        
        Lazy initialization of the database connection - only connects when first needed.
        Subsequent calls return the existing connection.
        
        Returns:
            Optional[Database]: MongoDB database object or None if connection fails
        """
        if self._db is None:
            self._db = self._connect()
        return self._db

    def _get_connection_string(self):
        """Generate MongoDB connection string using credentials
        
        Creates a connection string for MongoDB Atlas using the format:
        mongodb+srv://<username>:<password>@<host>/?<options>
        
        Returns:
            str: Formatted MongoDB connection string with proper authentication and options
        """
        return f"mongodb+srv://{self.username}:{self.password}@{self.host}/?retryWrites=true&w=majority&appName=wireprotocols"

    def _connect(self) -> Optional[Database]:
        """Establish connection to MongoDB database
        
        Attempts to establish a connection to MongoDB using the connection string.
        Implements error handling to gracefully handle connection failures.
        
        Returns:
            Optional[Database]: MongoDB database object or None if connection fails
        
        Note:
            Connection errors are caught and printed to console. In production,
            you might want to implement proper logging instead of print statements.
        """
        try:
            client = MongoClient(self._get_connection_string(), retryWrites=True)
            return client[self.database_name]
        except Exception as e:
            print(f"Error connecting to MongoDB {self.db_type}: {e}")
            return None
