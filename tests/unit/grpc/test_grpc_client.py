import pytest
from unittest.mock import MagicMock, patch
from client.grpc_client import GRPCClient
from generated import chat_pb2
import grpc

@pytest.fixture
def grpc_client(mock_logger):
    with patch('grpc.insecure_channel') as mock_channel:
        client = GRPCClient('localhost', 50051, mock_logger)
        yield client

def test_create_account_success(grpc_client):
    """Test successful account creation"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Account created successfully"
    grpc_client.stub.CreateAccount = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.create_account("test@example.com", "testuser", "password123")

    # Verify
    assert result == {
        'code': 0,
        'message': "Account created successfully"
    }

def test_create_account_failure(grpc_client):
    """Test account creation with connection failure"""
    # Setup mock error
    mock_error = grpc.RpcError()
    mock_error.__str__ = lambda _: "Connection failed"  # Override __str__ method
    grpc_client.stub.CreateAccount = MagicMock(side_effect=mock_error)

    # Test
    result = grpc_client.create_account("test@example.com", "testuser", "password123")

    # Verify
    assert result['code'] == -1

def test_login_success(grpc_client):
    """Test successful user login"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Login successful"
    mock_response.user.id = "user123"
    mock_response.user.username = "testuser"
    mock_response.user.email = "test@example.com"
    grpc_client.stub.Login = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.login("test@example.com", "password123")

    # Verify
    assert result == {
        'code': 0,
        'message': "Login successful",
        'data': {
            'user': {
                '_id': "user123",
                'username': "testuser",
                'email': "test@example.com"
            }
        }
    }

def test_login_failure(grpc_client):
    """Test login with connection failure"""
    # Setup mock error
    mock_error = grpc.RpcError()
    mock_error.__str__ = lambda _: "Connection failed"
    grpc_client.stub.Login = MagicMock(side_effect=mock_error)

    # Test
    result = grpc_client.login("test@example.com", "password123")

    # Verify
    assert result['code'] == -1
    # assert result['message'] == "Connection failed"

def test_login_error_response(grpc_client):
    """Test login with invalid credentials"""
    # Setup mock response with error
    mock_response = MagicMock()
    mock_response.code = 1
    mock_response.message = "Invalid credentials"
    grpc_client.stub.Login = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.login("test@example.com", "password123")

    # Verify
    assert result == {
        'code': 1,
        'message': "Invalid credentials"
    }

