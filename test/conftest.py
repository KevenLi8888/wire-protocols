import json
import os
import socket
import tempfile
from datetime import datetime
from typing import Dict, List
from unittest.mock import MagicMock
import pytest


# 数据库相关fixtures
@pytest.fixture
def mock_db():
    """模拟数据库连接"""
    class MockDB:
        def __init__(self):
            self.users: Dict[str, dict] = {}
            self.messages: List[dict] = []
            self.next_message_id = 1  # 添加消息ID计数器
            
        def add_user(self, username: str, password_hash: str):
            self.users[username] = {
                "username": username,
                "password_hash": password_hash,
                "created_at": datetime.now(),
                "is_online": False
            }
            
        def add_message(self, sender: str, recipient: str, content: str):
            message = {
                "id": self.next_message_id,  # 使用递增的ID
                "sender": sender,
                "recipient": recipient,
                "content": content,
                "timestamp": datetime.now(),
                "is_read": False
            }
            self.messages.append(message)
            self.next_message_id += 1  # 递增ID计数器
            return message["id"]
            
        def clear(self):
            self.users.clear()
            self.messages.clear()
    
    db = MockDB()
    yield db
    db.clear()

# 网络相关fixtures
@pytest.fixture
def mock_socket():
    """模拟socket连接"""
    class MockSocket:
        def __init__(self):
            self.sent_data = []
            self.received_data = []
            self.is_connected = True
            
        def send(self, data: bytes):
            self.sent_data.append(data)
            return len(data)
            
        def recv(self, buffer_size: int) -> bytes:
            if self.received_data:
                return self.received_data.pop(0)
            return b""
            
        def close(self):
            self.is_connected = False
            
    return MockSocket()

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
        "username": "dbAdmin",
        "password": "123",
        "host": "projects.test.mongodb.net",
        "name": "chatapp"
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
    
    # 清理临时文件
    os.unlink(config_path)

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
