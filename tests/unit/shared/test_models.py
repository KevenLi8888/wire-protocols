import pytest
from datetime import datetime
from shared.models import User, Message

def test_user_model():
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'created_at': datetime.now(),
        'password_hash': 'hashed_password'
    }
    
    user = User.from_dict(user_data)
    
    assert user.username == user_data['username']
    assert user.email == user_data['email']
    assert user.password_hash == user_data['password_hash']
    
    user_dict = user.to_dict()
    assert user_dict['username'] == user_data['username']
    assert user_dict['email'] == user_data['email']

def test_message_model():
    message_data = {
        'sender_id': 'user1',
        'recipient_id': 'user2',
        'content': 'Hello!',
        'timestamp': datetime.now(),
        'is_read': False
    }
    
    message = Message.from_dict(message_data)
    
    assert message.sender_id == message_data['sender_id']
    assert message.recipient_id == message_data['recipient_id']
    assert message.content == message_data['content']
    assert message.is_read == message_data['is_read']
    
    message_dict = message.to_dict()
    assert message_dict['sender_id'] == message_data['sender_id']
    assert message_dict['content'] == message_data['content']