def test_send_message_success(grpc_client):
    """Test successful message sending"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Message sent"
    mock_response.data.message_id = "msg123"
    mock_response.data.sender_id = "sender123"
    mock_response.data.recipient_id = "recipient123"
    mock_response.data.content = "Hello!"
    mock_response.data.timestamp = "2024-03-14T12:00:00"
    grpc_client.stub.SendMessage = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.send_message("Hello!", "recipient123", "sender123")

    # Verify
    assert result == {
        'code': 0,
        'message': "Message sent",
        'data': {
            'message_id': "msg123",
            'sender_id': "sender123",
            'recipient_id': "recipient123",
            'content': "Hello!",
            'timestamp': "2024-03-14T12:00:00"
        }
    }

def test_send_message_failure(grpc_client):
    """Test message sending with connection failure"""
    # Setup mock error
    mock_error = grpc.RpcError()
    mock_error.__str__ = lambda _: "Connection failed"
    grpc_client.stub.SendMessage = MagicMock(side_effect=mock_error)

    # Test
    result = grpc_client.send_message("Hello!", "recipient123", "sender123")

    # Verify
    assert result['code'] == -1
    # assert result['message'] == "Connection failed"

def test_send_message_error_response(grpc_client):
    # Setup mock response with error
    mock_response = MagicMock()
    mock_response.code = 1
    mock_response.message = "Recipient not found"
    grpc_client.stub.SendMessage = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.send_message("Hello!", "recipient123", "sender123")

    # Verify
    assert result == {
        'code': 1,
        'message': "Recipient not found"
    }

def test_search_users_success(grpc_client):
    """Test successful user search"""
    # Setup mock response
    mock_user = MagicMock()
    mock_user.id = "user123"
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"

    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Users found"
    mock_response.users = [mock_user]
    mock_response.total_pages = 1
    grpc_client.stub.SearchUsers = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.search_users("test", 1, "current123")

    # Verify
    assert result == {
        'code': 0,
        'message': "Users found",
        'data': {
            'users': [{
                '_id': "user123",
                'username': "testuser",
                'email': "test@example.com"
            }],
            'total_pages': 1
        }
    }

def test_search_users_failure(grpc_client):
    """Test user search with connection failure"""
    # Setup mock error
    mock_error = grpc.RpcError()
    mock_error.__str__ = lambda _: "Connection failed"
    grpc_client.stub.SearchUsers = MagicMock(side_effect=mock_error)

    # Test
    result = grpc_client.search_users("test", 1, "current123")

    # Verify
    assert result['code'] == -1
    # assert result['message'] == "Connection failed"

def test_search_users_error_response(grpc_client):
    # Setup mock response with error
    mock_response = MagicMock()
    mock_response.code = 1
    mock_response.message = "Search failed"
    grpc_client.stub.SearchUsers = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.search_users("test", 1, "current123")

    # Verify
    assert result == {
        'code': 1,
        'message': "Search failed"
    }

def test_get_recent_chats_success(grpc_client):
    """Test successful retrieval of recent chats"""
    # Setup mock response
    mock_chat = MagicMock()
    mock_chat.user_id = "user123"
    mock_chat.username = "testuser"
    mock_chat.unread_count = 2
    mock_chat.last_message.content = "Hello!"
    mock_chat.last_message.timestamp = "2024-03-14T12:00:00"
    mock_chat.last_message.is_from_me = True

    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Chats retrieved"
    mock_response.chats = [mock_chat]
    mock_response.total_pages = 1
    grpc_client.stub.GetRecentChats = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.get_recent_chats("user123", 1)

    # Verify
    assert result == {
        'code': 0,
        'message': "Chats retrieved",
        'data': {
            'chats': [{
                'user_id': "user123",
                'username': "testuser",
                'unread_count': 2,
                'last_message': {
                    'content': "Hello!",
                    'timestamp': "2024-03-14T12:00:00",
                    'is_from_me': True
                }
            }],
            'total_pages': 1
        }
    }

def test_get_recent_chats_error_response(grpc_client):
    """Test retrieval of recent chats with connection failure"""
    # Setup mock response with error
    mock_response = MagicMock()
    mock_response.code = 1
    mock_response.message = "Failed to retrieve chats"
    grpc_client.stub.GetRecentChats = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.get_recent_chats("user123", 1)

    # Verify
    assert result == {
        'code': 1,
        'message': "Failed to retrieve chats"
    }

def test_delete_account_success(grpc_client):
    """Test successful account deletion"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Account deleted successfully"
    grpc_client.stub.DeleteAccount = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.delete_account("test@example.com", "password123")

    # Verify
    assert result == {
        'code': 0,
        'message': "Account deleted successfully"
    }

def test_get_previous_messages_success(grpc_client):
    """Test successful retrieval of previous messages"""
    # Setup mock response
    mock_message = MagicMock()
    mock_message.message_id = "msg123"
    mock_message.content = "Hello!"
    mock_message.timestamp = "2024-03-14T12:00:00"
    mock_message.is_from_me = True
    mock_message.sender.user_id = "sender123"
    mock_message.sender.username = "testuser"

    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Messages retrieved"
    mock_response.user_id = "user123"
    mock_response.other_user_id = "other123"
    mock_response.messages = [mock_message]
    mock_response.total_pages = 1
    grpc_client.stub.GetPreviousMessages = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.get_previous_messages("user123", "other123", 1)

    # Verify
    assert result == {
        'code': 0,
        'message': "Messages retrieved",
        'data': {
            'user_id': "user123",
            'other_user_id': "other123",
            'messages': [{
                'message_id': "msg123",
                'content': "Hello!",
                'timestamp': "2024-03-14T12:00:00",
                'is_from_me': True,
                'sender': {
                    'user_id': "sender123",
                    'username': "testuser"
                }
            }],
            'total_pages': 1
        }
    }

def test_get_previous_messages_failure(grpc_client):
    """Test retrieval of previous messages with connection failure"""
    # Setup mock error
    mock_error = grpc.RpcError()
    mock_error.__str__ = lambda _: "Connection failed"
    grpc_client.stub.GetPreviousMessages = MagicMock(side_effect=mock_error)

    # Test
    result = grpc_client.get_previous_messages("user123", "other123", 1)

    # Verify
    assert result['code'] == -1
    # assert result['message'] == "Connection failed"

def test_get_previous_messages_error_response(grpc_client):
    # Setup mock response with error
    mock_response = MagicMock()
    mock_response.code = 1
    mock_response.message = "Failed to retrieve messages"
    grpc_client.stub.GetPreviousMessages = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.get_previous_messages("user123", "other123", 1)

    # Verify
    assert result == {
        'code': 1,
        'message': "Failed to retrieve messages"
    }

