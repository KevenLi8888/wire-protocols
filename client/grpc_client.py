import grpc
import uuid
from generated import chat_pb2, chat_pb2_grpc
from shared.constants import ERROR_RPC_ERROR, ERROR_CONNECTION_ERROR

class GRPCClient:
    def __init__(self, host, port, logger):
        self.host = host
        self.port = port
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
        self.election_stub = chat_pb2_grpc.LeaderElectionServiceStub(self.channel)
        self.logger = logger
        self.client_id = str(uuid.uuid4())[:8]  # Generate a unique client ID for tracking

    def _handle_error(self, e: grpc.RpcError):
        """Convert gRPC errors to appropriate error codes and messages.
        
        This identifies connection-related errors vs. other RPC errors, allowing
        the client to handle connection failures appropriately.
        """
        self.logger.error(f"RPC failed: {str(e)}")
        
        # Check if this is a connection-related error
        if e.code() in [grpc.StatusCode.UNAVAILABLE,
                        grpc.StatusCode.DEADLINE_EXCEEDED,
                        grpc.StatusCode.FAILED_PRECONDITION]:
            return {
                'code': ERROR_CONNECTION_ERROR,
                'message': f"Connection error: {str(e)}"
            }
        else:
            return {
                'code': ERROR_RPC_ERROR,
                'message': f"RPC error: {str(e)}"
            }

    def get_leader_info(self, timeout=3):
        """
        Request current leader information from a server replica.
        
        Args:
            timeout (int): Timeout in seconds for the request
            
        Returns:
            dict: Information about the leader with the following format:
                {
                    'found': True/False,
                    'leader_id': str,
                    'leader_host': str,
                    'leader_port': int,
                    'election_in_progress': True/False
                }
        """
        try:
            request = chat_pb2.LeaderInfoRequest(client_id=self.client_id)
            response = self.election_stub.GetLeaderInfo(request, timeout=timeout)
            
            return {
                'found': response.leader_found,
                'leader_id': response.leader_id if response.leader_found else None,
                'leader_host': response.leader_host if response.leader_found else None,
                'leader_port': response.leader_port if response.leader_found else None,
                'election_in_progress': response.election_in_progress
            }
        except grpc.RpcError as e:
            self.logger.error(f"Failed to get leader info: {str(e)}")
            return {
                'found': False,
                'leader_id': None,
                'leader_host': None, 
                'leader_port': None,
                'election_in_progress': False
            }
    
    def reconnect(self, host, port):
        """
        Reconnect the client to a new server address and verify the connection
        
        Args:
            host (str): New server hostname
            port (int): New server port
            
        Returns:
            bool: True if reconnection successful, False otherwise
        """
        try:
            # Close existing channel
            self.channel.close()
            
            # Create a new channel to the new address
            self.host = host
            self.port = port
            self.channel = grpc.insecure_channel(f'{host}:{port}')
            self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
            self.election_stub = chat_pb2_grpc.LeaderElectionServiceStub(self.channel)
            
            # Verify connection by making a simple heartbeat request
            try:
                request = chat_pb2.LeaderInfoRequest(client_id=self.client_id)
                response = self.election_stub.GetLeaderInfo(request, timeout=3)
                self.logger.info(f"Successfully reconnected to server at {host}:{port}")
                return True
            except grpc.RpcError as e:
                self.logger.error(f"Failed to verify connection to {host}:{port}: {str(e)}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to reconnect to {host}:{port}: {str(e)}")
            return False

    def create_account(self, email, username, password):
        try:
            request = chat_pb2.CreateAccountRequest(
                email=email,
                username=username,
                password=password
            )
            response = self.stub.CreateAccount(request)
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def login(self, email, password):
        try:
            request = chat_pb2.LoginRequest(email=email, password=password)
            response = self.stub.Login(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'user': {
                            '_id': response.user.id,
                            'username': response.user.username,
                            'email': response.user.email
                        }
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def delete_account(self, email, password):
        try:
            request = chat_pb2.DeleteAccountRequest(email=email, password=password)
            response = self.stub.DeleteAccount(request)
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def send_message(self, content, recipient_id, sender_id):
        try:
            request = chat_pb2.SendMessageRequest(
                content=content,
                recipient_id=recipient_id,
                sender_id=sender_id
            )
            response = self.stub.SendMessage(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'message_id': response.data.message_id,
                        'sender_id': response.data.sender_id,
                        'recipient_id': response.data.recipient_id,
                        'content': response.data.content,
                        'timestamp': response.data.timestamp
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def search_users(self, pattern, page, current_user_id):
        try:
            request = chat_pb2.SearchUsersRequest(
                pattern=pattern,
                page=page,
                current_user_id=current_user_id
            )
            response = self.stub.SearchUsers(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'users': [{
                            '_id': user.id,
                            'username': user.username,
                            'email': user.email
                        } for user in response.users],
                        'total_pages': response.total_pages
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def get_recent_chats(self, user_id, page):
        try:
            request = chat_pb2.GetRecentChatsRequest(
                user_id=user_id,
                page=page
            )
            response = self.stub.GetRecentChats(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'chats': [{
                            'user_id': chat.user_id,
                            'username': chat.username,
                            'unread_count': chat.unread_count,
                            'last_message': {
                                'content': chat.last_message.content,
                                'timestamp': chat.last_message.timestamp,
                                'is_from_me': chat.last_message.is_from_me
                            }
                        } for chat in response.chats],
                        'total_pages': response.total_pages
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def get_previous_messages(self, user_id, other_user_id, page):
        try:
            request = chat_pb2.GetPreviousMessagesRequest(
                user_id=user_id,
                other_user_id=other_user_id,
                page=page
            )
            response = self.stub.GetPreviousMessages(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'user_id': response.user_id,
                        'other_user_id': response.other_user_id,
                        'messages': [{
                            'message_id': msg.message_id,
                            'content': msg.content,
                            'timestamp': msg.timestamp,
                            'is_from_me': msg.is_from_me,
                            'sender': {
                                'user_id': msg.sender.user_id,
                                'username': msg.sender.username
                            }
                        } for msg in response.messages],
                        'total_pages': response.total_pages
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def get_chat_unread_count(self, user_id, other_user_id):
        try:
            request = chat_pb2.GetChatUnreadCountRequest(
                user_id=user_id,
                other_user_id=other_user_id
            )
            response = self.stub.GetChatUnreadCount(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'user_id': response.user_id,
                        'other_user_id': response.other_user_id,
                        'count': response.count
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def get_unread_messages(self, user_id, other_user_id, num_messages):
        try:
            request = chat_pb2.GetUnreadMessagesRequest(
                user_id=user_id,
                other_user_id=other_user_id,
                num_messages=num_messages
            )
            response = self.stub.GetUnreadMessages(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'messages': [{
                            'message_id': msg.message_id,
                            'sender_id': msg.sender_id,
                            'recipient_id': msg.recipient_id,
                            'content': msg.content,
                            'timestamp': msg.timestamp,
                            'is_read': msg.is_read,
                            'is_from_me': msg.is_from_me
                        } for msg in response.messages]
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def delete_messages(self, message_ids):
        try:
            request = chat_pb2.DeleteMessagesRequest(
                message_ids=message_ids
            )
            response = self.stub.DeleteMessages(request)
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)
