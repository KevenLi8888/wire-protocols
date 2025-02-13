from typing import Dict, Any
from shared.constants import *
import logging

# Handles messages received from the server
class MessageHandler:
    """
    Handles all message communication between client and server.
    Manages callbacks for various UI updates and message processing.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        # UI update callbacks section
        # Each callback is triggered by specific server responses to update the UI
        self.on_login_success = None         # Called after successful login
        self.on_user_list_update = None      # Called when user list needs updating
        self.on_user_data_update = None      # Called when current user data changes
        self.on_message_received = None      # Called when new message arrives
        self.on_error = None                 # Called to display error messages
        self.on_login_window_close = None    # Called to close login window
        self.on_register_window_close = None # Called to close registration window
        self.on_search_results = None        # Called when search results arrive
        self.on_recent_chats_update = None   # Called when recent chats list updates
        self.on_previous_messages = None
        self.on_message_sent = None          
        self.on_unread_count = None
        self.on_new_message_update = None
        self.on_delete_window_close = None    # Add new callback
        
        # Message handler mapping
        # Routes incoming message types to their respective handler methods
        self.message_handlers = {
            MSG_CREATE_ACCOUNT_RESPONSE: self.handle_create_account_response,
            MSG_LOGIN_RESPONSE: self.handle_login_response,
            MSG_DELETE_ACCOUNT_RESPONSE: self.handle_delete_account_response,
            MSG_GET_USERS_RESPONSE: self.handle_get_users_response,
            MSG_NEW_MESSAGE_UPDATE: self.handle_new_message_update,
            MSG_SEND_MESSAGE_RESPONSE: self.handle_send_message_response,
            MSG_GET_UNREAD_MESSAGES_RESPONSE: self.handle_unread_messages,
            MSG_SEARCH_USERS_RESPONSE: self.handle_search_users_response,
            MSG_GET_RECENT_CHATS_RESPONSE: self.handle_recent_chats_response,
            MSG_ERROR_RESPONSE: self.handle_error_message,
            MSG_GET_PREVIOUS_MESSAGES_RESPONSE: self.handle_previous_messages_response,
            MSG_GET_CHAT_UNREAD_COUNT_RESPONSE: self.handle_chat_unread_count_response,
        }

    # Callback setter methods section
    # These methods allow the UI to register callbacks for different events
    def set_login_success_callback(self, callback):
        """Set handler for successful login response"""
        self.on_login_success = callback

    def set_update_user_list_callback(self, callback):
        """Set handler for user list updates"""
        self.on_user_list_update = callback

    def set_current_user_callback(self, callback):
        """Set handler for current user data updates"""
        self.on_user_data_update = callback

    def set_receive_message_callback(self, callback):
        """Set handler for incoming messages"""
        self.on_message_received = callback

    def set_show_error_callback(self, callback):
        """Set handler for error display"""
        self.on_error = callback

    def set_close_login_window_callback(self, callback):
        """Set handler for closing login window"""
        self.on_login_window_close = callback

    def set_close_register_window_callback(self, callback):
        """Set handler for closing registration window"""
        self.on_register_window_close = callback

    def set_search_results_callback(self, callback):
        """Set handler for search results"""
        self.on_search_results = callback

    def set_recent_chats_callback(self, callback):
        """Set handler for recent chats updates"""
        self.on_recent_chats_update = callback

    def set_previous_messages_callback(self, callback):
        """Set handler for previous messages updates"""
        self.on_previous_messages = callback

    def set_message_sent_callback(self, callback):
        """Set handler for successful message sending"""
        self.on_message_sent = callback

    def set_unread_count_callback(self, callback):
        """Set handler for chat unread count updates"""
        self.on_unread_count = callback

    def set_new_message_update_callback(self, callback):
        """Set handler for new message updates"""
        self.on_new_message_update = callback

    def set_close_delete_window_callback(self, callback):
        """Set handler for closing delete window"""
        self.on_delete_window_close = callback

    def handle_message(self, message_type: int, data: Dict[str, Any]):
        """
        Main message routing method.
        Routes incoming messages to appropriate handlers based on message type.
        
        Args:
            message_type: Integer identifying the type of message
            data: Dictionary containing the message payload
        """
        if message_type in self.message_handlers:
            self.message_handlers[message_type](data)
        else:
            self.logger.warning(f"Unhandled message type: {message_type}")

    # Response handler section
    # Each method handles a specific type of server response
    def handle_create_account_response(self, data: Dict[str, Any]):
        """
        Handle response from server after account creation attempt.
        
        Args:
            data: Dictionary containing response code and optional error message
        Success: Closes registration window
        Failure: Displays error message
        """
        if data['code'] == SUCCESS:
            self.logger.info("Account created successfully")
            if self.on_register_window_close:
                self.on_register_window_close()
        else:
            self.logger.error(f"Account creation failed: {data['message']}")
            if self.on_error:
                self.on_error(data['message'])

    def handle_login_response(self, data: Dict[str, Any]):
        """Handle response from server after login attempt"""
        if data['code'] == SUCCESS:
            self.logger.info("Login successful")
            if self.on_user_data_update and 'data' in data and 'user' in data['data']:
                self.on_user_data_update(data['data']['user'])
            if self.on_login_window_close:
                self.on_login_window_close()
            if self.on_login_success:
                self.on_login_success()
        else:
            self.logger.error(f"Login failed: {data['message']}")
            if self.on_error:
                self.on_error(data['message'])

    def handle_delete_account_response(self, data: Dict[str, Any]):
        """Handle response from server after account deletion attempt"""
        if data['code'] == SUCCESS:
            self.logger.info("Account deleted successfully")
            if self.on_delete_window_close:
                self.on_delete_window_close()
            if self.on_error:
                self.on_error("Account deleted successfully")
        else:
            self.logger.error(f"Account deletion failed: {data['message']}")
            if self.on_error:
                self.on_error(data['message'])

    def handle_get_users_response(self, data: Dict[str, Any]):
        """Handle response containing list of users"""
        if data['code'] == SUCCESS:
            if self.on_user_list_update and 'data' in data and 'users' in data['data']:
                self.on_user_list_update(data['data']['users'])
            self.logger.info("Users fetched successfully")
        else:
            self.logger.error(f"Users fetch failed: {data['message']}")

    def handle_new_message_update(self, data: Dict[str, Any]):
        """
        Handle notification of new message arrival.
        Triggers UI update to show new message indicator.
        """
        if self.on_new_message_update:
            self.on_new_message_update(1)

    def handle_unread_messages(self, data: Dict[str, Any]):
        """
        Handle response for unread messages request.
        On success: 
        1. Refreshes message display
        2. Updates unread message count
        On failure: Shows error message
        """
        if data['code'] == SUCCESS:
            # After getting unread messages, request latest page of messages
            if self.on_message_sent:
                self.on_message_sent(-1)  # Refresh messages
            # Request updated unread count
            if self.on_unread_count:
                self.on_unread_count(data['data'].get('count', 0))
        else:
            self.logger.error(f"Failed to get unread messages: {data['message']}")
            if self.on_error:
                self.on_error(data['message'])

    def handle_send_message_response(self, data: Dict[str, Any]):
        """Handle response after attempting to send a message"""
        if data['code'] == SUCCESS:
            self.logger.info("Message sent successfully")
            if self.on_message_sent and 'data' in data:
                self.on_message_sent(-1)
        else:
            self.logger.error(f"Failed to send message: {data['message']}")
            if self.on_error:
                self.on_error(data['message'])

    def handle_search_users_response(self, data: Dict[str, Any]):
        """Handle response containing user search results"""
        if data['code'] == SUCCESS and self.on_search_results:
            self.on_search_results(data['data']['users'], data['data']['total_pages'])
        elif self.on_error:
            self.on_error(data['message'])

    def handle_recent_chats_response(self, data: Dict[str, Any]):
        """Handle response containing recent chats"""
        if data['code'] == SUCCESS:
            if self.on_recent_chats_update and 'data' in data:
                self.on_recent_chats_update(data['data']['chats'], data['data']['total_pages'])
            self.logger.info("Recent chats fetched successfully")
        else:
            self.logger.error(f"Recent chats fetch failed: {data['message']}")
            if self.on_error:
                self.on_error(data['message'])

    def handle_previous_messages_response(self, data: Dict[str, Any]):
        """Handle response containing previous messages"""
        if data['code'] == SUCCESS:
            if self.on_previous_messages:
                self.on_previous_messages(data['data']['messages'], data['data']['total_pages'])
        else:
            self.logger.error(f"Previous messages fetch failed: {data['message']}")
            if self.on_error:
                self.on_error(data['message'])

    def handle_error_message(self, data: Dict[str, Any]):
        """Handle error messages from server"""
        error_message = data.get('message', 'Unknown error occurred')
        self.logger.error(f"Server error: {error_message}")
        if self.on_error:
            self.on_error(error_message)

    def handle_chat_unread_count_response(self, data: Dict[str, Any]):
        """
        Handle response containing chat unread count.
        Updates the UI with the number of unread messages for the current chat.
        """
        if data['code'] == SUCCESS:
            if self.on_unread_count and 'data' in data:
                self.on_unread_count(data['data']['count'])
        else:
            self.logger.error(f"Chat unread count fetch failed: {data['message']}")
            if self.on_error:
                self.on_error(data['message'])