def test_get_chat_unread_count_success(grpc_client):
    """Test successful retrieval of unread message count"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Unread count retrieved"
    mock_response.user_id = "user123"
    mock_response.other_user_id = "other123"
    mock_response.count = 5
    grpc_client.stub.GetChatUnreadCount = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.get_chat_unread_count("user123", "other123")

    # Verify
    assert result == {
        'code': 0,
        'message': "Unread count retrieved",
        'data': {
            'user_id': "user123",
            'other_user_id': "other123",
            'count': 5
        }
    }

def test_get_chat_unread_count_failure(grpc_client):
    """Test retrieval of unread message count with connection failure"""
    # Setup mock error
    mock_error = grpc.RpcError()
    mock_error.__str__ = lambda _: "Connection failed"
    grpc_client.stub.GetChatUnreadCount = MagicMock(side_effect=mock_error)

    # Test
    result = grpc_client.get_chat_unread_count("user123", "other123")

    # Verify
    assert result['code'] == -1
    # assert result['message'] == "Connection failed"

def test_get_chat_unread_count_error_response(grpc_client):
    """Test retrieval of unread message count with error"""
    # Setup mock response with error
    mock_response = MagicMock()
    mock_response.code = 1
    mock_response.message = "Failed to get unread count"
    grpc_client.stub.GetChatUnreadCount = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.get_chat_unread_count("user123", "other123")

    # Verify
    assert result == {
        'code': 1,
        'message': "Failed to get unread count"
    }

def test_get_unread_messages_success(grpc_client):
    """Test successful retrieval of unread messages"""
    # Setup mock response
    mock_message = MagicMock()
    mock_message.message_id = "msg123"
    mock_message.sender_id = "sender123"
    mock_message.recipient_id = "recipient123"
    mock_message.content = "Hello!"
    mock_message.timestamp = "2024-03-14T12:00:00"
    mock_message.is_read = False
    mock_message.is_from_me = False

    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Unread messages retrieved"
    mock_response.messages = [mock_message]
    grpc_client.stub.GetUnreadMessages = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.get_unread_messages("user123", "other123", 10)

    # Verify
    assert result == {
        'code': 0,
        'message': "Unread messages retrieved",
        'data': {
            'messages': [{
                'message_id': "msg123",
                'sender_id': "sender123",
                'recipient_id': "recipient123",
                'content': "Hello!",
                'timestamp': "2024-03-14T12:00:00",
                'is_read': False,
                'is_from_me': False
            }]
        }
    }

def test_get_unread_messages_failure(grpc_client):
    """Test retrieval of unread messages with connection failure"""
    # Setup mock error
    mock_error = grpc.RpcError()
    mock_error.__str__ = lambda _: "Connection failed"
    grpc_client.stub.GetUnreadMessages = MagicMock(side_effect=mock_error)

    # Test
    result = grpc_client.get_unread_messages("user123", "other123", 10)

    # Verify
    assert result['code'] == -1
    #assert result['message'] == "Connection failed"

def test_get_unread_messages_error_response(grpc_client):
    """Test retrieval of unread messages with error"""
    # Setup mock response with error
    mock_response = MagicMock()
    mock_response.code = 1
    mock_response.message = "Failed to get unread messages"
    grpc_client.stub.GetUnreadMessages = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.get_unread_messages("user123", "other123", 10)

    # Verify
    assert result == {
        'code': 1,
        'message': "Failed to get unread messages"
    }

def test_delete_messages_success(grpc_client):
    """Test successful deletion of messages"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.code = 0
    mock_response.message = "Messages deleted successfully"
    grpc_client.stub.DeleteMessages = MagicMock(return_value=mock_response)

    # Test
    result = grpc_client.delete_messages(["msg123", "msg456"])

    # Verify
    assert result == {
        'code': 0,
        'message': "Messages deleted successfully"
    }

def test_delete_account_failure(grpc_client):
    """Test account deletion with connection failure"""
    # Setup mock error
    mock_error = grpc.RpcError()
    mock_error.__str__ = lambda _: "Connection failed"
    grpc_client.stub.DeleteAccount = MagicMock(side_effect=mock_error)

    # Test
    result = grpc_client.delete_account("test@example.com", "password123")

    # Verify
    assert result['code'] == -1
    # assert result['message'] == "Connection failed"
