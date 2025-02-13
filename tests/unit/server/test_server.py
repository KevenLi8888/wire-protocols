import pytest
from unittest.mock import MagicMock, patch
from server.server import TCPServer
from shared.constants import *

class TestTCPServer:
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager"""
        with patch('server.server.DatabaseManager') as mock_db_manager:
            # Create a mock database object
            mock_db = MagicMock()
            # Add necessary collections
            mock_db['users'] = MagicMock()
            mock_db['messages'] = MagicMock()
            # Set get_instance().db to return the mock database object
            mock_db_manager.get_instance.return_value.db = mock_db
            yield mock_db_manager

    @pytest.fixture
    def server(self, temp_config_file, mock_db_manager, mock_logger):
        """Create server instance"""
        # Add mock instances for UserHandler and MessageHandler
        with patch('server.server.setup_logger', return_value=mock_logger), \
             patch('server.server.UserHandler') as mock_user_handler, \
             patch('server.server.MessageHandler') as mock_message_handler:
            
            # Create mock handler instances
            mock_user_handler_instance = MagicMock()
            mock_message_handler_instance = MagicMock()
            
            # Set handler constructor to return mock instances
            mock_user_handler.return_value = mock_user_handler_instance
            mock_message_handler.return_value = mock_message_handler_instance
            
            server = TCPServer(temp_config_file)
            return server

    def test_server_initialization(self, server):
        # Verify server initialization
        assert server.host == '127.0.0.1'
        assert server.port == 13570
        assert len(server.clients) == 0
        assert len(server.online_users) == 0
        assert server.message_handlers is not None

    def test_handle_message_invalid_type(self, server, mock_socket):
        # Test handling invalid message type
        invalid_message_type = "INVALID_MESSAGE_TYPE"
        data = {"some": "data"}
        
        response = server.handle_message(invalid_message_type, data, mock_socket)
        
        assert response['code'] == ERROR_INVALID_MESSAGE
        assert response['message'] == MESSAGE_INVALID_MESSAGE

    def test_handle_message_valid_login(self, server, mock_socket):
        # Prepare login data
        login_data = {
            'email': 'test@example.com',
            'password': 'hashedpassword123'
        }
        
        mock_response = {
            'code': SUCCESS,
            'message': MESSAGE_OK,
            'data': {
                'user': {
                    '_id': '123',
                    'username': 'testuser',
                    'email': 'test@example.com'
                }
            }
        }
        
        # Set handler return value directly, not using MagicMock
        server.user_handler.login.return_value = mock_response
        server.communication = MagicMock()
        
        # Execute test
        response = server.handle_message(MSG_LOGIN_REQUEST, login_data, mock_socket)
        
        # Verify result
        assert response == mock_response
        assert mock_socket in server.online_users
        assert server.online_users[mock_socket] == mock_response['data']['user']

    def test_handle_message_send_message(self, server, mock_socket):
        message_data = {
            'sender_id': 'user1',
            'recipient_id': 'user2',
            'content': 'Hello!'
        }
        
        mock_response = {
            'code': SUCCESS,
            'message': MESSAGE_OK,
            'data': {
                'message_id': '1',
                'content': message_data['content'],
                'timestamp': '2024-02-12T10:00:00'
            }
        }
        
        # Set return value directly
        server.message_handler.send_message.return_value = mock_response
        server.communication = MagicMock()
        
        response = server.handle_message(MSG_SEND_MESSAGE_REQUEST, message_data, mock_socket)
        
        assert response == mock_response

    def test_handle_message_login_failure(self, server, mock_socket):
        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        mock_response = {
            'code': ERROR_INVALID_CREDENTIALS,
            'message': MESSAGE_INVALID_CREDENTIALS
        }
        
        # Set return value directly
        server.user_handler.login.return_value = mock_response
        server.communication = MagicMock()
        
        response = server.handle_message(MSG_LOGIN_REQUEST, login_data, mock_socket)
        
        assert response == mock_response
        assert mock_socket not in server.online_users

    def test_handle_message_send_message_to_online_user(self, server, mock_socket):
        recipient_socket = MagicMock()
        server.online_users[recipient_socket] = {
            '_id': 'user2',
            'username': 'recipient'
        }
        
        message_data = {
            'sender_id': 'user1',
            'recipient_id': 'user2',
            'content': 'Hello!'
        }
        
        mock_response = {
            'code': SUCCESS,
            'message': MESSAGE_OK,
            'data': {
                'message_id': '1',
                'content': message_data['content'],
                'timestamp': '2024-02-12T10:00:00'
            }
        }
        
        # Set return value directly
        server.message_handler.send_message.return_value = mock_response
        server.communication = MagicMock()
        
        response = server.handle_message(MSG_SEND_MESSAGE_REQUEST, message_data, mock_socket)
        
        assert response == mock_response
        server.communication.send.assert_any_call(
            MSG_NEW_MESSAGE_UPDATE,
            mock_response['data'],
            recipient_socket
        )

    def test_handle_message_server_error(self, server, mock_socket):
        server.user_handler.login.side_effect = Exception("Unexpected error")
        server.communication = MagicMock()
        
        login_data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        
        expected_response = {
            'code': ERROR_SERVER_ERROR,
            'message': MESSAGE_SERVER_ERROR
        }
        
        response = server.handle_message(MSG_LOGIN_REQUEST, login_data, mock_socket)
        
        assert response == expected_response

    def test_handle_client_normal_disconnect(self, server, mock_socket):
        """Test normal client disconnection"""
        # Set mock data
        server.communication = MagicMock()
        server.communication.receive.side_effect = [(None, None)]  # Simulate client disconnection
        server.clients.append(mock_socket)  # Use append instead of add
        server.online_users[mock_socket] = "test_user"
        
        # Execute test
        server.handle_client(mock_socket, ('127.0.0.1', 12345))
        
        # Verify result
        assert mock_socket not in server.online_users
        assert mock_socket not in server.clients
        mock_socket.close.assert_called_once()

    def test_handle_client_connection_error(self, server, mock_socket):
        """Test connection error handling"""
        # Set mock data
        server.communication = MagicMock()
        server.communication.receive.side_effect = ConnectionError("Connection lost")
        server.clients.append(mock_socket)  # Use append instead of add
        server.online_users[mock_socket] = "test_user"
        
        # Execute test
        server.handle_client(mock_socket, ('127.0.0.1', 12345))
        
        # Verify result
        assert mock_socket not in server.online_users
        assert mock_socket not in server.clients
        mock_socket.close.assert_called_once()

    def test_handle_client_unexpected_error(self, server, mock_socket):
        """Test unexpected error during message handling"""
        # Set mock data
        server.communication = MagicMock()
        # First return data triggers error, second return None indicates client disconnection
        server.communication.receive.side_effect = [
            ({"data": "test"}, "test_type"),
            (None, None)
        ]
        server.handle_message = MagicMock(side_effect=Exception("Unexpected error"))
        server.clients.append(mock_socket)
        
        # Execute test
        server.handle_client(mock_socket, ('127.0.0.1', 12345))
        
        # Verify result
        assert mock_socket not in server.online_users
        assert mock_socket not in server.clients
        mock_socket.close.assert_called_once()
        # Verify error is correctly logged
        server.logger.error.assert_called()

    def test_handle_client_error_response_failure(self, server, mock_socket):
        """Test failure in sending error response"""
        # Set mock data
        server.communication = MagicMock()
        # First return data triggers error, second return None indicates client disconnection
        server.communication.receive.side_effect = [
            ({"data": "test"}, "test_type"),
            (None, None)
        ]
        server.handle_message = MagicMock(side_effect=Exception("Initial error"))
        server.communication.send.side_effect = ConnectionError("Failed to send error response")
        server.clients.append(mock_socket)
        
        # Execute test
        server.handle_client(mock_socket, ('127.0.0.1', 12345))
        
        # Verify result
        assert mock_socket not in server.online_users
        assert mock_socket not in server.clients
        mock_socket.close.assert_called_once()
        # Verify error is correctly logged
        server.logger.error.assert_called()

    def test_server_initialization_with_invalid_config(self, temp_config_file, mock_db_manager, mock_logger):
        """Test server initialization with invalid configuration"""
        with patch('server.server.Config') as mock_config, \
             patch('server.server.setup_logger', return_value=mock_logger), \
             patch('server.server.UserHandler'), \
             patch('server.server.MessageHandler'):
            
            # Mock Config instance
            mock_config_instance = MagicMock()
            mock_config.get_instance.return_value = mock_config_instance
            
            # Mock the get method to raise ValueError specifically for host
            def mock_get(*args):
                if args == ('communication', 'host'):
                    raise ValueError("Invalid config")
                elif args == ('env',):
                    return 'test'
                return None
            
            mock_config_instance.get.side_effect = mock_get
            
            with pytest.raises(RuntimeError) as exc_info:
                TCPServer(temp_config_file)
            
            assert "Server configuration is invalid" in str(exc_info.value)
            # Verify error was logged with the configuration error
            mock_logger.error.assert_called_with(
                "Configuration error: Invalid config",
                exc_info=True
            )

    def test_server_initialization_with_missing_values(self, temp_config_file, mock_db_manager, mock_logger):
        """Test server initialization with missing host and port"""
        with patch('server.server.Config') as mock_config, \
             patch('server.server.setup_logger', return_value=mock_logger), \
             patch('server.server.UserHandler'), \
             patch('server.server.MessageHandler'):
            
            # Mock Config to return None for host and port
            mock_config.get_instance.return_value.get.side_effect = lambda *args: {
                ('communication', 'host'): None,
                ('communication', 'port'): None,
                ('communication', 'protocol_type'): 'json',
                'env': 'test'
            }.get(args, None)
            
            server = TCPServer(temp_config_file)
            
            # Verify default values are set
            assert server.host == '127.0.0.1'
            assert server.port == 13570
            # Verify warnings were logged
            mock_logger.warning.assert_any_call("No host configured, using default: 127.0.0.1")
            mock_logger.warning.assert_any_call("No port configured, using default: 13570")

    def test_server_start_with_database_connection_failure(self, server):
        """Test server start with database connection failure"""
        with patch('server.server.DatabaseManager') as mock_db_manager:
            # Mock database connection failure
            mock_db_manager.get_instance.return_value.db = None
            
            server.start()
            
            # Verify error is logged
            server.logger.error.assert_called_with(
                "Failed to connect to database. Server shutting down.",
                exc_info=True
            )

    def test_server_start_with_socket_bind_error(self, server):
        """Test server start with socket binding failure"""
        # Create a new mock socket instead of trying to modify the existing one
        mock_socket = MagicMock()
        mock_socket.bind.side_effect = Exception("Bind error")
        
        # Replace the server's socket with our mock
        server.server_socket = mock_socket
        
        with pytest.raises(Exception):
            server.start()
        
        # Verify error is logged
        server.logger.error.assert_called()

    def test_server_main_with_database_failure(self, server):
        """Test main method with database connection failure"""
        with patch('server.server.DatabaseManager') as mock_db_manager:
            # Mock database connection failure
            mock_db_manager.get_instance.return_value.db = None
            
            server.main()
            
            # Verify error is logged
            server.logger.error.assert_called_with(
                "Failed to connect to database. Server shutting down.",
                exc_info=True
            )

    def test_server_main_with_keyboard_interrupt(self, server):
        """Test main method with keyboard interrupt"""
        # Create a new mock socket
        mock_socket = MagicMock()
        server.server_socket = mock_socket
        
        # Mock start method to raise KeyboardInterrupt
        server.start = MagicMock(side_effect=KeyboardInterrupt)
        
        server.main()
        
        # Verify shutdown message is logged and socket is closed
        server.logger.info.assert_called_with("Server shutting down...")
        mock_socket.close.assert_called_once()
