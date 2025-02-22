from typing import Dict, Any, Optional
from .constants import *
from client.grpc_client import GRPCClient

class GRPCMessageHandler:
    def __init__(self, logger=None):
        self.logger = logger

    def handle_message(self, message_type: int, data: Dict[str, Any], grpc_client: GRPCClient) -> Optional[Dict]:
        """Handle gRPC message based on message type
        
        Args:
            message_type (int): Type of the message to handle
            data (Dict[str, Any]): Message data
            grpc_client (GRPCClient): gRPC client instance
            
        Returns:
            Optional[Dict]: Response from the gRPC call
        """
        if message_type == MSG_CREATE_ACCOUNT_REQUEST:
            return self._handle_create_account(data, grpc_client)
        # Add more message handlers here
        
        raise ValueError(f"Unsupported gRPC message type: {message_type}")
    
    def _handle_create_account(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        response = grpc_client.create_account(
            data['email'],
            data['username'],
            data['password']
        )
        if self.logger:
            self.logger.debug(f"gRPC create account response: {response}")
        return response
