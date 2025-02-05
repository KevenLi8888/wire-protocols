import tkinter as tk
import json
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

class ChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chat Application")
        self.send_callback = None
        self.create_login_window()

    def set_send_callback(self, callback):
        """设置发送消息的回调函数"""
        self.send_callback = callback

    def send_message(self):
        message = self.message_entry.get()
        if message and self.send_callback:
            # 使用回调函数发送消息，而不是直接访问client
            self.send_callback(message)
            self.message_entry.delete(0, tk.END)

    def on_message_received(self, message):
        """接收消息的回调方法"""
        self.message_area.insert(tk.END, f"{message}\n")
        self.message_area.see(tk.END)

    def create_login_window(self):
        # 登录窗口
        self.login_frame = ttk.Frame(self.root, padding="10")
        self.login_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.login_frame, text="Login", command=self.login).grid(row=2, column=0, pady=10)
        ttk.Button(self.login_frame, text="Register", command=self.register).grid(row=2, column=1, pady=10)

    def create_chat_window(self):
        # 主聊天窗口
        self.chat_frame = ttk.Frame(self.root, padding="10")
        self.chat_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 消息显示区域
        self.message_area = ScrolledText(self.chat_frame, wrap=tk.WORD, width=50, height=20)
        self.message_area.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        # 用户列表
        self.user_listbox = tk.Listbox(self.chat_frame, width=20, height=20)
        self.user_listbox.grid(row=0, column=2, padx=5, pady=5)

        # 消息输入区域
        self.message_entry = ttk.Entry(self.chat_frame, width=40)
        self.message_entry.grid(row=1, column=0, padx=5, pady=5)

        # 发送按钮
        self.send_button = ttk.Button(self.chat_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=5, pady=5)

    def login(self):
        # TODO: 实现登录逻辑
        username = self.username_entry.get()
        password = self.password_entry.get()
        # 连接服务器并验证
        self.client.connect()
        self.create_chat_window()
        self.login_frame.destroy()

    def register(self):
        # TODO: 实现注册逻辑
        pass

    def send_message(self):
        message = self.message_entry.get()
        if message:
            self.client.client_socket.send(message.encode('utf-8'))
            self.message_entry.delete(0, tk.END)

    def receive_message(self, message):
        self.message_area.insert(tk.END, f"{message}\n")
        self.message_area.see(tk.END)

    def run(self):
        self.root.mainloop()
