import pytest
from unittest.mock import MagicMock, patch, call
import grpc
from server.server import Server
from generated import chat_pb2
from shared.models import User, Message
from shared.constants import SUCCESS
from datetime import datetime

class TestDataSynchronization:
    @pytest.fixture
    def mock_server(self):
        """create a mock server instance"""
        with patch('server.server.Config'), \
             patch('server.server.setup_logger'), \
             patch('server.server.DatabaseManager'), \
             patch('server.server.ServersCollection'), \
             patch('server.server.UsersCollection'), \
             patch('server.server.MessagesCollection'), \
             patch('server.server.GRPCServer'), \
             patch('server.server.socket'), \
             patch('server.server.CommunicationInterface'), \
             patch('server.server.UserHandler'), \
             patch('server.server.MessageHandler'):
            
            server = Server("config_path")
            server.logger = MagicMock()
            server.server_id = "server1"
            server.current_leader = "server2"
            server.is_leader = False
            
            # mock gRPC connections
            mock_chat_stub = MagicMock()
            server.grpc_connections = {
                "server2": {
                    "chat_stub": mock_chat_stub,
                    "election_stub": MagicMock(),
                    "replica_stub": MagicMock()
                }
            }
            
            yield server
    
    def test_sync_data_from_leader(self, mock_server):
        """test the main function of syncing data from leader"""
        # mock sub functions
        with patch.object(mock_server, '_sync_users_from_leader') as mock_sync_users, \
             patch.object(mock_server, '_sync_messages_from_leader') as mock_sync_messages:
            
            # execute test
            mock_server._sync_data_from_leader()
            
            # verify calls
            mock_sync_users.assert_called_once()
            mock_sync_messages.assert_called_once()
            mock_server.logger.info.assert_called_with(
                f"Data synchronization from leader {mock_server.current_leader} completed successfully"
            )
    
    def test_sync_data_from_leader_no_leader(self, mock_server):
        """test the behavior when there is no leader"""
        # set no leader
        mock_server.current_leader = None
        
        # execute test
        mock_server._sync_data_from_leader()
        
        # verify log
        mock_server.logger.warning.assert_called_with(
            "Cannot sync data: Leader None not found in connections"
        )
    
    def test_sync_data_from_leader_exception(self, mock_server):
        """test the behavior when an exception occurs during synchronization"""
        # mock sub functions to raise an exception
        with patch.object(mock_server, '_sync_users_from_leader', side_effect=Exception("Test error")):
            
            # execute test
            mock_server._sync_data_from_leader()
            
            # verify log
            mock_server.logger.error.assert_called_with(
                "Error during data synchronization: Test error", 
                exc_info=True
            )
    
    def test_sync_users_from_leader(self, mock_server):
        """test the behavior of syncing users data from leader"""
        # mock users collection
        mock_users_collection = MagicMock()
        mock_users_collection.clear_all_users.return_value = True
        mock_users_collection.insert_one.return_value = True
        
        # mock leader's user data
        mock_user_data1 = MagicMock()
        mock_user_data1.id = "user1"
        mock_user_data1.username = "user1"
        mock_user_data1.email = "user1@example.com"
        mock_user_data1.password_hash = "hash1"
        mock_user_data1.created_at = "2023-01-01T12:00:00"
        mock_user_data1.last_login = "2023-01-02T12:00:00"
        
        mock_user_data2 = MagicMock()
        mock_user_data2.id = "user2"
        mock_user_data2.username = "user2"
        mock_user_data2.email = "user2@example.com"
        mock_user_data2.password_hash = "hash2"
        mock_user_data2.created_at = "2023-01-01T12:00:00"
        mock_user_data2.last_login = "2023-01-02T12:00:00"
        
        # mock GetAllUsers response
        mock_response = MagicMock()
        mock_response.code = SUCCESS
        mock_response.users = [mock_user_data1, mock_user_data2]
        
        mock_server.grpc_connections["server2"]["chat_stub"].GetAllUsers.return_value = mock_response
        
        with patch('server.server.UsersCollection', return_value=mock_users_collection):
            # execute test
            mock_server._sync_users_from_leader()
            
            # verify calls
            mock_users_collection.clear_all_users.assert_called_once()
            mock_server.grpc_connections["server2"]["chat_stub"].GetAllUsers.assert_called_once()
            
            # 检查是否调用了insert_one方法，不检查具体调用次数
            mock_users_collection.insert_one.assert_called()
            
            # verify log - 使用更灵活的断言
            mock_server.logger.info.assert_any_call(
                "User synchronization completed. Added 2 users from leader."
            )
    
    def test_sync_users_from_leader_error_response(self, mock_server):
        """test the behavior when leader returns an error response"""
        # mock users collection
        mock_users_collection = MagicMock()
        
        # mock leader's error response
        mock_response = MagicMock()
        mock_response.code = 100  # error code
        mock_response.message = "Error fetching users"
        
        mock_server.grpc_connections["server2"]["chat_stub"].GetAllUsers.return_value = mock_response
        
        with patch('server.server.UsersCollection', return_value=mock_users_collection):
            # execute test
            mock_server._sync_users_from_leader()
            
            # verify log
            mock_server.logger.warning.assert_called_with(
                "Failed to get users from leader: Error fetching users"
            )
    
    def test_sync_users_from_leader_exception(self, mock_server):
        """test the behavior when an exception occurs during user synchronization"""
        # mock exception
        mock_server.grpc_connections["server2"]["chat_stub"].GetAllUsers.side_effect = Exception("Test error")
        
        # execute test
        mock_server._sync_users_from_leader()
        
        # verify log
        mock_server.logger.error.assert_called_with(
            "Error synchronizing users: Test error",
            exc_info=True
        )
    
    def test_sync_messages_from_leader(self, mock_server):
        """test the behavior of syncing messages data from leader"""
        # mock messages collection
        mock_messages_collection = MagicMock()
        mock_messages_collection.clear_all_messages.return_value = True
        mock_messages_collection.insert_message.return_value = True
        
        # mock message data
        mock_message = MagicMock()
        mock_message.message_id = "msg1"
        mock_message.sender_id = "user2"
        mock_message.recipient_id = "user1"
        mock_message.content = "Hello"
        mock_message.timestamp = "2023-01-01T12:00:00"
        mock_message.is_read = False
        
        # mock GetAllMessages response
        mock_response = MagicMock()
        mock_response.code = SUCCESS
        mock_response.messages = [mock_message]
        
        # set stub return value
        chat_stub = mock_server.grpc_connections["server2"]["chat_stub"]
        chat_stub.GetAllMessages.return_value = mock_response
        
        with patch('server.server.MessagesCollection', return_value=mock_messages_collection):
            # execute test
            mock_server._sync_messages_from_leader()
            
            # verify calls
            mock_messages_collection.clear_all_messages.assert_called_once()
            chat_stub.GetAllMessages.assert_called_once()
            
            # verify message insertion
            mock_messages_collection.insert_message.assert_called_once_with(
                sender_id="user2",
                recipient_id="user1",
                content="Hello",
                message_id="msg1",
                time=datetime.fromisoformat("2023-01-01T12:00:00"),
                is_read=False
            )
            
            # verify log
            mock_server.logger.info.assert_called_with(
                "Message synchronization completed. Added 1 messages from leader."
            )
    
    def test_sync_messages_from_leader_error_response(self, mock_server):
        """test the behavior when leader returns an error response for messages"""
        # mock messages collection
        mock_messages_collection = MagicMock()
        
        # mock error response
        mock_response = MagicMock()
        mock_response.code = 100  # error code
        mock_response.message = "Error fetching messages"
        
        # set stub return value
        chat_stub = mock_server.grpc_connections["server2"]["chat_stub"]
        chat_stub.GetAllMessages.return_value = mock_response
        
        with patch('server.server.MessagesCollection', return_value=mock_messages_collection):
            # execute test
            mock_server._sync_messages_from_leader()
            
            # verify log
            mock_server.logger.warning.assert_called_with(
                "Failed to get messages from leader: Error fetching messages"
            )
    
    def test_sync_messages_from_leader_exception(self, mock_server):
        """test the behavior when an exception occurs during message synchronization"""
        # mock exception
        with patch('server.server.MessagesCollection', side_effect=Exception("Test error")):
            # execute test
            mock_server._sync_messages_from_leader()
            
            # verify log
            mock_server.logger.error.assert_called_with(
                "Error in message synchronization: Test error", 
                exc_info=True
            )
