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

    def send(self, message_type: int, data: Dict[str, Any], socket) -> None:
        if self.protocol_type == 'json':
            message = json.dumps({'type': message_type, 'data': data}).encode('utf-8')
        else:
            message_format = globals()[MESSAGE_FORMATS[message_type]]
            message = WireProtocol.marshal(message_type, message_format, data)
        socket.send(message)
        if self.logger:
            peer_name = socket.getpeername()
            self.logger.debug(f"Sent message type {message_type} to {peer_name[0]}:{peer_name[1]}: {data}")

    def receive(self, socket) -> Tuple[Dict[str, Any], int]:
        message = socket.recv(1024)
        if self.protocol_type == 'json':
            parsed = json.loads(message.decode('utf-8'))
            if self.logger:
                peer_name = socket.getpeername()
                self.logger.debug(f"Received message type {parsed['type']} from {peer_name[0]}:{peer_name[1]}: {parsed['data']}")
            return parsed['data'], parsed['type']
        else:
            version, message_type, body = WireProtocol.unmarshal(message)
            message_format = globals()[MESSAGE_FORMATS[message_type]]
            if self.logger:
                peer_name = socket.getpeername()
                self.logger.debug(f"Received message type {message_type} from {peer_name[0]}:{peer_name[1]}: {message_format.unpack(body)}")
            return message_format.unpack(body), message_type
