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
    """全局模拟数据库管理器"""
    with patch('database.collections.DatabaseManager') as mock_manager:
        # 创建一个模拟的数据库对象
        mock_db = MagicMock()
        
        # 设置 messages 集合
        mock_messages_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_messages_collection
        
        # 设置 db 属性
        mock_manager.get_instance.return_value.db = mock_db
        
        yield mock_manager

@pytest.fixture(autouse=True)
def mock_logger():
    """全局模拟logger"""
    with patch('server.server.setup_logger') as mock_setup_logger:
        logger = MagicMock()
        logger.error = MagicMock()
        logger.info = MagicMock()
        logger.warning = MagicMock()
        mock_setup_logger.return_value = logger
        yield logger

# 数据库相关fixtures
@pytest.fixture
def mock_db():
    """模拟数据库连接"""
    class MockDB:
        def __init__(self):
            self.users: Dict[str, dict] = {}
            self.messages: List[dict] = []
            self.next_message_id = 1
            self.next_user_id = 1
            
        def insert_one(self, user):
            """添加新用户"""
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
            """更新最后登录时间"""
            pass
            
        def find_by_email(self, email: str):
            """通过邮箱查找用户"""
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
            # 简单返回空列表和1页
            return [], 1
            
        def get_previous_messages_between_users(self, user_id: str, other_user_id: str, page: int):
            # 简单返回空列表和1页
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
            """返回所有用户"""
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
            """搜索用户"""
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
    """模拟socket连接"""
    socket_mock = MagicMock()
    socket_mock.send = MagicMock(return_value=None)
    socket_mock.recv = MagicMock(return_value=b'')
    socket_mock.getpeername = MagicMock(return_value=('127.0.0.1', 12345))
    socket_mock.close = MagicMock()
    return socket_mock

# 测试用户数据fixtures
@pytest.fixture
def test_users():
    """返回测试用户数据"""
    return [
        {
            "username": "test_user1",
            "password": "password123",
            "password_hash": "hashed_password_1"  # 实际应该是真实的hash值
        },
        {
            "username": "test_user2",
            "password": "password456",
            "password_hash": "hashed_password_2"
        }
    ]

# 测试消息数据fixtures
@pytest.fixture
def test_messages():
    """返回测试消息数据"""
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

# 服务器配置fixtures
@pytest.fixture
def server_config():
    """返回服务器配置"""
    return {
        "host": "localhost",
        "port": 12345,
        "max_connections": 5,
        "buffer_size": 1024
    }

# 临时配置文件fixtures
@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
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

# 模拟客户端fixtures
@pytest.fixture
def mock_client():
    """返回模拟的客户端实例"""
    client = MagicMock()
    client.connected = True
    client.username = None
    return client

# 模拟服务器fixtures
@pytest.fixture
def mock_server():
    """返回模拟的服务器实例"""
    server = MagicMock()
    server.clients = {}
    server.running = True
    return server

# 协议处理fixtures
@pytest.fixture
def protocol_handler():
    """返回协议处理器"""
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
