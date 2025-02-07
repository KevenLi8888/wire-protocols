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
    def __init__(self, username: str, email: str, password_hash: str, created_at: datetime,
                 last_login: datetime, _id: Optional[ObjectId] = None):
        self._id = _id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self.last_login = last_login

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "last_login": self.last_login
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserDocument':
        _id = data.pop('_id', None)
        return cls(_id=_id, **data)
