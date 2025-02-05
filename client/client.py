import socket
import threading
import json
from tk_gui import ChatGUI


class Client:
    def __init__(self, tcpclient=None, account=None, gui=None):
        self.tcpclient = TCPClient(host, port)
        self.account = None
        self.gui = ChatGUI()

        # 设置GUI的消息回调
        self.tcpclient.set_message_callback(self.gui.on_message_received)
        self.gui.set_send_callback(self.tcpclient.send_message)

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
    def __init__(self, host='127.0.0.1', port=13579):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_callback = None

    def set_message_callback(self, callback):
        """设置接收消息的回调函数"""
        self.message_callback = callback

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

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                # 使用回调函数处理消息
                if self.message_callback:
                    self.message_callback(message)
            except Exception as e:
                print(f"Error receiving message: {str(e)}")
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
