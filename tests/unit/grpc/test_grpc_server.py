import pytest
import grpc
from unittest.mock import MagicMock, patch
from server.grpc_server import ChatServiceServicer, GRPCServer
from generated import chat_pb2
from shared.constants import SUCCESS, ERROR_INVALID_CREDENTIALS

class TestChatServiceServicer:
    @pytest.fixture
    def service(self, mock_logger):
        return ChatServiceServicer(mock_logger)

    def test_create_account_success(self, service):
        """Test successful account creation"""  
        # Arrange
        request = chat_pb2.CreateAccountRequest(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        context = MagicMock()
        
        with patch('server.handlers.user_handler.UserHandler.create_account') as mock_create:
            # Set up mock return value
            mock_create.return_value = {'code': SUCCESS, 'message': 'Account created successfully'}
            
            # Act
            response = service.CreateAccount(request, context)
            
            # Assert
            assert response.code == SUCCESS
            mock_create.assert_called_once_with({
                'email': "test@example.com",
                'username': "testuser",
                'password': "password123"
            })

    def test_login_success(self, service):
        """Test successful user login"""
        # Arrange
        request = chat_pb2.LoginRequest(
            email="test@example.com",
            password="password123"
        )
        context = MagicMock()
        
        mock_user_data = {
            '_id': '123',
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        with patch('server.handlers.user_handler.UserHandler.login') as mock_login:
            # Set up mock return value
            mock_login.return_value = {
                'code': SUCCESS,
                'data': {'user': mock_user_data}
            }
            
            # Act
            response = service.Login(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert response.user.id == '123'
            assert response.user.username == 'testuser'
            assert response.user.email == 'test@example.com'

    def test_login_failure(self, service):
        """Test login with invalid credentials"""
        # Arrange
        request = chat_pb2.LoginRequest(
            email="test@example.com",
            password="wrongpassword"
        )
        context = MagicMock()
        
        with patch('server.handlers.user_handler.UserHandler.login') as mock_login:
            # Set up mock return value
            mock_login.return_value = {
                'code': ERROR_INVALID_CREDENTIALS,
                'message': 'Invalid credentials'
            }
            
            # Act
            response = service.Login(request, context)
            
            # Assert
            assert response.code == ERROR_INVALID_CREDENTIALS
            assert response.message == 'Invalid credentials'

    def test_send_message_success(self, service):
        """Test successful message sending"""
        # Arrange
        request = chat_pb2.SendMessageRequest(
            content="Hello!",
            recipient_id="456",
            sender_id="123"
        )
        context = MagicMock()
        
        mock_message_data = {
            'message_id': '789',
            'sender_id': '123',
            'recipient_id': '456',
            'content': 'Hello!',
            'timestamp': '2024-01-01T12:00:00'
        }
        
        with patch('server.handlers.message_handler.MessageHandler.send_message') as mock_send:
            # Set up mock return value
            mock_send.return_value = {
                'code': SUCCESS,
                'data': mock_message_data
            }
            
            # Act
            response = service.SendMessage(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert response.data.message_id == '789'
            assert response.data.content == 'Hello!'

    def test_delete_account_success(self, service):
        """Test successful account deletion"""
        # Arrange
        request = chat_pb2.DeleteAccountRequest(
            email="test@example.com",
            password="password123"
        )
        context = MagicMock()
        
        with patch('server.handlers.user_handler.UserHandler.delete_user') as mock_delete:
            # Set up mock return value
            mock_delete.return_value = {'code': SUCCESS, 'message': 'Account deleted successfully'}
            
            # Act
            response = service.DeleteAccount(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert response.message == 'Account deleted successfully'
            mock_delete.assert_called_once_with({
                'email': "test@example.com",
                'password': "password123"
            })

    def test_search_users_success(self, service):
        """Test successful user search"""
        # Arrange
        request = chat_pb2.SearchUsersRequest(
            pattern="test",
            page=1,
            current_user_id="123"
        )
        context = MagicMock()
        
        mock_users = [
            {'_id': '456', 'username': 'testuser1', 'email': 'test1@example.com'},
            {'_id': '789', 'username': 'testuser2', 'email': 'test2@example.com'}
        ]
        
        with patch('server.handlers.user_handler.UserHandler.search_users') as mock_search:
            # Set up mock return value
            mock_search.return_value = {
                'code': SUCCESS,
                'data': {
                    'users': mock_users,
                    'total_pages': 1
                }
            }
            
            # Act
            response = service.SearchUsers(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert len(response.users) == 2
            assert response.users[0].id == '456'
            assert response.users[0].username == 'testuser1'
            assert response.total_pages == 1

    def test_get_recent_chats_success(self, service):
        """Test successful retrieval of recent chats"""
        # Arrange
        request = chat_pb2.GetRecentChatsRequest(
            user_id="123",
            page=1
        )
        context = MagicMock()
        
        mock_chats = [{
            'user_id': '456',
            'username': 'testuser',
            'unread_count': 2,
            'last_message': {
                'content': 'Hello!',
                'timestamp': '2024-01-01T12:00:00',
                'is_from_me': False
            }
        }]
        
        with patch('server.handlers.message_handler.MessageHandler.get_recent_chats') as mock_get:
            # Set up mock return value
            mock_get.return_value = {
                'code': SUCCESS,
                'data': {
                    'chats': mock_chats,
                    'total_pages': 1
                }
            }
            
            # Act
            response = service.GetRecentChats(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert len(response.chats) == 1
            assert response.chats[0].user_id == '456'
            assert response.chats[0].unread_count == 2
            assert response.chats[0].last_message.content == 'Hello!'

    def test_error_handling(self, service):
        """Test error handling for login"""
        # Arrange
        request = chat_pb2.LoginRequest(
            email="test@example.com",
            password="password123"
        )
        context = MagicMock()
        
        with patch('server.handlers.user_handler.UserHandler.login', side_effect=Exception("Test error")):
            # Act
            response = service.Login(request, context)
            
            # Assert
            assert response == chat_pb2.LoginResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in Login: Test error")

    def test_get_previous_messages_success(self, service):
        """Test successful retrieval of previous messages"""
        # Arrange
        request = chat_pb2.GetPreviousMessagesRequest(
            user_id="123",
            other_user_id="456",
            page=1
        )
        context = MagicMock()
        
        mock_messages = [{
            'message_id': '789',
            'content': 'Hello!',
            'timestamp': '2024-01-01T12:00:00',
            'is_from_me': True,
            'sender': {
                'user_id': '123',
                'username': 'testuser'
            }
        }]
        
        with patch('server.handlers.message_handler.MessageHandler.get_previous_messages') as mock_get:
            mock_get.return_value = {
                'code': SUCCESS,
                'data': {
                    'user_id': '123',
                    'other_user_id': '456',
                    'messages': mock_messages,
                    'total_pages': 1
                }
            }
            
            # Act
            response = service.GetPreviousMessages(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert len(response.messages) == 1
            assert response.messages[0].message_id == '789'
            assert response.messages[0].content == 'Hello!'
            assert response.messages[0].is_from_me == True

    def test_get_chat_unread_count_success(self, service):
        """Test successful retrieval of unread message count"""
        # Arrange
        request = chat_pb2.GetChatUnreadCountRequest(
            user_id="123",
            other_user_id="456"
        )
        context = MagicMock()
        
        with patch('server.handlers.message_handler.MessageHandler.get_chat_unread_count') as mock_get:
            mock_get.return_value = {
                'code': SUCCESS,
                'data': {
                    'user_id': '123',
                    'other_user_id': '456',
                    'count': 5
                }
            }
            
            # Act
            response = service.GetChatUnreadCount(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert response.count == 5
            assert response.user_id == '123'
            assert response.other_user_id == '456'

    def test_get_unread_messages_success(self, service):
        """Test successful retrieval of unread messages"""
        # Arrange
        request = chat_pb2.GetUnreadMessagesRequest(
            user_id="123",
            other_user_id="456",
            num_messages=5
        )
        context = MagicMock()
        
        mock_messages = [{
            'message_id': '789',
            'sender_id': '456',
            'recipient_id': '123',
            'content': 'Hello!',
            'timestamp': '2024-01-01T12:00:00',
            'is_read': False,
            'is_from_me': False
        }]
        
        with patch('server.handlers.message_handler.MessageHandler.get_chat_unread_messages') as mock_get:
            mock_get.return_value = {
                'code': SUCCESS,
                'data': {
                    'messages': mock_messages
                }
            }
            
            # Act
            response = service.GetUnreadMessages(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert len(response.messages) == 1
            assert response.messages[0].message_id == '789'
            assert response.messages[0].content == 'Hello!'
            assert response.messages[0].is_read == False

    def test_delete_messages_success(self, service):
        """Test successful deletion of messages"""
        # Arrange
        request = chat_pb2.DeleteMessagesRequest(
            message_ids=['789', '790']
        )
        context = MagicMock()
        
        with patch('server.handlers.message_handler.MessageHandler.delete_messages') as mock_delete:
            mock_delete.return_value = {
                'code': SUCCESS,
                'message': 'Messages deleted successfully'
            }
            
            # Act
            response = service.DeleteMessages(request, context)
            
            # Assert
            assert response.code == SUCCESS
            assert response.message == 'Messages deleted successfully'
            mock_delete.assert_called_once_with({
                'message_ids': ['789', '790']
            })

    def test_create_account_exception(self, service):
        """Test account creation with exception"""
        # Arrange
        request = chat_pb2.CreateAccountRequest(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        context = MagicMock()
        
        with patch('server.handlers.user_handler.UserHandler.create_account', side_effect=Exception("Test error")):
            # Act
            response = service.CreateAccount(request, context)
            
            # Assert
            assert response == chat_pb2.CreateAccountResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in CreateAccount: Test error")

    def test_delete_account_exception(self, service):
        """Test account deletion with exception"""
        # Arrange
        request = chat_pb2.DeleteAccountRequest(
            email="test@example.com",
            password="password123"
        )
        context = MagicMock()
        
        with patch('server.handlers.user_handler.UserHandler.delete_user', side_effect=Exception("Test error")):
            # Act
            response = service.DeleteAccount(request, context)
            
            # Assert
            assert response == chat_pb2.BasicResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in DeleteAccount: Test error")

    def test_search_users_exception(self, service):
        """Test user search with exception"""
        # Arrange
        request = chat_pb2.SearchUsersRequest(
            pattern="test",
            page=1,
            current_user_id="123"
        )
        context = MagicMock()
        
        with patch('server.handlers.user_handler.UserHandler.search_users', side_effect=Exception("Test error")):
            # Act
            response = service.SearchUsers(request, context)
            
            # Assert
            assert response == chat_pb2.SearchUsersResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in SearchUsers: Test error")

    def test_send_message_exception(self, service):
        """Test message sending with exception"""
        # Arrange
        request = chat_pb2.SendMessageRequest(
            content="Hello!",
            recipient_id="456",
            sender_id="123"
        )
        context = MagicMock()
        
        with patch('server.handlers.message_handler.MessageHandler.send_message', side_effect=Exception("Test error")):
            # Act
            response = service.SendMessage(request, context)
            
            # Assert
            assert response == chat_pb2.SendMessageResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in SendMessage: Test error")

    def test_get_recent_chats_exception(self, service):
        """Test retrieval of recent chats with exception"""
        # Arrange
        request = chat_pb2.GetRecentChatsRequest(
            user_id="123",
            page=1
        )
        context = MagicMock()
        
        with patch('server.handlers.message_handler.MessageHandler.get_recent_chats', side_effect=Exception("Test error")):
            # Act
            response = service.GetRecentChats(request, context)
            
            # Assert
            assert response == chat_pb2.GetRecentChatsResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in GetRecentChats: Test error")

    def test_get_previous_messages_exception(self, service):
        """Test retrieval of previous messages with exception"""
        # Arrange
        request = chat_pb2.GetPreviousMessagesRequest(
            user_id="123",
            other_user_id="456",
            page=1
        )
        context = MagicMock()
        
        with patch('server.handlers.message_handler.MessageHandler.get_previous_messages', side_effect=Exception("Test error")):
            # Act
            response = service.GetPreviousMessages(request, context)
            
            # Assert
            assert response == chat_pb2.GetPreviousMessagesResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in GetPreviousMessages: Test error")

    def test_get_chat_unread_count_exception(self, service):
        """Test retrieval of unread message count with exception"""
        # Arrange
        request = chat_pb2.GetChatUnreadCountRequest(
            user_id="123",
            other_user_id="456"
        )
        context = MagicMock()
        
        with patch('server.handlers.message_handler.MessageHandler.get_chat_unread_count', side_effect=Exception("Test error")):
            # Act
            response = service.GetChatUnreadCount(request, context)
            
            # Assert
            assert response == chat_pb2.GetChatUnreadCountResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in GetChatUnreadCount: Test error")

    def test_get_unread_messages_exception(self, service):
        """Test retrieval of unread messages with exception"""
        # Arrange
        request = chat_pb2.GetUnreadMessagesRequest(
            user_id="123",
            other_user_id="456",
            num_messages=5
        )
        context = MagicMock()
        
        with patch('server.handlers.message_handler.MessageHandler.get_chat_unread_messages', side_effect=Exception("Test error")):
            # Act
            response = service.GetUnreadMessages(request, context)
            
            # Assert
            assert response == chat_pb2.GetUnreadMessagesResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in GetUnreadMessages: Test error")

    def test_delete_messages_exception(self, service):
        """Test deletion of messages with exception"""
        # Arrange
        request = chat_pb2.DeleteMessagesRequest(
            message_ids=['789', '790']
        )
        context = MagicMock()
        
        with patch('server.handlers.message_handler.MessageHandler.delete_messages', side_effect=Exception("Test error")):
            # Act
            response = service.DeleteMessages(request, context)
            
            # Assert
            assert response == chat_pb2.BasicResponse()
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Test error")
            service.logger.error.assert_called_once_with("Error in DeleteMessages: Test error")

class TestGRPCServer:
    def test_server_initialization(self, mock_logger):
        """Test server initialization"""
        # Arrange
        host = 'localhost'
        port = 50051
        
        # Act
        server = GRPCServer(host, port, mock_logger)
        
        # Assert
        assert server.host == host
        assert server.port == port
        assert server.logger == mock_logger

    def test_server_start(self, mock_logger):
        """Test server start"""
        # Arrange
        server = GRPCServer('localhost', 50051, mock_logger)
        
        with patch.object(server.server, 'start') as mock_start:
            with patch.object(server.server, 'add_insecure_port') as mock_add_port:
                # Act
                server.start()
                
                # Assert
                mock_add_port.assert_called_once_with('localhost:50051')
                mock_start.assert_called_once()
                mock_logger.info.assert_called_once_with(
                    'gRPC server started on localhost:50051'
                )

    def test_server_stop(self, mock_logger):
        """Test server stop"""
        # Arrange
        server = GRPCServer('localhost', 50051, mock_logger)
        
        with patch.object(server.server, 'stop') as mock_stop:
            # Act
            server.stop()
            
            # Assert
            mock_stop.assert_called_once_with(None)  # Default is None for grace period
            mock_logger.info.assert_called_with('gRPC server stopped')
