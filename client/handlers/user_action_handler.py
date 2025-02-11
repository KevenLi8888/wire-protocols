from typing import Dict, Any, Callable
from shared.constants import *

class UserActionHandler:
    """Handles user-initiated actions by sending appropriate requests to server"""
    def __init__(self, send_message_func: Callable, current_user_id: str = None):
        self.send_to_server = send_message_func
        self.current_user_id = current_user_id

    def create_account(self, email: str, username: str, password: str):
        """Sends an account creation request"""
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        self.send_to_server(MSG_CREATE_ACCOUNT_REQUEST, data)

    def attempt_login(self, email: str, password: str):
        """Sends a login authentication request"""
        data = {
            'email': email,
            'password': password
        }
        self.send_to_server(MSG_LOGIN_REQUEST, data)

    def send_chat_message(self, content: str, recipient_id: str):
        """Sends a chat message to another user"""
        data = {
            'content': content,
            'recipient_id': recipient_id,
            'sender_id': self.current_user_id
        }
        self.send_to_server(MSG_SEND_MESSAGE_REQUEST, data)

    def request_user_list(self):
        """Requests the current list of active users"""
        self.send_to_server(MSG_GET_USERS_REQUEST, {"user_id": "-1"})

    def fetch_unread_messages(self, user_id: str):
        """Requests any unread messages for the user"""
        data = {
            'user_id': user_id
        }
        self.send_to_server(MSG_GET_UNREAD_MESSAGES_REQUEST, data)

    def search_users(self, pattern: str, page: int):
        """Sends a user search request"""
        data = {
            'pattern': pattern,
            'page': page,
            'current_user_id': self.current_user_id
        }
        self.send_to_server(MSG_SEARCH_USERS_REQUEST, data)

    def request_recent_chats(self, page: int):
        """Requests recent chat list with pagination
        Args:
            page (int): Page number to request
        """
        data = {
            'user_id': self.current_user_id,
            'page': page
        }
        self.send_to_server(MSG_GET_RECENT_CHATS_REQUEST, data)

    def request_previous_messages(self, other_user_id: str, page: int):
        """Requests previous messages between current user and other user"""
        data = {
            'user_id': self.current_user_id,
            'other_user_id': other_user_id,
            'page': page
        }
        self.send_to_server(MSG_GET_PREVIOUS_MESSAGES_REQUEST, data)
