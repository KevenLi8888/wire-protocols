from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class Document:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        raise NotImplementedError

class UserDocument(Document):
    def __init__(self, username: str, password_hash: str, created_at: datetime,
                 last_login: datetime, unread_count: int, _id: Optional[ObjectId] = None):
        self._id = _id
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at
        self.last_login = last_login
        self.unread_count = unread_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "unread_count": self.unread_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserDocument':
        _id = data.pop('_id', None)
        return cls(_id=_id, **data)

# class MessageDocument(Document):
#     # ...existing code...
