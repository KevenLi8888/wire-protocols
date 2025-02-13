import json
import struct
from typing import Tuple, Dict, Any
from .wire_protocol import WireProtocol
from .message_format import *
from .constants import MESSAGE_FORMATS

class CommunicationInterface:
    """Interface for handling network communication using either JSON or wire protocol formats"""
    def __init__(self, protocol_type='json', logger=None):
        """Initialize the communication interface
        
        Args:
            protocol_type (str): Protocol type to use ('json' or wire protocol)
            logger: Logger instance for debug and error logging
        """
        self.protocol_type = protocol_type
        self.logger = logger
        if self.logger:
            self.logger.debug(f"Initialized communication interface with protocol: {protocol_type}")

    def _recvall(self, socket, n: int) -> bytes:
        """Helper method to receive n bytes or return None if EOF is hit
        
        This method handles partial receives and continues reading until all expected bytes
        are received or connection is closed.
        """
        data = bytearray()
        while len(data) < n:
            packet = socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return bytes(data)

    def send(self, message_type: int, data: Dict[str, Any], socket) -> None:
        """Send a message through the specified socket using the configured protocol
        
        Args:
            message_type (int): Type identifier for the message
            data (Dict[str, Any]): Message data to send
            socket: Socket connection to send through
            
        The method handles two protocols:
        1. JSON: Messages are sent with a length prefix followed by JSON encoded data
        2. Wire Protocol: Messages are marshalled according to predefined message formats
        """
        try:
            if self.protocol_type == 'json':
                # Encode message as JSON with type and data, prefixed with length
                message = json.dumps({'type': message_type, 'data': data}).encode('utf-8')
                length_prefix = struct.pack('!I', len(message))  # Network byte order (big-endian)
                socket.sendall(length_prefix + message)
            else:
                # Use wire protocol with predefined message formats
                message_format = globals()[MESSAGE_FORMATS[message_type]]
                message = WireProtocol.marshal(message_type, message_format, data)
                if self.logger:
                    self.logger.debug(f"Marshalled message: {message}")
                socket.sendall(message)
            
            if self.logger:
                try:
                    peer_name = socket.getpeername()
                    self.logger.debug(f"Sent message type {message_type} to {peer_name[0]}:{peer_name[1]}: {data}")
                except:
                    self.logger.debug(f"Sent message type {message_type}: {data}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error sending message: {str(e)}")

    def receive(self, socket) -> Tuple[Dict[str, Any], int]:
        """Receive a message from the specified socket using the configured protocol
        
        Args:
            socket: Socket connection to receive from
            
        Returns:
            Tuple[Dict[str, Any], int]: Tuple containing (message data, message type)
                                      Returns ({}, -1) on error
                                      
        The method handles two protocols:
        1. JSON: Expects length-prefixed JSON messages
        2. Wire Protocol: Expects messages with headers containing version, type, and length
        """
        try:
            if self.protocol_type == 'json':
                # Read 4-byte length prefix
                length_bytes = self._recvall(socket, 4)
                if not length_bytes:
                    return {}, -1
                
                # Unpack length prefix and read the full message
                message_length = struct.unpack('!I', length_bytes)[0]  # Network byte order (big-endian)
                message = self._recvall(socket, message_length)
                if not message:
                    return {}, -1

                try:
                    parsed = json.loads(message.decode('utf-8'))
                    if self.logger:
                        try:
                            peer_name = socket.getpeername()
                            self.logger.debug(f"Received message type {parsed['type']} from {peer_name[0]}:{peer_name[1]}: {parsed['data']}")
                        except:
                            self.logger.debug(f"Received message type {parsed['type']}: {parsed['data']}")
                    return parsed['data'], parsed['type']
                except json.JSONDecodeError:
                    if self.logger:
                        self.logger.error("Failed to decode JSON message")
                    return {}, -1
            else:
                # Read wire protocol header first
                header = self._recvall(socket, WireProtocol.HEADER_SIZE)
                if not header:
                    return {}, -1
                
                try:
                    # Parse header to get message metadata
                    version, message_type, length = WireProtocol.parse_header(header)
                    
                    # Read message body based on length from header
                    body = self._recvall(socket, length)
                    if not body:
                        return {}, -1

                    # Validate message type and get corresponding format
                    if message_type not in MESSAGE_FORMATS:
                        if self.logger:
                            self.logger.error(f"Invalid message type: {message_type}")
                        return {}, -1

                    message_format = globals()[MESSAGE_FORMATS[message_type]]
                    if self.logger:
                        try:
                            peer_name = socket.getpeername()
                            self.logger.debug(f"Received message type {message_type} from {peer_name[0]}:{peer_name[1]}")
                        except:
                            self.logger.debug(f"Received message type {message_type}")
                    unpacked, _ = message_format.unpack(body)
                    if self.logger:
                        self.logger.debug(f"Unpacked message: {unpacked}")
                    return unpacked, message_type
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Failed to unmarshal message: {str(e)}", exc_info=True)
                    return {}, -1
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error receiving message: {str(e)}")
            return {}, -1
