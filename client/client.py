import socket
import threading
import argparse
import logging
from typing import Optional, Dict, Any
from shared.models import User
from shared.communication import CommunicationInterface
from shared.constants import *
from client.handlers.message_handler import MessageHandler
from client.handlers.callback_handler import CallbackHandler
from config.config import Config
from client.tk_gui import ChatGUI
from shared.logger import setup_logger  # Updated import

class Client:
    def __init__(self, config_path):
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
                self.logger.error(f"Configuration error: {str(e)}")
                raise RuntimeError("Client configuration is invalid") from e
            
            if not self.host:
                self.host = '127.0.0.1'
                self.logger.warning(f"No host configured, using default: {self.host}")
            
            if not self.port:
                self.port = 13570
                self.logger.warning(f"No port configured, using default: {self.port}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize client: {str(e)}") from e

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.communication = CommunicationInterface(self.protocol_type)
        self.message_handler = MessageHandler()
        self.current_user: Optional[User] = None
        self.gui = ChatGUI()

        self.logger.debug("Client initialized")
        
        # Initialize callback handler
        self.callback_handler = CallbackHandler(self.send_message)
        
        # Set up GUI callbacks
        self.gui.set_send_callback(self.callback_handler.handle_send_message)
        self.gui.set_login_callback(self.callback_handler.handle_login)
        self.gui.set_create_account_callback(self.callback_handler.handle_create_account)

    def connect(self) -> bool:
        try:
            self.client_socket.connect((self.host, self.port))
            self.logger.info(f"Connected to server {self.host}:{self.port}")
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False

    def send_message(self, message_type: int, data: Dict[str, Any]):
        try:
            self.communication.send(message_type, data, self.client_socket)
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")

    def receive_messages(self):
        while True:
            try:
                data, message_type = self.communication.receive(self.client_socket)
                self.message_handler.handle_message(message_type, data)
            except Exception as e:
                self.logger.error(f"Error in receive loop: {str(e)}")
                break
        self.client_socket.close()

    def run(self):
        if self.connect():
            self.gui.run()

    def main(self):
        """Main function to start the client"""
        try:
            self.run()
        except KeyboardInterrupt:
            self.logger.info("Client shutting down...")
        except Exception as e:
            self.logger.error(f"Client error: {str(e)}")
        finally:
            self.client_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the chat client')
    parser.add_argument('--config', type=str, default='./config.json', help='Path to config file')
    
    args = parser.parse_args()
    client = Client(config_path=args.config)
    client.main()
