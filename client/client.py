import socket
import threading
import argparse
import logging
from typing import Optional, Dict, Any
from shared.models import User
from shared.communication import CommunicationInterface
from shared.constants import *
from client.handlers.message_handler import MessageHandler
from client.handlers.user_action_handler import UserActionHandler  # Updated import
from config.config import Config
from client.tk_gui import ChatGUI
from shared.logger import setup_logger  # Updated import

class Client:
    def __init__(self, config_path):
        """Main client class that handles network communication, GUI, and message handling.
        Initializes all core components needed for the chat application.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Initialize core components
        self._init_config(config_path)
        self._init_network()
        self._init_handlers()
        self._init_gui()
        self._setup_callbacks()

    def _init_config(self, config_path):
        """Initialize configuration from the config file.
        Sets up logging and loads network configuration settings.
        Falls back to default values if config is missing.
        """
        config = Config.get_instance(config_path)  # 移除外层 try-except，让异常直接传播
        env = config.get('env')
        self.logger = setup_logger('client', env)
        
        # Get configuration with error handling
        try:
            self.host = config.get('communication', 'host')
            self.port = config.get('communication', 'port')
            self.protocol_type = config.get('communication', 'protocol_type')
        except ValueError as e:
            self.logger.error(f"Configuration error: {str(e)}", exc_info=True)
            # Set default values if config values are missing
            self.host = self.host if hasattr(self, 'host') else '127.0.0.1'
            self.port = self.port if hasattr(self, 'port') else 13570

    def _init_network(self):
        """Initialize network components.
        Creates TCP socket and sets up the communication interface
        for handling protocol-specific message formatting.
        """
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
        self.message_handler.set_receive_message_callback(self.gui.display_message) # no longer needed
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
    def connect(self) -> bool:
        """Establish connection to server.
        
        Returns:
            bool: True if connection successful, False otherwise
        
        Handles various connection errors and displays them to the user
        through the GUI while also logging them.
        """
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
            self.communication.send(message_type, data, self.client_socket)
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}", exc_info=True)

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
            self.client_socket.close()

if __name__ == '__main__': # pragma no cover
    parser = argparse.ArgumentParser(description='Start the chat client')
    parser.add_argument('--config', type=str, default='./config.json', help='Path to config file')
    
    args = parser.parse_args()
    client = Client(config_path=args.config)
    client.main()
