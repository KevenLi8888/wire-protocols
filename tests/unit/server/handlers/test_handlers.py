import pytest
from datetime import datetime
from server.handlers.message_handler import MessageHandler
from server.handlers.user_handler import UserHandler
from shared.constants import *
from shared.models import User

# MessageHandler 测试
class TestMessageHandler:
    @pytest.fixture
    def message_handler(self, mock_db, mock_logger):
        handler = MessageHandler(logger=mock_logger)
        # 直接设置 mock_db，避免创建真实的数据库连接
        handler.messages = mock_db
        return handler

    def test_send_message_success(self, message_handler):
        # 准备测试数据
        test_data = {
            'sender_id': 'user1',
            'recipient_id': 'user2',
            'content': 'Hello, World!'
        }
        
        # 执行测试
        result = message_handler.send_message(test_data)
        
        # 验证结果
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert result['data']['sender_id'] == test_data['sender_id']
        assert result['data']['recipient_id'] == test_data['recipient_id']
        assert result['data']['content'] == test_data['content']
        assert 'timestamp' in result['data']
        assert 'message_id' in result['data']

    def test_send_message_failure(self, message_handler):
        # 准备错误的测试数据
        test_data = {}  # 完全空的数据会触发错误
        
        # 执行测试
        result = message_handler.send_message(test_data)
        
        # 验证结果
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_recent_chats(self, message_handler):
        test_data = {
            'user_id': 'user1',
            'page': 1
        }
        result = message_handler.get_recent_chats(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'chats' in result['data']
        assert 'total_pages' in result['data']

    def test_get_recent_chats_error(self, message_handler):
        test_data = {}  # 缺少必要参数
        result = message_handler.get_recent_chats(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_previous_messages(self, message_handler):
        test_data = {
            'user_id': 'user1',
            'other_user_id': 'user2',
            'page': 1
        }
        result = message_handler.get_previous_messages(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'messages' in result['data']
        assert 'total_pages' in result['data']

    def test_get_previous_messages_error(self, message_handler):
        test_data = {}  # 缺少必要参数
        result = message_handler.get_previous_messages(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_chat_unread_count(self, message_handler):
        test_data = {
            'user_id': 'user1',
            'other_user_id': 'user2'
        }
        result = message_handler.get_chat_unread_count(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'count' in result['data']

    def test_get_chat_unread_count_error(self, message_handler):
        test_data = {}  # 缺少必要参数
        result = message_handler.get_chat_unread_count(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_chat_unread_messages(self, message_handler):
        test_data = {
            'user_id': 'user1',
            'other_user_id': 'user2',
            'num_messages': 10
        }
        result = message_handler.get_chat_unread_messages(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'messages' in result['data']

    def test_get_chat_unread_messages_error(self, message_handler):
        test_data = {}  # 缺少必要参数
        result = message_handler.get_chat_unread_messages(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_delete_messages_success(self, message_handler):
        test_data = {
            'message_ids': ['1', '2', '3']
        }
        result = message_handler.delete_messages(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK

    def test_delete_messages_error(self, message_handler):
        test_data = {}  # 缺少必要参数
        result = message_handler.delete_messages(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_chat_unread_messages_with_messages(self, message_handler):
        # 准备测试消息数据
        test_messages = [
            {
                '_id': '1',
                'sender_id': 'user2',
                'recipient_id': 'user1',
                'content': 'Test message',
                'timestamp': datetime.now(),
                'is_read': False
            }
        ]
        
        # 直接重写 MockDB 的方法
        def mock_get_unread_messages(*args, **kwargs):
            return test_messages
            
        def mock_mark_as_read(*args, **kwargs):
            return True
            
        message_handler.messages.get_unread_messages = mock_get_unread_messages
        message_handler.messages.mark_as_read = mock_mark_as_read
        
        test_data = {
            'user_id': 'user1',
            'other_user_id': 'user2',
            'num_messages': 10
        }
        result = message_handler.get_chat_unread_messages(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert len(result['data']['messages']) == 1

# UserHandler 测试
class TestUserHandler:
    @pytest.fixture
    def user_handler(self, mock_db):
        handler = UserHandler()
        handler.users = mock_db
        return handler

    def test_create_account_success(self, user_handler):
        # 准备测试数据
        test_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'hashedpassword123'
        }
        
        # 执行测试
        result = user_handler.create_account(test_data)
        
        # 验证结果
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK

    def test_create_account_user_exists(self, user_handler):
        # 先创建一个用户
        test_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'hashedpassword123'
        }
        
        # 先创建账户
        user_handler.create_account(test_data)
        
        # 尝试创建同样的用户
        result = user_handler.create_account(test_data)
        
        # 验证结果
        assert result['code'] == ERROR_USER_EXISTS
        assert result['message'] == MESSAGE_USER_EXISTS

    def test_login_success(self, user_handler):
        # 先创建用户
        create_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'hashedpassword123'
        }
        user_handler.create_account(create_data)
        
        # 执行登录测试
        login_data = {
            'email': create_data['email'],
            'password': create_data['password']
        }
        result = user_handler.login(login_data)
        
        # 验证结果
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'user' in result['data']
        assert result['data']['user']['username'] == create_data['username']
        assert result['data']['user']['email'] == create_data['email']

    def test_login_invalid_credentials(self, user_handler):
        # 准备错误的登录数据
        login_data = {
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        }
        
        # 执行测试
        result = user_handler.login(login_data)
        
        # 验证结果
        assert result['code'] == ERROR_INVALID_CREDENTIALS
        assert result['message'] == MESSAGE_INVALID_CREDENTIALS

    def test_get_users(self, user_handler):
        # 先创建一些用户
        user_handler.create_account({
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'password1'
        })
        user_handler.create_account({
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'password2'
        })
        
        result = user_handler.get_users({})
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'users' in result['data']
        assert len(result['data']['users']) >= 2

    def test_search_users(self, user_handler):
        # 先创建一些用户
        user_handler.create_account({
            'username': 'testuser1',
            'email': 'test1@example.com',
            'password': 'password1'
        })
        user_handler.create_account({
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'password2'
        })
        
        test_data = {
            'pattern': 'test',
            'page': 1,
            'current_user_id': 'some_id'
        }
        result = user_handler.search_users(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'users' in result['data']
        assert 'total_pages' in result['data']

    def test_search_users_error(self, user_handler):
        test_data = {}  # 缺少必要参数
        result = user_handler.search_users(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_create_account_invalid_data(self, user_handler):
        test_data = {}  # 缺少必要参数
        result = user_handler.create_account(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_login_missing_data(self, user_handler):
        test_data = {}  # 缺少必要参数
        result = user_handler.login(test_data)
        
        assert result['code'] == ERROR_INVALID_CREDENTIALS
        assert result['message'] == MESSAGE_INVALID_CREDENTIALS

    def test_create_account_missing_fields(self, user_handler):
        # Test each required field missing
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            test_data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123'
            }
            del test_data[field]
            
            result = user_handler.create_account(test_data)
            assert result['code'] == ERROR_SERVER_ERROR
            assert result['message'] == MESSAGE_SERVER_ERROR

    def test_login_database_error(self, user_handler):
        # 模拟数据库错误
        def mock_find_by_email(*args, **kwargs):
            raise Exception("Database error")
            
        user_handler.users.find_by_email = mock_find_by_email
        
        test_data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        
        result = user_handler.login(test_data)
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR


    def test_search_users_missing_required_fields(self, user_handler):
        # Test with missing pattern
        test_data = {
            'current_user_id': 'user1'
        }
        result = user_handler.search_users(test_data)
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

        # Test with missing current_user_id
        test_data = {
            'pattern': 'test'
        }
        result = user_handler.search_users(test_data)
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR
