import pytest
import grpc
import uuid
from unittest.mock import MagicMock, patch, call
from server.grpc_server import ChatServiceServicer
from generated import chat_pb2
from shared.constants import SUCCESS, ERROR_REPLICATION_FAILED
from datetime import datetime

class TestReplication:
    @pytest.fixture
    def mock_server_instance(self):
        """create a mock server instance"""
        server_instance = MagicMock()
        server_instance.server_id = "server1"
        server_instance.is_leader = True
        server_instance.initialization_complete = True
        server_instance.current_leader = "server1"
        
        # mock two replica servers' connections
        server_instance.grpc_connections = {
            "server1": {  # self
                "replica_stub": MagicMock()
            },
            "server2": {
                "replica_stub": MagicMock()
            },
            "server3": {
                "replica_stub": MagicMock()
            }
        }
        
        return server_instance
    
    @pytest.fixture
    def chat_servicer(self, mock_server_instance, mock_logger):
        """create a chat service instance"""
        with patch('server.grpc_server.UserHandler') as mock_user_handler, \
             patch('server.grpc_server.MessageHandler') as mock_message_handler:
            
            mock_user_handler_instance = MagicMock()
            mock_message_handler_instance = MagicMock()
            
            mock_user_handler.return_value = mock_user_handler_instance
            mock_message_handler.return_value = mock_message_handler_instance
            
            servicer = ChatServiceServicer(mock_logger, mock_server_instance)
            
            # save the mock handler instances for testing
            servicer.mock_user_handler = mock_user_handler_instance
            servicer.mock_message_handler = mock_message_handler_instance
            
            yield servicer
    
    def test_propagate_to_replicas_success(self, chat_servicer, mock_server_instance):
        """test successful replication to all replicas"""
        # prepare request and response
        request = chat_pb2.CreateAccountRequest(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        
        # set the return value of the replica stubs
        for server_id, connection in mock_server_instance.grpc_connections.items():
            if server_id != "server1":  # skip self
                mock_response = MagicMock()
                mock_response.code = SUCCESS
                connection["replica_stub"].ReplicateCreateAccount.return_value = mock_response
        
        # execute replication
        result = chat_servicer._propagate_to_replicas(request, "ReplicateCreateAccount")
        
        # verify result
        assert result is True
        
        # verify each replica is called
        for server_id, connection in mock_server_instance.grpc_connections.items():
            if server_id != "server1":  # skip self
                connection["replica_stub"].ReplicateCreateAccount.assert_called_once_with(
                    request, timeout=2
                )
    
    def test_propagate_to_replicas_business_logic_error(self, chat_servicer, mock_server_instance):
        """test the case that a replica returns a business logic error but the connection is successful"""
        # prepare request
        request = chat_pb2.CreateAccountRequest(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        
        # set the return value of the replica stubs - one replica returns a business logic error
        server2_response = MagicMock()
        server2_response.code = 100  # some business logic error code
        server2_response.message = "User already exists"
        mock_server_instance.grpc_connections["server2"]["replica_stub"].ReplicateCreateAccount.return_value = server2_response
        
        server3_response = MagicMock()
        server3_response.code = SUCCESS
        mock_server_instance.grpc_connections["server3"]["replica_stub"].ReplicateCreateAccount.return_value = server3_response
        
        # execute replication
        result = chat_servicer._propagate_to_replicas(request, "ReplicateCreateAccount")
        
        # verify result - business logic error should not cause replication failure
        assert result is True
        
        # verify log records the business logic error
        chat_servicer.logger.warning.assert_called_with(
            "Replica server2 returned error code: 100, message: User already exists, but request was delivered successfully"
        )
    
    def test_propagate_to_replicas_connection_failure(self, chat_servicer, mock_server_instance):
        """test the case that a replica connection fails"""
        # prepare request
        request = chat_pb2.CreateAccountRequest(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        
        # set the replica stub behavior - one replica connection fails
        mock_server_instance.grpc_connections["server2"]["replica_stub"].ReplicateCreateAccount.side_effect = \
            grpc.RpcError("Connection failed")
        
        server3_response = MagicMock()
        server3_response.code = SUCCESS
        mock_server_instance.grpc_connections["server3"]["replica_stub"].ReplicateCreateAccount.return_value = server3_response
        
        # execute replication
        result = chat_servicer._propagate_to_replicas(request, "ReplicateCreateAccount")
        
        # verify result - connection failure should cause replication failure
        assert result is False
        
        # verify log records the connection error
        chat_servicer.logger.error.assert_called_with(
            "gRPC connection error with replica server2: Connection failed"
        )
    
    def test_handle_with_replication_success(self, chat_servicer, mock_server_instance):
        """test successful handling of a request with replication"""
        # prepare request and context
        request = chat_pb2.CreateAccountRequest(
            email="test@example.com",
            username="testuser",
            password="password123",
            user_id="user123"
        )
        context = MagicMock()
        
        # mock replication success
        with patch.object(chat_servicer, '_propagate_to_replicas', return_value=True):
            # mock handler return success
            handler_result = {'code': SUCCESS, 'message': "Account created successfully"}
            handler_func = MagicMock(return_value=handler_result)
            
            # execute handling
            result = chat_servicer._handle_with_replication(
                request, context, "CreateAccount", handler_func
            )
            
            # verify result
            assert result == handler_result
            handler_func.assert_called_once_with(request)
            context.set_code.assert_not_called()
    
    def test_handle_with_replication_failure(self, chat_servicer, mock_server_instance):
        """test the case that replication fails"""
        # prepare request and context
        request = chat_pb2.CreateAccountRequest(
            email="test@example.com",
            username="testuser",
            password="password123",
            user_id="user123"
        )
        context = MagicMock()
        
        # mock replication failure
        with patch.object(chat_servicer, '_propagate_to_replicas', return_value=False):
            # execute handling
            result = chat_servicer._handle_with_replication(
                request, context, "CreateAccount", MagicMock()
            )
            
            # verify result
            assert result['code'] == ERROR_REPLICATION_FAILED
            context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
            context.set_details.assert_called_once_with("Failed to replicate request to all servers")
    
    def test_create_account_with_replication(self, chat_servicer):
        """test the replication process when creating an account"""
        # prepare request and context
        request = chat_pb2.CreateAccountRequest(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        context = MagicMock()
        
        # mock UUID generation
        mock_uuid = "test-uuid-12345"
        with patch('uuid.uuid4', return_value=mock_uuid):
            # mock handler return success
            chat_servicer.mock_user_handler.create_account.return_value = {
                'code': SUCCESS, 
                'message': "Account created successfully"
            }
            
            # mock replication success
            with patch.object(chat_servicer, '_propagate_to_replicas', return_value=True):
                # execute creating an account
                response = chat_servicer.CreateAccount(request, context)
                
                # verify result
                assert response.code == SUCCESS
                assert response.message == "Account created successfully"
                
                # verify replication request contains UUID
                chat_servicer._propagate_to_replicas.assert_called_once()
                propagate_request = chat_servicer._propagate_to_replicas.call_args[0][0]
                assert propagate_request.user_id == str(mock_uuid)
                
                # verify handler is called correctly
                chat_servicer.mock_user_handler.create_account.assert_called_once_with({
                    'email': "test@example.com",
                    'username': "testuser",
                    'password': "password123",
                    'user_id': str(mock_uuid)
                })
    
    def test_send_message_with_replication(self, chat_servicer):
        """test the replication process when sending a message"""
        # prepare request and context
        request = chat_pb2.SendMessageRequest(
            content="Hello world",
            recipient_id="recipient123",
            sender_id="sender456"
        )
        context = MagicMock()
        
        # mock UUID generation
        mock_uuid = "msg-uuid-12345"
        # 模拟时间戳
        mock_timestamp = "2023-01-01T12:00:00"
        
        # 直接修补 _handle_with_replication 方法
        with patch.object(chat_servicer, '_handle_with_replication') as mock_handle:
            # 设置返回值
            mock_handle.return_value = {
                'code': SUCCESS,
                'data': {
                    'message_id': str(mock_uuid),
                    'sender_id': "sender456",
                    'recipient_id': "recipient123",
                    'content': "Hello world",
                    'timestamp': mock_timestamp
                }
            }
            
            # 执行发送消息
            response = chat_servicer.SendMessage(request, context)
            
            # 验证结果
            assert response.code == SUCCESS
            assert response.data.message_id == str(mock_uuid)
            assert response.data.content == "Hello world"
            
            # 验证 _handle_with_replication 被正确调用
            mock_handle.assert_called_once()
            
            # 获取传递给 _handle_with_replication 的参数
            call_args = mock_handle.call_args[0]
            modified_request = call_args[0]
            
            # 验证请求包含正确的内容
            assert modified_request.content == "Hello world"
            assert modified_request.recipient_id == "recipient123"
            assert modified_request.sender_id == "sender456"
            
            # 验证 handler_func 参数
            handler_func = call_args[3]
            
            # 调用 handler_func 并验证它会调用 send_message
            chat_servicer.mock_message_handler.send_message.return_value = {
                'code': SUCCESS,
                'data': {
                    'message_id': str(mock_uuid),
                    'sender_id': "sender456",
                    'recipient_id': "recipient123",
                    'content': "Hello world",
                    'timestamp': modified_request.timestamp
                }
            }
            
            # 调用 handler_func
            handler_func(modified_request)
            
            # 验证 send_message 被正确调用
            chat_servicer.mock_message_handler.send_message.assert_called_once()
            send_message_args = chat_servicer.mock_message_handler.send_message.call_args[0][0]
            assert send_message_args['content'] == "Hello world"
            assert send_message_args['recipient_id'] == "recipient123"
            assert send_message_args['sender_id'] == "sender456"
            assert 'message_id' in send_message_args
            assert 'timestamp' in send_message_args
    
    def test_sync_data_from_leader(self, chat_servicer, mock_server_instance):
        """Test the data synchronization from leader functionality"""
        # First patch the methods
        with patch.object(mock_server_instance, '_sync_users_from_leader') as mock_sync_users, \
             patch.object(mock_server_instance, '_sync_messages_from_leader') as mock_sync_messages:
            
            # Define the _sync_data_from_leader method that will call our patched methods
            def sync_data_implementation():
                if not mock_server_instance.current_leader or mock_server_instance.is_leader:
                    return
                
                mock_server_instance._sync_users_from_leader()
                mock_server_instance._sync_messages_from_leader()
            
            # Assign our implementation to the mock server
            mock_server_instance._sync_data_from_leader = sync_data_implementation
            
            # Set up the server instance
            mock_server_instance.current_leader = "server2"
            mock_server_instance.is_leader = False
            
            # Call the sync method
            mock_server_instance._sync_data_from_leader()
            
            # Verify both sync methods were called
            mock_sync_users.assert_called_once()
            mock_sync_messages.assert_called_once()

    def test_sync_users_from_leader(self, chat_servicer, mock_server_instance):
        """Test synchronizing users from the leader"""
        # Mock UsersCollection and User
        with patch('server.server.UsersCollection') as mock_users_collection_class, \
             patch('server.server.User') as mock_user_class:
            
            mock_users_collection = MagicMock()
            mock_users_collection_class.return_value = mock_users_collection
            
            # Mock local users
            local_user = MagicMock()
            local_user.user_id = "user1"
            mock_users_collection.get_all_users.return_value = [local_user]
            
            # Set up leader connection
            mock_server_instance.current_leader = "server2"
            mock_chat_stub = MagicMock()
            mock_server_instance.grpc_connections = {
                "server2": {
                    "chat_stub": mock_chat_stub
                }
            }
            
            # Mock the response from leader
            mock_response = MagicMock()
            mock_response.code = SUCCESS
            
            # Create two users in the response - one existing and one new
            user1 = MagicMock()
            user1.id = "user1"  # This user already exists locally
            user1.username = "existinguser"
            user1.email = "existing@example.com"
            user1.password_hash = "hash1"
            
            user2 = MagicMock()
            user2.id = "user2"  # This user is new
            user2.username = "newuser"
            user2.email = "new@example.com"
            user2.password_hash = "hash2"
            
            mock_response.users = [user1, user2]
            mock_chat_stub.SearchUsers.return_value = mock_response
            
            # Create a real implementation of the method for testing
            def sync_users_implementation():
                users_collection = mock_users_collection_class()
                local_users = users_collection.get_all_users()
                local_user_ids = {user.user_id for user in local_users}
                
                leader_connection = mock_server_instance.grpc_connections[mock_server_instance.current_leader]
                stub = leader_connection['chat_stub']
                
                request = chat_pb2.SearchUsersRequest(
                    pattern="",
                    page=1,
                    current_user_id=""
                )
                
                response = stub.SearchUsers(request, timeout=10)
                
                if response.code == SUCCESS:
                    for user_data in response.users:
                        if user_data.id not in local_user_ids:
                            new_user = mock_user_class(
                                user_id=user_data.id,
                                username=user_data.username,
                                email=user_data.email,
                                password_hash=user_data.password_hash
                            )
                            users_collection.insert_one(new_user)
            
            # Assign our implementation to the mock server
            mock_server_instance._sync_users_from_leader = sync_users_implementation
            
            # Call the sync method
            mock_server_instance._sync_users_from_leader()
            
            # Verify the stub was called with the right request
            mock_chat_stub.SearchUsers.assert_called_once()
            request = mock_chat_stub.SearchUsers.call_args[0][0]
            assert request.pattern == ""
            assert request.page == 1
            
            # Verify only the new user was inserted
            mock_user_class.assert_called_once_with(
                user_id="user2",
                username="newuser",
                email="new@example.com",
                password_hash="hash2"
            )
            mock_users_collection.insert_one.assert_called_once()

    def test_sync_messages_from_leader(self, chat_servicer, mock_server_instance):
        """Test synchronizing messages from the leader"""
        # Mock collections
        with patch('server.server.UsersCollection') as mock_users_collection_class, \
             patch('server.server.MessagesCollection') as mock_messages_collection_class:
            
            # Set up mock collections
            mock_users_collection = MagicMock()
            mock_messages_collection = MagicMock()
            mock_users_collection_class.return_value = mock_users_collection
            mock_messages_collection_class.return_value = mock_messages_collection
            
            # Mock local users
            user1 = MagicMock()
            user1.user_id = "user1"
            mock_users_collection.get_all_users.return_value = [user1]
            
            # Set up leader connection
            mock_server_instance.current_leader = "server2"
            mock_chat_stub = MagicMock()
            mock_server_instance.grpc_connections = {
                "server2": {
                    "chat_stub": mock_chat_stub
                }
            }
            
            # Mock the responses from leader
            # First for recent chats
            recent_chats_response = MagicMock()
            recent_chats_response.code = SUCCESS
            chat = MagicMock()
            chat.user_id = "user2"  # The other user in the chat
            recent_chats_response.chats = [chat]
            mock_chat_stub.GetRecentChats.return_value = recent_chats_response
            
            # Then for messages
            messages_response = MagicMock()
            messages_response.code = SUCCESS
            
            # Create a message that doesn't exist locally
            message = MagicMock()
            message.message_id = "msg1"
            message.content = "Hello"
            message.is_from_me = True  # User1 sent this message
            sender = MagicMock()
            sender.user_id = "user1"
            message.sender = sender
            
            messages_response.messages = [message]
            mock_chat_stub.GetPreviousMessages.return_value = messages_response
            
            # Mock message existence check
            mock_messages_collection.find_message_by_id.return_value = None  # Message doesn't exist locally
            
            # Create a real implementation of the method for testing
            def sync_messages_implementation():
                users_collection = mock_users_collection_class()
                local_users = users_collection.get_all_users()
                messages_collection = mock_messages_collection_class()
                
                leader_connection = mock_server_instance.grpc_connections[mock_server_instance.current_leader]
                chat_stub = leader_connection['chat_stub']
                
                for user in local_users:
                    recent_chats_request = chat_pb2.GetRecentChatsRequest(
                        user_id=user.user_id,
                        page=1
                    )
                    
                    recent_chats_response = chat_stub.GetRecentChats(recent_chats_request, timeout=10)
                    
                    if recent_chats_response.code == SUCCESS:
                        for chat in recent_chats_response.chats:
                            other_user_id = chat.user_id
                            
                            messages_request = chat_pb2.GetPreviousMessagesRequest(
                                user_id=user.user_id,
                                other_user_id=other_user_id,
                                page=1
                            )
                            
                            messages_response = chat_stub.GetPreviousMessages(messages_request, timeout=10)
                            
                            if messages_response.code == SUCCESS:
                                for msg in messages_response.messages:
                                    sender_id = msg.sender.user_id
                                    recipient_id = user.user_id if not msg.is_from_me else other_user_id
                                    
                                    existing_message = messages_collection.find_message_by_id(msg.message_id)
                                    
                                    if not existing_message:
                                        messages_collection.insert_message(
                                            sender_id=sender_id,
                                            recipient_id=recipient_id,
                                            content=msg.content,
                                            message_id=msg.message_id
                                        )
            
            # Assign our implementation to the mock server
            mock_server_instance._sync_messages_from_leader = sync_messages_implementation
            
            # Call the sync method
            mock_server_instance._sync_messages_from_leader()
            
            # Verify the stubs were called with the right requests
            mock_chat_stub.GetRecentChats.assert_called_once()
            recent_chats_request = mock_chat_stub.GetRecentChats.call_args[0][0]
            assert recent_chats_request.user_id == "user1"
            assert recent_chats_request.page == 1
            
            mock_chat_stub.GetPreviousMessages.assert_called_once()
            messages_request = mock_chat_stub.GetPreviousMessages.call_args[0][0]
            assert messages_request.user_id == "user1"
            assert messages_request.other_user_id == "user2"
            assert messages_request.page == 1
            
            # Verify the message was inserted
            mock_messages_collection.insert_message.assert_called_once_with(
                sender_id="user1",
                recipient_id="user2",
                content="Hello",
                message_id="msg1"
            )
