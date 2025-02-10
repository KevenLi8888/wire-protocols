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
        self.chat_frame = None
        self.get_users_callback = None
        self.update_user_list_callback = None
        self.user_map = {}  # 添加用户映射字典，用于存储用户名和ID的对应关系
        self.current_chat_user = None  # 添加当前聊天对象

    def set_send_callback(self, callback):
        """Set callback for sending messages"""
        self.send_callback = callback

    def set_login_callback(self, callback):
        """Set callback for login"""
        self.login_callback = callback

    def set_create_account_callback(self, callback):
        """Set callback for account creation"""
        self.create_account_callback = callback

    def set_get_users_callback(self, callback):
        """Set callback for getting users list"""
        self.get_users_callback = callback

    def create_login_window(self):
        # 登录窗口
        self.login_frame = ttk.Frame(self.root, padding="10")
        self.login_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.login_frame, text="Email:").grid(row=0, column=0, sticky=tk.W)
        self.email_entry = ttk.Entry(self.login_frame)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.login_frame, text="Login", command=self.login).grid(row=2, column=0, pady=10)
        ttk.Button(self.login_frame, text="Register", command=self.register).grid(row=2, column=1, pady=10)

    def create_chat_window(self):
        # 如果聊天窗口已经存在，先销毁
        if self.chat_frame:
            self.chat_frame.destroy()
            
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

        # 绑定用户列表的选择事件
        self.user_listbox.bind('<<ListboxSelect>>', self.on_user_select)

        # 绑定回车键发送消息
        self.message_entry.bind('<Return>', lambda e: self.send_message())

    def append_message(self, message):
        """添加消息到显示区域"""
        self.message_area.configure(state='normal')  # 临时启用编辑
        self.message_area.insert(tk.END, message + '\n')
        self.message_area.configure(state='disabled')  # 恢复只读状态
        self.message_area.see(tk.END)  # 滚动到最新消息

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        if self.login_callback:
            self.login_callback(email, password)

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

    def on_user_select(self, event):
        """处理用户选择事件"""
        selected_indices = self.user_listbox.curselection()
        if not selected_indices:
            return
            
        selected_username = self.user_listbox.get(selected_indices[0])
        self.current_chat_user = {
            'username': selected_username,
            'id': self.user_map[selected_username]
        }
        # 更新聊天窗口标题
        self.root.title(f"Chat with {selected_username}")

    def send_message(self):
        """发送消息"""
        message = self.message_entry.get().strip()
        
        if not message:
            return
            
        if not self.current_chat_user:
            messagebox.showerror("Error", "请先选择一个聊天对象")
            return
            
        if self.send_callback:
            self.send_callback(message, self.current_chat_user['id'])
            # 在本地显示发送的消息
            self.display_message({
                'content': message,
                'sender_id': 'self',  # 用'self'标记自己发送的消息
                'timestamp': None  # 服务器会提供实际时间戳
            })
            self.message_entry.delete(0, tk.END)

    def display_message(self, message_data):
        """显示消息"""
        try:
            is_self = message_data['sender_id'] == 'self'
            sender_username = "You" if is_self else self.get_username_by_id(message_data['sender_id'])
            
            # 格式化消息
            timestamp = message_data.get('timestamp', '')
            if timestamp:
                timestamp = f"[{timestamp}] "
            else:
                timestamp = ""
                
            formatted_message = f"{timestamp}{sender_username}: {message_data['content']}"
            
            # 在消息区域显示消息
            self.message_area.configure(state='normal')
            self.message_area.insert(tk.END, formatted_message + '\n')
            self.message_area.configure(state='disabled')
            self.message_area.see(tk.END)  # 滚动到最新消息
            
        except Exception as e:
            messagebox.showerror("Error", f"显示消息时出错: {str(e)}")

    def get_username_by_id(self, user_id):
        """根据用户ID获取用户名"""
        for username, uid in self.user_map.items():
            if uid == user_id:
                return username
        return "Unknown User"

    def update_user_list(self, users):
        """更新用户列表"""
        self.user_listbox.delete(0, tk.END)
        self.user_map.clear()
        
        for user in users:
            # 跳过当前用户自己
            if user.get('is_self', False):
                continue
            display_name = user['username']
            self.user_listbox.insert(tk.END, display_name)
            self.user_map[display_name] = user['_id']  # 存储用户名和ID的映射
            
        # 如果当前正在聊天的用户不在新的用户列表中，清除当前聊天对象
        if self.current_chat_user and self.current_chat_user['username'] not in self.user_map:
            self.current_chat_user = None
            self.root.title("Chat Application")

    def show_error(self, message):
        """Display error message"""
        messagebox.showerror("Error", message)

    def show_success(self, message):
        """Display success message"""
        messagebox.showinfo("Success", message)

    def show_chat_window(self):
        """Login success callback to switch to chat window"""
        # Destroy login frame
        self.login_frame.destroy()
        # Create and display chat window
        self.create_chat_window()
        if self.get_users_callback:
            self.get_users_callback()

    def run(self):
        self.root.mainloop()
