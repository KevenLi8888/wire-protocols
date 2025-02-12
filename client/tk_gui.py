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
        self.on_user_search = None           # Called when user performs a search
        self.on_recent_chats_request = None  # Called when UI needs recent chats refresh
        self.on_previous_messages_request = None  
        self.selected_user = None
        self.chat_frame = None
        self.user_map = {}
        self.current_chat_user = None
        self.page_size = 10
        self.current_messages_page = 1
        self.total_messages_pages = 1
        
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

    def set_user_search_callback(self, callback):
        """Set handler for user search
        Args:
            callback (callable): Function(pattern: str, page: int)
        """
        self.on_user_search = callback

    def set_recent_chats_callback(self, callback):
        """Set handler for recent chats refresh requests
        Args:
            callback (callable): Function(page: int) -> None
        """
        self.on_recent_chats_request = callback

    def set_previous_messages_callback(self, callback):
        """Set handler for previous messages requests"""
        self.on_previous_messages_request = callback

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
        # If chat window exists, destroy it first
        if self.chat_frame:
            self.chat_frame.destroy()
            
        # Main chat window
        self.chat_frame = ttk.Frame(self.root, padding="10")
        self.chat_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for resizing
        self.chat_frame.grid_columnconfigure(1, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        # Left panel frame for chat list
        left_panel = ttk.Frame(self.chat_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        left_panel.grid_rowconfigure(1, weight=1)  # Chat list takes remaining space
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Recent chats header with refresh button
        header_frame = ttk.Frame(left_panel)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(header_frame, text="Recent Chats").pack(side=tk.LEFT, padx=5)
        ttk.Button(header_frame, text="⟳", width=3, 
                   command=lambda: self.load_recent_chats(1)).pack(side=tk.RIGHT, padx=5)
        
        # Chat list frame
        chat_list_frame = ttk.Frame(left_panel)
        chat_list_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # Recent chats listbox
        self.chat_listbox = tk.Listbox(chat_list_frame, width=20)
        chat_scrollbar = ttk.Scrollbar(chat_list_frame, orient=tk.VERTICAL, 
                                     command=self.chat_listbox.yview)
        self.chat_listbox.configure(yscrollcommand=chat_scrollbar.set)
        
        self.chat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pagination frame
        pagination_frame = ttk.Frame(left_panel)
        pagination_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        self.prev_chat_btn = ttk.Button(pagination_frame, text="←", width=3, 
                                       state=tk.DISABLED)
        self.prev_chat_btn.pack(side=tk.LEFT, padx=5)
        
        self.chat_page_label = ttk.Label(pagination_frame, text="Page 1")
        self.chat_page_label.pack(side=tk.LEFT, expand=True)
        
        self.next_chat_btn = ttk.Button(pagination_frame, text="→", width=3, 
                                       state=tk.DISABLED)
        self.next_chat_btn.pack(side=tk.RIGHT, padx=5)
        
        # New Chat button
        new_chat_btn = ttk.Button(left_panel, text="New Chat", 
                                 command=self.show_new_chat_window)
        new_chat_btn.grid(row=3, column=0, sticky=(tk.E, tk.W), pady=(5, 0))

        # Bind events
        self.chat_listbox.bind('<<ListboxSelect>>', self.on_chat_select)
        
        # Initialize current page
        self.current_chat_page = 1
        self.total_chat_pages = 1

        # Right side chat area
        chat_area_frame = ttk.Frame(self.chat_frame)
        chat_area_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.W, tk.E), padx=(10, 0))
        chat_area_frame.grid_rowconfigure(0, weight=1)
        chat_area_frame.grid_columnconfigure(0, weight=1)

        # Message display area
        self.message_area = ScrolledText(chat_area_frame, wrap=tk.WORD, width=50, height=20, state='disabled')
        self.message_area.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Message input area
        self.message_entry = ttk.Entry(chat_area_frame)
        self.message_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Send button
        self.send_button = ttk.Button(chat_area_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=(5, 0), pady=(5, 0))

        # Bind message entry to Enter key
        self.message_entry.bind('<Return>', lambda e: self.send_message())

        # Load initial recent chats
        self.load_recent_chats(1)

    def show_new_chat_window(self):
        """Display the new chat window with user search"""
        self.search_window = tk.Toplevel(self.root)
        self.search_window.title("New Chat")
        self.search_window.geometry("300x400")
        
        # Search frame
        search_frame = ttk.Frame(self.search_window, padding="5")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search entry
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Search button
        search_btn = ttk.Button(search_frame, text="Search", 
                               command=lambda: self.perform_search(1))
        search_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Results frame
        results_frame = ttk.Frame(self.search_window)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results listbox
        self.search_results = tk.Listbox(results_frame)
        self.search_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, 
                                 command=self.search_results.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_results.configure(yscrollcommand=scrollbar.set)
        
        # Pagination frame
        pagination_frame = ttk.Frame(self.search_window)
        pagination_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_btn = ttk.Button(pagination_frame, text="Previous", 
                                  state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT)
        
        self.next_btn = ttk.Button(pagination_frame, text="Next", 
                                  state=tk.DISABLED)
        self.next_btn.pack(side=tk.RIGHT)
        
        self.page_label = ttk.Label(pagination_frame, text="Page 1")
        self.page_label.pack(side=tk.LEFT, padx=5)
        
        # Select button
        select_btn = ttk.Button(self.search_window, text="Start Chat", 
                               command=self.select_chat_user)
        select_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Bind events
        self.search_entry.bind('<Return>', lambda e: self.perform_search(1))
        self.search_results.bind('<Double-Button-1>', lambda e: self.select_chat_user())
        
        self.current_page = 1
        self.total_pages = 1
        self.search_results_data = {}  # Store user data for selection
        
        # Initial search
        self.perform_search(1)

    def perform_search(self, page):
        """Perform user search with pagination"""
        if self.on_user_search:
            pattern = self.search_entry.get()
            self.current_page = page
            self.on_user_search(pattern, page)

    def update_search_results(self, users, total_pages):
        """Update search results listbox and pagination"""
        self.search_results.delete(0, tk.END)
        self.search_results_data.clear()
        
        for user in users:
            self.search_results.insert(tk.END, user['username'])
            self.search_results_data[user['username']] = user['_id']
        
        self.total_pages = total_pages
        self.page_label.config(text=f"Page {self.current_page} of {total_pages}")
        
        # Update pagination buttons
        self.prev_btn.config(
            state=tk.NORMAL if self.current_page > 1 else tk.DISABLED,
            command=lambda: self.perform_search(self.current_page - 1)
        )
        
        self.next_btn.config(
            state=tk.NORMAL if self.current_page < total_pages else tk.DISABLED,
            command=lambda: self.perform_search(self.current_page + 1)
        )

    def select_chat_user(self):
        """Handle chat user selection"""
        selection = self.search_results.curselection()
        if not selection:
            return
            
        username = self.search_results.get(selection[0])
        user_id = self.search_results_data.get(username)
        
        if user_id:
            self.current_chat_user = {
                'username': username,
                'id': user_id
            }
            self.root.title(f"Chat with {username}")
            self.search_window.destroy()
            
            # Clear and set up message area for the new chat
            self.clear_message_area()
            self.setup_message_navigation()
            # Request the last page of messages
            self.load_previous_messages(-1)

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
        selected_indices = self.chat_listbox.curselection()  # Changed from user_listbox to chat_listbox
        if not selected_indices:
            return
            
        selected_username = self.chat_listbox.get(selected_indices[0])  # Changed from user_listbox to chat_listbox
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
            self.message_entry.delete(0, tk.END)
            # Message display is now handled after server confirmation

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
        """This method is now deprecated and should not be used"""
        pass  # Keep the method for compatibility but don't do anything

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

    def load_recent_chats(self, page):
        """Request recent chats from server"""
        if self.on_recent_chats_request:
            self.on_recent_chats_request(page)

    def update_recent_chats(self, chats, total_pages):
        """Update recent chats display"""
        self.chat_listbox.delete(0, tk.END)
        self.chat_map = {}
        
        for chat in chats:
            username = chat['username']
            unread = chat['unread_count']
            last_msg = chat['last_message']['content'][:20]
            
            # Format display text with last message preview
            display_text = f"{username}"
            if unread > 0:
                display_text += f" ({unread} new message(s))"
            
            self.chat_listbox.insert(tk.END, display_text)
            self.chat_map[display_text] = chat['user_id']
        
        # Update pagination
        self.current_chat_page = self.current_chat_page
        self.total_chat_pages = total_pages
        self.chat_page_label.config(text=f"Page {self.current_chat_page} of {total_pages}")
        
        self.prev_chat_btn.config(
            state=tk.NORMAL if self.current_chat_page > 1 else tk.DISABLED,
            command=lambda: self.load_recent_chats(self.current_chat_page - 1)
        )
        
        self.next_chat_btn.config(
            state=tk.NORMAL if self.current_chat_page < total_pages else tk.DISABLED,
            command=lambda: self.load_recent_chats(self.current_chat_page + 1)
        )

    def on_chat_select(self, event):
        """Handle chat selection"""
        selected = self.chat_listbox.curselection()
        if not selected:
            return
            
        chat_text = self.chat_listbox.get(selected[0])
        # Extract username from the multiline display (first line before newline)
        username = chat_text.split('\n')[0]
        # Remove unread count if present
        username = username.split(' (')[0]
        
        user_id = self.chat_map.get(chat_text)
        if user_id:
            self.current_chat_user = {
                'username': username,
                'id': user_id
            }
            self.root.title(f"Chat with {username}")
            self.clear_message_area()
            self.setup_message_navigation()
            # Request last page by using -1
            self.load_previous_messages(-1)

    def setup_message_navigation(self):
        """Create message navigation controls"""
        nav_frame = ttk.Frame(self.chat_frame)
        nav_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.prev_msg_btn = ttk.Button(nav_frame, text="←", width=3,
                                      command=lambda: self.load_previous_messages(self.current_messages_page - 1))
        self.prev_msg_btn.pack(side=tk.LEFT, padx=5)
        
        self.msg_page_label = ttk.Label(nav_frame, text="Page 1")
        self.msg_page_label.pack(side=tk.LEFT, expand=True)
        
        self.next_msg_btn = ttk.Button(nav_frame, text="→", width=3,
                                      command=lambda: self.load_previous_messages(self.current_messages_page + 1))
        self.next_msg_btn.pack(side=tk.RIGHT, padx=5)

    def clear_message_area(self):
        """Clear the message display area"""
        self.message_area.configure(state='normal')
        self.message_area.delete('1.0', tk.END)
        self.message_area.configure(state='disabled')

    def load_previous_messages(self, page):
        """Request previous messages for the current chat"""
        if self.current_chat_user and self.on_previous_messages_request:
            self.current_messages_page = page
            self.on_previous_messages_request(self.current_chat_user['id'], page)

    def update_previous_messages(self, messages, total_pages):
        """Display previous messages with pagination"""
        self.clear_message_area()
        self.total_messages_pages = total_pages
        
        # If page was -1 or 1, set to last page
        if self.current_messages_page < 1:
            self.current_messages_page = total_pages
        
        self.message_area.configure(state='normal')
        for message in messages:
            username = "You" if message['is_from_me'] else message['sender']['username']
            timestamp = message['timestamp']
            content = message['content']
            
            self.message_area.insert(tk.END, f"{username}, at {timestamp}:\n")
            self.message_area.insert(tk.END, f"{content}\n\n")
        
        self.message_area.configure(state='disabled')
        self.message_area.see(tk.END)
        
        # Update navigation buttons
        self.msg_page_label.config(text=f"Page {self.current_messages_page} of {total_pages}")
        self.prev_msg_btn.config(state=tk.NORMAL if self.current_messages_page > 1 else tk.DISABLED)
        self.next_msg_btn.config(state=tk.NORMAL if self.current_messages_page < total_pages else tk.DISABLED)

    def run(self):
        self.root.mainloop()
