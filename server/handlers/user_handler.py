from datetime import datetime
from database.collections import UsersCollection
from shared.constants import *
from shared.models import User
import logging

class UserHandler:
    def __init__(self):
        self.users = UsersCollection()

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

    def search_users(self, data):
        """Handle user search request"""
        try:
            pattern = data.get('pattern', '')
            page = data.get('page', 1)
            current_user_id = data.get('current_user_id')
            
            users, total_pages = self.users.search_users_by_username_paginated(
                current_user_id, pattern, page
            )
            
            users_data = [{
                '_id': str(user._id),
                'username': user.username,
                'email': user.email
            } for user in users]
            
            return {
                "code": SUCCESS,
                "message": MESSAGE_OK,
                "users": users_data,
                "total_pages": total_pages
            }
        except Exception as e:
            logging.error(f"Error searching users: {str(e)}")
            return {
                "code": ERROR_SERVER_ERROR,
                "message": MESSAGE_SERVER_ERROR
            }
