import struct
from typing import Dict, Any, Tuple
from .message_format import MessageFormat

class WireProtocol:
    VERSION = 1
    HEADER_FORMAT = '!BBI'  # version (1 byte), message_type (1 byte), body_length (4 bytes)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @staticmethod
    def create_header(message_type: int, length: int) -> bytes:
        """Create a header for wire protocol message"""
        return struct.pack('!BHH', WireProtocol.VERSION, message_type, length)

    @staticmethod
    def parse_header(header: bytes) -> tuple:
        """Parse a wire protocol header"""
        version, message_type, length = struct.unpack('!BHH', header)
        return version, message_type, length

    @staticmethod
    def marshal(message_type: int, message_format: MessageFormat, data: Dict[str, Any]) -> bytes:
        body = message_format.pack(data)
        header = WireProtocol.create_header(message_type, len(body))
        return header + body

    @staticmethod
    def unmarshal(message_format, data: bytes) -> dict:
        """Unmarshal wire protocol format data"""
        return message_format.unpack(data)
