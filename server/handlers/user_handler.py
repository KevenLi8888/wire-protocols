from datetime import datetime
from re import M
from database.collections import MessagesCollection, UsersCollection
from shared.constants import *
from shared.models import User
import logging
from shared.utils import hash_password
from tests.unit.database.test_collections import messages_collection

class UserHandler:
    def __init__(self):
        self.users = UsersCollection()

    def create_account(self, data):
        try:
            if not all(key in data for key in ['username', 'email', 'password']):
                return {"code": ERROR_SERVER_ERROR, "message": MESSAGE_SERVER_ERROR}
                
            user = self.users.find_by_email(data['email'])
            if user:
                return {"code": ERROR_USER_EXISTS, "message": MESSAGE_USER_EXISTS}
            
            # Password is already hashed from client
            self.users.insert_one(User(
                username=data['username'], 
                email=data['email'], 
                password_hash=data['password'],  # Store hashed password
                created_at=datetime.now()
            ))
            return {"code": SUCCESS, "message": MESSAGE_OK}
        except Exception as e:
            logging.error(f"Error creating account: {str(e)}")
            return {"code": ERROR_SERVER_ERROR, "message": MESSAGE_SERVER_ERROR}

    def login(self, data):
        try:
            if not all(key in data for key in ['email', 'password']):
                return {"code": ERROR_INVALID_CREDENTIALS, "message": MESSAGE_INVALID_CREDENTIALS}
                
            user = self.users.find_by_email(data['email'])
            # Compare hashed passwords
            if not user or user.password_hash != data['password']:
                return {"code": ERROR_INVALID_CREDENTIALS, "message": MESSAGE_INVALID_CREDENTIALS}
            
            self.users.update_last_login(str(user._id))
            return {
                "code": SUCCESS, 
                "message": MESSAGE_OK,
                "data": {
                    "user": {
                        "_id": str(user._id),
                        "username": user.username,
                        "email": user.email
                    }
                }
            }
        except Exception as e:
            logging.error(f"Error during login: {str(e)}")
            return {"code": ERROR_SERVER_ERROR, "message": MESSAGE_SERVER_ERROR}

    def get_users(self, data):
        """Handle get users request"""
        try:
            users = self.users.get_all_users()
            
            users_data = [{
                '_id': str(user._id),
                'username': user.username,
                'email': user.email
            } for user in users]
            
            return {
                "code": SUCCESS,
                "message": MESSAGE_OK,
                "data": {
                    "users": users_data
                }
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
            if not all(key in data for key in ['pattern', 'current_user_id']):
                return {
                    "code": ERROR_SERVER_ERROR,
                    "message": MESSAGE_SERVER_ERROR
                }
                
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
                "data": {
                    "users": users_data,
                    "total_pages": total_pages
                }
            }
        except Exception as e:
            logging.error(f"Error searching users: {str(e)}")
            return {
                "code": ERROR_SERVER_ERROR,
                "message": MESSAGE_SERVER_ERROR
            }
        
    def delete_user(self, data):
        """Handle delete user request"""
        try:
            if not all(key in data for key in ['email', 'password']):
                return {
                    "code": ERROR_SERVER_ERROR,
                    "message": MESSAGE_SERVER_ERROR
                }
            
            user = self.users.find_by_email(data['email'])
            if not user or user.password_hash != data['password']:
                return {
                    "code": ERROR_INVALID_CREDENTIALS,
                    "message": MESSAGE_INVALID_CREDENTIALS
                }
            messages_collection = MessagesCollection()
            messages_collection.delete_user_messages(str(user._id))
            self.users.delete_one(str(user._id))
            return {
                "code": SUCCESS,
                "message": MESSAGE_OK
            }
        except Exception as e:
            logging.error(f"Error deleting user: {str(e)}")
            return {
                "code": ERROR_SERVER_ERROR,
                "message": MESSAGE_SERVER_ERROR
            }

