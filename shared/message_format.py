import struct
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class MessageField:
    name: str
    format_char: str

class MessageFormat:
    DELIMITER = b'\0'
    ESCAPE = b'\\'
    
    def __init__(self, fields: Dict[str, MessageField]):
        self.fields = fields
    
    @classmethod
    def escape_bytes(cls, data: bytes) -> bytes:
        # Escape both escape char and delimiter
        escaped = data.replace(cls.ESCAPE, cls.ESCAPE + cls.ESCAPE)
        escaped = escaped.replace(cls.DELIMITER, cls.ESCAPE + cls.DELIMITER)
        return escaped
    
    @classmethod
    def unescape_bytes(cls, data: bytes) -> bytes:
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i:i+1] == cls.ESCAPE:
                if i + 1 < len(data):
                    result.append(data[i+1])
                    i += 2
                    continue
            result.append(data[i])
            i += 1
        return bytes(result)

    def pack(self, data: Dict[str, Any]) -> bytes:
        result = b''
        for field_name, field in self.fields.items():
            value = data.get(field_name, '')
            if field.format_char == 's':
                value_bytes = value.encode('utf-8')
                escaped_bytes = self.escape_bytes(value_bytes)
                result += escaped_bytes + self.DELIMITER
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
            if field.format_char == 's':
                result[field_name] = unescaped.decode('utf-8')
            else:
                result[field_name] = struct.unpack(f'!{field.format_char}', unescaped)[0]
        return result

# Message format definitions
CREATE_ACCOUNT_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'username': MessageField('username', 's'),
    'password': MessageField('password', 's')
})

LOGIN_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'password': MessageField('password', 's')
})

RESPONSE_FORMAT = MessageFormat({
    'code': MessageField('code', 'I'),
    'message': MessageField('message', 's')
})

DELETE_ACCOUNT_REQUEST = MessageFormat({
    'email': MessageField('email', 's'),
    'password': MessageField('password', 's')
})
