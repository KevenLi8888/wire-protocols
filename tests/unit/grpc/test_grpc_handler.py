import pytest
from unittest.mock import MagicMock, patch
from shared.grpc_handler import GRPCMessageHandler
from shared.constants import (
    MSG_CREATE_ACCOUNT_REQUEST, MSG_LOGIN_REQUEST, MSG_DELETE_ACCOUNT_REQUEST,
    MSG_SEND_MESSAGE_REQUEST, MSG_SEARCH_USERS_REQUEST, MSG_GET_RECENT_CHATS_REQUEST,
    MSG_GET_PREVIOUS_MESSAGES_REQUEST, MSG_GET_CHAT_UNREAD_COUNT_REQUEST,
    MSG_GET_UNREAD_MESSAGES_REQUEST, MSG_DELETE_MESSAGE_REQUEST
)


@pytest.fixture
def grpc_handler():
    """Return a GRPCMessageHandler instance with a mock logger"""
    mock_logger = MagicMock()
    return GRPCMessageHandler(logger=mock_logger)


@pytest.fixture
def mock_grpc_client():
    """Return a mock GRPCClient"""
    mock_client = MagicMock()
    # Set up return values for client methods
    mock_client.create_account.return_value = {"status": "success", "user_id": "123"}
    mock_client.login.return_value = {"status": "success", "user_id": "123", "token": "abc123"}
    mock_client.delete_account.return_value = {"status": "success"}
    mock_client.send_message.return_value = {"status": "success", "message_id": "456"}
    mock_client.search_users.return_value = {"status": "success", "users": []}
    mock_client.get_recent_chats.return_value = {"status": "success", "chats": []}
    mock_client.get_previous_messages.return_value = {"status": "success", "messages": []}
    mock_client.get_chat_unread_count.return_value = {"status": "success", "count": 0}
    mock_client.get_unread_messages.return_value = {"status": "success", "messages": []}
    mock_client.delete_messages.return_value = {"status": "success"}
    return mock_client


class TestGRPCMessageHandler:
    
    def test_handle_create_account(self, grpc_handler, mock_grpc_client):
        """Test successful account creation"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
        
        result = grpc_handler.handle_message(MSG_CREATE_ACCOUNT_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.create_account.assert_called_once_with(
            "test@example.com", "testuser", "password123"
        )
        assert result == {"status": "success", "user_id": "123"}
    
    def test_handle_login(self, grpc_handler, mock_grpc_client):
        """Test successful user login"""
        data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        result = grpc_handler.handle_message(MSG_LOGIN_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.login.assert_called_once_with(
            "test@example.com", "password123"
        )
        assert result == {"status": "success", "user_id": "123", "token": "abc123"}
    
    def test_handle_delete_account(self, grpc_handler, mock_grpc_client):
        """Test successful account deletion"""
        data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        result = grpc_handler.handle_message(MSG_DELETE_ACCOUNT_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.delete_account.assert_called_once_with(
            "test@example.com", "password123"
        )
        assert result == {"status": "success"}
    
    def test_handle_send_message(self, grpc_handler, mock_grpc_client):
        """Test successful message sending"""
        data = {
            "content": "Hello, world!",
            "recipient_id": "456",
            "sender_id": "123"
        }
        
        result = grpc_handler.handle_message(MSG_SEND_MESSAGE_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.send_message.assert_called_once_with(
            "Hello, world!", "456", "123"
        )
        assert result == {"status": "success", "message_id": "456"}
    
    def test_handle_search_users(self, grpc_handler, mock_grpc_client):
        """Test successful user search"""
        data = {
            "pattern": "test",
            "page": 1,
            "current_user_id": "123"
        }
        
        result = grpc_handler.handle_message(MSG_SEARCH_USERS_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.search_users.assert_called_once_with(
            "test", 1, "123"
        )
        assert result == {"status": "success", "users": []}
    
    def test_handle_get_recent_chats(self, grpc_handler, mock_grpc_client):
        """Test successful retrieval of recent chats"""
        data = {
            "user_id": "123",
            "page": 1
        }
        
        result = grpc_handler.handle_message(MSG_GET_RECENT_CHATS_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.get_recent_chats.assert_called_once_with(
            "123", 1
        )
        assert result == {"status": "success", "chats": []}
    
    def test_handle_get_previous_messages(self, grpc_handler, mock_grpc_client):
        """Test successful retrieval of previous messages"""
        data = {
            "user_id": "123",
            "other_user_id": "456",
            "page": 1
        }
        
        result = grpc_handler.handle_message(MSG_GET_PREVIOUS_MESSAGES_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.get_previous_messages.assert_called_once_with(
            "123", "456", 1
        )
        assert result == {"status": "success", "messages": []}
    
    def test_handle_get_chat_unread_count(self, grpc_handler, mock_grpc_client):
        """Test successful retrieval of unread message count"""
        data = {
            "user_id": "123",
            "other_user_id": "456"
        }
        
        result = grpc_handler.handle_message(MSG_GET_CHAT_UNREAD_COUNT_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.get_chat_unread_count.assert_called_once_with(
            "123", "456"
        )
        assert result == {"status": "success", "count": 0}
    
    def test_handle_get_unread_messages(self, grpc_handler, mock_grpc_client):
        """Test successful retrieval of unread messages"""
        data = {
            "user_id": "123",
            "other_user_id": "456",
            "num_messages": 10
        }
        
        result = grpc_handler.handle_message(MSG_GET_UNREAD_MESSAGES_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.get_unread_messages.assert_called_once_with(
            "123", "456", 10
        )
        assert result == {"status": "success", "messages": []}
    
    def test_handle_delete_messages(self, grpc_handler, mock_grpc_client):
        """Test successful deletion of messages"""
        data = {
            "message_ids": ["1", "2", "3"]
        }
        
        result = grpc_handler.handle_message(MSG_DELETE_MESSAGE_REQUEST, data, mock_grpc_client)
        
        mock_grpc_client.delete_messages.assert_called_once_with(
            ["1", "2", "3"]
        )
        assert result == {"status": "success"}
    
    def test_handle_unsupported_message_type(self, grpc_handler, mock_grpc_client):
        """Test handling of unsupported message type"""
        data = {"some": "data"}
        
        with pytest.raises(ValueError) as excinfo:
            grpc_handler.handle_message(999, data, mock_grpc_client)
        
        assert "Unsupported gRPC message type: 999" in str(excinfo.value)
