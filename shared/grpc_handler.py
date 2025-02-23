from typing import Dict, Any, Optional
from .constants import *
from client.grpc_client import GRPCClient

class GRPCMessageHandler:
    def __init__(self, logger=None):
        self.logger = logger

    def handle_message(self, message_type: int, data: Dict[str, Any], grpc_client: GRPCClient) -> Optional[Dict]:
        """Handle gRPC message based on message type"""
        handlers = {
            MSG_CREATE_ACCOUNT_REQUEST: self._handle_create_account,
            MSG_LOGIN_REQUEST: self._handle_login,
            MSG_DELETE_ACCOUNT_REQUEST: self._handle_delete_account,
            MSG_SEND_MESSAGE_REQUEST: self._handle_send_message,
            MSG_SEARCH_USERS_REQUEST: self._handle_search_users,
            MSG_GET_RECENT_CHATS_REQUEST: self._handle_get_recent_chats,
            MSG_GET_PREVIOUS_MESSAGES_REQUEST: self._handle_get_previous_messages,
            MSG_GET_CHAT_UNREAD_COUNT_REQUEST: self._handle_get_chat_unread_count,
            MSG_GET_UNREAD_MESSAGES_REQUEST: self._handle_get_unread_messages,
            MSG_DELETE_MESSAGE_REQUEST: self._handle_delete_messages,
        }
        
        handler = handlers.get(message_type)
        if not handler:
            raise ValueError(f"Unsupported gRPC message type: {message_type}")
            
        return handler(data, grpc_client)

    def _handle_create_account(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.create_account(
            data['email'],
            data['username'],
            data['password']
        )

    def _handle_login(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.login(
            data['email'],
            data['password']
        )

    def _handle_delete_account(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.delete_account(
            data['email'],
            data['password']
        )

    def _handle_send_message(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.send_message(
            data['content'],
            data['recipient_id'],
            data['sender_id']
        )

    def _handle_search_users(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.search_users(
            data['pattern'],
            data['page'],
            data['current_user_id']
        )

    def _handle_get_recent_chats(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.get_recent_chats(
            data['user_id'],
            data['page']
        )

    def _handle_get_previous_messages(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.get_previous_messages(
            data['user_id'],
            data['other_user_id'],
            data['page']
        )

    def _handle_get_chat_unread_count(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.get_chat_unread_count(
            data['user_id'],
            data['other_user_id']
        )

    def _handle_get_unread_messages(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.get_unread_messages(
            data['user_id'],
            data['other_user_id'],
            data['num_messages']
        )

    def _handle_delete_messages(self, data: Dict[str, Any], grpc_client: GRPCClient) -> Dict:
        return grpc_client.delete_messages(
            data['message_ids']
        )
