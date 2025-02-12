import struct
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

@dataclass
class MessageField:
    """Message field definition with format specifiers.
    
    Common format_char values (from struct module):
    'c' - char (1 byte)
    's' - string (bytes)
    'b' - signed char (1 byte)
    'B' - unsigned char (1 byte)
    'h' - short (2 bytes)
    'H' - unsigned short (2 bytes)
    'i' - int (4 bytes) 
    'I' - unsigned int (4 bytes)
    'l' - long (4 bytes)
    'L' - unsigned long (4 bytes)
    'q' - long long (8 bytes)
    'Q' - unsigned long long (8 bytes)
    'f' - float (4 bytes)
    'd' - double (8 bytes)
    '?' - boolean (1 byte)
    """
    name: str
    format_char: Optional[str] = None
    is_nested: bool = False
    is_list: bool = False
    nested_format: 'MessageFormat' = None

class MessageFormat:
    DELIMITER = b'\0'
    LIST_DELIMITER = b'\1'
    
    def __init__(self, fields: Dict[str, MessageField]):
        self.fields = fields
    

    def pack(self, data: Dict[str, Any]) -> bytes:
        packed_data = b''
        for field_name, field in self.fields.items():
            value = data.get(field_name)
            if value is None:
                # Consider how to handle missing data, perhaps raise an exception or use a default value
                continue

            if field.format_char:
                try:
                    if field.format_char == 's':
                        # Ensure the value is encoded to bytes
                        if isinstance(value, str):
                            value = value.encode('utf-8')
                        packed_data += struct.pack(f'!{len(value)}s', value)
                        packed_data += MessageFormat.DELIMITER
                    elif field.format_char == '?':
                        packed_data += struct.pack(f'!{field.format_char}', value)
                    else:
                        packed_data += struct.pack(f'!{field.format_char}', value)
                except struct.error as e:
                    raise ValueError(f"Error packing field '{field_name}': {e}")
            elif field.is_nested:
                if field.is_list:
                    if isinstance(value, list):
                        for item in value:
                            packed_data += field.nested_format.pack(item)
                            packed_data += MessageFormat.LIST_DELIMITER
                        # Remove the last LIST_DELIMITER if the list is not empty
                        if value:
                            packed_data = packed_data[:-len(MessageFormat.LIST_DELIMITER)]
                    else:
                        raise ValueError(f"Expected a list for field '{field_name}'")
                else:
                    packed_data += field.nested_format.pack(value)
            else:
                raise ValueError(f"Field '{field_name}' must have either a format character or be nested")
        return packed_data

    def unpack(self, data: bytes, offset: int = 0) -> Tuple[Dict[str, Any], int]:
        unpacked_data = {}
        while offset < len(data):
            for field_name, field in self.fields.items():
                if field.format_char:
                    format_size = struct.calcsize(field.format_char)
                    if field.format_char == 's':
                        delimiter_index = data.find(MessageFormat.DELIMITER, offset)
                        if delimiter_index == -1:
                            raise ValueError(f"Delimiter not found for string field '{field_name}'")
                        
                        string_length = delimiter_index - offset
                        format_string = f'{string_length}s'
                        
                        try:
                            value = struct.unpack(f'!{format_string}', data[offset:delimiter_index])[0].decode('utf-8')
                        except struct.error as e:
                            raise ValueError(f"Error unpacking string field '{field_name}': {e}")
                        
                        unpacked_data[field_name] = value
                        offset = delimiter_index + len(MessageFormat.DELIMITER)
                    else:
                        try:
                            if len(data[offset:offset + format_size]) != format_size:
                                raise ValueError(f"Buffer size mismatch for field '{field_name}'")
                            value = struct.unpack(f'!{field.format_char}', data[offset:offset + format_size])[0]
                        except struct.error as e:
                            raise ValueError(f"Error unpacking field '{field_name}': {e}")
                        unpacked_data[field_name] = value
                        offset += format_size
                elif field.is_nested:
                    if field.is_list:
                        unpacked_list = []
                        while offset < len(data):
                            delimiter_index = data.find(MessageFormat.LIST_DELIMITER, offset)
                            if delimiter_index == -1:
                                delimiter_index = len(data)  # No more list delimiters, consume the rest of the data
                            
                            item_data = data[offset:delimiter_index]
                            if not item_data:
                                break  # Avoid unpacking empty data
                            try:
                                unpacked_item, new_offset = field.nested_format.unpack(item_data)
                                unpacked_list.append(unpacked_item)
                                offset = new_offset
                            except Exception as e:
                                raise ValueError(f"Error unpacking list item for field '{field_name}': {e}")
                            
                            offset = delimiter_index + len(MessageFormat.LIST_DELIMITER)
                        unpacked_data[field_name] = unpacked_list
                    else:
                        try:
                            unpacked_nested, new_offset = field.nested_format.unpack(data, offset)
                            unpacked_data[field_name] = unpacked_nested
                            offset = new_offset
                        except Exception as e:
                            raise ValueError(f"Error unpacking nested field '{field_name}': {e}")
                else:
                    raise ValueError(f"Field '{field_name}' must have either a format character or be nested")
        return unpacked_data, offset

# Wire Protocol Message format definitions
# Refer to Message Format Mapping in shared/constants.py
CREATE_ACCOUNT_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'username': MessageField('username', 's'),
    'password': MessageField('password', 's')
})

CODEMSG_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's')
})

LOGIN_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'password': MessageField('password', 's')
})

