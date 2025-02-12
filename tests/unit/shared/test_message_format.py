import pytest
from shared.message_format import MessageFormat, MessageField

def test_message_format_pack_unpack():
    format_def = MessageFormat({
        'username': MessageField('username', 's'),
        'age': MessageField('age', 'i')
    })
    
    test_data = {
        'username': 'test_user',
        'age': 25
    }
    
    packed = format_def.pack(test_data)
    unpacked = format_def.unpack(packed)
    
    assert unpacked['username'] == test_data['username']
    assert unpacked['age'] == test_data['age']

def test_message_format_escape_unescape():
    test_bytes = b'test\0data\\more'
    escaped = MessageFormat.escape_bytes(test_bytes)
    unescaped = MessageFormat.unescape_bytes(escaped)
    
    assert unescaped == test_bytes

def test_create_account_request_format():
    from shared.message_format import CREATE_ACCOUNT_REQUEST
    
    test_data = {
        'email': 'test@example.com',
        'username': 'testuser',
        'password': 'password123'
    }
    
    packed = CREATE_ACCOUNT_REQUEST.pack(test_data)
    unpacked = CREATE_ACCOUNT_REQUEST.unpack(packed)
    
    assert unpacked == test_data