from typing import Dict, Any, Callable
from shared.constants import *

class CallbackHandler:
    def __init__(self, send_message_func: Callable):
        self.send_message = send_message_func

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
        data = {
            'content': content,
            'recipient_id': recipient_id
        }
        self.send_message(MSG_SEND_MESSAGE_REQUEST, data)
