import pytest
from unittest.mock import MagicMock, patch
from client.client import Client
from shared.models import User
from shared.constants import *
pytest_plugins = ['pytest_asyncio']

@pytest.fixture
def mock_gui():
    """Mock GUI interface"""
    gui = MagicMock()
    gui.run = MagicMock()
    gui.show_error = MagicMock()
    gui.display_message = MagicMock()
    gui.show_chat_window = MagicMock()
    return gui

@pytest.fixture
def mock_communication():
    """Mock communication interface"""
    comm = MagicMock()
    comm.send = MagicMock()
    comm.receive = MagicMock()
    return comm

@pytest.fixture
def client(temp_config_file, mock_gui, mock_communication):
    """Create client instance for testing"""
    with patch('client.client.ChatGUI') as mock_gui_class, \
         patch('client.client.CommunicationInterface') as mock_comm_class:
        mock_gui_class.return_value = mock_gui
        mock_comm_class.return_value = mock_communication
        client = Client(config_path=temp_config_file)
        return client

def test_client_initialization(client):
    """Test client initialization"""
    assert client.host == '127.0.0.1'
    assert client.port == 13570
    assert client.current_user is None
    assert hasattr(client, 'message_handler')
    assert hasattr(client, 'action_handler')

def test_client_connect(client, mock_socket):
    """Test client connection success"""
    # mock communication interface and socket
    client.communication = MagicMock()
    client.client_socket = mock_socket
    
    # set basic properties
    client.host = 'localhost'
    client.port = 12345
    
    # execute connection
    result = client.connect()
    
    # verify result
    assert result is True
    mock_socket.connect.assert_called_once_with(('localhost', 12345))

def test_send_message(client):
    """Test sending message"""
    message_type = MSG_SEND_MESSAGE_REQUEST
    data = {"content": "Hello", "recipient_id": "123"}
    client.send_message(message_type, data)
    client.communication.send.assert_called_once_with(message_type, data, client.client_socket)

def test_set_current_user(client):
    """Test setting current user"""
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
    """Test handling received message"""
    message_data = {
        'sender_id': '123',
        'content': 'Hello',
        'timestamp': '2024-01-01 12:00:00'
    }
    client.handle_received_message(message_data)
    mock_gui.display_message.assert_called_once_with(message_data)

def test_update_recent_chats(client, mock_gui):
    """Test updating recent chats list"""
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
    """Test message receiving loop"""
    client.message_handler.handle_message = MagicMock()
    
    # mock receiving a message and then exiting
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
    """Test error handling"""
    error_message = "Test error"
    
    # create an error response that matches the message format
    message_type = MSG_ERROR_RESPONSE
    data = {
        "message": error_message
    }
    
    # call message handler to handle error message
    client.message_handler.handle_message(message_type, data)
    
    # verify GUI's show_error method is called
    client.gui.show_error.assert_called_once_with(error_message)

def test_init_config_with_missing_values(temp_config_file):
    """测试配置文件缺少值时的默认行为"""
    with patch('config.config.Config') as mock_config:
        # 模拟配置对象
        config_instance = MagicMock()
        mock_config.get_instance.return_value = config_instance
        
        # 模拟获取配置时抛出ValueError
        config_instance.get.side_effect = [
            'development',  # env
            ValueError("Missing host"),  # host
            ValueError("Missing port"),  # port
            'tcp'  # protocol_type
        ]
        
        client = Client(config_path=temp_config_file)
        
        # 验证使用了默认值
        assert client.host == '127.0.0.1'
        assert client.port == 13570

def test_connection_refused(client):
    """测试连接被拒绝的情况"""
    # 修改：使用MagicMock来模拟socket对象
    mock_socket = MagicMock()
    mock_socket.connect.side_effect = ConnectionRefusedError("Connection refused")
    client.client_socket = mock_socket
    
    # 修改：在连接前设置错误消息回调
    error_message = None
    def show_error(msg):
        nonlocal error_message
        error_message = msg
    client.gui.show_error = show_error
    
    result = client.connect()
    
    assert result is False
    assert error_message is not None
    assert "Connection refused" in error_message

def test_connection_general_error(client):
    """测试连接时的一般错误"""
    # 修改：使用MagicMock来模拟socket对象
    mock_socket = MagicMock()
    mock_socket.connect.side_effect = Exception("Unknown error")
    client.client_socket = mock_socket
    
    # 修改：在连接前设置错误消息回调
    error_message = None
    def show_error(msg):
        nonlocal error_message
        error_message = msg
    client.gui.show_error = show_error
    
    result = client.connect()
    
    assert result is False
    assert error_message is not None
    assert "Unknown error" in error_message

def test_set_current_user_error(client):
    """测试设置当前用户时的错误处理"""
    invalid_user_data = {
        'invalid_field': 'value'  # 缺少必要的用户字段
    }
    
    # 修改：直接调用set_current_user并验证结果
    client.set_current_user(invalid_user_data)
    
    # 验证当前用户未被设置
    assert client.current_user is None

def test_handle_received_message_error(client, mock_gui):
    """测试处理接收消息时的错误"""
    mock_gui.display_message.side_effect = Exception("Display error")
    
    # 不应该抛出异常，而是应该被记录
    client.handle_received_message({"content": "test"})

def test_update_recent_chats_error(client, mock_gui):
    """测试更新最近聊天列表时的错误"""
    mock_gui.update_recent_chats.side_effect = Exception("Update error")
    
    # 不应该抛出异常，而是应该被记录
    client.update_recent_chats({"chats": [], "total_pages": 1})
