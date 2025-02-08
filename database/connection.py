# Requires: python -m pip install "pymongo[srv]"

from pymongo import MongoClient
from urllib.parse import quote_plus
from typing import Optional
from pymongo.database import Database
from config.config import Config

class DatabaseManager:
    _instance = None

    def __init__(self):
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
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    @property
    def db(self) -> Optional[Database]:
        if self._db is None:
            self._db = self._connect()
        return self._db

    def _get_connection_string(self):
        return f"mongodb+srv://{self.username}:{self.password}@{self.host}/?retryWrites=true&w=majority&appName=wireprotocols"

    def _connect(self) -> Optional[Database]:
        try:
            # Enable retryWrites for Atlas compatibility
            client = MongoClient(self._get_connection_string(), retryWrites=True)
            return client[self.database_name]
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None
