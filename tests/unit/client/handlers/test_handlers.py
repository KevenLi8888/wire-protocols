import pytest
from unittest.mock import MagicMock, patch
from client.handlers.message_handler import MessageHandler
from client.handlers.user_action_handler import UserActionHandler
from shared.constants import *

@pytest.fixture
def message_handler():
    """Create a fixture for MessageHandler instance"""
    logger = MagicMock()
    return MessageHandler(logger)

@pytest.fixture
def user_action_handler():
    """Create a fixture for UserActionHandler instance"""
    send_message_func = MagicMock()
    return UserActionHandler(send_message_func, current_user_id="test_user_id")

class TestMessageHandler:
    def test_handle_create_account_success(self, message_handler):
        """Test handling successful account creation"""
        # set callback
        close_callback = MagicMock()
        message_handler.set_close_register_window_callback(close_callback)
        
        # mock successful response
        data = {"code": SUCCESS, "message": "Account created"}
        message_handler.handle_create_account_response(data)
        
        # verify callback is called
        close_callback.assert_called_once()

    def test_handle_create_account_failure(self, message_handler):
        """Test handling failed account creation"""
        # set callback
        error_callback = MagicMock()
        message_handler.set_show_error_callback(error_callback)
        
        # mock failed response
        error_msg = "Email already exists"
        data = {"code": -1, "message": error_msg}
        message_handler.handle_create_account_response(data)
        
        # verify error callback is called
        error_callback.assert_called_once_with(error_msg)

    def test_handle_login_success(self, message_handler):
        """Test handling successful login"""
        # set callback
        login_success = MagicMock()
        close_window = MagicMock()
        user_data_update = MagicMock()
        
        message_handler.set_login_success_callback(login_success)
        message_handler.set_close_login_window_callback(close_window)
        message_handler.set_current_user_callback(user_data_update)
        
        # mock successful login response
        user_data = {"id": "123", "username": "test_user"}
        data = {
            "code": SUCCESS,
            "data": {"user": user_data}
        }
        message_handler.handle_login_response(data)
        
        # verify all callbacks are called correctly
        login_success.assert_called_once()
        close_window.assert_called_once()
        user_data_update.assert_called_once_with(user_data)

    def test_handle_login_response_failure(self, message_handler):
        """Test handling login failure"""
        error_callback = MagicMock()
        message_handler.set_show_error_callback(error_callback)
        
        error_msg = "Invalid credentials"
        data = {"code": -1, "message": error_msg}
        message_handler.handle_login_response(data)
        
        error_callback.assert_called_once_with(error_msg)
        message_handler.logger.error.assert_called_once()

    def test_handle_message_unknown_type(self, message_handler):
        """Test handling unknown message type"""
        unknown_type = 9999
        data = {"some": "data"}
        message_handler.handle_message(unknown_type, data)
        # verify log warning is recorded
        message_handler.logger.warning.assert_called_once()

    def test_handle_get_users_response_success(self, message_handler):
        """Test handling successful users fetch"""
        update_callback = MagicMock()
        message_handler.set_update_user_list_callback(update_callback)
        
        users_data = [{"id": "1", "username": "user1"}, {"id": "2", "username": "user2"}]
        data = {"code": SUCCESS, "data": {"users": users_data}}
        
        message_handler.handle_get_users_response(data)
        update_callback.assert_called_once_with(users_data)

    def test_handle_get_users_response_failure(self, message_handler):
        """Test handling failed users fetch"""
        data = {"code": -1, "message": "Failed to fetch users"}
        message_handler.handle_get_users_response(data)
        message_handler.logger.error.assert_called_once()

    def test_handle_get_users_response_no_callback(self, message_handler):
        """Test handling get users list when no callback is set"""
        message_handler.on_user_list_update = None
        data = {"code": SUCCESS, "data": {"users": []}}
        message_handler.handle_get_users_response(data)
        message_handler.logger.info.assert_called_once()

    def test_handle_new_message_update(self, message_handler):
        """Test handling new message update"""
        update_callback = MagicMock()
        message_handler.set_new_message_update_callback(update_callback)
        
        data = {"code": SUCCESS}
        message_handler.handle_new_message_update(data)
        update_callback.assert_called_once_with(1)

    def test_handle_unread_messages_success(self, message_handler):
        """Test handling successful unread messages response"""
        message_sent_callback = MagicMock()
        unread_count_callback = MagicMock()
        message_handler.set_message_sent_callback(message_sent_callback)
        message_handler.set_unread_count_callback(unread_count_callback)
        
        data = {"code": SUCCESS, "data": {"count": 5}}
        message_handler.handle_unread_messages(data)
        
        message_sent_callback.assert_called_once_with(-1)
        unread_count_callback.assert_called_once_with(5)

    def test_handle_unread_messages_failure(self, message_handler):
        """Test handling failed unread messages response"""
        error_callback = MagicMock()
        message_handler.set_show_error_callback(error_callback)
        
        error_msg = "Failed to fetch unread messages"
        data = {"code": -1, "message": error_msg}
        message_handler.handle_unread_messages(data)
        
        error_callback.assert_called_once_with(error_msg)

    def test_handle_send_message_response_success(self, message_handler):
        """Test handling successful message send response"""
        message_sent_callback = MagicMock()
        message_handler.set_message_sent_callback(message_sent_callback)
        
        data = {"code": SUCCESS, "data": {}}
        message_handler.handle_send_message_response(data)
        message_sent_callback.assert_called_once_with(-1)

    def test_handle_search_users_response_success(self, message_handler):
        """Test handling successful user search response"""
        search_callback = MagicMock()
        message_handler.set_search_results_callback(search_callback)
        
        users = [{"id": "1", "username": "test"}]
        data = {"code": SUCCESS, "data": {"users": users, "total_pages": 1}}
        message_handler.handle_search_users_response(data)
        search_callback.assert_called_once_with(users, 1)

    def test_handle_recent_chats_response_success(self, message_handler):
        """Test handling successful recent chats response"""
        chats_callback = MagicMock()
        message_handler.set_recent_chats_callback(chats_callback)
        
        chats = [{"id": "1", "name": "chat1"}]
        data = {"code": SUCCESS, "data": {"chats": chats, "total_pages": 1}}
        message_handler.handle_recent_chats_response(data)
        chats_callback.assert_called_once_with(chats, 1)

    def test_handle_recent_chats_response_no_callback(self, message_handler):
        """Test handling recent chats when no callback is set"""
        message_handler.on_recent_chats_update = None
        data = {"code": SUCCESS, "data": {"chats": [], "total_pages": 1}}
        message_handler.handle_recent_chats_response(data)
        message_handler.logger.info.assert_called_once()

    def test_handle_previous_messages_response_success(self, message_handler):
        """Test handling successful previous messages response"""
        messages_callback = MagicMock()
        message_handler.set_previous_messages_callback(messages_callback)
        
        messages = [{"id": "1", "content": "test"}]
        data = {"code": SUCCESS, "data": {"messages": messages, "total_pages": 1}}
        message_handler.handle_previous_messages_response(data)
        messages_callback.assert_called_once_with(messages, 1)

    def test_handle_previous_messages_response_no_callback(self, message_handler):
        """Test handling previous messages when no callback is set"""
        message_handler.on_previous_messages = None
        data = {"code": SUCCESS, "data": {"messages": [], "total_pages": 1}}
        message_handler.handle_previous_messages_response(data)
        # Should not raise any exception

    def test_handle_chat_unread_count_response_success(self, message_handler):
        """Test handling successful chat unread count response"""
        unread_callback = MagicMock()
        message_handler.set_unread_count_callback(unread_callback)
        
        data = {"code": SUCCESS, "data": {"count": 3}}
        message_handler.handle_chat_unread_count_response(data)
        unread_callback.assert_called_once_with(3)

    def test_set_receive_message_callback(self, message_handler):
        """Test setting message receive callback"""
        callback = MagicMock()
        message_handler.set_receive_message_callback(callback)
        assert message_handler.on_message_received == callback

    def test_handle_error_message(self, message_handler):
        """Test handling error message"""
        error_callback = MagicMock()
        message_handler.set_show_error_callback(error_callback)
        
        error_msg = "Test error message"
        data = {"message": error_msg}
        message_handler.handle_error_message(data)
        
        error_callback.assert_called_once_with(error_msg)
        message_handler.logger.error.assert_called_once()

    def test_handle_delete_account_success(self, message_handler):
        """Test handling successful account deletion"""
        delete_window_callback = MagicMock()
        error_callback = MagicMock()
        message_handler.set_close_delete_window_callback(delete_window_callback)
        message_handler.set_show_error_callback(error_callback)
        
        data = {"code": SUCCESS}
        message_handler.handle_delete_account_response(data)
        
        delete_window_callback.assert_called_once()
        error_callback.assert_called_once_with("Account deleted successfully")

    def test_handle_delete_account_failure(self, message_handler):
        """Test handling failed account deletion"""
        error_callback = MagicMock()
        message_handler.set_show_error_callback(error_callback)
        
        error_msg = "Failed to delete account"
        data = {"code": -1, "message": error_msg}
        message_handler.handle_delete_account_response(data)
        
        error_callback.assert_called_once_with(error_msg)

    def test_handle_send_message_response_failure(self, message_handler):
        """Test handling failed message send response"""
        error_callback = MagicMock()
        message_handler.set_show_error_callback(error_callback)
        
        error_msg = "Failed to send message"
        data = {"code": -1, "message": error_msg}
        message_handler.handle_send_message_response(data)
        
        error_callback.assert_called_once_with(error_msg)

