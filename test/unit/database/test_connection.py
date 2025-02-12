import pytest
from unittest.mock import patch, MagicMock
from database.connection import DatabaseManager
from config.config import Config

@pytest.fixture
def mock_config():
    config = MagicMock()
    # Create a mock database configuration object
    db_config = MagicMock()
    db_config.username = "test_user"
    db_config.password = "test_pass"
    db_config.host = "test.mongodb.net"
    db_config.name = "test_db"
    
    # Set the get method to return the database configuration object
    config.get.return_value = db_config
    return config

@pytest.fixture
def reset_singleton():
    """Reset DatabaseManager singleton"""
    DatabaseManager._instance = None
    yield
    DatabaseManager._instance = None

class TestDatabaseManager:
    def test_singleton_pattern(self, reset_singleton):
        """Test if DatabaseManager correctly implements singleton pattern"""
        instance1 = DatabaseManager.get_instance()
        instance2 = DatabaseManager.get_instance()
        assert instance1 is instance2

    def test_connection_string_format(self, reset_singleton, mock_config):
        """Test if connection string format is correct"""
        with patch.object(Config, 'get_instance', return_value=mock_config):
            db_manager = DatabaseManager()
            connection_string = db_manager._get_connection_string()
            assert "mongodb+srv://" in connection_string
            assert "test_user" in connection_string
            assert "test_pass" in connection_string
            assert "test.mongodb.net" in connection_string
            assert "retryWrites=true" in connection_string

    @patch('database.connection.MongoClient')
    def test_successful_connection(self, mock_mongo_client, reset_singleton, mock_config):
        """Test successful database connection"""
        # Create a mock database object
        mock_db = MagicMock()
        # Create a mock client object
        mock_client = MagicMock()
        # Set up client behavior to return database
        mock_client.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client

        with patch.object(Config, 'get_instance', return_value=mock_config):
            db_manager = DatabaseManager.get_instance()
            assert db_manager.db is not None
            # 验证是否使用了正确的数据库名
            mock_client.__getitem__.assert_called_once_with("test_db")  # 直接使用字符串值而不是mock对象

    @patch('database.connection.MongoClient')
    def test_connection_error(self, mock_mongo_client, reset_singleton, mock_config):
        """Test database connection error handling"""
        mock_mongo_client.side_effect = Exception("Connection failed")
        
        with patch.object(Config, 'get_instance', return_value=mock_config):
            db_manager = DatabaseManager.get_instance()
            assert db_manager.db is None

    def test_database_property_caching(self, reset_singleton, mock_config):
        """Test if database connection is properly cached"""
        with patch.object(Config, 'get_instance', return_value=mock_config):
            with patch('database.connection.MongoClient') as mock_mongo_client:
                # Create mock objects
                mock_db = MagicMock()
                mock_client = MagicMock()
                mock_client.__getitem__.return_value = mock_db
                mock_mongo_client.return_value = mock_client

                db_manager = DatabaseManager.get_instance()
                # First access to db property
                db1 = db_manager.db
                # Second access to db property
                db2 = db_manager.db

                # Ensure the same object is returned
                assert db1 is db2
                # MongoClient should only be called once
                mock_mongo_client.assert_called_once()
