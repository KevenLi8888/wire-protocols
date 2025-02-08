import tkinter as tk
import json
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

class ChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chat Application")
        self.send_callback = None
        self.login_callback = None
        self.create_account_callback = None
        self.selected_user = None
        self.create_login_window()

    def set_send_callback(self, callback):
        """Set callback for sending messages"""
        self.send_callback = callback

    def set_login_callback(self, callback):
        """Set callback for login"""
        self.login_callback = callback

    def set_create_account_callback(self, callback):
        """Set callback for account creation"""
        self.create_account_callback = callback

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

        # 创建用户列表的滚动条框架
        user_frame = ttk.Frame(self.chat_frame)
        user_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.N, tk.S))
        
        self.user_listbox = tk.Listbox(user_frame, width=15, height=20)
        user_scrollbar = ttk.Scrollbar(user_frame, orient=tk.VERTICAL, command=self.user_listbox.yview)
        self.user_listbox.configure(yscrollcommand=user_scrollbar.set)
        
        self.user_listbox.pack(side=tk.LEFT, fill=tk.Y)
        user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 消息显示区域（设置为只读）
        self.message_area = ScrolledText(self.chat_frame, wrap=tk.WORD, width=60, height=20, state='disabled')
        self.message_area.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 消息输入区域
        self.message_entry = ttk.Entry(self.chat_frame, width=50)
        self.message_entry.grid(row=1, column=1, padx=5, pady=5)

        # 发送按钮
        self.send_button = ttk.Button(self.chat_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=2, padx=5, pady=5)

        # 配置列的权重，使聊天区域能够自适应扩展
        self.chat_frame.columnconfigure(1, weight=1)

    def append_message(self, message):
        """添加消息到显示区域"""
        self.message_area.configure(state='normal')  # 临时启用编辑
        self.message_area.insert(tk.END, message + '\n')
        self.message_area.configure(state='disabled')  # 恢复只读状态
        self.message_area.see(tk.END)  # 滚动到最新消息

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        if self.login_callback:
            self.login_callback(username, password)

    def register(self):
        # Create a new registration window
        register_window = tk.Toplevel(self.root)
        register_window.title("Register")
        
        ttk.Label(register_window, text="Email:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        email_entry = ttk.Entry(register_window)
        email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(register_window, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        username_entry = ttk.Entry(register_window)
        username_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(register_window, text="Password:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        password_entry = ttk.Entry(register_window, show="*")
        password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        def submit_registration():
            email = email_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            
            if not email or not username or not password:
                messagebox.showerror("Error", "Please fill in all fields")
                return
                
            if self.create_account_callback:
                self.create_account_callback(email, username, password)
            register_window.destroy()
            
        ttk.Button(register_window, text="Submit", command=submit_registration).grid(row=3, column=0, columnspan=2, pady=10)

    def send_message(self):
        message = self.message_entry.get()
        selected_indices = self.user_listbox.curselection()
        
        if not message:
            return
            
        if not selected_indices:
            messagebox.showerror("Error", "Please select a recipient")
            return
            
        recipient_id = self.user_listbox.get(selected_indices[0])
        
        if self.send_callback:
            self.send_callback(message, recipient_id)
            self.message_entry.delete(0, tk.END)

    def update_user_list(self, users):
        """Update the list of available users"""
        self.user_listbox.delete(0, tk.END)
        for user in users:
            self.user_listbox.insert(tk.END, user)

    def show_error(self, message):
        """Display error message"""
        messagebox.showerror("Error", message)

    def show_success(self, message):
        """Display success message"""
        messagebox.showinfo("Success", message)

    def run(self):
        self.root.mainloop()