class TestUserActionHandler:
    def test_create_account(self, user_action_handler):
        """Test sending account creation request"""
        email = "test@example.com"
        username = "testuser"
        password = "password123"
        
        user_action_handler.create_account(email, username, password)
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once()
        call_args = user_action_handler.send_to_server.call_args[0]
        assert call_args[0] == MSG_CREATE_ACCOUNT_REQUEST
        assert call_args[1]["email"] == email
        assert call_args[1]["username"] == username
        assert "password" in call_args[1]  # password should be hashed

    def test_send_chat_message(self, user_action_handler):
        """Test sending chat message"""
        content = "Hello!"
        recipient_id = "recipient123"
        
        user_action_handler.send_chat_message(content, recipient_id)
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once()
        call_args = user_action_handler.send_to_server.call_args[0]
        assert call_args[0] == MSG_SEND_MESSAGE_REQUEST
        assert call_args[1]["content"] == content
        assert call_args[1]["recipient_id"] == recipient_id
        assert call_args[1]["sender_id"] == "test_user_id"

    def test_request_user_list(self, user_action_handler):
        """Test requesting user list"""
        user_action_handler.request_user_list()
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once_with(
            MSG_GET_USERS_REQUEST,
            {"user_id": "-1"}
        )

    def test_search_users(self, user_action_handler):
        """Test searching users"""
        pattern = "test"
        page = 1
        
        user_action_handler.search_users(pattern, page)
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once()
        call_args = user_action_handler.send_to_server.call_args[0]
        assert call_args[0] == MSG_SEARCH_USERS_REQUEST
        assert call_args[1]["pattern"] == pattern
        assert call_args[1]["page"] == page
        assert call_args[1]["current_user_id"] == "test_user_id"

    def test_request_recent_chats(self, user_action_handler):
        """Test requesting recent chats"""
        page = 2
        
        user_action_handler.request_recent_chats(page)
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once_with(
            MSG_GET_RECENT_CHATS_REQUEST,
            {
                "user_id": "test_user_id",
                "page": page
            }
        )

    def test_request_previous_messages(self, user_action_handler):
        """Test requesting previous messages"""
        other_user_id = "other123"
        page = 3
        
        user_action_handler.request_previous_messages(other_user_id, page)
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once_with(
            MSG_GET_PREVIOUS_MESSAGES_REQUEST,
            {
                "user_id": "test_user_id",
                "other_user_id": other_user_id,
                "page": page
            }
        )

    def test_get_chat_unread_count(self, user_action_handler):
        """Test getting unread message count for a chat"""
        other_user_id = "other123"
        
        user_action_handler.get_chat_unread_count(other_user_id)
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once_with(
            MSG_GET_CHAT_UNREAD_COUNT_REQUEST,
            {
                "user_id": "test_user_id",
                "other_user_id": other_user_id
            }
        )

    def test_get_chat_unread_messages(self, user_action_handler):
        """Test getting unread messages for a chat"""
        other_user_id = "other123"
        num_messages = 5
        
        user_action_handler.get_chat_unread_messages(other_user_id, num_messages)
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once_with(
            MSG_GET_UNREAD_MESSAGES_REQUEST,
            {
                "user_id": "test_user_id",
                "other_user_id": other_user_id,
                "num_messages": num_messages
            }
        )

    def test_delete_messages(self, user_action_handler):
        """Test deleting messages"""
        message_ids = ["msg1", "msg2", "msg3"]
        
        user_action_handler.delete_messages(message_ids)
        
        # verify correct message is sent
        user_action_handler.send_to_server.assert_called_once_with(
            MSG_DELETE_MESSAGE_REQUEST,
            {
                "message_ids": message_ids
            }
        )
