from typing import Dict, Any
from shared.constants import *

class MessageHandler:
    def __init__(self):
        self.login_success_callback = None
        self.update_user_list_callback = None
        self.current_user_callback = None
        self.message_handlers = {
            MSG_CREATE_ACCOUNT_RESPONSE: self.handle_create_account_response,
            MSG_LOGIN_RESPONSE: self.handle_login_response,
            MSG_DELETE_ACCOUNT_RESPONSE: self.handle_delete_account_response,
            MSG_GET_USERS_RESPONSE: self.handle_get_users_response,
            MSG_RECEIVE_MESSAGE: self.handle_receive_message,
            MSG_SEND_MESSAGE_RESPONSE: self.handle_send_message_response,
            MSG_GET_UNREAD_MESSAGES_RESPONSE: self.handle_unread_messages
        }
        self.receive_message_callback = None

    def set_login_success_callback(self, callback):
        self.login_success_callback = callback

    def set_update_user_list_callback(self, callback):
        self.update_user_list_callback = callback

    def set_current_user_callback(self, callback):
        self.current_user_callback = callback

    def set_receive_message_callback(self, callback):
        self.receive_message_callback = callback

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
            if self.current_user_callback and 'user' in data:
                self.current_user_callback(data['user'])
            if self.login_success_callback:
                self.login_success_callback()
        else:
            print(f"Login failed: {data['message']}")

    def handle_delete_account_response(self, data: Dict[str, Any]):
        if data['code'] == SUCCESS:
            print("Account deleted successfully")
        else:
            print(f"Account deletion failed: {data['message']}")

    def handle_get_users_response(self, data: Dict[str, Any]):
        if data['code'] == SUCCESS:
            if self.update_user_list_callback and 'users' in data:
                self.update_user_list_callback(data['users'])
            print("Users fetched successfully")
        else:
            print(f"Users fetch failed: {data['message']}")

    def handle_receive_message(self, data: Dict[str, Any]):
        if self.receive_message_callback:
            message_data = {
                'sender_id': data['sender_id'],
                'content': data['content'],
                'timestamp': data['timestamp']
            }
            self.receive_message_callback(message_data)

    def handle_unread_messages(self, data: Dict[str, Any]):
        if data['code'] == SUCCESS and self.receive_message_callback:
            for message in data['messages']:
                self.receive_message_callback(message)

    def handle_send_message_response(self, data: Dict[str, Any]):
        if data['code'] == SUCCESS:
            print("Message sent successfully")
        else:
            print(f"Failed to send message: {data['message']}")
