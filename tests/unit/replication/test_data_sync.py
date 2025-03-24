import pytest
from unittest.mock import MagicMock, patch, call
import grpc
from server.server import Server
from generated import chat_pb2
from shared.models import User, Message
from shared.constants import SUCCESS

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
        # mock local users collection
        mock_users_collection = MagicMock()
        mock_users_collection.get_all_users.return_value = [
            User(user_id="user1", username="user1", email="user1@example.com", password_hash="hash1")
        ]
        mock_users_collection.insert_one.return_value = True
        
        # mock leader's user data
        mock_user_data1 = MagicMock()
        mock_user_data1.id = "user1"  # existing user
        mock_user_data1.username = "user1"
        mock_user_data1.email = "user1@example.com"
        mock_user_data1.password_hash = "hash1"
        
        mock_user_data2 = MagicMock()
        mock_user_data2.id = "user2"  # new user
        mock_user_data2.username = "user2"
        mock_user_data2.email = "user2@example.com"
        mock_user_data2.password_hash = "hash2"
        
        mock_response = MagicMock()
        mock_response.code = SUCCESS
        mock_response.users = [mock_user_data1, mock_user_data2]
        
        mock_server.grpc_connections["server2"]["chat_stub"].SearchUsers.return_value = mock_response
        
        with patch('server.server.UsersCollection', return_value=mock_users_collection):
            # execute test
            mock_server._sync_users_from_leader()
            
            # verify calls
            mock_users_collection.get_all_users.assert_called_once()
            mock_server.grpc_connections["server2"]["chat_stub"].SearchUsers.assert_called_once()
            
            # verify only new user is inserted
            mock_users_collection.insert_one.assert_called_once()
            args, _ = mock_users_collection.insert_one.call_args
            assert args[0].user_id == "user2"
            
            # verify log
            mock_server.logger.info.assert_called_with(
                "User synchronization completed. Added 1 new users out of 2 total users."
            )
    
    def test_sync_users_from_leader_error_response(self, mock_server):
        """test the behavior when leader returns an error response"""
        # mock local users collection
        mock_users_collection = MagicMock()
        mock_users_collection.get_all_users.return_value = []
        
        # mock leader's error response
        mock_response = MagicMock()
        mock_response.code = 100  # error code
        mock_response.message = "Error fetching users"
        
        mock_server.grpc_connections["server2"]["chat_stub"].SearchUsers.return_value = mock_response
        
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
        mock_server.grpc_connections["server2"]["chat_stub"].SearchUsers.side_effect = Exception("Test error")
        
        # execute test
        mock_server._sync_users_from_leader()
        
        # verify log
        mock_server.logger.error.assert_called_with(
            "Error synchronizing users: Test error", 
            exc_info=True
        )
    
    def test_sync_messages_from_leader(self, mock_server):
        """test the behavior of syncing messages data from leader"""
        # mock local users collection
        mock_users_collection = MagicMock()
        mock_users_collection.get_all_users.return_value = [
            User(user_id="user1", username="user1", email="user1@example.com", password_hash="hash1")
        ]
        
        # mock messages collection
        mock_messages_collection = MagicMock()
        mock_messages_collection.find_message_by_id.return_value = None  # message not found
        mock_messages_collection.insert_message.return_value = True
        
        # mock recent chats response
        mock_chat = MagicMock()
        mock_chat.user_id = "user2"
        
        mock_recent_chats_response = MagicMock()
        mock_recent_chats_response.code = SUCCESS
        mock_recent_chats_response.chats = [mock_chat]
        
        # mock messages response
        mock_message = MagicMock()
        mock_message.message_id = "msg1"
        mock_message.sender.user_id = "user2"
        mock_message.is_from_me = False
        mock_message.content = "Hello"
        
        mock_messages_response = MagicMock()
        mock_messages_response.code = SUCCESS
        mock_messages_response.messages = [mock_message]
        
        # set stub return values
        chat_stub = mock_server.grpc_connections["server2"]["chat_stub"]
        chat_stub.GetRecentChats.return_value = mock_recent_chats_response
        chat_stub.GetPreviousMessages.return_value = mock_messages_response
        
        with patch('server.server.UsersCollection', return_value=mock_users_collection), \
             patch('server.server.MessagesCollection', return_value=mock_messages_collection):
            
            # execute test
            mock_server._sync_messages_from_leader()
            
            # verify calls
            mock_users_collection.get_all_users.assert_called_once()
            chat_stub.GetRecentChats.assert_called_once()
            chat_stub.GetPreviousMessages.assert_called_once()
            
            # verify message insertion
            mock_messages_collection.insert_message.assert_called_once_with(
                sender_id="user2",
                recipient_id="user1",
                content="Hello",
                message_id="msg1"
            )
            
            # verify log
            mock_server.logger.info.assert_called_with(
                "Message synchronization completed. Added 1 new messages."
            )
    
    def test_sync_messages_from_leader_existing_message(self, mock_server):
        """Test synchronizing an already existing message"""
        # mock local users collection
        mock_users_collection = MagicMock()
        mock_users_collection.get_all_users.return_value = [
            User(user_id="user1", username="user1", email="user1@example.com", password_hash="hash1")
        ]
        
        # mock messages collection - message already exists
        mock_messages_collection = MagicMock()
        mock_messages_collection.find_message_by_id.return_value = Message(
            message_id="msg1", 
            sender_id="user2", 
            recipient_id="user1", 
            content="Hello",
            timestamp="2023-01-01T12:00:00"  # Add the timestamp parameter
        )
        
        # Mock recent chats response
        mock_chat = MagicMock()
        mock_chat.user_id = "user2"
        
        mock_recent_chats_response = MagicMock()
        mock_recent_chats_response.code = SUCCESS
        mock_recent_chats_response.chats = [mock_chat]
        
        # Mock messages response
        mock_message = MagicMock()
        mock_message.message_id = "msg1"
        mock_message.sender.user_id = "user2"
        mock_message.is_from_me = False
        mock_message.content = "Hello"
        
        mock_messages_response = MagicMock()
        mock_messages_response.code = SUCCESS
        mock_messages_response.messages = [mock_message]
        
        # Set stub return values
        chat_stub = mock_server.grpc_connections["server2"]["chat_stub"]
        chat_stub.GetRecentChats.return_value = mock_recent_chats_response
        chat_stub.GetPreviousMessages.return_value = mock_messages_response
        
        with patch('server.server.UsersCollection', return_value=mock_users_collection), \
             patch('server.server.MessagesCollection', return_value=mock_messages_collection):
            
            # Execute test
            mock_server._sync_messages_from_leader()
            
            # Verify no insertion of existing message
            mock_messages_collection.insert_message.assert_not_called()
            
            # Verify log
            mock_server.logger.info.assert_called_with(
                "Message synchronization completed. Added 0 new messages."
            )
    
    def test_sync_messages_from_leader_chat_error(self, mock_server):
        """test the behavior when getting chat list fails"""
        # mock local users collection
        mock_users_collection = MagicMock()
        mock_users_collection.get_all_users.return_value = [
            User(user_id="user1", username="user1", email="user1@example.com", password_hash="hash1")
        ]
        
        # mock recent chats response error
        mock_recent_chats_response = MagicMock()
        mock_recent_chats_response.code = 100  # error code
        mock_recent_chats_response.message = "Error fetching chats"
        
        # set stub return values
        chat_stub = mock_server.grpc_connections["server2"]["chat_stub"]
        chat_stub.GetRecentChats.return_value = mock_recent_chats_response
        
        with patch('server.server.UsersCollection', return_value=mock_users_collection):
            # execute test
            mock_server._sync_messages_from_leader()
            
            # verify log
            mock_server.logger.warning.assert_called_with(
                "Failed to get recent chats for user user1: Error fetching chats"
            )
    
    def test_sync_messages_from_leader_messages_error(self, mock_server):
        """test the behavior when getting message list fails"""
        # mock local users collection
        mock_users_collection = MagicMock()
        mock_users_collection.get_all_users.return_value = [
            User(user_id="user1", username="user1", email="user1@example.com", password_hash="hash1")
        ]
        
        # mock recent chats response
        mock_chat = MagicMock()
        mock_chat.user_id = "user2"
        
        mock_recent_chats_response = MagicMock()
        mock_recent_chats_response.code = SUCCESS
        mock_recent_chats_response.chats = [mock_chat]
        
        # mock messages response error
        mock_messages_response = MagicMock()
        mock_messages_response.code = 100  # error code
        mock_messages_response.message = "Error fetching messages"
        
        # set stub return values
        chat_stub = mock_server.grpc_connections["server2"]["chat_stub"]
        chat_stub.GetRecentChats.return_value = mock_recent_chats_response
        chat_stub.GetPreviousMessages.return_value = mock_messages_response
        
        with patch('server.server.UsersCollection', return_value=mock_users_collection):
            # execute test
            mock_server._sync_messages_from_leader()
            
            # verify log
            mock_server.logger.warning.assert_called_with(
                "Failed to get messages for user user1 with user2: Error fetching messages"
            )
    
    def test_sync_messages_from_leader_exception(self, mock_server):
        """test the behavior when an exception occurs during message synchronization"""
        # mock exception
        with patch('server.server.UsersCollection', side_effect=Exception("Test error")):
            # execute test
            mock_server._sync_messages_from_leader()
            
            # verify log
            mock_server.logger.error.assert_called_with(
                "Error in message synchronization: Test error", 
                exc_info=True
            )
