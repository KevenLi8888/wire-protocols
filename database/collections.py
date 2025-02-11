import math
from typing import Optional
from datetime import datetime
from shared.models import User
from database.connection import DatabaseManager
from bson import ObjectId

class UsersCollection:
    def __init__(self):
        self.db = DatabaseManager.get_instance().db
        self.collection = self.db['users']

    def insert_one(self, user: User) -> Optional[str]:
        user_dict = user.to_dict()
        result = self.collection.insert_one(user_dict)
        return str(result.inserted_id) if result else None

    def find_by_username(self, username: str) -> Optional[User]:
        data = self.collection.find_one({"username": username})
        return User.from_dict(data) if data else None

    def find_by_email(self, email: str) -> Optional[User]:
        data = self.collection.find_one({"email": email})
        return User.from_dict(data) if data else None

    def update_last_login(self, user_id: str) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.now()}}
        )
        return result.modified_count > 0

    def get_all_users(self) -> list[User]:
        users = self.collection.find({}, {'_id': 1, 'username': 1, 'email': 1})
        return [u for u in (User.from_dict(user) for user in users) if u is not None]
    
    def search_users_by_username(self, current_user_id: str, filter_str: str) -> list[User]:
        '''Search users by username, filter_string is regex, excluding the current user'''
        users = self.collection.find({
            'username': {'$regex': filter_str, '$options': 'i'},
            '_id': {'$ne': ObjectId(current_user_id)}
        }, {'_id': 1, 'username': 1, 'email': 1})
        return [u for u in (User.from_dict(user) for user in users) if u is not None]

    def search_users_by_username_paginated(self, current_user_id: str, pattern: str, page: int, per_page: int = 10) -> tuple[list[User], int]:
        """Search users by username pattern with pagination"""
        skip = (page - 1) * per_page
        
        query = {
            'username': {'$regex': pattern, '$options': 'i'},
            '_id': {'$ne': ObjectId(current_user_id)}
        }
        
        total = self.collection.count_documents(query)
        total_pages = math.ceil(total / per_page)
        
        users = self.collection.find(
            query,
            {'_id': 1, 'username': 1, 'email': 1}
        ).skip(skip).limit(per_page)
        
        return [u for u in (User.from_dict(user) for user in users) if u is not None], total_pages

    def find_by_id(self, user_id: str) -> Optional[User]:
        try:
            data = self.collection.find_one({"_id": ObjectId(user_id)})
            return User.from_dict(data) if data else None
        except:
            return None

class MessagesCollection:
    def __init__(self):
        self.db = DatabaseManager.get_instance().db
        self.collection = self.db['messages']

    def insert_message(self, sender_id: str, recipient_id: str, content: str) -> Optional[str]:
        message = {
            'sender_id': ObjectId(sender_id),
            'recipient_id': ObjectId(recipient_id),
            'content': content,
            'timestamp': datetime.now(),
            'is_read': False
        }
        result = self.collection.insert_one(message)
        return str(result.inserted_id) if result else None

    def get_unread_messages(self, user_id: str) -> list:
        messages = self.collection.find({
            'recipient_id': ObjectId(user_id),
            'is_read': False
        }).sort('timestamp', 1)
        return [{
            '_id': str(msg['_id']),
            'sender_id': str(msg['sender_id']),
            'content': msg['content'],
            'timestamp': msg['timestamp']
        } for msg in messages]

    def mark_as_read(self, message_ids: list[str]) -> bool:
        result = self.collection.update_many(
            {'_id': {'$in': [ObjectId(mid) for mid in message_ids]}},
            {'$set': {'is_read': True}}
        )
        return result.modified_count > 0

    def get_recent_chats(self, user_id: str, page: int = 1, per_page: int = 20):
        """Get recent chats for a user with pagination"""
        user_object_id = ObjectId(user_id)
        skip = (page - 1) * per_page
        
        # Pipeline to get the most recent message for each chat
        pipeline = [
            # Match messages where user is either sender or recipient
            {'$match': {
                '$or': [
                    {'sender_id': user_object_id},
                    {'recipient_id': user_object_id}
                ]
            }},
            # Sort by timestamp descending
            {'$sort': {'timestamp': -1}},
            # Group by the other user in the conversation
            {'$group': {
                '_id': {
                    '$cond': [
                        {'$eq': ['$sender_id', user_object_id]},
                        '$recipient_id',
                        '$sender_id'
                    ]
                },
                'last_message': {'$first': '$$ROOT'},
                'unread_count': {
                    '$sum': {
                        '$cond': [
                            {'$and': [
                                {'$eq': ['$recipient_id', user_object_id]},
                                {'$eq': ['$is_read', False]}
                            ]},
                            1,
                            0
                        ]
                    }
                }
            }},
            # Skip and limit for pagination
            {'$skip': skip},
            {'$limit': per_page}
        ]
        
        # Execute pipeline
        chats = list(self.collection.aggregate(pipeline))
        
        # Get total count for pagination
        total_chats = len(list(self.collection.aggregate(pipeline[:-2])))
        total_pages = math.ceil(total_chats / per_page)
        
        # Look up usernames for the other users in the chats
        users_collection = UsersCollection()
        formatted_chats = []
        for chat in chats:
            other_user = users_collection.find_by_id(str(chat['_id']))
            formatted_chat = {
                'user_id': str(chat['_id']),  # Convert ObjectId to string
                'username': other_user.username if other_user else 'Unknown User',
                'unread_count': chat['unread_count']
            }
            
            # Format the last message
            msg = chat['last_message']
            formatted_chat['last_message'] = {
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat(),
                'is_from_me': msg['sender_id'] == user_object_id
            }
            formatted_chats.append(formatted_chat)
        
        return formatted_chats, total_pages
