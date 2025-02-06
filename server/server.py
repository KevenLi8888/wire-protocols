import socket
import threading
import json
import argparse
from database.collections import UsersCollection
from database.connection import DatabaseManager
from config.config import Config


class TCPServer:
    # TODO: fix hard-coded values
    def __init__(self, host='127.0.0.1', port=13570, config_path=None):
        Config.get_instance(config_path)  # Initialize config first
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.users = UsersCollection()
        # self.messages = MessagesCollection()
        

    def start(self):
        # Check database connection
        if DatabaseManager.get_instance().db == None:
            print("Failed to connect to database. Server shutting down.")
            return

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started successfully, listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New client connected: {client_address}")
            self.clients.append(client_socket)

            # Create a new thread to handle messages for each client
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()

    def handle_client(self, client_socket, client_address):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                data = json.loads(message)
                print(f"Received message from {client_address}: {data}")
                
                if data['type'] == 'login':
                    user = self.users.find_by_username(data['username'])
                    if user and user.password_hash == data['password']:  # In reality, use proper password hashing
                        self.users.update_last_login(str(user._id))
                        self.send_message(json.dumps({
                            "type": "login_response",
                            "message": "Login successful"
                        }), client_socket)
                    else:
                        self.send_message(json.dumps({
                            "type": "login_response",
                            "message": "Invalid credentials"
                        }), client_socket)

            except Exception as e:
                print(f"Client {client_address} error: {str(e)}")
                break

        self.clients.remove(client_socket)
        client_socket.close()
        print(f"Client {client_address} disconnected")

    def send_message(self, message, client_socket):
        """向指定客户端发送消息"""
        try:
            client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to client: {str(e)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the TCP server')
    parser.add_argument('--config', type=str, default='./config.json', help='Path to config file')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind')
    parser.add_argument('--port', type=int, default=13570, help='Port to bind')
    
    args = parser.parse_args()
    server = TCPServer(host=args.host, port=args.port, config_path=args.config)
    server.start()
