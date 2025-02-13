# Requires: python -m pip install "pymongo[srv]"

from pymongo import MongoClient
from urllib.parse import quote_plus
from typing import Optional
from pymongo.database import Database
from config.config import Config

class DatabaseManager:
    """Singleton class to manage MongoDB database connections
    
    This class implements the Singleton pattern to ensure only one database
    connection is maintained throughout the application's lifecycle. It handles
    connection establishment, credential management, and database operations.
    """
    _instance = None  # Class variable to store the singleton instance

    def __init__(self):
        """Initialize database manager with configuration settings
        
        Retrieves database configuration from the Config singleton and sets up
        connection parameters with proper URL encoding for special characters
        in credentials.
        """
        config = Config.get_instance()
        # Now using the new config access pattern
        db_config = config.get('database')
        self.username = quote_plus(db_config.username)
        self.password = quote_plus(db_config.password)
        self.host = db_config.host
        self.database_name = db_config.name
        self._db: Optional[Database] = None

    @classmethod
    def get_instance(cls):
        """Get or create singleton instance of DatabaseManager
        
        This method implements the Singleton pattern, ensuring only one instance
        of DatabaseManager exists throughout the application.
        
        Returns:
            DatabaseManager: The singleton instance, creating it if it doesn't exist
        """
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

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
            print(f"Error connecting to MongoDB: {e}")
            return None
