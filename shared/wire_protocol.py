import struct
from typing import Dict, Any, Tuple
from .message_format import MessageFormat

class WireProtocol:
    VERSION = 1
    HEADER_FORMAT = '!BBI'  # version (1 byte), message_type (1 byte), body_length (4 bytes)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @staticmethod
    def marshal(message_type: int, message_format: MessageFormat, data: Dict[str, Any]) -> bytes:
        body = message_format.pack(data)
        header = struct.pack(WireProtocol.HEADER_FORMAT, WireProtocol.VERSION, message_type, len(body))
        return header + body

    @staticmethod
    def unmarshal(data: bytes) -> Tuple[int, int, bytes]:
        if len(data) < WireProtocol.HEADER_SIZE:
            raise ValueError("Incomplete message header")
        
        version, message_type, body_length = struct.unpack(WireProtocol.HEADER_FORMAT, 
                                                          data[:WireProtocol.HEADER_SIZE])
        
        if version != WireProtocol.VERSION:
            raise ValueError(f"Unsupported protocol version: {version}")
        
        body = data[WireProtocol.HEADER_SIZE:WireProtocol.HEADER_SIZE + body_length]
        return version, message_type, body
