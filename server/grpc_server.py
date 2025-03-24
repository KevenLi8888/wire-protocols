import grpc
from concurrent import futures
from generated import chat_pb2, chat_pb2_grpc
from server.handlers.user_handler import UserHandler
from server.handlers.message_handler import MessageHandler
from shared.constants import (
    SUCCESS, MESSAGE_OK, ERROR_SERVER_ERROR, MESSAGE_SERVER_ERROR,
    ERROR_REPLICATION_FAILED, MESSAGE_REPLICATION_FAILED
)
import threading
import uuid

class ChatServiceServicer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, logger, server_instance):
        self.user_handler = UserHandler()
        self.message_handler = MessageHandler(logger)
        self.logger = logger
        self.server_instance = server_instance  # Reference to the main server instance

    def _check_server_state(self, context):
        """
        Check if the server is initialized and is the leader (if applicable)
        Returns True if request should be processed, False otherwise
        """
        if self.server_instance:
            # Check if server is still initializing
            if not self.server_instance.initialization_complete:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Server is still initializing, please try again later")
                return False
                
            # Check if this server is the leader
            if not self.server_instance.is_leader and self.server_instance.current_leader is not None:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details("This server is not the leader, please connect to the leader server")
                return False
        
        return True

    def _propagate_to_replicas(self, request, method_name):
        """
        Propagate request to all replica servers concurrently using threads.
        Returns True if all replicas acknowledge the request (connection successful), False otherwise.
        
        NOTE: Only gRPC connection failures are considered as replication failures.
        If a replica successfully receives and processes the request but returns
        a business logic error code (e.g., user already exists), it is still
        considered a successful replication since the data was properly synchronized.
        """
        if not self.server_instance or not self.server_instance.is_leader:
            return True

        # Use a thread-safe list to track failures and a lock for access control
        failures = []
        failures_lock = threading.Lock()
        threads = []
        
        def call_replica(server_id, connection):
            try:
                replica_stub = connection['replica_stub']
                method = getattr(replica_stub, method_name)
                
                # Call the method synchronously with timeout
                response = method(request, timeout=2)  # 2 second timeout for replica responses
                
                # We received a response from the replica, so the connection was successful
                # Log any business logic errors but don't count them as replication failures
                if hasattr(response, 'code') and response.code != SUCCESS:
                    error_code = getattr(response, 'code', 'unknown')
                    if hasattr(response, 'message'):
                        error_message = getattr(response, 'message', 'unknown')
                        self.logger.warning(f"Replica {server_id} returned error code: {error_code}, message: {error_message}, but request was delivered successfully")
                    else:
                        self.logger.warning(f"Replica {server_id} returned error code: {error_code}, but request was delivered successfully")
                else:
                    self.logger.info(f"Replica {server_id} successfully processed {method_name}")
                    
            except grpc.RpcError as e:
                # These are actual connection failures that should count as replication failures
                self.logger.error(f"gRPC connection error with replica {server_id}: {str(e)}")
                with failures_lock:
                    failures.append(server_id)
            except Exception as e:
                # Any other exception is also a connection/processing failure
                self.logger.error(f"Error propagating to replica {server_id}: {str(e)}")
                with failures_lock:
                    failures.append(server_id)

        # Create and start a thread for each replica
        for server_id, connection in self.server_instance.grpc_connections.items():
            # print(server_id, connection)
            if server_id == self.server_instance.server_id:  # Don't propagate to self
                continue
                
            thread = threading.Thread(
                target=call_replica, 
                args=(server_id, connection),
                daemon=True
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=4)  # Wait with timeout to prevent hanging

        # Check if any threads are still running (timed out)
        active_threads = [t for t in threads if t.is_alive()]
        if active_threads:
            self.logger.warning(f"{len(active_threads)} replica requests timed out")
            return False

        # Return success only if no failures occurred
        return len(failures) == 0

    def _handle_with_replication(self, request, context, method_name, handler_func):
        """Generic handler for requests that need replication"""
        if not self._check_server_state(context):
            return None

        # If we're not the leader, the request should have been redirected
        if not self.server_instance.is_leader:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("This server is not the leader")
            return None

        try:
            # Propagate to replicas first using concurrent threads
            # Only connection failures count as replication failures, not business logic errors
            success = self._propagate_to_replicas(request, f"Replicate{method_name}")
            if not success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to replicate request to all servers")
                return {'code': ERROR_REPLICATION_FAILED, 'message': "Failed to replicate request to all servers"}

            # If replication successful, handle the request on leader
            return handler_func(request)
        except Exception as e:
            self.logger.error(f"Error in {method_name}: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return {'code': ERROR_SERVER_ERROR, 'message': str(e)}

    def CreateAccount(self, request, context): # pragma: no cover
        # Generate a unique user_id for this new account request
        user_id = str(uuid.uuid4())
        
        # Create a modified request that includes the user_id for replication
        modified_request = chat_pb2.CreateAccountRequest(
            email=request.email,
            username=request.username,
            password=request.password,
            user_id=user_id
        )
        
        result = self._handle_with_replication(
            modified_request, context, 
            "CreateAccount",
            lambda req: self.user_handler.create_account({
                'email': req.email,
                'username': req.username,
                'password': req.password,
                'user_id': user_id
            })
        )
        
        return chat_pb2.CreateAccountResponse(
            code=result['code'] if result else ERROR_SERVER_ERROR,
            message=result.get('message', MESSAGE_SERVER_ERROR) if result else MESSAGE_SERVER_ERROR
        )
        

    def Login(self, request, context): # pragma: no cover
        result = self._handle_with_replication(
            request, context,
            "Login",
            lambda req: self.user_handler.login({
                'email': req.email,
                'password': req.password
            })
        )
        if not result:
            return chat_pb2.LoginResponse(
                code=ERROR_SERVER_ERROR,
                message=MESSAGE_SERVER_ERROR
            )
        if result['code'] == SUCCESS:
            user_data = result['data']['user']
            return chat_pb2.LoginResponse(
                code=SUCCESS,
                message=MESSAGE_OK,
                user=chat_pb2.UserData(
                    id=str(user_data['user_id']),
                    username=user_data['username'],
                    email=user_data['email']
                )
            )
        return chat_pb2.LoginResponse(code=result['code'], message=result['message'])

    def DeleteAccount(self, request, context): # pragma: no cover
        result = self._handle_with_replication(
            request, context,
            "DeleteAccount",
            lambda req: self.user_handler.delete_user({
                'email': req.email,
                'password': req.password
            })
        )
        return chat_pb2.BasicResponse(
            code=result['code'] if result else ERROR_SERVER_ERROR,
            message=result.get('message', MESSAGE_SERVER_ERROR) if result else MESSAGE_SERVER_ERROR
        )

    def SearchUsers(self, request, context): # pragma: no cover
        try:
            # Check server state before processing request
            if not self._check_server_state(context):
                return chat_pb2.SearchUsersResponse()
                
            result = self.user_handler.search_users({
                'pattern': request.pattern,
                'page': request.page,
                'current_user_id': request.current_user_id
            })
            if result['code'] == SUCCESS:
                return chat_pb2.SearchUsersResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    users=[chat_pb2.UserData(
                        id=str(user['user_id']),
                        username=user['username'],
                        email=user['email'],
                        password_hash=user['password_hash']
                    ) for user in result['data']['users']],
                    total_pages=result['data']['total_pages']
                )
            return chat_pb2.SearchUsersResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in SearchUsers: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.SearchUsersResponse()

    def SendMessage(self, request, context): # pragma: no cover
        # Generate a unique message_id for this message
        message_id = str(uuid.uuid4())
        
        # Create a modified request that includes the message_id for replication
        modified_request = chat_pb2.SendMessageRequest(
            content=request.content,
            recipient_id=request.recipient_id,
            sender_id=request.sender_id,
            message_id=message_id
        )
        
        result = self._handle_with_replication(
            modified_request, context,
            "SendMessage",
            lambda req: self.message_handler.send_message({
                'content': req.content,
                'recipient_id': req.recipient_id,
                'sender_id': req.sender_id,
                'message_id': message_id
            })
        )
        if not result:
            return chat_pb2.SendMessageResponse(
                code=ERROR_SERVER_ERROR,
                message=MESSAGE_SERVER_ERROR
            )
        if result['code'] == SUCCESS:
            msg_data = result['data']
            return chat_pb2.SendMessageResponse(
                code=SUCCESS,
                message=MESSAGE_OK,
                data=chat_pb2.MessageData(
                    message_id=msg_data['message_id'],
                    sender_id=msg_data['sender_id'],
                    recipient_id=msg_data['recipient_id'],
                    content=msg_data['content'],
                    timestamp=msg_data['timestamp']
                )
            )
        return chat_pb2.SendMessageResponse(code=result['code'], message=result['message'])

    def GetRecentChats(self, request, context): # pragma: no cover
        try:
            # Check server state before processing request
            if not self._check_server_state(context):
                return chat_pb2.GetRecentChatsResponse()
                
            result = self.message_handler.get_recent_chats({
                'user_id': request.user_id,
                'page': request.page
            })
            if result['code'] == SUCCESS:
                chats_data = result['data']['chats']
                return chat_pb2.GetRecentChatsResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    chats=[chat_pb2.ChatData(
                        user_id=str(chat['user_id']),
                        username=chat['username'],
                        unread_count=chat['unread_count'],
                        last_message=chat_pb2.LastMessage(
                            content=chat['last_message']['content'],
                            timestamp=chat['last_message']['timestamp'],
                            is_from_me=chat['last_message']['is_from_me']
                        )
                    ) for chat in chats_data],
                    total_pages=result['data']['total_pages']
                )
            return chat_pb2.GetRecentChatsResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in GetRecentChats: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.GetRecentChatsResponse()

    def GetPreviousMessages(self, request, context): # pragma: no cover
        try:
            # Check server state before processing request
            if not self._check_server_state(context):
                return chat_pb2.GetPreviousMessagesResponse()
                
            result = self.message_handler.get_previous_messages({
                'user_id': request.user_id,
                'other_user_id': request.other_user_id,
                'page': request.page
            })
            if result['code'] == SUCCESS:
                return chat_pb2.GetPreviousMessagesResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    user_id=result['data']['user_id'],
                    other_user_id=result['data']['other_user_id'],
                    messages=[chat_pb2.ChatMessage(
                        message_id=str(msg['message_id']),
                        content=msg['content'],
                        timestamp=msg['timestamp'],
                        is_from_me=msg['is_from_me'],
                        sender=chat_pb2.MessageSender(
                            user_id=str(msg['sender']['user_id']),
                            username=msg['sender']['username']
                        )
                    ) for msg in result['data']['messages']],
                    total_pages=result['data']['total_pages']
                )
            return chat_pb2.GetPreviousMessagesResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in GetPreviousMessages: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.GetPreviousMessagesResponse()

    def GetChatUnreadCount(self, request, context): # pragma: no cover
        try:
            # Check server state before processing request
            if not self._check_server_state(context):
                return chat_pb2.GetChatUnreadCountResponse()
                
            result = self.message_handler.get_chat_unread_count({
                'user_id': request.user_id,
                'other_user_id': request.other_user_id
            })
            if result['code'] == SUCCESS:
                return chat_pb2.GetChatUnreadCountResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    user_id=result['data']['user_id'],
                    other_user_id=result['data']['other_user_id'],
                    count=result['data']['count']
                )
            return chat_pb2.GetChatUnreadCountResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in GetChatUnreadCount: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.GetChatUnreadCountResponse()

    def GetUnreadMessages(self, request, context): # pragma: no cover
        result = self._handle_with_replication(
            request, context,
            "GetUnreadMessages",
            lambda req: self.message_handler.get_chat_unread_messages({
                'user_id': req.user_id,
                'other_user_id': req.other_user_id,
                'num_messages': req.num_messages
            })
        )
        if not result:
            return chat_pb2.GetUnreadMessagesResponse(
                code=ERROR_SERVER_ERROR,
                message=MESSAGE_SERVER_ERROR
            )
        if result['code'] == SUCCESS:
            return chat_pb2.GetUnreadMessagesResponse(
                code=SUCCESS,
                message=MESSAGE_OK,
                messages=[chat_pb2.UnreadMessage(
                    message_id=str(msg['message_id']),
                    sender_id=msg['sender_id'],
                    recipient_id=msg['recipient_id'],
                    content=msg['content'],
                    timestamp=msg['timestamp'],
                    is_read=msg['is_read'],
                    is_from_me=msg['is_from_me']
                ) for msg in result['data']['messages']]
            )
        return chat_pb2.GetUnreadMessagesResponse(code=result['code'], message=result['message'])

    def DeleteMessages(self, request, context): # pragma: no cover
        result = self._handle_with_replication(
            request, context,
            "DeleteMessages",
            lambda req: self.message_handler.delete_messages({
                'message_ids': list(req.message_ids)
            })
        )
        return chat_pb2.BasicResponse(
            code=result['code'] if result else ERROR_SERVER_ERROR,
            message=result.get('message', MESSAGE_SERVER_ERROR) if result else MESSAGE_SERVER_ERROR
        )

