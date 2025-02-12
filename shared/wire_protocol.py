import struct
from typing import Dict, Any, Tuple
from .message_format import MessageFormat

class WireProtocol:
    VERSION = 1
    HEADER_FORMAT = '!BHI'  # version (1 byte), message_type (2 bytes), body_length (4 bytes)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @staticmethod
    def create_header(message_type: int, length: int) -> bytes:
        """Create a header for wire protocol message"""
        return struct.pack(WireProtocol.HEADER_FORMAT, WireProtocol.VERSION, message_type, length)

    @staticmethod
    def parse_header(header: bytes) -> tuple:
        """Parse a wire protocol header"""
        if len(header) != WireProtocol.HEADER_SIZE:
            raise ValueError(f"Header must be exactly {WireProtocol.HEADER_SIZE} bytes")
        return struct.unpack(WireProtocol.HEADER_FORMAT, header)

    @staticmethod
    def marshal(message_type: int, message_format: MessageFormat, data: Dict[str, Any]) -> bytes:
        """Marshal data into wire protocol format"""
        if data is None:
            data = {}
        body = message_format.pack(data)
        header = WireProtocol.create_header(message_type, len(body))
        return header + body

    @staticmethod
    def unmarshal(message_format: MessageFormat, data: bytes) -> dict:
        """Unmarshal wire protocol format data"""
        if not data:
            return {}
        return message_format.unpack(data)
