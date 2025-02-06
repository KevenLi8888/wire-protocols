import socket
import threading
import json
from tk_gui import ChatGUI
from shared.models import User, Message
from typing import Optional


class Client:
    def __init__(self, tcpclient=None, account=None, gui=None, host='127.0.0.1', port=13570):
        self.tcpclient = TCPClient(host, port)
        self.current_user: Optional[User] = None
        self.account = None
        self.gui = ChatGUI()

        # 设置GUI的消息回调
        self.gui.set_send_callback(self.tcpclient.send_message)
        self.gui.set_receive_callback(self.tcpclient.receive_message)

        # 连接服务器
        self.tcpclient.connect()


class Account:
    def __init__(self, login=None, password=None):
        self.login = login
        self.password = password


# t = {
#     "type": "",
#
# }

class TCPClient:
    def __init__(self, host='127.0.0.1', port=13570):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def send_message(self, message):
        """发送单条消息的方法"""
        try:
            self.client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to server {self.host}:{self.port}")

            # 创建接收消息的线程
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True  # 设置为守护线程
            receive_thread.start()

        except Exception as e:
            print(f"Connection failed: {str(e)}")

    def receive_message(self):
        """接收单条消息的方法"""
        try:
            message = self.client_socket.recv(1024).decode('utf-8')
            return message
        except Exception as e:
            print(f"Error receiving message: {str(e)}")
            return None

    def receive_messages(self):
        """持续接收消息的循环方法"""
        while True:
            try:
                message = self.receive_message()
                if not message:
                    break
            except Exception as e:
                print(f"Error in receive loop: {str(e)}")
                break

        self.client_socket.close()

    def send_messages(self):
        while True:
            try:
                message = input()
                if message.lower() == 'quit':
                    break
                self.client_socket.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message: {str(e)}")
                break

        self.client_socket.close()


if __name__ == '__main__':
    client = Client()
    client.gui.run()