class LeaderElectionServicer(chat_pb2_grpc.LeaderElectionServiceServicer):
    def __init__(self, server_instance, logger):
        self.server_instance = server_instance
        self.logger = logger

    def Election(self, request, context):
        """Handle election request from another server"""
        self.logger.info(f"Received election request from server {request.server_id}")
        
        # Participate in election by triggering our own election process
        if self.server_instance.server_id > request.server_id:
            # Our ID is higher, so we should take over the election process
            self.logger.info(f"Server ID {self.server_instance.server_id} is higher than {request.server_id}, starting election")
            self.server_instance.start_election()
            return chat_pb2.ElectionResponse(acknowledged=True)
        else:
            # Our ID is lower, so ignore election request
            self.logger.info(f"Server ID {self.server_instance.server_id} is lower than {request.server_id}, ignoring election")
            return chat_pb2.ElectionResponse(acknowledged=False)

    def Coordinator(self, request, context):
        """Handle coordinator announcement from the elected leader"""
        leader_id = request.server_id
        self.logger.info(f"Received coordinator message from server {leader_id}")
        
        # Update local leader info
        self.server_instance.update_leader(leader_id)
        return chat_pb2.CoordinatorResponse(acknowledged=True)

    def Heartbeat(self, request, context):
        """Handle heartbeat checks from other servers"""
        server_id = request.server_id
        self.logger.debug(f"Received heartbeat from server {server_id}")

        # If this is the leader checking on us, or we're the leader checking on replicas
        if (server_id == self.server_instance.current_leader or 
            self.server_instance.is_leader):
            return chat_pb2.HeartbeatResponse(
                is_alive=True,
                is_leader=self.server_instance.is_leader
            )
        else:
            # If it's not from the leader and we're not the leader, consider it suspicious
            self.logger.warning(f"Received unexpected heartbeat from non-leader server {server_id}")
            return chat_pb2.HeartbeatResponse(
                is_alive=True,
                is_leader=False
            )
    
    def GetLeaderInfo(self, request, context):
        """Provide leader information to clients
        
        If a leader is known, return its details.
        If an election is in progress, indicate that in the response.
        If no leader is known, trigger an election and indicate that.
        """
        client_id = request.client_id
        self.logger.info(f"Received leader info request from client {client_id}")
        
        # Check if we know who the leader is
        leader_id = self.server_instance.current_leader
        election_in_progress = self.server_instance.election_in_progress
        
        # If we don't know who the leader is and no election is in progress, start one
        if leader_id is None and not election_in_progress:
            self.logger.info(f"No leader known and no election in progress, starting election")
            self.server_instance.start_election()
            return chat_pb2.LeaderInfoResponse(
                leader_found=False,
                election_in_progress=True
            )
        
        # If election is in progress, inform the client
        if election_in_progress:
            self.logger.info(f"Election currently in progress, notifying client")
            return chat_pb2.LeaderInfoResponse(
                leader_found=False,
                election_in_progress=True
            )
        
        # If we know who the leader is, provide that information
        if leader_id is not None:
            # If we are the leader, return our own details
            if self.server_instance.is_leader:
                self.logger.info(f"We are the leader, providing our details to client")
                return chat_pb2.LeaderInfoResponse(
                    leader_found=True,
                    leader_id=self.server_instance.server_id,
                    leader_host=self.server_instance.host,
                    leader_port=self.server_instance.port,
                    election_in_progress=False
                )
            
            # Otherwise, find the leader in our connections
            if leader_id in self.server_instance.grpc_connections:
                leader_info = self.server_instance.grpc_connections[leader_id]
                self.logger.info(f"Providing leader {leader_id} details to client")
                return chat_pb2.LeaderInfoResponse(
                    leader_found=True,
                    leader_id=leader_id,
                    leader_host=leader_info['host'],
                    leader_port=leader_info['port'],
                    election_in_progress=False
                )
        
        # If we get here, we couldn't provide leader info for some reason
        self.logger.warning(f"Could not provide leader info to client {client_id}")
        return chat_pb2.LeaderInfoResponse(
            leader_found=False,
            election_in_progress=False
        )

