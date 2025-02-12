import pytest
from unittest.mock import MagicMock, patch
from client.handlers.message_handler import MessageHandler
from client.handlers.user_action_handler import UserActionHandler
from shared.constants import *

@pytest.fixture
def message_handler():
    """创建MessageHandler实例的fixture"""
    logger = MagicMock()
    return MessageHandler(logger)

@pytest.fixture
def user_action_handler():
    """创建UserActionHandler实例的fixture"""
    send_message_func = MagicMock()
    return UserActionHandler(send_message_func, current_user_id="test_user_id")

# 移除全局fixture
# @pytest.fixture(autouse=True)
# def mock_database_manager():
#     with patch('server.server.DatabaseManager') as mock_manager:
#         yield mock_manager

class TestMessageHandler:
    def test_handle_create_account_success(self, message_handler):
        """测试成功创建账户的处理"""
        # 设置回调
        close_callback = MagicMock()
        message_handler.set_close_register_window_callback(close_callback)
        
        # 模拟成功响应
        data = {"code": SUCCESS, "message": "Account created"}
        message_handler.handle_create_account_response(data)
        
        # 验证回调被调用
        close_callback.assert_called_once()

    def test_handle_create_account_failure(self, message_handler):
        """测试创建账户失败的处理"""
        # 设置回调
        error_callback = MagicMock()
        message_handler.set_show_error_callback(error_callback)
        
        # 模拟失败响应
        error_msg = "Email already exists"
        data = {"code": -1, "message": error_msg}
        message_handler.handle_create_account_response(data)
        
        # 验证错误回调被调用
        error_callback.assert_called_once_with(error_msg)

    def test_handle_login_success(self, message_handler):
        """测试成功登录的处理"""
        # 设置回调
        login_success = MagicMock()
        close_window = MagicMock()
        user_data_update = MagicMock()
        
        message_handler.set_login_success_callback(login_success)
        message_handler.set_close_login_window_callback(close_window)
        message_handler.set_current_user_callback(user_data_update)
        
        # 模拟成功登录响应
        user_data = {"id": "123", "username": "test_user"}
        data = {
            "code": SUCCESS,
            "data": {"user": user_data}
        }
        message_handler.handle_login_response(data)
        
        # 验证所有回调被正确调用
        login_success.assert_called_once()
        close_window.assert_called_once()
        user_data_update.assert_called_once_with(user_data)

    def test_handle_message_unknown_type(self, message_handler):
        """测试处理未知消息类型"""
        unknown_type = 9999
        data = {"some": "data"}
        message_handler.handle_message(unknown_type, data)
        # 验证日志警告被记录
        message_handler.logger.warning.assert_called_once()

class TestUserActionHandler:
    def test_create_account(self, user_action_handler):
        """测试发送创建账户请求"""
        email = "test@example.com"
        username = "testuser"
        password = "password123"
        
        user_action_handler.create_account(email, username, password)
        
        # 验证发送了正确的消息
        user_action_handler.send_to_server.assert_called_once()
        call_args = user_action_handler.send_to_server.call_args[0]
        assert call_args[0] == MSG_CREATE_ACCOUNT_REQUEST
        assert call_args[1]["email"] == email
        assert call_args[1]["username"] == username
        assert "password" in call_args[1]  # 密码应该被哈希

    def test_send_chat_message(self, user_action_handler):
        """测试发送聊天消息"""
        content = "Hello!"
        recipient_id = "recipient123"
        
        user_action_handler.send_chat_message(content, recipient_id)
        
        # 验证发送了正确的消息
        user_action_handler.send_to_server.assert_called_once()
        call_args = user_action_handler.send_to_server.call_args[0]
        assert call_args[0] == MSG_SEND_MESSAGE_REQUEST
        assert call_args[1]["content"] == content
        assert call_args[1]["recipient_id"] == recipient_id
        assert call_args[1]["sender_id"] == "test_user_id"

    def test_request_user_list(self, user_action_handler):
        """测试请求用户列表"""
        user_action_handler.request_user_list()
        
        # 验证发送了正确的消息
        user_action_handler.send_to_server.assert_called_once_with(
            MSG_GET_USERS_REQUEST,
            {"user_id": "-1"}
        )

    def test_search_users(self, user_action_handler):
        """测试搜索用户"""
        pattern = "test"
        page = 1
        
        user_action_handler.search_users(pattern, page)
        
        # 验证发送了正确的消息
        user_action_handler.send_to_server.assert_called_once()
        call_args = user_action_handler.send_to_server.call_args[0]
        assert call_args[0] == MSG_SEARCH_USERS_REQUEST
        assert call_args[1]["pattern"] == pattern
        assert call_args[1]["page"] == page
        assert call_args[1]["current_user_id"] == "test_user_id"
