import socket
import threading
import argparse
from database.collections import UsersCollection
from database.connection import DatabaseManager
from config.config import Config
from shared.communication import CommunicationInterface
from shared.constants import *
from handlers.user_handler import UserHandler

class TCPServer:
    def __init__(self, config_path):
        config = Config.get_instance(config_path)
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('port', 13570)
        self.protocol_type = config.get('protocol_type', 'json')
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.communication = CommunicationInterface(self.protocol_type)
        self.user_handler = UserHandler()
        self.message_handlers = {
            1: (self.user_handler.create_account, 2),  # (handler_function, response_type)
            2: (self.user_handler.login, 3)
        }

    def start(self):
        if DatabaseManager.get_instance().db is None:
            print("Failed to connect to database. Server shutting down.")
            return

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started successfully, listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New client connected: {client_address}")
            self.clients.append(client_socket)
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()

    def handle_client(self, client_socket, client_address):
        while True:
            try:
                data, message_type = self.communication.receive(client_socket)
                print(f"Received message from {client_address}: {data}")
                
                response = self.handle_message(message_type, data, client_socket)
                print(f"Sent response to {client_address}: {response}")

            except Exception as e:
                print(f"Client {client_address} error: {str(e)}")
                break

        self.clients.remove(client_socket)
        client_socket.close()
        print(f"Client {client_address} disconnected")

    def handle_message(self, message_type, data, client_socket):
        if message_type not in self.message_handlers:
            return {"code": ERROR_INVALID_MESSAGE, "message": MESSAGE_INVALID_MESSAGE}
        
        handler_func, response_type = self.message_handlers[message_type]
        response = handler_func(data)
        self.communication.send(response_type, response, client_socket)
        return response

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the TCP server')
    parser.add_argument('--config', type=str, default='./config.json', help='Path to config file')
    
    args = parser.parse_args()
    server = TCPServer(config_path=args.config)
    server.start()
