import socket
import threading
import json


class TCPServer:
    def __init__(self, host='127.0.0.1', port=13579):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []

    def start(self):
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

                print(f"Received message from {client_address}: {message}")

                # Broadcast message to all clients
                # self.broadcast(message, client_socket)

            except Exception as e:
                print(f"Client {client_address} error: {str(e)}")
                break

        self.clients.remove(client_socket)
        client_socket.close()
        print(f"Client {client_address} disconnected")

    def broadcast(self, message, sender_socket):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    pass


if __name__ == '__main__':
    server = TCPServer()
    server.start()
