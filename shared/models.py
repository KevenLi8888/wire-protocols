from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, TypeVar, Type

T = TypeVar('T', bound='BaseModel')

@dataclass
class BaseModel:
    def to_dict(self):
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls: Type[T], data: dict) -> Optional[T]:
        if not data:
            return None
        if '_id' in data:
            data['_id'] = str(data['_id'])
        return cls(**data)

@dataclass
class User(BaseModel):
    username: str
    email: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    _id: Optional[str] = None
    password_hash: Optional[str] = None

@dataclass
class Message(BaseModel):
    sender_id: str
    recipient_id: str
    content: str
    timestamp: datetime
    read: bool = False
    _id: Optional[str] = None  # Changed from id to _id for consistency
