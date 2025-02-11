import tkinter as tk
import json
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

class ChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chat Application")
        self.on_message_send = None          # Called when user sends a message
        self.on_login_attempt = None         # Called when user attempts to login
        self.on_account_create = None        # Called when user attempts to create account
        self.on_user_list_request = None     # Called when UI needs users list refresh
        self.selected_user = None
        self.chat_frame = None
        self.user_map = {}
        self.current_chat_user = None
        
        # Create initial window
        self.create_initial_window()

    def set_send_callback(self, callback):
        """Set handler for when user sends a message
        Args:
            callback (callable): Function(message: str, recipient_id: str)
        """
        self.on_message_send = callback

    def set_login_callback(self, callback):
        """Set handler for login attempts
        Args:
            callback (callable): Function(email: str, password: str)
        """
        self.on_login_attempt = callback

    def set_create_account_callback(self, callback):
        """Set handler for account creation attempts
        Args:
            callback (callable): Function(email: str, username: str, password: str)
        """
        self.on_account_create = callback

    def set_get_users_callback(self, callback):
        """Set handler for user list refresh requests
        Args:
            callback (callable): Function() -> None
        """
        self.on_user_list_request = callback

    def create_initial_window(self):
        """Create the initial window with Login and Register buttons"""
        self.initial_frame = ttk.Frame(self.root, padding="20")
        self.initial_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(self.initial_frame, text="Login", command=self.show_login_window).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(self.initial_frame, text="Register", command=self.show_register_window).grid(row=0, column=1, padx=10, pady=10)

    def show_login_window(self):
        """Display the login window"""
        
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Login")
        self.login_window.transient(self.root)
        self.login_window.grab_set()  # Make window modal
        
        frame = ttk.Frame(self.login_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text="Email:").grid(row=0, column=0, sticky=tk.W)
        email_entry = ttk.Entry(frame)
        email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        password_entry = ttk.Entry(frame, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def handle_login():
            email = email_entry.get()
            password = password_entry.get()
            
            if not email or not password:
                messagebox.showerror("Error", "Please fill in all fields")
                return
                
            if self.on_login_attempt:
                self.on_login_attempt(email, password)
                # Window will be destroyed in response handler
        
        ttk.Button(frame, text="Login", command=handle_login).grid(row=2, column=0, columnspan=2, pady=10)

    def show_register_window(self):
        """Display the registration window"""
        
        self.register_window = tk.Toplevel(self.root)
        self.register_window.title("Register")
        self.register_window.transient(self.root)
        self.register_window.grab_set()  # Make window modal
        
        frame = ttk.Frame(self.register_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text="Email:").grid(row=0, column=0, sticky=tk.W)
        email_entry = ttk.Entry(frame)
        email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky=tk.W)
        username_entry = ttk.Entry(frame)
        username_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky=tk.W)
        password_entry = ttk.Entry(frame, show="*")
        password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        def handle_register():
            email = email_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            
            if not email or not username or not password:
                messagebox.showerror("Error", "Please fill in all fields")
                return
                
            if self.on_account_create:
                self.on_account_create(email, username, password)
                # Window will be destroyed in response handler
        
        ttk.Button(frame, text="Register", command=handle_register).grid(row=3, column=0, columnspan=2, pady=10)

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
                
            if self.on_account_create:
                self.on_account_create(email, username, password)
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
            
        if self.on_message_send:
            self.on_message_send(message, self.current_chat_user['id'])
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
        """Display error message in a separate window"""
        error_window = tk.Toplevel(self.root)
        error_window.title("Error")
        error_window.transient(self.root)
        
        # Make the window modal
        error_window.grab_set()
        
        # Set minimum size
        error_window.minsize(300, 100)
        
        frame = ttk.Frame(error_window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Message label with word wrap
        message_label = ttk.Label(frame, text=message, wraplength=250)
        message_label.grid(row=0, column=0, padx=5, pady=5)
        
        def close_error_window():
            error_window.grab_release()  # Release the grab before destroying
            error_window.destroy()
            self.root.focus_set()  # Return focus to main window
        
        # OK button to close the window
        ttk.Button(frame, text="OK", command=close_error_window).grid(row=1, column=0, pady=10)
        
        # Bind the window close button (X) to our close handler
        error_window.protocol("WM_DELETE_WINDOW", close_error_window)
        
        # Center the window
        error_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50))
        
        # Set focus to the error window
        error_window.focus_set()

    def show_success(self, message):
        """Display success message"""
        messagebox.showinfo("Success", message)

    def show_chat_window(self):
        """Login success callback to switch to chat window"""
        self.create_chat_window()
        if self.on_user_list_request:
            self.on_user_list_request()

    def close_login_window(self):
        """Close login window and destroy initial frame"""
        try:
            if hasattr(self, 'login_window') and self.login_window:
                self.login_window.destroy()
            if hasattr(self, 'initial_frame') and self.initial_frame:
                self.initial_frame.destroy()
        except Exception as e:
            print(f"Error closing login window: {e}")

    def close_register_window(self):
        """Close registration window"""
        try:
            if hasattr(self, 'register_window') and self.register_window:
                self.register_window.destroy()
        except Exception as e:
            print(f"Error closing register window: {e}")

    def run(self):
        self.root.mainloop()
