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
    """Message format handler for packing and unpacking structured data.
    
    Handles serialization and deserialization of structured data using a defined message format.
    Uses custom delimiters to separate records and list items.
    """
    
    # Use ASCII control characters as delimiters to avoid conflicts with regular data
    DELIMITER = b'\x1E'  # Record Separator (RS) - Separates records in a data stream
    LIST_DELIMITER = b'\x1F'  # Unit Separator (US) - Separates items within a list
    
    def __init__(self, fields: Dict[str, MessageField]):
        self.fields = fields
    

    def pack(self, data: Dict[str, Any]) -> bytes:
        """Pack structured data into bytes according to the defined message format.
        
        The packing process follows these steps for each field:
        1. For basic types (using format_char): directly pack using struct
        2. For strings: add 4-byte length prefix, then the encoded string
        3. For nested structures: recursively pack and add length prefix
        4. For lists: add list length, then pack each item with its own length prefix
        """
        packed_data = b''
        for field_name, field in self.fields.items():
            value = data.get(field_name)
            if value is None:
                continue

            if field.format_char:
                try:
                    if field.format_char == 's':
                        if field.is_list:
                            # Handle list of strings
                            packed_data += struct.pack('!I', len(value))  # List length
                            for item in value:
                                if isinstance(item, str):
                                    item = item.encode('utf-8')
                                item_length = len(item)
                                packed_data += struct.pack('!I', item_length)  # String length
                                packed_data += item
                        else:
                            # Ensure the value is encoded to bytes
                            if not isinstance(value, (str, bytes)):
                                raise ValueError(f"Field '{field_name}' expects string or bytes, got {type(value)}")
                        if isinstance(value, str):
                            value = value.encode('utf-8')
                            # Add length prefix for strings
                            length = len(value)
                            packed_data += struct.pack('!I', length)  # 4-byte length prefix
                            packed_data += value
                    else:
                        # For non-string types, pack directly
                        packed_data += struct.pack(f'!{field.format_char}', value)
                except struct.error as e:
                    raise ValueError(f"Error packing field '{field_name}': {e}")
            elif field.is_nested:
                if field.is_list:
                    if isinstance(value, list):
                        # Add list length prefix
                        packed_data += struct.pack('!I', len(value))
                        for item in value:
                            item_packed = field.nested_format.pack(item)
                            # Add length prefix for each item
                            packed_data += struct.pack('!I', len(item_packed))
                            packed_data += item_packed
                    else:
                        raise ValueError(f"Expected a list for field '{field_name}'")
                else:
                    nested_packed = field.nested_format.pack(value)
                    # Add length prefix for nested structure
                    packed_data += struct.pack('!I', len(nested_packed))
                    packed_data += nested_packed
            else:
                raise ValueError(f"Field '{field_name}' must have either a format character or be nested")
        return packed_data

    def unpack(self, data: bytes, offset: int = 0) -> Tuple[Dict[str, Any], int]:
        """Unpack bytes data into structured format according to the message definition.
        
        The unpacking process mirrors the packing process:
        1. For basic types: directly unpack using struct
        2. For strings: read length prefix, then decode string data
        3. For nested structures: read length, then recursively unpack
        4. For lists: read list length, then unpack each item using its length prefix
        """
        unpacked_data = {}
        original_offset = offset
        
        for field_name, field in self.fields.items():
            if offset >= len(data):
                break
                
            if field.format_char:
                if field.format_char == 's':
                    if field.is_list:
                        # Read list length
                        list_length = struct.unpack('!I', data[offset:offset + 4])[0]
                        offset += 4
                        string_list = []
                        
                        # Read each string in the list
                        for _ in range(list_length):
                            str_length = struct.unpack('!I', data[offset:offset + 4])[0]
                            offset += 4
                            string_value = data[offset:offset + str_length].decode('utf-8')
                            string_list.append(string_value)
                            offset += str_length
                        
                        unpacked_data[field_name] = string_list
                    else:
                        # Read string length
                        length = struct.unpack('!I', data[offset:offset + 4])[0]
                        offset += 4
                        value = data[offset:offset + length].decode('utf-8')
                        offset += length
                        unpacked_data[field_name] = value
                else:
                    format_size = struct.calcsize(f'!{field.format_char}')
                    value = struct.unpack(f'!{field.format_char}', data[offset:offset + format_size])[0]
                    offset += format_size
                    unpacked_data[field_name] = value
            elif field.is_nested:
                if field.is_list:
                    # Read list length
                    list_length = struct.unpack('!I', data[offset:offset + 4])[0]
                    offset += 4
                    unpacked_list = []
                    
                    for _ in range(list_length):
                        # Read item length
                        item_length = struct.unpack('!I', data[offset:offset + 4])[0]
                        offset += 4
                        item_data = data[offset:offset + item_length]
                        unpacked_item, _ = field.nested_format.unpack(item_data)
                        unpacked_list.append(unpacked_item)
                        offset += item_length
                    
                    unpacked_data[field_name] = unpacked_list
                else:
                    # Read nested structure length
                    struct_length = struct.unpack('!I', data[offset:offset + 4])[0]
                    offset += 4
                    nested_data = data[offset:offset + struct_length]
                    unpacked_nested, _ = field.nested_format.unpack(nested_data)
                    unpacked_data[field_name] = unpacked_nested
                    offset += struct_length
            else:
                raise ValueError(f"Field '{field_name}' must have either a format character or be nested")
                
        return unpacked_data, offset

# Wire Protocol Message Formats
# Each format defines the structure of messages exchanged between client and server

# Authentication Related Formats
CREATE_ACCOUNT_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'username': MessageField('username', 's'),
    'password': MessageField('password', 's')
})

LOGIN_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'password': MessageField('password', 's')
})

# Standard Response Format for Operations
CODEMSG_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),  # Status code (success/error)
    'message': MessageField('message', 's')  # Status message or error description
})

# Chat and Messaging Related Formats
SEND_MESSAGE_REQUEST = MessageFormat({
    'content': MessageField('content', 's'),
    'recipient_id': MessageField('recipient_id', 's'),
    'sender_id': MessageField('sender_id', 's')
})

# User Search and Management Formats
SEARCH_USERS_REQUEST = MessageFormat({
    'pattern': MessageField('pattern', 's'),  # Search pattern/query
    'page': MessageField('page', 'i'),  # Pagination page number
    'current_user_id': MessageField('current_user_id', 's')
})

# Chat History and Recent Conversations
GET_RECENT_CHATS_REQUEST = MessageFormat({
    'user_id': MessageField('user_id', 's'),
    'page': MessageField('page', 'i')  # For pagination
})

# Message Management
DELETE_MESSAGE_REQUEST = MessageFormat({
    'message_ids': MessageField('message_ids', 's', is_list=True)  # List of message IDs to delete
})

# Account Management
DELETE_ACCOUNT_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'password': MessageField('password', 's')  # For verification
})

# Example/Reference Formats
USER_DATA_FORMAT = MessageFormat({
    'user_id': MessageField('user_id', 's'),
    'username': MessageField('username', 's'),
    'email': MessageField('email', 's')
})

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

GET_RECENT_CHATS_RESPONSE = MessageFormat({
    'code': MessageField('code', 'i'),
    'message': MessageField('message', 's'),
    'data': MessageField('data', None, is_nested=True, nested_format=MessageFormat({
        'chats': MessageField('chats', None, is_nested=True, is_list=True, nested_format=MessageFormat({
            'user_id': MessageField('user_id', 's'),
            'username': MessageField('username', 's'),
            'unread_count': MessageField('unread_count', 'i'),
            'last_message': MessageField('last_message', None, is_nested=True, nested_format=MessageFormat({
                'content': MessageField('content', 's'),
                'timestamp': MessageField('timestamp', 's'),
                'is_from_me': MessageField('is_from_me', '?')
            })),
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
