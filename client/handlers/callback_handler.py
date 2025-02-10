from typing import Dict, Any, Callable
from shared.constants import *

class CallbackHandler:
    def __init__(self, send_message_func: Callable, current_user_id: str = None):
        self.send_message = send_message_func
        self.current_user_id = current_user_id

    def handle_create_account(self, email: str, username: str, password: str):
        data = {
            'email': email,
            'username': username,
            'password': password
        }
        self.send_message(MSG_CREATE_ACCOUNT_REQUEST, data)

    def handle_login(self, email: str, password: str):
        data = {
            'email': email,
            'password': password
        }
        self.send_message(MSG_LOGIN_REQUEST, data)

    def handle_send_message(self, content: str, recipient_id: str):
        """处理发送消息请求"""
        data = {
            'content': content,
            'recipient_id': recipient_id,
            'sender_id': self.current_user_id
        }
        self.send_message(MSG_SEND_MESSAGE_REQUEST, data)

    def handle_get_users(self):
        """Handle request to get users list"""
        self.send_message(MSG_GET_USERS_REQUEST, {"user_id": "-1"}) # -1 means get all users

    def handle_get_unread_messages(self, user_id: str):
        data = {
            'user_id': user_id
        }
        self.send_message(MSG_GET_UNREAD_MESSAGES_REQUEST, data)