class ReplicaServicer(chat_pb2_grpc.ReplicaServiceServicer):
    def __init__(self, logger, server_instance):
        self.user_handler = UserHandler()
        self.message_handler = MessageHandler(logger)
        self.logger = logger
        self.server_instance = server_instance

    def ReplicateCreateAccount(self, request, context):
        try:
            # Pass the user_id provided by the leader to ensure consistency
            result = self.user_handler.create_account({
                'email': request.email,
                'username': request.username,
                'password': request.password,
                'user_id': request.user_id  # Use the ID generated by the leader
            })
            return chat_pb2.BasicResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:
            self.logger.error(f"Error in ReplicateCreateAccount: {str(e)}")
            return chat_pb2.BasicResponse(code=500, message=str(e))

    def ReplicateLogin(self, request, context):
        try:
            result = self.user_handler.login({
                'email': request.email,
                'password': request.password
            })
            return chat_pb2.BasicResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:
            self.logger.error(f"Error in ReplicateLogin: {str(e)}")
            return chat_pb2.BasicResponse(code=500, message=str(e))

    def ReplicateDeleteAccount(self, request, context):
        try:
            result = self.user_handler.delete_user({
                'email': request.email,
                'password': request.password
            })
            return chat_pb2.BasicResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:
            self.logger.error(f"Error in ReplicateDeleteAccount: {str(e)}")
            return chat_pb2.BasicResponse(code=500, message=str(e))

    def ReplicateSendMessage(self, request, context):
        try:
            # Pass the message_id provided by the leader to ensure consistency
            result = self.message_handler.send_message({
                'content': request.content,
                'recipient_id': request.recipient_id,
                'sender_id': request.sender_id,
                'message_id': request.message_id  # Use the ID generated by the leader
            })
            return chat_pb2.BasicResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:
            self.logger.error(f"Error in ReplicateSendMessage: {str(e)}")
            return chat_pb2.BasicResponse(code=500, message=str(e))

    def ReplicateGetUnreadMessages(self, request, context):
        try:
            result = self.message_handler.get_chat_unread_messages({
                'user_id': request.user_id,
                'other_user_id': request.other_user_id,
                'num_messages': request.num_messages
            })
            return chat_pb2.BasicResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:
            self.logger.error(f"Error in ReplicateGetUnreadMessages: {str(e)}")
            return chat_pb2.BasicResponse(code=500, message=str(e))

    def ReplicateDeleteMessages(self, request, context):
        try:
            result = self.message_handler.delete_messages({
                'message_ids': list(request.message_ids)
            })
            return chat_pb2.BasicResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:
            self.logger.error(f"Error in ReplicateDeleteMessages: {str(e)}")
            return chat_pb2.BasicResponse(code=500, message=str(e))

class GRPCServer: # pragma: no cover
    def __init__(self, host, port, logger, server_instance):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.logger = logger
        self.host = host
        self.port = port
        self.server_instance = server_instance  # Reference to the main server instance
        
        # Add chat service
        chat_pb2_grpc.add_ChatServiceServicer_to_server(
            ChatServiceServicer(logger, server_instance), self.server)
        
        # Add leader election service if server instance is provided
        if server_instance:
            chat_pb2_grpc.add_LeaderElectionServiceServicer_to_server(
                LeaderElectionServicer(server_instance, logger), self.server)
            
        # Add replica service
        chat_pb2_grpc.add_ReplicaServiceServicer_to_server(
            ReplicaServicer(logger, server_instance), self.server)

    def start(self): # pragma: no cover
        self.server.add_insecure_port(f'{self.host}:{self.port}')
        self.server.start()
        self.logger.info(f"gRPC server started on {self.host}:{self.port}")
        
    def stop(self, grace=None): # pragma: no cover
        self.server.stop(grace)
        self.logger.info("gRPC server stopped")