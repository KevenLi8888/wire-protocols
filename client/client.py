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
        # Initialize core components
        self._init_config(config_path)
        self._init_network()
        self._init_handlers()
        self._init_gui()
        self._setup_callbacks()

    def _init_config(self, config_path):
        """Initialize configuration"""
        try:
            config = Config.get_instance(config_path)
            env = config.get('env')
            self.logger = setup_logger('client', env)
            
           # Get configuration with error handling
            try:
                self.host = config.get('communication', 'host')
                self.port = config.get('communication', 'port')
                self.protocol_type = config.get('communication', 'protocol_type')
            except ValueError as e:
                self.logger.error(f"Configuration error: {str(e)}", exc_info=True)
                raise RuntimeError("Client configuration is invalid") from e
            
            if not self.host:
                self.host = '127.0.0.1'
                self.logger.warning(f"No host configured, using default: {self.host}")
            
            if not self.port:
                self.port = 13570
                self.logger.warning(f"No port configured, using default: {self.port}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize client config: {str(e)}") from e

    def _init_network(self):
        """Initialize network components"""
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
        """Set up all callback relationships between components"""
        # GUI -> Server (User actions)
        self.gui.set_send_callback(self.action_handler.send_chat_message)
        self.gui.set_login_callback(self.action_handler.attempt_login)
        self.gui.set_create_account_callback(self.action_handler.create_account)
        self.gui.set_get_users_callback(self.action_handler.request_user_list)

        # Server -> GUI (Server responses)
        self.message_handler.set_login_success_callback(self.gui.show_chat_window)
        self.message_handler.set_update_user_list_callback(self.update_user_list)
        self.message_handler.set_current_user_callback(self.set_current_user)
        self.message_handler.set_receive_message_callback(self.gui.display_message)
        self.message_handler.set_show_error_callback(self.gui.show_error)
        self.message_handler.set_close_login_window_callback(self.gui.close_login_window)
        self.message_handler.set_close_register_window_callback(self.gui.close_register_window)

    # Network operations
    def connect(self) -> bool:
        """Establish connection to server"""
        try:
            self.client_socket.connect((self.host, self.port))
            self.logger.info(f"Connected to server {self.host}:{self.port}")
            self._start_receive_thread()
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}", exc_info=True)
            return False

    def _start_receive_thread(self):
        """Start message receiving thread"""
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

    def send_message(self, message_type: int, data: Dict[str, Any]):
        """Send message to server"""
        try:
            self.communication.send(message_type, data, self.client_socket)
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}", exc_info=True)

    def receive_messages(self):
        """Message receiving loop"""
        while True:
            try:
                data, message_type = self.communication.receive(self.client_socket)
                self.message_handler.handle_message(message_type, data)
            except Exception as e:
                self.logger.error(f"Error in receive loop: {str(e)}", exc_info=True)
                break
        self.client_socket.close()

    # User management
    def update_user_list(self, users_data):
        """Update GUI with user list from server"""
        try:
            for user in users_data:
                user['is_self'] = user['_id'] == self.current_user._id
            self.gui.update_user_list(users_data)
        except Exception as e:
            self.logger.error(f"Error updating user list: {str(e)}", exc_info=True)

    def set_current_user(self, user_data):
        """Update current user after successful login"""
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
        """Handle received chat message"""
        try:
            self.gui.display_message(message_data)
        except Exception as e:
            self.logger.error(f"Error handling received message: {str(e)}", exc_info=True)

    # Application lifecycle
    def run(self):
        if self.connect():
            self.gui.run()

    def main(self):
        """Main application entry point"""
        try:
            self.run()
        except KeyboardInterrupt:
            self.logger.info("Client shutting down...")
        except Exception as e:
            self.logger.error(f"Client error: {str(e)}", exc_info=True)
        finally:
            self.client_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the chat client')
    parser.add_argument('--config', type=str, default='./config.json', help='Path to config file')
    
    args = parser.parse_args()
    client = Client(config_path=args.config)
    client.main()
