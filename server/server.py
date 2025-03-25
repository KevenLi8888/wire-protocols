import socket
import threading
import argparse
import logging
import time
import grpc
from datetime import datetime
from database.collections import UsersCollection, ServersCollection, MessagesCollection
from database.connection import DatabaseManager
from config.config import Config
from shared.communication import CommunicationInterface
from shared.constants import *
from server.handlers.user_handler import UserHandler
from shared.logger import setup_logger
from server.handlers.message_handler import MessageHandler
from server.grpc_server import GRPCServer
from shared.models import Server as ServerModel
from shared.models import User, Message
from generated import chat_pb2, chat_pb2_grpc

class Server: 
    def __init__(self, config_path): # pragma: no cover
        """Initialize TCP Server with configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.ELECTION_WAIT_TIME = 5  # seconds
        self.HEARTBEAT_INTERVAL = 10  # seconds
        self.HIGHER_SERVER_WAIT_TIME = 5  # seconds
        self.ELECTION_TIMEOUT = 10  # seconds
        self.COORDINATOR_TIMEOUT = 10  # seconds
        self.HEARTBEAT_TIMEOUT = 8  # seconds

        # Initialize server state
        self.initialization_complete = False
        
        # Load configuration and set up logging
        try:
            config = Config.get_instance(config_path)
            env = config.get('env')
            self.server_id = config.get('server', 'id')
            self.logger = setup_logger('server-'+self.server_id, env)
            
            # Get configuration with error handling
            try:              
                # Server configuration
                self.host = config.get('server', 'host')
                self.port = config.get('server', 'port')
                self.protocol_type = config.get('server', 'protocol_type')
                
                # Registry configuration
                self.registry_host = config.get('registry', 'host')
                self.registry_username = config.get('registry', 'username')
                self.registry_password = config.get('registry', 'password')
                self.registry_name = config.get('registry', 'name')
                
            except ValueError as e:
                self.logger.error(f"Configuration error: {str(e)}", exc_info=True)
                raise RuntimeError("Server configuration is invalid") from e
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize server: {str(e)}") from e
        
        # Initialize database connections
        self._init_database_connections()
        
        # Initialize server components
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []  # List to track all connected clients
        self.online_users = {}  # Dictionary to track authenticated users {client_socket: username}
        self.communication = CommunicationInterface(self.protocol_type, self.logger)
        self.user_handler = UserHandler()
        self.message_handler = MessageHandler(self.logger)
        
        # Leader election state variables
        self.is_leader = False
        self.current_leader = None
        self.election_in_progress = False
        self.election_lock = threading.Lock()
        
        # Message routing dictionary: maps message types to their handlers and response types
        self.message_handlers = {
            MSG_CREATE_ACCOUNT_REQUEST: (self.user_handler.create_account, MSG_CREATE_ACCOUNT_RESPONSE),
            MSG_LOGIN_REQUEST: (self.user_handler.login, MSG_LOGIN_RESPONSE),
            MSG_GET_USERS_REQUEST: (self.user_handler.get_users, MSG_GET_USERS_RESPONSE),
            MSG_SEND_MESSAGE_REQUEST: (self.message_handler.send_message, MSG_SEND_MESSAGE_RESPONSE),
            MSG_SEARCH_USERS_REQUEST: (self.user_handler.search_users, MSG_SEARCH_USERS_RESPONSE),
            MSG_GET_RECENT_CHATS_REQUEST: (self.message_handler.get_recent_chats, MSG_GET_RECENT_CHATS_RESPONSE),
            MSG_GET_PREVIOUS_MESSAGES_REQUEST: (self.message_handler.get_previous_messages, MSG_GET_PREVIOUS_MESSAGES_RESPONSE),
            MSG_GET_CHAT_UNREAD_COUNT_REQUEST: (self.message_handler.get_chat_unread_count, MSG_GET_CHAT_UNREAD_COUNT_RESPONSE),
            MSG_GET_UNREAD_MESSAGES_REQUEST: (self.message_handler.get_chat_unread_messages, MSG_GET_UNREAD_MESSAGES_RESPONSE),
            MSG_DELETE_MESSAGE_REQUEST: (self.message_handler.delete_messages, MSG_DELETE_MESSAGE_RESPONSE),
            MSG_DELETE_ACCOUNT_REQUEST: (self.user_handler.delete_user, MSG_DELETE_ACCOUNT_RESPONSE),
        }
        
        # Initialize list to store other servers' information
        self.other_servers = []
        self.grpc_connections = {}
        
        # Initialize gRPC server if needed
        if self.protocol_type == 'grpc':
            try:
                self.grpc_server = GRPCServer(self.host, self.port, self.logger, self)
                self.grpc_server.start()
                self.logger.info(f"gRPC server started successfully, listening on {self.host}:{self.port}")
            except Exception as e:
                self.logger.error(f"Failed to start gRPC server: {str(e)}", exc_info=True)
        
        # Register server with registry service
        self._register_with_registry()
        
        # Mark initialization as complete
        self.initialization_complete = True
        self.logger.info("Server initialization complete")

    def _init_database_connections(self): # pragma: no cover
        """Initialize connections to both main database and registry database"""
        # Connect to the main database
        self.db_manager = DatabaseManager.get_instance('database')
        if self.db_manager.db is None:
            self.logger.error("Failed to connect to main database.", exc_info=True)
            raise RuntimeError("Database connection failed.")
            
        # Connect to registry database
        self.registry_manager = DatabaseManager.get_instance('registry')
        if self.registry_manager.db is None:
            self.logger.error("Failed to connect to registry database.", exc_info=True)
            raise RuntimeError("Registry connection failed.")
        
        self.logger.info("Successfully connected to both databases.")
        
    def _register_with_registry(self): # pragma: no cover
        """Register this server with the registry service and discover other servers"""
        try:
            # Create a server object to register
            server_data = ServerModel(
                server_id=self.server_id,
                host=self.host,
                port=self.port,
                status="ONLINE",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_leader=False
            )
            
            # Initialize server registry collection and register this server
            servers_collection = ServersCollection()
            result = servers_collection.register_server(server_data)
            
            if result:
                self.logger.info(f"Successfully registered server {self.server_id} with registry")
            else:
                self.logger.warning(f"Failed to register server {self.server_id} with registry")
            
            # check if there is already a leader
            current_leader = servers_collection.get_leader()
            
            if current_leader:
                # if there is already a leader, accept it without election
                self.logger.info(f"Existing leader found: {current_leader.server_id}, accepting as leader")
                self.current_leader = current_leader.server_id
                self.is_leader = (current_leader.server_id == self.server_id)
                
                # discover other servers and establish connections
                self._discover_servers()
                
                # if using gRPC, start leader health check
                if self.protocol_type == 'grpc':
                    self._start_leader_health_check()
                    
                    # if not leader, sync data from leader
                    if not self.is_leader and self.current_leader != self.server_id:
                        self._sync_data_from_leader()
            else:
                # no leader exists, wait for a while to allow other servers to register
                self.logger.info(f"No leader found. Waiting for {self.ELECTION_WAIT_TIME} seconds to allow other servers to register...")
                time.sleep(self.ELECTION_WAIT_TIME)
                
                # if using gRPC, start election
                if self.protocol_type == 'grpc':
                    self.start_election()
                
        except Exception as e:
            self.logger.error(f"Error registering with registry: {str(e)}", exc_info=True)
    
    def _sync_data_from_leader(self):
        """sync data from leader to new joined servers"""
        if not self.current_leader or self.current_leader not in self.grpc_connections:
            self.logger.warning(f"Cannot sync data: Leader {self.current_leader} not found in connections")
            return
        
        try:
            self.logger.info(f"Starting data synchronization from leader {self.current_leader}")
            
            # 1. sync users data
            self._sync_users_from_leader()
            
            # 2. sync messages data
            self._sync_messages_from_leader()
            
            self.logger.info(f"Data synchronization from leader {self.current_leader} completed successfully")
        except Exception as e:
            self.logger.error(f"Error during data synchronization: {str(e)}", exc_info=True)

    def _sync_users_from_leader(self):
        """sync users data from leader"""
        try:
            # get local users collection
            users_collection = UsersCollection()
            local_users = users_collection.get_all_users()
            local_user_ids = {user.user_id for user in local_users}
            
            # get all users from leader
            leader_connection = self.grpc_connections[self.current_leader]
            stub = leader_connection['chat_stub']
            
            # Use GetAllUsers RPC
            request = chat_pb2.GetAllUsersRequest()
            response = stub.GetAllUsers(request, timeout=10)
            
            if response.code == SUCCESS:
                # handle each user from leader
                new_users_count = 0
                for user_data in response.users:
                    if user_data.id not in local_user_ids:
                        # if user does not exist locally, create user
                        new_user = User(
                            user_id=user_data.id,
                            username=user_data.username,
                            email=user_data.email,
                            password_hash=user_data.password_hash,
                            created_at=datetime.fromisoformat(user_data.created_at) if user_data.created_at else None,
                            last_login=datetime.fromisoformat(user_data.last_login) if user_data.last_login else None,
                        )
                        users_collection.insert_one(new_user)
                        self.logger.info(f"Synchronized user: {user_data.username} (ID: {user_data.id})")
                        new_users_count += 1
                
                self.logger.info(f"User synchronization completed. Added {new_users_count} new users out of {len(response.users)} total users.")
            else:
                self.logger.warning(f"Failed to get users from leader: {response.message}")
        except Exception as e:
            self.logger.error(f"Error synchronizing users: {str(e)}", exc_info=True)

    def _sync_messages_from_leader(self):
        """sync messages data from leader"""
        try:
            # get messages collection
            messages_collection = MessagesCollection()
            
            # Use GetAllMessages RPC
            leader_connection = self.grpc_connections[self.current_leader]
            chat_stub = leader_connection['chat_stub']
            
            request = chat_pb2.GetAllMessagesRequest()
            response = chat_stub.GetAllMessages(request, timeout=10)
            
            if response.code == SUCCESS:
                # handle each message from leader
                new_messages_count = 0
                for msg in response.messages:
                    # Check if message exists
                    existing_message = messages_collection.find_message_by_id(msg.message_id)
                    
                    if not existing_message:
                        # Insert message if it doesn't exist
                        messages_collection.insert_message(
                            sender_id=msg.sender_id,
                            recipient_id=msg.recipient_id,
                            content=msg.content,
                            message_id=msg.message_id,
                            time=datetime.fromisoformat(msg.timestamp),
                            is_read=msg.is_read
                        )
                        new_messages_count += 1
                        
                self.logger.info(f"Message synchronization completed. Added {new_messages_count} new messages out of {len(response.messages)} total messages.")
            else:
                self.logger.warning(f"Failed to get messages from leader: {response.message}")
        except Exception as e:
            self.logger.error(f"Error in message synchronization: {str(e)}", exc_info=True)

    def start_election(self):
        """Start leader election using Bully algorithm"""
        with self.election_lock:
            # If an election is already in progress, don't start another one
            if self.election_in_progress:
                self.logger.info("Election already in progress, not starting a new one")
                return
                
            self.election_in_progress = True
            self.is_leader = False  # Reset leader status during election
            self.current_leader = None
            
        self.logger.info(f"Starting election from server {self.server_id}")

        # Get all registered servers
        self._discover_servers()
        
        # Find servers with higher IDs
        higher_servers = [server for server in self.other_servers 
                         if server['server_id'] > self.server_id]
        
        if not higher_servers:
            # No servers with higher IDs, we are the leader
            self.logger.info(f"No servers with higher IDs found. Server {self.server_id} becomes leader")
            self._become_leader()
            return
            
        # Send election messages to all servers with higher IDs
        responses_received = []
        
        for server in higher_servers:
            server_id = server['server_id']
            if server_id not in self.grpc_connections:
                self.logger.warning(f"No connection to server {server_id}, skipping election message")
                continue
                
            try:
                # Send election message with increased timeout
                stub = self.grpc_connections[server_id]['election_stub']
                request = chat_pb2.ElectionRequest(server_id=self.server_id)
                
                try:
                    response = stub.Election(request, timeout=self.ELECTION_TIMEOUT)
                    if response.acknowledged:
                        self.logger.info(f"Server {server_id} responded to election")
                        responses_received.append(server_id)
                except grpc.RpcError as e:
                    if 'deadline exceeded' in str(e).lower():
                        self.logger.warning(f"Election request to server {server_id} timed out after {self.ELECTION_TIMEOUT}s")
                    else:
                        self.logger.warning(f"Failed to get response from server {server_id}: {str(e)}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to send election message to server {server_id}: {str(e)}")
            
            if not self.is_leader:
                self._start_leader_health_check()
                time.sleep(3)
                self._sync_data_from_leader()
        
        # Wait for a short time to see if any higher servers take over
        time.sleep(self.HIGHER_SERVER_WAIT_TIME)  # Give higher servers time to send coordinator message
        
        # If no responses received from higher servers AND we haven't received a coordinator message,
        # become leader
        if not responses_received and not self.current_leader:
            self.logger.info(f"No higher servers responded. Server {self.server_id} becomes leader")
            self._become_leader()
        else:
            # We received responses, wait for coordinator message
            self.logger.info(f"Received responses from higher servers: {responses_received}")
            # Reset election flag after timeout
            threading.Timer(self.ELECTION_TIMEOUT, self._reset_election_flag).start()

    def _discover_servers(self):
        """Discover other servers from the registry"""
        try:
            servers_collection = ServersCollection()
            all_servers = servers_collection.get_all_servers()
            # print(all_servers)
            
            # Clear current server list
            self.other_servers = []
            
            # Process servers
            for server in all_servers:
                # Skip this server
                if server.server_id == self.server_id:
                    continue
                    
                # Add server to the list of other servers
                self.other_servers.append({
                    'server_id': server.server_id,
                    'host': server.host,
                    'port': server.port,
                    'status': server.status,
                    'is_leader': server.is_leader
                })
                
            self.logger.info(f"Discovered {len(self.other_servers)} other server(s)")
            
            # Connect to other servers
            if self.protocol_type == 'grpc':
                self._establish_grpc_connections()
                
        except Exception as e:
            self.logger.error(f"Error discovering servers: {str(e)}", exc_info=True)
    
    def _establish_grpc_connections(self):
        """Establish gRPC connections to other servers"""
        # Keep track of current servers to remove stale connections later
        current_server_ids = set()
        
        # Update or create new connections
        for server in self.other_servers:
            server_id = server['server_id']
            current_server_ids.add(server_id)
            
            # Skip if connection already exists and is valid
            if (server_id in self.grpc_connections and 
                self.grpc_connections[server_id]['host'] == server['host'] and 
                self.grpc_connections[server_id]['port'] == server['port']):
                continue
                
            try:
                host = server['host']
                port = server['port']
                
                # Close existing connection if it exists
                if server_id in self.grpc_connections and 'channel' in self.grpc_connections[server_id]:
                    try:
                        self.grpc_connections[server_id]['channel'].close()
                    except:
                        pass
                
                # Create gRPC channel
                channel = grpc.insecure_channel(f"{host}:{port}")
                
                # Create stubs for different services
                chat_stub = chat_pb2_grpc.ChatServiceStub(channel)
                election_stub = chat_pb2_grpc.LeaderElectionServiceStub(channel)
                replica_stub = chat_pb2_grpc.ReplicaServiceStub(channel)  # Add replica stub
                
                # Store connection info
                self.grpc_connections[server_id] = {
                    'server_id': server_id,
                    'host': host,
                    'port': port,
                    'channel': channel,
                    'chat_stub': chat_stub,
                    'election_stub': election_stub,
                    'replica_stub': replica_stub,  # Store replica stub
                    'is_leader': server['is_leader']
                }
                
                self.logger.info(f"Established gRPC connection to server {server_id} at {host}:{port}")
            except Exception as e:
                self.logger.error(f"Failed to establish gRPC connection to server {server_id}: {str(e)}")
        
        # Remove stale connections
        stale_server_ids = set(self.grpc_connections.keys()) - current_server_ids
        for server_id in stale_server_ids:
            if 'channel' in self.grpc_connections[server_id]:
                try:
                    self.grpc_connections[server_id]['channel'].close()
                except:
                    pass
            del self.grpc_connections[server_id]
            self.logger.info(f"Removed stale connection to server {server_id}")
    
    
    def _reset_election_flag(self):
        """Reset election in progress flag after timeout"""
        with self.election_lock:
            self.election_in_progress = False
        self.logger.info("Reset election flag, ready for new elections")
    
    def _become_leader(self):
        """Become the leader and notify all other servers"""
        self.is_leader = True
        self.current_leader = self.server_id
        
        # Update leader status in database
        try:
            servers_collection = ServersCollection()
            # First reset any existing leader status
            servers_collection.reset_all_leader_status()
            # Then set this server as leader
            servers_collection.update_server_leader_status(self.server_id, True)
            self.logger.info(f"Updated leader status in registry for server {self.server_id}")
        except Exception as e:
            self.logger.error(f"Failed to update leader status: {str(e)}")
        
        # Notify all other servers
        for server_id, connection in self.grpc_connections.items():
            try:
                stub = connection['election_stub']
                request = chat_pb2.CoordinatorRequest(server_id=self.server_id)
                
                try:
                    response = stub.Coordinator(request, timeout=self.COORDINATOR_TIMEOUT)
                    if response.acknowledged:
                        self.logger.info(f"Server {server_id} acknowledged {self.server_id} as leader")
                    else:
                        self.logger.warning(f"Server {server_id} did not acknowledge leader message")
                except grpc.RpcError as e:
                    if 'deadline exceeded' in str(e).lower():
                        self.logger.warning(f"Coordinator request to server {server_id} timed out after {self.COORDINATOR_TIMEOUT}s")
                    else:
                        self.logger.warning(f"Failed to get acknowledgment from server {server_id}: {str(e)}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to send coordinator message to server {server_id}: {str(e)}")
        
        # start replica monitoring thread
        if self.protocol_type == 'grpc':
            replica_monitor_thread = threading.Thread(target=self._monitor_replicas, daemon=True)
            replica_monitor_thread.start()
            self.logger.info("Started replica monitoring thread as leader")
        
        with self.election_lock:
            self.election_in_progress = False
            
        self.logger.info(f"Server {self.server_id} is now the leader")
    
    def update_leader(self, leader_id):
        """Update the leader information based on coordinator messages"""
        # Update local leader information
        if leader_id != self.current_leader:
            self.logger.info(f"Updating leader from {self.current_leader} to {leader_id}")
            self.current_leader = leader_id
            self.is_leader = (leader_id == self.server_id)
            
            # Reset election flag
            with self.election_lock:
                self.election_in_progress = False
    
    def _monitor_replicas(self):
        """Monitor health of replica servers when this server is the leader"""
        while True:
            self._discover_servers()
            # print("monitor replicas")
            if not self.is_leader:
                time.sleep(self.HEARTBEAT_INTERVAL)
                continue
                
            # periodically discover servers to ensure we know all new joined servers
            
            # Get current list of servers
            try:
                servers_collection = ServersCollection()
                all_servers = servers_collection.get_all_servers(include_terminated=False)
                
                # Check each server except ourselves
                for server in all_servers:
                    if server.server_id == self.server_id:
                        continue
                        
                    # Try to contact the replica
                    if server.server_id in self.grpc_connections:
                        try:
                            stub = self.grpc_connections[server.server_id]['election_stub']
                            request = chat_pb2.HeartbeatRequest(server_id=self.server_id)
                            
                            response = stub.Heartbeat(request, timeout=self.HEARTBEAT_TIMEOUT)
                            
                            if not response.is_alive:
                                self.logger.warning(f"Replica {server.server_id} reported not alive, marking as offline")
                                servers_collection.update_server_status(server.server_id, "OFFLINE")
                                
                        except grpc.RpcError as e:
                            self.logger.warning(f"Replica {server.server_id} unreachable, marking as offline: {str(e)}")
                            servers_collection.update_server_status(server.server_id, "OFFLINE")
                    else:
                        # if server exists in registry but no connection exists, attempt to connect
                        self.logger.info(f"Found server {server.server_id} in registry but no connection exists, attempting to connect")
                        self._establish_grpc_connections()
                    
            except Exception as e:
                self.logger.error(f"Error monitoring replicas: {str(e)}")
                
            time.sleep(self.HEARTBEAT_INTERVAL)

    def _check_leader_health(self):
        """Check if the current leader is alive, start election if not"""
        # Skip if we are the leader or no leader is elected yet
        if self.is_leader or not self.current_leader:
            return
                
        # Try to contact the leader
        if self.current_leader in self.grpc_connections:
            try:
                stub = self.grpc_connections[self.current_leader]['election_stub']
                request = chat_pb2.HeartbeatRequest(server_id=self.server_id)
                
                # Set timeout for heartbeat with increased timeout
                response = stub.Heartbeat(request, timeout=self.HEARTBEAT_TIMEOUT)
                
                if not response.is_alive or not response.is_leader:
                    self.logger.warning(f"Leader {self.current_leader} not functioning properly, marking as offline and starting election")
                    # Update leader status in registry
                    servers_collection = ServersCollection()
                    servers_collection.update_server_status(self.current_leader, "OFFLINE")
                    servers_collection.update_server_leader_status(self.current_leader, False)
                    self.start_election()
                    
            except grpc.RpcError as e:
                if 'deadline exceeded' in str(e).lower():
                    self.logger.warning(f"Heartbeat request to leader {self.current_leader} timed out after {self.HEARTBEAT_TIMEOUT}s")
                else:
                    self.logger.warning(f"Leader {self.current_leader} unreachable: {str(e)}")
                    
                # Update leader status in registry
                servers_collection = ServersCollection()
                servers_collection.update_server_status(self.current_leader, "OFFLINE")
                servers_collection.update_server_leader_status(self.current_leader, False)
                self.start_election()
        else:
            self.logger.warning(f"No connection to leader {self.current_leader}, marking as offline and starting election")
            # Update leader status in registry
            servers_collection = ServersCollection()
            servers_collection.update_server_status(self.current_leader, "OFFLINE")
            servers_collection.update_server_leader_status(self.current_leader, False)
            self.start_election()

    def _start_leader_health_check(self):
        """Start periodic health checks of the current leader"""
        def health_check_task():
            while True:
                time.sleep(self.HEARTBEAT_INTERVAL)
                self._check_leader_health()
        
        leader_check_thread = threading.Thread(target=health_check_task, daemon=True)
        leader_check_thread.start()
        self.logger.info("Started leader health check thread")
        
        # If using gRPC, also start replica monitoring thread
        if self.protocol_type == 'grpc':
            replica_monitor_thread = threading.Thread(target=self._monitor_replicas, daemon=True)
            replica_monitor_thread.start()
            self.logger.info("Started replica monitoring thread")

    def start(self): # pragma: no cover 
        """Start the appropriate server based on protocol type"""
        # Check database connections
        if self.db_manager.db is None:
            self.logger.error("Failed to connect to main database. Server shutting down.", exc_info=True)
            return
        
        if self.registry_manager.db is None:
            self.logger.error("Failed to connect to registry database. Server shutting down.", exc_info=True)
            return
            
        if self.protocol_type == 'grpc':
            self.grpc_server.server.wait_for_termination()
        else:
            try:
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen(5)
                self.logger.info(f"Server started successfully, listening on {self.host}:{self.port}")
            except Exception as e:
                self.logger.error(f"Failed to bind server socket: {str(e)}", exc_info=True)
                raise
            while True:
                client_socket, client_address = self.server_socket.accept()
                self.logger.info(f"New client connected: {client_address}")
                self.clients.append(client_socket)
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_thread.start()

    def handle_client(self, client_socket, client_address): # pragma: no cover
        """Handle individual client connections and message processing
        
        Args:
            client_socket: Socket object for client connection
            client_address: Address info for connected client
        """
        while True:
            try:
                # Receive and process incoming messages
                data, message_type = self.communication.receive(client_socket)
                if not data:
                    self.logger.info(f"Client {client_address} disconnected (connection closed by client)")
                    break
                response = self.handle_message(message_type, data, client_socket)
            except (ConnectionError, socket.error) as e:
                self.logger.info(f"Client {client_address} disconnected: {str(e)}")
                break
            except Exception as e:
                # Handle unexpected errors and send error response to client
                self.logger.error(f"Error processing message from {client_address}: {str(e)}", exc_info=True)
                try:
                    error_response = {"code": ERROR_SERVER_ERROR, "message": MSG_ERROR_RESPONSE}
                    self.communication.send(MSG_ERROR_RESPONSE, error_response, client_socket)
                except (ConnectionError, socket.error):
                    self.logger.info(f"Failed to send error response to {client_address} - client likely disconnected")
                    break
                except Exception as e:
                    self.logger.error(f"Error sending error response to {client_address}: {str(e)}", exc_info=True)
                    break
                continue
        # Cleanup disconnected client
        if client_socket in self.online_users:
            username = self.online_users.pop(client_socket)
            self.logger.info(f"User {username} logged out. Current online users: {list(self.online_users.values())}")
        
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        try:
            client_socket.close()
        except:
            pass  # Socket might already be closed
        self.logger.info(f"Client {client_address} connection cleaned up")

    def handle_message(self, message_type, data, client_socket): # pragma: no cover
        """Process incoming messages and route to appropriate handlers
        
        Args:
            message_type: Type of message received
            data: Message payload/content
            client_socket: Socket object for client connection
            
        Returns:
            dict: Response data to be sent back to client
        """
        # Check if server is still initializing
        if not self.initialization_complete:
            response = {"code": ERROR_SERVER_INITIALIZING, "message": MESSAGE_SERVER_INITIALIZING}
            self.communication.send(MSG_ERROR_RESPONSE, response, client_socket)
            return response
            
        # Validate message type
        if message_type not in self.message_handlers:
            response = {"code": ERROR_INVALID_MESSAGE, "message": MESSAGE_INVALID_MESSAGE}
            self.communication.send(MSG_ERROR_RESPONSE, response, client_socket)
            return response
        
        try:
            # Get appropriate handler and response type for the message
            handler_func, response_type = self.message_handlers[message_type]
            response = handler_func(data)
            
            # Handle successful login by updating online users
            if message_type == MSG_LOGIN_REQUEST and response.get('code') == 0:
                self.online_users[client_socket] = response.get('data').get('user')
                self.logger.info(f"User {response.get('data').get('user').get('username')} logged in. Current online users: {list(self.online_users.values())}")
            
            # Handle real-time message notifications for online recipients
            elif message_type == MSG_SEND_MESSAGE_REQUEST and response.get('code') == SUCCESS:
                recipient_id = data['recipient_id']
                # Find recipient's socket if they're online
                recipient_socket = next(
                    (socket for socket, user in self.online_users.items() 
                     if str(user['_id']) == recipient_id), None)
                
                if recipient_socket:
                    # Notify online recipient of new message
                    self.communication.send(MSG_NEW_MESSAGE_UPDATE, response['data'], recipient_socket)
            
            self.communication.send(response_type, response, client_socket)
            return response
            
        except Exception as e:
            self.logger.error(f"Error in message handler: {str(e)}", exc_info=True)
            response = {"code": ERROR_SERVER_ERROR, "message": MESSAGE_SERVER_ERROR}
            self.communication.send(MSG_ERROR_RESPONSE, response, client_socket)
            return response
    
    def update_server_status(self, status, stopped: bool = False):
        """Update this server's status in the registry
        
        Args:
            status: New status ("ONLINE", "STOPPED", "OFFLINE")
            stopped: Boolean indicating if server is stopping (if it is, then the leader status would be set to False)
        """
        try:
            servers_collection = ServersCollection()
            result = servers_collection.update_server_status(self.server_id, status)
            if result:
                self.logger.info(f"Updated server status to {status}")
            else:
                self.logger.warning(f"Failed to update server status to {status}")
                
            # Also update leader status if this server is a leader
            if self.is_leader:
                servers_collection.update_server_leader_status(self.server_id, False if stopped else self.is_leader)
                
        except Exception as e:
            self.logger.error(f"Error updating server status: {str(e)}", exc_info=True)
    
    def main(self): # pragma: no cover
        """Main function to start the server and handle shutdown"""
        try:
            self.start()
        except KeyboardInterrupt:
            self.logger.info("Server shutting down...")
            self.update_server_status("STOPPED", True)
        except Exception as e:
            self.logger.error(f"Server error: {str(e)}", exc_info=True)
            self.update_server_status("OFFLINE")
        finally:
            # Close gRPC connections
            for server_id in self.grpc_connections:
                if 'channel' in self.grpc_connections[server_id]:
                    try:
                        self.grpc_connections[server_id]['channel'].close()
                    except:
                        pass
                        
            if hasattr(self, 'server_socket'):
                self.server_socket.close()
