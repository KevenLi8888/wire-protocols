import json
import os
import socket
import tempfile
from datetime import datetime
from typing import Dict, List
from unittest.mock import MagicMock, patch
import pytest
import logging

@pytest.fixture(autouse=True)
def mock_database_manager():
    """Global mock database manager"""
    with patch('database.collections.DatabaseManager') as mock_manager:
        # create a mock database object
        mock_db = MagicMock()
        
        # set messages collection
        mock_messages_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_messages_collection
        
        # set db property
        mock_manager.get_instance.return_value.db = mock_db
        
        yield mock_manager

@pytest.fixture(autouse=True)
def mock_logger():
    """Global mock logger"""
    with patch('server.server.setup_logger') as mock_setup_logger:
        logger = MagicMock()
        logger.error = MagicMock()
        logger.info = MagicMock()
        logger.warning = MagicMock()
        mock_setup_logger.return_value = logger
        yield logger

# database related fixtures
@pytest.fixture
def mock_db():
    """Mock database connection"""
    class MockDB:
        def __init__(self):
            self.users: Dict[str, dict] = {}
            self.messages: List[dict] = []
            self.next_message_id = 1
            self.next_user_id = 1
            
        def insert_one(self, user):
            """Add new user"""
            user_id = str(self.next_user_id)
            self.next_user_id += 1
            self.users[user.email] = {
                "_id": user_id,
                "username": user.username,
                "email": user.email,
                "password_hash": user.password_hash,
                "created_at": user.created_at
            }
            
        def update_last_login(self, user_id: str):
            """Update last login time"""
            pass
            
        def find_by_email(self, email: str):
            """Find user by email"""
            user = self.users.get(email)
            if user:
                return type('User', (), {
                    '_id': user['_id'],
                    'username': user['username'],
                    'email': email,
                    'password_hash': user['password_hash'],
                    'created_at': user['created_at']
                })
            return None
            
        def insert_message(self, sender_id: str, recipient_id: str, content: str):
            message_id = self.next_message_id
            self.next_message_id += 1
            message = {
                "_id": message_id,
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "content": content,
                "timestamp": datetime.now(),
                "is_read": False
            }
            self.messages.append(message)
            return message_id
            
        def get_recent_chats(self, user_id: str, page: int):
            # return empty list and 1 page
            return [], 1
            
        def get_previous_messages_between_users(self, user_id: str, other_user_id: str, page: int):
            # return empty list and 1 page
            return [], 1
            
        def get_chat_unread_count(self, user_id: str, other_user_id: str):
            return 0
            
        def get_unread_messages(self, user_id: str, other_user_id: str, num_messages: int):
            return []
            
        def mark_as_read(self, message_ids: List[str]):
            pass
            
        def delete_messages(self, message_ids: List[str]):
            return True
            
        def clear(self):
            self.users.clear()
            self.messages.clear()
            self.next_message_id = 1
            self.next_user_id = 1
            
        def get_all_users(self):
            """Return all users"""
            return [
                type('User', (), {
                    '_id': user['_id'],
                    'username': user['username'],
                    'email': email,
                    'password_hash': user['password_hash']
                })
                for email, user in self.users.items()
            ]
            
        def search_users_by_username_paginated(self, current_user_id, pattern, page):
            """Search users"""
            matching_users = [
                type('User', (), {
                    '_id': user['_id'],
                    'username': user['username'],
                    'email': email,
                    'password_hash': user['password_hash']
                })
                for email, user in self.users.items()
                if pattern.lower() in user['username'].lower()
            ]
            return matching_users, 1
    
    db = MockDB()
    yield db
    db.clear()

# 网络相关fixtures
@pytest.fixture
def mock_socket():
    """Mock socket connection"""
    socket_mock = MagicMock()
    socket_mock.send = MagicMock(return_value=None)
    socket_mock.recv = MagicMock(return_value=b'')
    socket_mock.getpeername = MagicMock(return_value=('127.0.0.1', 12345))
    socket_mock.close = MagicMock()
    return socket_mock

# test user data fixtures
@pytest.fixture
def test_users():
    """Return test user data"""
    return [
        {
            "username": "test_user1",
            "password": "password123",
            "password_hash": "hashed_password_1"  # actually should be the real hash value
        },
        {
            "username": "test_user2",
            "password": "password456",
            "password_hash": "hashed_password_2"
        }
    ]

# test message data fixtures
@pytest.fixture
def test_messages():
    """Return test message data"""
    return [
        {
            "id": 1,
            "sender": "test_user1",
            "recipient": "test_user2",
            "content": "Hello, User2!",
            "timestamp": datetime.now(),
            "is_read": False
        },
        {
            "id": 2,
            "sender": "test_user2",
            "recipient": "test_user1",
            "content": "Hi, User1!",
            "timestamp": datetime.now(),
            "is_read": True
        }
    ]

# server configuration fixtures
@pytest.fixture
def server_config():
    """Return server configuration"""
    return {
        "host": "localhost",
        "port": 12345,
        "max_connections": 5,
        "buffer_size": 1024
    }

# temporary configuration file fixtures
@pytest.fixture
def temp_config_file():
    """Create temporary configuration file"""
    config = {
        "database": {
            "username": "test_user",
            "password": "test_pass",
            "host": "test.mongodb.net",
            "name": "test_db"
        },
        "communication": {
            "protocol_type": "json",
            "host": "127.0.0.1",
            "port": 13570
        },
        "env": "debug"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    yield config_path
    
    try:
        os.unlink(config_path)
    except OSError:
        pass

# mock client fixtures
@pytest.fixture
def mock_client():
    """Return mock client instance"""
    client = MagicMock()
    client.connected = True
    client.username = None
    return client

# mock server fixtures
@pytest.fixture
def mock_server():
    """Return mock server instance"""
    server = MagicMock()
    server.clients = {}
    server.running = True
    return server

# protocol handler fixtures
@pytest.fixture
def protocol_handler():
    """Return protocol handler"""
    class ProtocolHandler:
        @staticmethod
        def encode_message(message_type: str, payload: dict) -> bytes:
            data = {
                "type": message_type,
                "payload": payload
            }
            return json.dumps(data).encode()
            
        @staticmethod
        def decode_message(data: bytes) -> tuple:
            message = json.loads(data.decode())
            return message["type"], message["payload"]
    
    return ProtocolHandler()
