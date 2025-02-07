from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    username: str
    email: str
    created_at: datetime
    last_login: datetime
    id: Optional[str] = None
    password_hash: Optional[str] = None

@dataclass
class Message:
    sender_id: str
    recipient_id: str
    content: str
    timestamp: datetime
    read: bool = False
    id: Optional[str] = None
