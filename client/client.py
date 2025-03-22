import socket
import threading
import argparse
import logging
import random
import time
import grpc
from typing import Optional, Dict, Any, List
from shared.models import User
from shared.communication import CommunicationInterface
from shared.constants import *
from client.handlers.message_handler import MessageHandler
from client.handlers.user_action_handler import UserActionHandler
from config.config import Config
from client.tk_gui import ChatGUI
from shared.logger import setup_logger
from client.grpc_client import GRPCClient
from database.connection import DatabaseManager
from database.collections import ServersCollection
from shared.models import Server

class Client:
    def __init__(self, config_path):
        """Main client class that handles network communication, GUI, and message handling.
        Initializes all core components needed for the chat application.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Constants for failover
        self.MAX_FAILOVER_RETRIES = 5
        self.FAILOVER_RETRY_DELAY = 2  # seconds
        self.ELECTION_WAIT_TIME = 3  # seconds
        
        # Initialize core components
        self._init_config(config_path)
        self._init_registry_connection()
        self._init_known_servers()  # Initialize list of known servers
        self._init_network()
        self._init_handlers()
        self._init_gui()
        self._setup_callbacks()

    def _init_config(self, config_path):
        """Initialize configuration from the config file.
        Sets up logging and loads network configuration settings.
        Falls back to default values if config is missing.
        """
        config = Config.get_instance(config_path)
        env = config.get('env')
        self.logger = setup_logger('client', env)
        
        # Get configuration, if any error, exits the application
        try:
            self.protocol_type = config.get('client', 'protocol_type')
            
            # Registry configuration
            self.registry_host = config.get('registry', 'host')
            self.registry_username = config.get('registry', 'username')
            self.registry_password = config.get('registry', 'password')
            self.registry_name = config.get('registry', 'name')

            # Default server settings (will be updated from registry)
            self.host = '127.0.0.1'  # This will be updated from registry
            self.port = 13572  # This will be updated from registry
        except Exception as e:
            error_msg = f"Error loading configuration: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)

    def _init_registry_connection(self):
        """Connect to registry database to discover available servers"""
        try:
            self.registry_manager = DatabaseManager.get_instance('registry')
            if self.registry_manager.db is None:
                self.logger.error("Failed to connect to registry database.", exc_info=True)
                raise RuntimeError("Registry connection failed.")
            
            self.logger.info("Successfully connected to registry database.")
            
            # Update server details from registry
            server_details = self._fetch_server_details_from_registry()
            if server_details:
                self.host = server_details.get('host', self.host)
                self.port = server_details.get('port', self.port)
                self.logger.info(f"Using server at {self.host}:{self.port}")
            else:
                self.logger.warning("Could not find server details in registry, using defaults")
                
        except Exception as e:
            self.logger.error(f"Registry connection error: {str(e)}", exc_info=True)
            self.logger.warning("Will use default server settings")

    def _init_known_servers(self):
        """Initialize list of known server addresses that can be used for failover"""
        self.known_servers = []
        
        try:
            # Get all servers from registry
            servers_collection = ServersCollection('registry')
            all_servers = servers_collection.get_all_servers(include_terminated=False)
            
            for server in all_servers:
                if server.status == 'ONLINE':
                    self.known_servers.append({
                        'server_id': server.server_id,
                        'host': server.host,
                        'port': server.port,
                        'is_leader': server.is_leader
                    })
            
            self.logger.info(f"Loaded {len(self.known_servers)} servers from registry")
        except Exception as e:
            self.logger.error(f"Error loading server list from registry: {str(e)}", exc_info=True)
            # If we can't get servers from registry, add default server
            self.known_servers.append({
                'server_id': '1',
                'host': self.host,
                'port': self.port,
                'is_leader': True
            })
            self.logger.info("Using default server as fallback")

    def _init_network(self):
        """Initialize network components based on protocol type"""
        self.client_socket = None
        self.grpc_client = None
        if self.protocol_type == 'grpc':
            self.grpc_client = GRPCClient(self.host, self.port, self.logger)
        else:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.communication = CommunicationInterface(self.protocol_type, self.logger)

    def _init_handlers(self):
        """Initialize message and user action handlers"""
        self.message_handler = MessageHandler(self.logger)
        self.current_user: Optional[User] = None
        self.action_handler = UserActionHandler(self.send_message)  # Renamed instance

    def _init_gui(self):
        """Initialize GUI components"""
        self.gui = ChatGUI()

    def _setup_callbacks(self):
        """Set up all callback relationships between components.
        
        Establishes two main types of callbacks:
        1. GUI -> Server: User actions that need to be sent to server
        2. Server -> GUI: Server responses that need to update the GUI
        """
        # GUI -> Server (User actions)
        self.gui.set_send_callback(self.action_handler.send_chat_message)
        self.gui.set_login_callback(self.action_handler.attempt_login)
        self.gui.set_create_account_callback(self.action_handler.create_account)
        self.gui.set_user_search_callback(self.action_handler.search_users)
        self.gui.set_recent_chats_callback(self.action_handler.request_recent_chats)
        self.gui.set_previous_messages_callback(self.action_handler.request_previous_messages)
        self.gui.set_get_unread_count_callback(self.action_handler.get_chat_unread_count)
        self.gui.set_get_unread_messages_callback(self.action_handler.get_chat_unread_messages)
        self.gui.set_delete_messages_callback(self.action_handler.delete_messages)
        self.gui.set_delete_account_callback(self.action_handler.delete_account)

        # Server -> GUI (Server responses)
        self.message_handler.set_login_success_callback(self.gui.show_chat_window)
        self.message_handler.set_current_user_callback(self.set_current_user)
        self.message_handler.set_receive_message_callback(self.gui.display_message)
        self.message_handler.set_show_error_callback(self.gui.show_error)
        self.message_handler.set_close_login_window_callback(self.gui.close_login_window)
        self.message_handler.set_close_register_window_callback(self.gui.close_register_window)
        self.message_handler.set_search_results_callback(self.gui.update_search_results)
        self.message_handler.set_recent_chats_callback(self.gui.update_recent_chats)
        self.message_handler.set_previous_messages_callback(self.gui.update_previous_messages)
        self.message_handler.set_message_sent_callback(self.gui.load_previous_messages) 
        self.message_handler.set_unread_count_callback(self.gui.show_unread_notification)
        self.message_handler.set_new_message_update_callback(self.gui.load_recent_chats)
        self.message_handler.set_close_delete_window_callback(self.gui.close_delete_window)
        
    # Network operations
    def _fetch_server_details_from_registry(self):
        """Fetch server details from registry database, specifically targeting the leader server.
        Will retry for 3 times if no leader is found.
        
        Returns:
            dict: Dictionary containing server details like host and port
        """
        try:
            self.logger.info("Fetching leader server details from registry database")
            servers_collection = ServersCollection('registry')
            
            # Try for 3 times to find a leader
            retries = 3
            retry_interval = 5
            leader = None
            while retries > 0:
                leader = servers_collection.get_leader()
                if leader:
                    break
                self.logger.info(f"No leader found, retrying in {retry_interval} second... ({retries} retries left)")
                import time
                time.sleep(retry_interval)
                retries -= 1
            
            if leader:
                self.logger.info(f"Found leader server: {leader.server_id}")
                return {
                    'host': leader.host,
                    'port': leader.port
                }
            else:
                self.logger.error("No leader server found after retries")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching server details: {str(e)}", exc_info=True)
            return None
    
    def _find_leader_from_replicas(self) -> Optional[Dict[str, Any]]:
        """Find the leader server by asking replicas.
        
        This is a failover mechanism when direct registry access is not possible
        or returns stale information.
        
        Returns:
            dict: Dictionary with leader details (host, port) or None if not found
        """
        if not self.known_servers:
            self.logger.warning("No known servers to query for leader information")
            return None
            
        # Shuffle the list of servers to try them in random order
        servers_to_try = self.known_servers.copy()
        random.shuffle(servers_to_try)
        
        for server in servers_to_try:
            try:
                # Skip the server we're currently connected to (which might be down)
                if (self.grpc_client and server['host'] == self.grpc_client.host and 
                    server['port'] == self.grpc_client.port):
                    continue
                    
                self.logger.info(f"Trying to get leader info from server at {server['host']}:{server['port']}")
                
                # Create temporary connection to this server to ask for leader info
                temp_client = GRPCClient(server['host'], server['port'], self.logger)
                leader_info = temp_client.get_leader_info()
                
                if leader_info['found']:
                    self.logger.info(f"Found leader: {leader_info['leader_id']} at {leader_info['leader_host']}:{leader_info['leader_port']}")
                    return {
                        'host': leader_info['leader_host'],
                        'port': leader_info['leader_port']
                    }
                elif leader_info['election_in_progress']:
                    self.logger.info("Election in progress, waiting before retrying")
                    # Wait for the election to complete
                    time.sleep(self.ELECTION_WAIT_TIME)
                    
                    # Try this server again after waiting
                    leader_info = temp_client.get_leader_info()
                    if leader_info['found']:
                        self.logger.info(f"Leader elected: {leader_info['leader_id']} at {leader_info['leader_host']}:{leader_info['leader_port']}")
                        return {
                            'host': leader_info['leader_host'],
                            'port': leader_info['leader_port']
                        }
            except Exception as e:
                self.logger.warning(f"Failed to contact server at {server['host']}:{server['port']}: {str(e)}")
                continue
                
        self.logger.error("Could not find leader from any known server")
        return None

    def _handle_connection_error(self):
        """
        Handle connection errors by attempting to find the leader server from replicas.
        
        Returns:
            bool: True if successfully reconnected to leader, False otherwise
        """
        self.logger.info("Connection failed, attempting to find new leader")
        
        # First try to get the leader from replicas
        retry_count = 0
        while retry_count < self.MAX_FAILOVER_RETRIES:
            # Find the leader from known replicas
            leader_info = self._find_leader_from_replicas()
            
            if leader_info:
                # Try to connect to the new leader
                self.logger.info(f"Attempting to connect to leader at {leader_info['host']}:{leader_info['port']}")
                if self.grpc_client.reconnect(leader_info['host'], leader_info['port']):
                    self.host = leader_info['host']
                    self.port = leader_info['port']
                    self.logger.info(f"Successfully reconnected to leader at {self.host}:{self.port}")
                    return True
            
            # If we couldn't find a leader or connect to it, wait and retry
            retry_count += 1
            self.logger.info(f"Retrying in {self.FAILOVER_RETRY_DELAY} seconds... (Attempt {retry_count}/{self.MAX_FAILOVER_RETRIES})")
            time.sleep(self.FAILOVER_RETRY_DELAY)
        
        # If all attempts fail, try one last time with the registry
        try:
            self.logger.info("All failover attempts failed, trying registry as last resort")
            server_details = self._fetch_server_details_from_registry()
            if server_details:
                self.logger.info(f"Found leader in registry at {server_details['host']}:{server_details['port']}")
                if self.grpc_client.reconnect(server_details['host'], server_details['port']):
                    self.host = server_details['host']
                    self.port = server_details['port']
                    self.logger.info(f"Successfully reconnected to leader at {self.host}:{self.port}")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to connect via registry: {str(e)}")
        
        # If we get here, we were unable to reconnect
        self.logger.error("Could not reconnect to any server")
        self.gui.show_error("Could not connect to server. Please try again later.")
        return False

    def connect(self) -> bool:
        """Establish connection to server based on protocol type"""
        try:            
            if self.protocol_type == 'grpc':
                # gRPC connection is handled by the communication interface
                return True
            else:
                # TCP connection
                try:
                    self.client_socket.connect((self.host, self.port))
                    self.logger.info(f"Connected to server {self.host}:{self.port}")
                    self._start_receive_thread()
                    return True
                except ConnectionRefusedError as e:
                    error_msg = f"Connection refused: {str(e)}"
                    self.logger.error(error_msg, exc_info=True)
                    self.gui.show_error(error_msg)
                    return False
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.gui.show_error(error_msg)
            return False

    def _start_receive_thread(self):
        """Start message receiving thread"""
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

    def send_message(self, message_type: int, data: Dict[str, Any]):
        """Send formatted message to server.
        
        Args:
            message_type (int): Type of message being sent (defined in constants)
            data (Dict[str, Any]): Message payload containing relevant data
        """
        try:
            response = self.communication.send(message_type, data, self.client_socket, self.grpc_client)
            
            if response and self.protocol_type == 'grpc':
                # Check for gRPC connection errors in the response
                if response.get('code') == ERROR_RPC_ERROR or response.get('code') == ERROR_CONNECTION_ERROR:
                    self.logger.error(f"gRPC connection error detected: {response.get('message')}")
                    
                    # Try to find another server and reconnect
                    if self._handle_connection_error():
                        # If reconnection successful, retry the original message
                        self.logger.info("Retrying message after successful reconnection")
                        self.send_message(message_type, data)
                        return
                    else:
                        # If reconnection failed, show error to user
                        self.gui.show_error(f"Could not connect to server: {response.get('message')}")
                        return
                
                # Handle gRPC response directly since there's no receive loop
                self.message_handler.handle_message(message_type + 1, response)
                
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}", exc_info=True)
            self.gui.show_error(f"Error sending message: {str(e)}")

    def receive_messages(self):
        """Continuous message receiving loop.
        Runs in a separate thread to handle incoming messages from server.
        Passes received messages to the message handler for processing.
        """
        while True:
            try:
                data, message_type = self.communication.receive(self.client_socket)
                self.message_handler.handle_message(message_type, data)
            except Exception as e:
                self.logger.error(f"Error in receive loop: {str(e)}", exc_info=True)
                break
        self.client_socket.close()

    # User management
    def set_current_user(self, user_data):
        """Update current user information after successful login.
        
        Args:
            user_data (dict): User information received from server containing
                            id, username, and email
        """
        try:
            self.current_user = User(
                _id=user_data['_id'],
                username=user_data['username'],
                email=user_data['email']
            )
            self.action_handler.current_user_id = str(self.current_user._id)
            self.logger.info(f"Current user set: {self.current_user.username}")
        except Exception as e:
            self.logger.error(f"Error setting current user: {str(e)}", exc_info=True)

    def handle_received_message(self, message_data):
        """Process and display received chat messages in the GUI.
        
        Args:
            message_data (dict): Message information including sender, content, etc.
        """
        try:
            self.gui.display_message(message_data)
        except Exception as e:
            self.logger.error(f"Error handling received message: {str(e)}", exc_info=True)

    def update_recent_chats(self, chats_data):
        """Update the GUI with the list of recent chats.
        
        Args:
            chats_data (dict): Contains 'chats' list and 'total_pages' for pagination
        """
        try:
            self.gui.update_recent_chats(chats_data['chats'], chats_data['total_pages'])
        except Exception as e:
            self.logger.error(f"Error updating recent chats: {str(e)}", exc_info=True)

    # Application lifecycle
    def run(self):
        """Start the client application.
        Attempts to connect to server and launches GUI if successful.
        """
        if self.connect():
            self.gui.run()

    def main(self): # pragma no cover
        """Main application entry point.
        Handles application lifecycle and ensures proper cleanup on exit.
        """
        try:
            self.run()
        except KeyboardInterrupt:
            self.logger.info("Client shutting down...")
        except Exception as e:
            self.logger.error(f"Client error: {str(e)}", exc_info=True)
        finally:
            if self.client_socket:
                self.client_socket.close()

if __name__ == '__main__': # pragma no cover
    parser = argparse.ArgumentParser(description='Start the chat client')
    parser.add_argument('--config', type=str, default='./config-client.json', help='Path to config file')
    
    args = parser.parse_args()
    client = Client(config_path=args.config)
    client.main()
