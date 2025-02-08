from typing import Dict, Any
from shared.constants import *

class MessageHandler:
    def __init__(self):
        self.message_handlers = {
            MSG_CREATE_ACCOUNT_RESPONSE: self.handle_create_account_response,
            MSG_LOGIN_RESPONSE: self.handle_login_response,
            MSG_DELETE_ACCOUNT_RESPONSE: self.handle_delete_account_response
        }

    def handle_message(self, message_type: int, data: Dict[str, Any]):
        if message_type in self.message_handlers:
            self.message_handlers[message_type](data)
        else:
            print(f"Unhandled message type: {message_type}")

    def handle_create_account_response(self, data: Dict[str, Any]):
        if data['code'] == SUCCESS:
            print("Account created successfully")
        else:
            print(f"Account creation failed: {data['message']}")

    def handle_login_response(self, data: Dict[str, Any]):
        if data['code'] == SUCCESS:
            print("Login successful")
        else:
            print(f"Login failed: {data['message']}")

    def handle_delete_account_response(self, data: Dict[str, Any]):
        if data['code'] == SUCCESS:
            print("Account deleted successfully")
        else:
            print(f"Account deletion failed: {data['message']}")
