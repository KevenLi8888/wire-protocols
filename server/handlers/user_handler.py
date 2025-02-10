from datetime import datetime
from database.collections import UsersCollection, MessagesCollection
from shared.constants import *
from shared.models import User
import logging

class UserHandler:
    def __init__(self):
        self.users = UsersCollection()
        self.messages = MessagesCollection()

    def create_account(self, data):
        user = self.users.find_by_email(data['email'])
        if user:
            return {"code": ERROR_USER_EXISTS, "message": MESSAGE_USER_EXISTS}
        # TODO: password should be hashed
        self.users.insert_one(User(username=data['username'], email=data['email'], password_hash=data['password'], created_at=datetime.now()))
        return {"code": SUCCESS, "message": MESSAGE_OK}

    def login(self, data):
        user = self.users.find_by_email(data['email'])
        if not user or user.password_hash != data['password']:
            return {"code": ERROR_INVALID_CREDENTIALS, "message": MESSAGE_INVALID_CREDENTIALS}
        self.users.update_last_login(str(user._id))
        # 添加用户信息到返回数据中
        return {
            "code": SUCCESS, 
            "message": MESSAGE_OK,
            "user": {
                "_id": str(user._id),
                "username": user.username,
                "email": user.email
            }
        }

    def get_users(self, data):
        """Handle get users request"""
        try:
            users_collection = UsersCollection()
            users = users_collection.get_all_users()
            
            # 只返回指定字段的用户数据
            users_data = [{
                '_id': str(user._id),
                'username': user.username,
                'email': user.email
            } for user in users]
            
            return {
                "code": SUCCESS,
                "message": MESSAGE_OK,
                "users": users_data
            }
        except Exception as e:
            logging.error(f"Error getting users: {str(e)}")
            return {
                "code": ERROR_SERVER_ERROR,
                "message": MESSAGE_SERVER_ERROR
            }

    def send_message(self, data):
        try:
            sender_id = data['sender_id']
            recipient_id = data['recipient_id']
            content = data['content']
            
            # 存储消息
            message_id = self.messages.insert_message(sender_id, recipient_id, content)
            
            message_data = {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'data': {
                    'message_id': message_id,
                    'sender_id': sender_id,
                    'recipient_id': recipient_id,
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                }
            }
            return message_data
            
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }

    def get_unread_messages(self, data):
        try:
            user_id = data['user_id']
            messages = self.messages.get_unread_messages(user_id)
            
            if messages:
                message_ids = [msg['_id'] for msg in messages]
                self.messages.mark_as_read(message_ids)
            
            return {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'messages': messages
            }
        except Exception as e:
            logging.error(f"Error getting unread messages: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }
