import struct
from dataclasses import dataclass
from typing import Dict, Any

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
    """
    name: str
    format_char: str
    is_nested: bool = False
    is_list: bool = False
    nested_format: 'MessageFormat' = None

class MessageFormat:
    DELIMITER = b'\0'
    ESCAPE = b'\\'
    LIST_DELIMITER = b'\1'  # New delimiter for list items
    
    def __init__(self, fields: Dict[str, MessageField]):
        self.fields = fields
    
    @classmethod
    def escape_bytes(cls, data: bytes) -> bytes:
        # First escape the escape character itself
        escaped = data.replace(cls.ESCAPE, cls.ESCAPE + cls.ESCAPE)
        # Then escape the delimiters
        escaped = escaped.replace(cls.DELIMITER, cls.ESCAPE + cls.DELIMITER)
        escaped = escaped.replace(cls.LIST_DELIMITER, cls.ESCAPE + cls.LIST_DELIMITER)
        return escaped
    
    @classmethod
    def unescape_bytes(cls, data: bytes) -> bytes:
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i:i+1] == cls.ESCAPE:
                if i + 1 < len(data):
                    next_byte = data[i+1:i+2]
                    # Only unescape if it's followed by an escape char or delimiter
                    if next_byte in [cls.ESCAPE, cls.DELIMITER, cls.LIST_DELIMITER]:
                        result.append(data[i+1])
                        i += 2
                        continue
            result.append(data[i])
            i += 1
        return bytes(result)

    def pack(self, data: Dict[str, Any]) -> bytes:
        result = b''
        for field_name, field in self.fields.items():
            value = data.get(field_name, '' if not field.is_list else [])
            
            if field.is_list:
                list_items = []
                for item in value:
                    if field.is_nested and field.nested_format:
                        item_bytes = field.nested_format.pack(item)
                    elif field.format_char == 's':
                        item_bytes = item.encode('utf-8')
                    else:
                        item_bytes = struct.pack(f'!{field.format_char}', item)
                    list_items.append(self.escape_bytes(item_bytes))
                value_bytes = self.LIST_DELIMITER.join(list_items)
            elif field.is_nested and field.nested_format:
                value_bytes = field.nested_format.pack(value)
            elif field.format_char == 's':
                value_bytes = value.encode('utf-8')
            else:
                value_bytes = struct.pack(f'!{field.format_char}', value)
                
            escaped_bytes = self.escape_bytes(value_bytes)
            result += escaped_bytes + self.DELIMITER
        return result

    def unpack(self, data: bytes) -> Dict[str, Any]:
        result = {}
        # Split on unescaped delimiters
        parts = []
        current = bytearray()
        i = 0
        while i < len(data):
            if data[i:i+1] == self.ESCAPE:
                if i + 1 < len(data):
                    current.append(data[i+1])
                    i += 2
                    continue
            elif data[i:i+1] == self.DELIMITER:
                parts.append(bytes(current))
                current = bytearray()
                i += 1
                continue
            current.append(data[i])
            i += 1

        for (field_name, field), value_bytes in zip(self.fields.items(), parts):
            unescaped = self.unescape_bytes(value_bytes)
            
            if field.is_list:
                items = unescaped.split(self.LIST_DELIMITER)
                result[field_name] = []
                for item in items:
                    if not item:  # Skip empty items
                        continue
                    if field.is_nested and field.nested_format:
                        result[field_name].append(field.nested_format.unpack(item))
                    elif field.format_char == 's':
                        result[field_name].append(item.decode('utf-8'))
                    else:
                        result[field_name].append(struct.unpack(f'!{field.format_char}', item)[0])
            elif field.is_nested and field.nested_format:
                result[field_name] = field.nested_format.unpack(unescaped)
            elif field.format_char == 's':
                result[field_name] = unescaped.decode('utf-8')
            else:
                result[field_name] = struct.unpack(f'!{field.format_char}', unescaped)[0]
        return result

# Wire Protocol Message format definitions
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

DELETE_ACCOUNT_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'password': MessageField('password', 's')
})

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