"""
Example Login Response
{
    "code": SUCCESS, 
    "message": MESSAGE_OK,
    "data": {
        "user": {
            "_id": str(user._id),
            "username": user.username,
            "email": user.email
        }
    }
}
"""
LOGIN_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=MessageFormat({
        'user': MessageField('user', None, is_nested=True, nested_format=MessageFormat({
            '_id': MessageField('_id', 's'),
            'username': MessageField('username', 's'),
            'email': MessageField('email', 's')
        }))
    }))
})

# GET_USERS_REQUEST = NOT CURRENTLY USED
# GET_USERS_RESPONSE = NOT CURRENTLY USED

SEND_MESSAGE_REQUEST = MessageFormat({
    'content': MessageField('content', 's'),
    'recipient_id': MessageField('recipient_id', 's'),
    'sender_id': MessageField('sender_id', 's')
})

SEND_MESSAGE_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=MessageFormat({
        'message_id': MessageField('message_id', 's'),
        'sender_id': MessageField('sender_id', 's'),
        'recipient_id': MessageField('recipient_id', 's'),
        'content': MessageField('content', 's'),
        'timestamp': MessageField('timestamp', 's'),
    }))
})

SEARCH_USERS_REQUEST = MessageFormat({
    'pattern': MessageField('pattern', 's'),
    'page': MessageField('page', 'i'),
    'current_user_id': MessageField('current_user_id', 's')
})

SEARCH_USERS_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=MessageFormat({
        'users': MessageField('users', None, is_nested=True, is_list=True, nested_format=MessageFormat({
            '_id': MessageField('_id', 's'),
            'username': MessageField('username', 's'),
            'email': MessageField('email', 's')
        })),
        'total_pages': MessageField('total_pages', 'i')
    }))
})

GET_RECENT_CHATS_REQUEST = MessageFormat({
    'user_id': MessageField('user_id', 's'),
    'page': MessageField('page', 'i')
})

GET_RECENT_CHATS_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=MessageFormat({
        'chats': MessageField('chats', None, is_nested=True, is_list=True, nested_format=MessageFormat({
            'user_id': MessageField('user_id', 's'),
            'username': MessageField('username', 's'),
            'last_message': MessageField('last_message', None, is_nested=True, nested_format=MessageFormat({
                'content': MessageField('content', 's'),
                'timestamp': MessageField('timestamp', 's'),
                'is_from_me': MessageField('is_from_me', '?')
            })),
            'timestamp': MessageField('timestamp', 's')
        })),
        'total_pages': MessageField('total_pages', 'i')
    }))
})

GET_PREVIOUS_MESSAGES_REQUEST = MessageFormat({
    'user_id': MessageField('user_id', 's'),
    'other_user_id': MessageField('other_user_id', 's'),
    'page': MessageField('page', 'i')
})

GET_PREVIOUS_MESSAGES_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=MessageFormat({
        'user_id': MessageField('user_id', 's'),
        'other_user_id': MessageField('other_user_id', 's'),
        'messages': MessageField('messages', None, is_nested=True, is_list=True, nested_format=MessageFormat({
            'message_id': MessageField('message_id', 's'),
            'content': MessageField('content', 's'),
            'timestamp': MessageField('timestamp', 's'),
            'is_from_me': MessageField('is_from_me', '?'),
            'sender': MessageField('sender', None, is_nested=True, nested_format=MessageFormat({
                'user_id': MessageField('user_id', 's'),
                'username': MessageField('username', 's')
            }))
        })),
        'total_pages': MessageField('total_pages', 'i')
    }))
})

GET_CHAT_UNREAD_COUNT_REQUEST = MessageFormat({
    'user_id': MessageField('user_id', 's'),
    'other_user_id': MessageField('other_user_id', 's')
})

GET_CHAT_UNREAD_COUNT_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=MessageFormat({
        'user_id': MessageField('user_id', 's'),
        'other_user_id': MessageField('other_user_id', 's'),
        'count': MessageField('count', 'i')
    }))
})

GET_UNREAD_MESSAGES_REQUEST = MessageFormat({
    'user_id': MessageField('user_id', 's'),
    'other_user_id': MessageField('other_user_id', 's'),
    'num_messages': MessageField('num_messages', 'i')
})

"""
formatted_messages = [{
                'message_id': str(msg['_id']),
                'sender_id': str(msg['sender_id']),
                'recipient_id': str(msg['recipient_id']),
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat(),
                'is_read': msg['is_read'],
                'is_from_me': msg['sender_id'] == user_id
            } for msg in messages]
            
            return {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'data': {
                    'messages': formatted_messages
                }
            }
"""
GET_UNREAD_MESSAGES_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=MessageFormat({
        'messages': MessageField('messages', None, is_nested=True, is_list=True, nested_format=MessageFormat({
            'message_id': MessageField('message_id', 's'),
            'sender_id': MessageField('sender_id', 's'),
            'recipient_id': MessageField('recipient_id', 's'),
            'content': MessageField('content', 's'),
            'timestamp': MessageField('timestamp', 's'),
            'is_read': MessageField('is_read', '?'),
            'is_from_me': MessageField('is_from_me', '?')
        }))
    }))
})

DELETE_MESSAGE_REQUEST = MessageFormat({
    'message_ids': MessageField('message_ids', 's', is_list=True)
})

DELETE_ACCOUNT_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'password': MessageField('password', 's')
})

# Examples below

USER_DATA_FORMAT = MessageFormat({
    'user_id': MessageField('user_id', 's'),
    'username': MessageField('username', 's'),
    'email': MessageField('email', 's')
})

USER_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=USER_DATA_FORMAT)
})

# Example format definitions using lists
USERS_LIST_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, is_list=True, nested_format=USER_DATA_FORMAT)
})
