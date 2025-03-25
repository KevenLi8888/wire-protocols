from datetime import datetime
from re import M
from database.collections import MessagesCollection, UsersCollection
from shared.constants import *
from shared.models import User
import logging
from shared.utils import hash_password
from tests.unit.database.test_collections import messages_collection
import uuid

class UserHandler:
    """
    Handles all user-related operations including account creation, authentication,
    user management, and search functionality.
    """
    
    def __init__(self):
        """Initialize UserHandler with Users collection"""
        self.users = UsersCollection()
        self.messages = MessagesCollection()

    def create_account(self, data):
        """
        Create a new user account.
        
        Args:
            data (dict): Contains user registration data
                - username: User's chosen display name
                - email: User's email address
                - password: Pre-hashed password from client
                
        Returns:
            dict: Response containing status code and message
        """
        try:
            if not all(key in data for key in ['username', 'email', 'password', 'user_id']):
                return {"code": ERROR_SERVER_ERROR, "message": MESSAGE_SERVER_ERROR}
                
            user = self.users.find_by_email(data['email'])
            if user:
                return {"code": ERROR_USER_EXISTS, "message": MESSAGE_USER_EXISTS}
            
            # Password is already hashed from client
            self.users.insert_one(User(
                user_id=data['user_id'],  # Unique user ID
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
        """
        Authenticate user login attempt.
        
        Args:
            data (dict): Contains login credentials
                - email: User's email address
                - password: Pre-hashed password from client
                
        Returns:
            dict: Response containing status code, message, and user data if successful
        """
        try:
            if not all(key in data for key in ['email', 'password']):
                return {"code": ERROR_INVALID_CREDENTIALS, "message": MESSAGE_INVALID_CREDENTIALS}
                
            user = self.users.find_by_email(data['email'])
            # Compare hashed passwords
            if not user or user.password_hash != data['password']:
                return {"code": ERROR_INVALID_CREDENTIALS, "message": MESSAGE_INVALID_CREDENTIALS}
            
            self.users.update_last_login(str(user.user_id))
            return {
                "code": SUCCESS, 
                "message": MESSAGE_OK,
                "data": {
                    "user": {
                        "user_id": user.user_id,
                        "username": user.username,
                        "email": user.email
                    }
                }
            }
        except Exception as e:
            logging.error(f"Error during login: {str(e)}")
            return {"code": ERROR_SERVER_ERROR, "message": MESSAGE_SERVER_ERROR}

    def get_users(self, data):
        """
        Retrieve all users in the system.
        
        Args:
            data (dict): Currently unused, maintained for consistency
            
        Returns:
            dict: Response containing status code, message, and list of all users
        """
        try:
            users = self.users.get_all_users()
            
            users_data = [{
                'user_id': user.user_id,
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
        """
        Search for users by username pattern with pagination.
        
        Args:
            data (dict): Search parameters
                - pattern: Search string to match against usernames
                - current_user_id: ID of user performing the search
                - page: (optional) Page number for pagination, defaults to 1
                
        Returns:
            dict: Response containing status code, message, matched users, and pagination info
        """
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
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "password_hash": user.password_hash
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
        """
        Delete a user account and all associated messages.
        
        Args:
            data (dict): User credentials for verification
                - email: User's email address
                - password: Pre-hashed password from client
                
        Returns:
            dict: Response containing status code and message
        """
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
            messages_collection.delete_user_messages(str(user.user_id))
            self.users.delete_one(str(user.user_id))
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

    def get_all_users(self):
        """
        Get all users with their complete data for synchronization purposes.
        This method is specifically for server-to-server synchronization and includes
        sensitive data like password hashes.
        
        Returns:
            dict: Response containing all users' data including password hashes
        """
        try:
            users = self.users.get_all_users()
            
            users_data = [{
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            } for user in users]
            
            return {
                "code": SUCCESS,
                "message": MESSAGE_OK,
                "data": users_data
            }
        except Exception as e:
            logging.error(f"Error getting all users for sync: {str(e)}")
            return {
                "code": ERROR_SERVER_ERROR,
                "message": MESSAGE_SERVER_ERROR
            }

