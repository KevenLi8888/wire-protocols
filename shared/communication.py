import json
import struct
from typing import Tuple, Dict, Any
from .wire_protocol import WireProtocol
from .message_format import *
from .constants import MESSAGE_FORMATS

class CommunicationInterface:
    def __init__(self, protocol_type='json', logger=None):
        self.protocol_type = protocol_type
        self.logger = logger
        if self.logger:
            self.logger.debug(f"Initialized communication interface with protocol: {protocol_type}")

    def _recvall(self, socket, n: int) -> bytes:
        """Helper method to receive n bytes or return None if EOF is hit"""
        data = bytearray()
        while len(data) < n:
            packet = socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return bytes(data)

    def send(self, message_type: int, data: Dict[str, Any], socket) -> None:
        if self.protocol_type == 'json':
            message = json.dumps({'type': message_type, 'data': data}).encode('utf-8')
            # Prepend message length as 4-byte integer
            length_prefix = struct.pack('!I', len(message))
            socket.sendall(length_prefix + message)
        else:
            message_format = globals()[MESSAGE_FORMATS[message_type]]
            message = WireProtocol.marshal(message_type, message_format, data)
            # print debug log of the marshalled message string
            self.logger.debug(f"Marshalled message: {message}")
            socket.sendall(message)
        if self.logger:
            peer_name = socket.getpeername()
            self.logger.debug(f"Sent message type {message_type} to {peer_name[0]}:{peer_name[1]}: {data}")

    def receive(self, socket) -> Tuple[Dict[str, Any], int]:
        if self.protocol_type == 'json':
            # First receive the length prefix (4 bytes)
            length_bytes = self._recvall(socket, 4)
            if not length_bytes:
                return {}, -1
            
            message_length = struct.unpack('!I', length_bytes)[0]
            # Now receive the actual message
            message = self._recvall(socket, message_length)
            if not message:
                return {}, -1

            try:
                parsed = json.loads(message.decode('utf-8'))
                if self.logger:
                    peer_name = socket.getpeername()
                    self.logger.debug(f"Received message type {parsed['type']} from {peer_name[0]}:{peer_name[1]}: {parsed['data']}")
                return parsed['data'], parsed['type']
            except json.JSONDecodeError:
                if self.logger:
                    self.logger.error("Failed to decode JSON message")
                return {}, -1
        else:
            # First receive the header (5 bytes)
            header = self._recvall(socket, 5)
            if not header:
                return {}, -1
            
            version, message_type, length = WireProtocol.parse_header(header)
            # Now receive the message body based on the length from header
            body = self._recvall(socket, length)
            if not body:
                return {}, -1

            try:
                message_format = globals()[MESSAGE_FORMATS[message_type]]
                if self.logger:
                    peer_name = socket.getpeername()
                    self.logger.debug(f"Received message type {message_type} from {peer_name[0]}:{peer_name[1]}: {message_format.unpack(body)}")
                return message_format.unpack(body), message_type
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to unmarshal message: {str(e)}")
                return {}, -1
