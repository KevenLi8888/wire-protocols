import pytest
from unittest.mock import MagicMock, patch
from client.client import Client
from shared.models import User
from shared.constants import *
pytest_plugins = ['pytest_asyncio']

@pytest.fixture
def mock_gui():
    """模拟GUI界面"""
    gui = MagicMock()
    gui.run = MagicMock()
    gui.show_error = MagicMock()
    gui.display_message = MagicMock()
    gui.show_chat_window = MagicMock()
    return gui

@pytest.fixture
def mock_communication():
    """模拟通信接口"""
    comm = MagicMock()
    comm.send = MagicMock()
    comm.receive = MagicMock()
    return comm

@pytest.fixture
def client(temp_config_file, mock_gui, mock_communication):
    """创建测试用的client实例"""
    with patch('client.client.ChatGUI') as mock_gui_class, \
         patch('client.client.CommunicationInterface') as mock_comm_class:
        mock_gui_class.return_value = mock_gui
        mock_comm_class.return_value = mock_communication
        client = Client(config_path=temp_config_file)
        return client

def test_client_initialization(client):
    """测试客户端初始化"""
    assert client.host == '127.0.0.1'
    assert client.port == 13570
    assert client.current_user is None
    assert hasattr(client, 'message_handler')
    assert hasattr(client, 'action_handler')

def test_client_connect_success(client, mock_socket):
    """测试客户端连接成功"""
    # 模拟通信接口和socket
    client.communication = MagicMock()
    client.client_socket = mock_socket
    
    # 设置基本属性
    client.host = 'localhost'
    client.port = 12345
    
    # 执行连接
    result = client.connect()
    
    # 验证结果
    assert result is True
    mock_socket.connect.assert_called_once_with(('localhost', 12345))

def test_client_connect_failure(client):
    """测试客户端连接失败"""
    with patch('socket.socket') as mock_socket_class:
        mock_socket_class.return_value.connect.side_effect = Exception("Connection failed")
        assert client.connect() is False

def test_send_message(client):
    """测试发送消息"""
    message_type = MSG_SEND_MESSAGE_REQUEST
    data = {"content": "Hello", "recipient_id": "123"}
    client.send_message(message_type, data)
    client.communication.send.assert_called_once_with(message_type, data, client.client_socket)

def test_set_current_user(client):
    """测试设置当前用户"""
    user_data = {
        '_id': '123',
        'username': 'test_user',
        'email': 'test@example.com'
    }
    client.set_current_user(user_data)
    assert isinstance(client.current_user, User)
    assert client.current_user._id == '123'
    assert client.current_user.username == 'test_user'
    assert client.current_user.email == 'test@example.com'
    assert client.action_handler.current_user_id == '123'

def test_handle_received_message(client, mock_gui):
    """测试处理接收到的消息"""
    message_data = {
        'sender_id': '123',
        'content': 'Hello',
        'timestamp': '2024-01-01 12:00:00'
    }
    client.handle_received_message(message_data)
    mock_gui.display_message.assert_called_once_with(message_data)

def test_update_recent_chats(client, mock_gui):
    """测试更新最近聊天列表"""
    chats_data = {
        'chats': [
            {
                'username': 'user1',
                'last_message': {'content': 'hi'},
                'unread_count': 2
            }
        ],
        'total_pages': 1
    }
    client.update_recent_chats(chats_data)
    mock_gui.update_recent_chats.assert_called_once_with(chats_data['chats'], chats_data['total_pages'])

def test_receive_messages(client, mock_communication):
    """测试接收消息循环"""
    # 创建一个 MagicMock 对象来模拟 message_handler
    client.message_handler.handle_message = MagicMock()
    
    # 模拟接收到一条消息后退出
    mock_communication.receive.side_effect = [
        ({"type": "message", "content": "test"}, MSG_NEW_MESSAGE_UPDATE),
        Exception("Connection closed")
    ]
    
    client.receive_messages()
    assert mock_communication.receive.call_count == 2
    client.message_handler.handle_message.assert_called_once_with(
        MSG_NEW_MESSAGE_UPDATE, 
        {"type": "message", "content": "test"}
    )

def test_client_error_handling(client, mock_gui):
    """测试错误处理"""
    error_message = "Test error"
    
    # 创建一个符合消息格式的错误响应
    message_type = MSG_ERROR_RESPONSE
    data = {
        "message": error_message
    }
    
    # 调用消息处理器处理错误消息
    client.message_handler.handle_message(message_type, data)
    
    # 验证GUI的show_error方法被调用
    client.gui.show_error.assert_called_once_with(error_message)
