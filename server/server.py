import socket
import threading
import argparse
import logging
from database.collections import UsersCollection
from database.connection import DatabaseManager
from config.config import Config
from shared.communication import CommunicationInterface
from shared.constants import *
from server.handlers.user_handler import UserHandler
from shared.logger import setup_logger  # Updated import
from server.handlers.message_handler import MessageHandler  # Add this import

class TCPServer:
    def __init__(self, config_path):
        try:
            config = Config.get_instance(config_path)
            env = config.get('env')
            self.logger = setup_logger('server', env)
            
            # Get configuration with error handling
            try:
                self.host = config.get('communication', 'host')
                self.port = config.get('communication', 'port')
                self.protocol_type = config.get('communication', 'protocol_type')
            except ValueError as e:
                self.logger.error(f"Configuration error: {str(e)}", exc_info=True)
                raise RuntimeError("Server configuration is invalid") from e
                
            if not self.host:
                self.host = '127.0.0.1'
                self.logger.warning(f"No host configured, using default: {self.host}")
            
            if not self.port:
                self.port = 13570
                self.logger.warning(f"No port configured, using default: {self.port}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize server: {str(e)}") from e
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.online_users = {}  # {client_socket: username}
        self.communication = CommunicationInterface(self.protocol_type, self.logger)
        self.user_handler = UserHandler()
        self.message_handler = MessageHandler(self.logger)  # Add message handler
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

    # no need to cover starting code
    def start(self): # pragma: no cover
        if DatabaseManager.get_instance().db is None:
            self.logger.error("Failed to connect to database. Server shutting down.", exc_info=True)
            return

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

    def handle_client(self, client_socket, client_address):
        while True:
            try:
                data, message_type = self.communication.receive(client_socket)
                # Check for empty data which indicates client disconnected
                if not data:
                    self.logger.info(f"Client {client_address} disconnected (connection closed by client)")
                    break
                response = self.handle_message(message_type, data, client_socket)
            except (ConnectionError, socket.error) as e:
                self.logger.info(f"Client {client_address} disconnected: {str(e)}")
                break
            except Exception as e:
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

        # Cleanup code moved outside the try-except block
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

    def handle_message(self, message_type, data, client_socket):
        if message_type not in self.message_handlers:
            response = {"code": ERROR_INVALID_MESSAGE, "message": MESSAGE_INVALID_MESSAGE}
            self.communication.send(MSG_ERROR_RESPONSE, response, client_socket)
            return response
        
        try:
            handler_func, response_type = self.message_handlers[message_type]
            response = handler_func(data)
            
            # 处理登录消息
            if message_type == MSG_LOGIN_REQUEST and response.get('code') == 0:
                self.online_users[client_socket] = response.get('data').get('user')
                self.logger.info(f"User {response.get('data').get('user').get('username')} logged in. Current online users: {list(self.online_users.values())}")
            
            # 处理发送消息
            elif message_type == MSG_SEND_MESSAGE_REQUEST and response.get('code') == SUCCESS:
                recipient_id = data['recipient_id']
                # 查找接收者的socket
                recipient_socket = next(
                    (socket for socket, user in self.online_users.items() 
                     if str(user['_id']) == recipient_id), None)
                
                if recipient_socket:
                    # if the recipient is online, notify them
                    self.communication.send(MSG_NEW_MESSAGE_UPDATE, response['data'], recipient_socket)
            
            self.communication.send(response_type, response, client_socket)
            return response
            
        except Exception as e:
            self.logger.error(f"Error in message handler: {str(e)}", exc_info=True)
            response = {"code": ERROR_SERVER_ERROR, "message": MESSAGE_SERVER_ERROR}
            self.communication.send(MSG_ERROR_RESPONSE, response, client_socket)
            return response

    
    def main(self):  # pragma: no cover
        """Main function to start the server"""
        if DatabaseManager.get_instance().db is None:
            self.logger.error("Failed to connect to database. Server shutting down.", exc_info=True)
            return
        try:
            self.start()
        except KeyboardInterrupt:
            self.logger.info("Server shutting down...")
        except Exception as e:
            self.logger.error(f"Server error: {str(e)}", exc_info=True)
        finally:
            self.server_socket.close()
