from datetime import datetime
from database.collections import MessagesCollection
from shared.constants import *
import logging

class MessageHandler:
    def __init__(self, logger: logging.Logger):
        self.messages = MessagesCollection()
        self.logger = logger

    def send_message(self, data):
        try:
            sender_id = data['sender_id']
            recipient_id = data['recipient_id']
            content = data['content']
            
            # Store message
            message_id = self.messages.insert_message(sender_id, recipient_id, content)
            
            message_data = {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'data': {
                    'message_id': message_id,
                    'sender_id': sender_id,
                    'recipient_id': recipient_id,
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                }
            }
            return message_data
            
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }

    def get_recent_chats(self, data):
        """Handle request for recent chats"""
        try:
            user_id = data['user_id']
            page = data.get('page', 1)
            
            chats, total_pages = self.messages.get_recent_chats(user_id, page)
            
            return {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'data': {
                    'chats': chats,
                    'total_pages': total_pages
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting recent chats: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }

    def get_previous_messages(self, data):
        """Handle request for previous messages between users"""
        try:
            user_id = data['user_id']
            other_user_id = data['other_user_id']
            page = data.get('page', 1)
            
            messages, total_pages = self.messages.get_previous_messages_between_users(user_id, other_user_id, page)
            
            return {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'data': {
                    'user_id': user_id,
                    'other_user_id': other_user_id,
                    'messages': messages,
                    'total_pages': total_pages
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting previous messages: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }
        
    def get_chat_unread_count(self, data):
        """Handle request for unread message count in a chat"""
        try:
            user_id = data['user_id']
            other_user_id = data['other_user_id']
            
            count = self.messages.get_chat_unread_count(user_id, other_user_id)
            
            return {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'data': {
                    'user_id': user_id,
                    'other_user_id': other_user_id,
                    'count': count
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting unread message count: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }

    def get_chat_unread_messages(self, data):
        try:
            user_id = data['user_id']
            other_user_id = data['other_user_id']
            num_messages = data['num_messages']
            messages = self.messages.get_unread_messages(user_id, other_user_id, num_messages)
            
            if messages:
                message_ids = [msg['_id'] for msg in messages]
                self.messages.mark_as_read(message_ids)
            
            formatted_messages = [{
                'message_id': str(msg['_id']),
                'sender_id': str(msg['sender_id']),
                'recipient_id': str(msg['recipient_id']),
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat(),
                'is_read': msg['is_read'],
                'is_from_me': msg['sender_id'] == user_id
            } for msg in messages]
            
            return {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'data': {
                    'messages': formatted_messages
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting unread messages: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }
    
    def delete_messages(self, data):
        try:
            message_ids = data['message_ids']
            if self.messages.delete_messages(message_ids):
                return {
                    'code': SUCCESS,
                    'message': MESSAGE_OK
                }
            else:
                return {
                    'code': ERROR_INVALID_MESSAGE,
                    'message': "No messages were deleted."
                }
            
        except Exception as e:
            self.logger.error(f"Error deleting message: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }