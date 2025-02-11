from datetime import datetime
from database.collections import MessagesCollection
from shared.constants import *
import logging

class MessageHandler:
    def __init__(self):
        self.messages = MessagesCollection()

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
            logging.error(f"Error sending message: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }

    def get_unread_messages(self, data):
        try:
            user_id = data['user_id']
            messages = self.messages.get_unread_messages(user_id)
            
            if messages:
                message_ids = [msg['_id'] for msg in messages]
                self.messages.mark_as_read(message_ids)
            
            return {
                'code': SUCCESS,
                'message': MESSAGE_OK,
                'messages': messages
            }
        except Exception as e:
            logging.error(f"Error getting unread messages: {str(e)}")
            return {
                'code': ERROR_SERVER_ERROR,
                'message': MESSAGE_SERVER_ERROR
            }
