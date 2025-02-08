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
        result = self.collection.insert_one(user.to_dict())
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

# class MessagesCollection:
#     # ...existing code...
