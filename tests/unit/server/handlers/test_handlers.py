import pytest
from datetime import datetime
from server.handlers.message_handler import MessageHandler
from server.handlers.user_handler import UserHandler
from shared.constants import *
from shared.models import User
from database.collections import MessagesCollection

# MessageHandler Tests
class TestMessageHandler:
    @pytest.fixture
    def message_handler(self, mock_db, mock_logger):
        handler = MessageHandler(logger=mock_logger)
        # Directly set mock_db to avoid creating real database connections
        handler.messages = mock_db
        return handler

    def test_send_message_success(self, message_handler):
        """Test successful message sending with valid data"""
        # Prepare test data
        test_data = {
            'sender_id': 'user1',
            'recipient_id': 'user2',
            'content': 'Hello, World!'
        }
        
        # Execute test
        result = message_handler.send_message(test_data)
        
        # Verify result
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert result['data']['sender_id'] == test_data['sender_id']
        assert result['data']['recipient_id'] == test_data['recipient_id']
        assert result['data']['content'] == test_data['content']
        assert 'timestamp' in result['data']
        assert 'message_id' in result['data']

    def test_send_message_failure(self, message_handler):
        """Test message sending failure with invalid empty data"""
        # Prepare incorrect test data
        test_data = {}  # Completely empty data will trigger error
        
        # Execute test
        result = message_handler.send_message(test_data)
        
        # Verify result
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_recent_chats(self, message_handler):
        """Test retrieving recent chats for a user with valid pagination"""
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
        """Test recent chats retrieval failure with missing parameters"""
        test_data = {}  # Missing required parameters
        result = message_handler.get_recent_chats(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_previous_messages(self, message_handler):
        """Test retrieving previous messages between two users with valid data"""
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
        """Test previous messages retrieval failure with missing parameters"""
        test_data = {}  # Missing required parameters
        result = message_handler.get_previous_messages(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_chat_unread_count(self, message_handler):
        """Test getting unread message count between two users"""
        test_data = {
            'user_id': 'user1',
            'other_user_id': 'user2'
        }
        result = message_handler.get_chat_unread_count(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'count' in result['data']

    def test_get_chat_unread_count_error(self, message_handler):
        """Test unread count retrieval failure with missing parameters"""
        test_data = {}  # Missing required parameters
        result = message_handler.get_chat_unread_count(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_chat_unread_messages(self, message_handler):
        """Test retrieving unread messages between two users"""
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
        """Test unread messages retrieval failure with missing parameters"""
        test_data = {}  # Missing required parameters
        result = message_handler.get_chat_unread_messages(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_delete_messages_success(self, message_handler):
        """Test successful deletion of multiple messages"""
        test_data = {
            'message_ids': ['1', '2', '3']
        }
        result = message_handler.delete_messages(test_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK

    def test_delete_messages_error(self, message_handler):
        """Test message deletion failure with missing message IDs"""
        test_data = {}  # Missing required parameters
        result = message_handler.delete_messages(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_get_chat_unread_messages_with_messages(self, message_handler):
        """Test retrieving unread messages with mock message data and read status update"""
        # Prepare test message data
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
        
        # Directly rewrite MockDB method
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

# UserHandler Tests
class TestUserHandler:
    @pytest.fixture
    def user_handler(self, mock_db):
        handler = UserHandler()
        handler.users = mock_db
        return handler

    def test_create_account_success(self, user_handler):
        """Test successful user account creation with valid data"""
        # Prepare test data
        test_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'hashedpassword123'
        }
        
        # Execute test
        result = user_handler.create_account(test_data)
        
        # Verify result
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK

    def test_create_account_user_exists(self, user_handler):
        """Test account creation failure when username already exists"""
        # First create a user
        test_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'hashedpassword123'
        }
        
        # First create account
        user_handler.create_account(test_data)
        
        # Try to create the same user
        result = user_handler.create_account(test_data)
        
        # Verify result
        assert result['code'] == ERROR_USER_EXISTS
        assert result['message'] == MESSAGE_USER_EXISTS

    def test_login_success(self, user_handler):
        """Test successful user login with valid credentials"""
        # First create user
        create_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'hashedpassword123'
        }
        user_handler.create_account(create_data)
        
        # Execute login test
        login_data = {
            'email': create_data['email'],
            'password': create_data['password']
        }
        result = user_handler.login(login_data)
        
        # Verify result
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK
        assert 'user' in result['data']
        assert result['data']['user']['username'] == create_data['username']
        assert result['data']['user']['email'] == create_data['email']

    def test_login_invalid_credentials(self, user_handler):
        """Test login failure with invalid credentials"""
        # Prepare incorrect login data
        login_data = {
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        }
        
        # Execute test
        result = user_handler.login(login_data)
        
        # Verify result
        assert result['code'] == ERROR_INVALID_CREDENTIALS
        assert result['message'] == MESSAGE_INVALID_CREDENTIALS

    def test_get_users(self, user_handler):
        """Test retrieving all users from database"""
        # First create some users
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
        """Test searching users by username pattern with pagination"""
        # First create some users
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
        """Test user search failure with missing search parameters"""
        test_data = {}  # Missing required parameters
        result = user_handler.search_users(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_create_account_invalid_data(self, user_handler):
        """Test account creation failure with invalid empty data"""
        test_data = {}  # Missing required parameters
        result = user_handler.create_account(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_login_missing_data(self, user_handler):
        """Test login failure with missing credentials"""
        test_data = {}  # Missing required parameters
        result = user_handler.login(test_data)
        
        assert result['code'] == ERROR_INVALID_CREDENTIALS
        assert result['message'] == MESSAGE_INVALID_CREDENTIALS

    def test_create_account_missing_fields(self, user_handler):
        """Test account creation failure with each required field missing"""
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
        """Test login failure when database operation fails"""
        # Simulate database error
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
        """Test user search failure with missing required search fields"""
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

    def test_get_users_database_error(self, user_handler):
        """Test user retrieval failure when database operation fails"""
        # Simulate database error
        def mock_get_all_users(*args, **kwargs):
            raise Exception("Database error")
            
        user_handler.users.get_all_users = mock_get_all_users
        
        result = user_handler.get_users({})
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_search_users_database_error(self, user_handler):
        """Test user search failure when database operation fails"""
        # Simulate database error
        def mock_search_users(*args, **kwargs):
            raise Exception("Database error")
            
        user_handler.users.search_users_by_username_paginated = mock_search_users
        
        test_data = {
            'pattern': 'test',
            'current_user_id': 'user1'
        }
        result = user_handler.search_users(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_delete_user_success(self, user_handler):
        """Test successful user deletion with valid credentials"""
        # Create a simulated user object, add _id field
        test_user = User(
            _id='507f1f77bcf86cd799439011',  # Add a valid ObjectId
            username='testuser',
            email='test@example.com',
            password_hash='hashedpassword123',
            created_at=datetime.now()
        )
        
        # Simulate database find_by_email method
        def mock_find_by_email(email):
            if email == test_user.email:
                return test_user
            return None
        user_handler.users.find_by_email = mock_find_by_email
        
        # Simulate database delete_one method
        def mock_delete_one(user_id):
            return True
        user_handler.users.delete_one = mock_delete_one
        
        # Simulate message collection delete_user_messages method
        def mock_delete_user_messages(user_id):
            return True
        user_handler.messages = MessagesCollection()  # Directly set messages attribute on user_handler
        user_handler.messages.delete_user_messages = mock_delete_user_messages
        
        # Execute delete operation
        delete_data = {
            'email': test_user.email,
            'password': test_user.password_hash
        }
        result = user_handler.delete_user(delete_data)
        
        assert result['code'] == SUCCESS
        assert result['message'] == MESSAGE_OK

    def test_delete_user_invalid_credentials(self, user_handler):
        """Test user deletion failure with invalid credentials"""
        delete_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        result = user_handler.delete_user(delete_data)
        
        assert result['code'] == ERROR_INVALID_CREDENTIALS
        assert result['message'] == MESSAGE_INVALID_CREDENTIALS

    def test_delete_user_missing_data(self, user_handler):
        """Test user deletion failure with missing data"""
        test_data = {}  # Missing required parameters
        result = user_handler.delete_user(test_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR

    def test_delete_user_database_error(self, user_handler):
        """Test user deletion failure when database operation fails"""
        # First create a user
        create_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'hashedpassword123'
        }
        user_handler.create_account(create_data)
        
        # Simulate database delete error
        def mock_delete_one(*args, **kwargs):
            raise Exception("Database error")
            
        user_handler.users.delete_one = mock_delete_one
        
        delete_data = {
            'email': create_data['email'],
            'password': create_data['password']
        }
        result = user_handler.delete_user(delete_data)
        
        assert result['code'] == ERROR_SERVER_ERROR
        assert result['message'] == MESSAGE_SERVER_ERROR
