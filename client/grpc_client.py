import grpc
from generated import chat_pb2, chat_pb2_grpc

class GRPCClient:
    def __init__(self, host, port, logger):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
        self.logger = logger

    def _handle_error(self, e: grpc.RpcError):
        self.logger.error(f"RPC failed: {str(e)}")
        return {
            'code': -1,
            'message': str(e)
        }

    def create_account(self, email, username, password):
        try:
            request = chat_pb2.CreateAccountRequest(
                email=email,
                username=username,
                password=password
            )
            response = self.stub.CreateAccount(request)
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def login(self, email, password):
        try:
            request = chat_pb2.LoginRequest(email=email, password=password)
            response = self.stub.Login(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'user': {
                            '_id': response.user.id,
                            'username': response.user.username,
                            'email': response.user.email
                        }
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def delete_account(self, email, password):
        try:
            request = chat_pb2.DeleteAccountRequest(email=email, password=password)
            response = self.stub.DeleteAccount(request)
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def send_message(self, content, recipient_id, sender_id):
        try:
            request = chat_pb2.SendMessageRequest(
                content=content,
                recipient_id=recipient_id,
                sender_id=sender_id
            )
            response = self.stub.SendMessage(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'message_id': response.data.message_id,
                        'sender_id': response.data.sender_id,
                        'recipient_id': response.data.recipient_id,
                        'content': response.data.content,
                        'timestamp': response.data.timestamp
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def search_users(self, pattern, page, current_user_id):
        try:
            request = chat_pb2.SearchUsersRequest(
                pattern=pattern,
                page=page,
                current_user_id=current_user_id
            )
            response = self.stub.SearchUsers(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'users': [{
                            '_id': user.id,
                            'username': user.username,
                            'email': user.email
                        } for user in response.users],
                        'total_pages': response.total_pages
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def get_recent_chats(self, user_id, page):
        try:
            request = chat_pb2.GetRecentChatsRequest(
                user_id=user_id,
                page=page
            )
            response = self.stub.GetRecentChats(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'chats': [{
                            'user_id': chat.user_id,
                            'username': chat.username,
                            'unread_count': chat.unread_count,
                            'last_message': {
                                'content': chat.last_message.content,
                                'timestamp': chat.last_message.timestamp,
                                'is_from_me': chat.last_message.is_from_me
                            }
                        } for chat in response.chats],
                        'total_pages': response.total_pages
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def get_previous_messages(self, user_id, other_user_id, page):
        try:
            request = chat_pb2.GetPreviousMessagesRequest(
                user_id=user_id,
                other_user_id=other_user_id,
                page=page
            )
            response = self.stub.GetPreviousMessages(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'user_id': response.user_id,
                        'other_user_id': response.other_user_id,
                        'messages': [{
                            'message_id': msg.message_id,
                            'content': msg.content,
                            'timestamp': msg.timestamp,
                            'is_from_me': msg.is_from_me,
                            'sender': {
                                'user_id': msg.sender.user_id,
                                'username': msg.sender.username
                            }
                        } for msg in response.messages],
                        'total_pages': response.total_pages
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def get_chat_unread_count(self, user_id, other_user_id):
        try:
            request = chat_pb2.GetChatUnreadCountRequest(
                user_id=user_id,
                other_user_id=other_user_id
            )
            response = self.stub.GetChatUnreadCount(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'user_id': response.user_id,
                        'other_user_id': response.other_user_id,
                        'count': response.count
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def get_unread_messages(self, user_id, other_user_id, num_messages):
        try:
            request = chat_pb2.GetUnreadMessagesRequest(
                user_id=user_id,
                other_user_id=other_user_id,
                num_messages=num_messages
            )
            response = self.stub.GetUnreadMessages(request)
            if response.code == 0:
                return {
                    'code': response.code,
                    'message': response.message,
                    'data': {
                        'messages': [{
                            'message_id': msg.message_id,
                            'sender_id': msg.sender_id,
                            'recipient_id': msg.recipient_id,
                            'content': msg.content,
                            'timestamp': msg.timestamp,
                            'is_read': msg.is_read,
                            'is_from_me': msg.is_from_me
                        } for msg in response.messages]
                    }
                }
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)

    def delete_messages(self, message_ids):
        try:
            request = chat_pb2.DeleteMessagesRequest(
                message_ids=message_ids
            )
            response = self.stub.DeleteMessages(request)
            return {
                'code': response.code,
                'message': response.message
            }
        except grpc.RpcError as e:
            return self._handle_error(e)
