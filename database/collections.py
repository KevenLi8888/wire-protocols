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
        users = self.collection.find({})
        return [User.from_dict(user) for user in users]

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
