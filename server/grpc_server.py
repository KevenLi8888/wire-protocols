import grpc
from concurrent import futures
from generated import chat_pb2, chat_pb2_grpc
from server.handlers.user_handler import UserHandler
from server.handlers.message_handler import MessageHandler
from shared.constants import SUCCESS, MESSAGE_OK

class ChatServiceServicer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, logger):
        self.user_handler = UserHandler()
        self.message_handler = MessageHandler(logger)
        self.logger = logger

    def CreateAccount(self, request, context):
        try:
            result = self.user_handler.create_account({
                'email': request.email,
                'username': request.username,
                'password': request.password
            })
            return chat_pb2.CreateAccountResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:  
            self.logger.error(f"Error in CreateAccount: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.CreateAccountResponse()

    def Login(self, request, context):
        try:
            result = self.user_handler.login({
                'email': request.email,
                'password': request.password
            })
            if result['code'] == SUCCESS:
                user_data = result['data']['user']
                return chat_pb2.LoginResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    user=chat_pb2.UserData(
                        id=str(user_data['_id']),
                        username=user_data['username'],
                        email=user_data['email']
                    )
                )
            return chat_pb2.LoginResponse(code=result['code'], message=result['message'])
        except Exception as e:
            self.logger.error(f"Error in Login: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.LoginResponse()

    def DeleteAccount(self, request, context):
        try:
            result = self.user_handler.delete_user({
                'email': request.email,
                'password': request.password
            })
            return chat_pb2.BasicResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:  
            self.logger.error(f"Error in DeleteAccount: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.BasicResponse()

    def SearchUsers(self, request, context):
        try:
            result = self.user_handler.search_users({
                'pattern': request.pattern,
                'page': request.page,
                'current_user_id': request.current_user_id
            })
            if result['code'] == SUCCESS:
                return chat_pb2.SearchUsersResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    users=[chat_pb2.UserData(
                        id=str(user['_id']),
                        username=user['username'],
                        email=user['email']
                    ) for user in result['data']['users']],
                    total_pages=result['data']['total_pages']
                )
            return chat_pb2.SearchUsersResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in SearchUsers: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.SearchUsersResponse()

    def SendMessage(self, request, context):
        try:
            result = self.message_handler.send_message({
                'content': request.content,
                'recipient_id': request.recipient_id,
                'sender_id': request.sender_id
            })
            if result['code'] == SUCCESS:
                msg_data = result['data']
                return chat_pb2.SendMessageResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    data=chat_pb2.MessageData(
                        message_id=str(msg_data['message_id']),
                        sender_id=msg_data['sender_id'],
                        recipient_id=msg_data['recipient_id'],
                        content=msg_data['content'],
                        timestamp=msg_data['timestamp']
                    )
                )
            return chat_pb2.SendMessageResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in SendMessage: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.SendMessageResponse()

    def GetRecentChats(self, request, context):
        try:
            result = self.message_handler.get_recent_chats({
                'user_id': request.user_id,
                'page': request.page
            })
            if result['code'] == SUCCESS:
                chats_data = result['data']['chats']
                return chat_pb2.GetRecentChatsResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    chats=[chat_pb2.ChatData(
                        user_id=str(chat['user_id']),
                        username=chat['username'],
                        unread_count=chat['unread_count'],
                        last_message=chat_pb2.LastMessage(
                            content=chat['last_message']['content'],
                            timestamp=chat['last_message']['timestamp'],
                            is_from_me=chat['last_message']['is_from_me']
                        )
                    ) for chat in chats_data],
                    total_pages=result['data']['total_pages']
                )
            return chat_pb2.GetRecentChatsResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in GetRecentChats: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.GetRecentChatsResponse()

    def GetPreviousMessages(self, request, context):
        try:
            result = self.message_handler.get_previous_messages({
                'user_id': request.user_id,
                'other_user_id': request.other_user_id,
                'page': request.page
            })
            if result['code'] == SUCCESS:
                return chat_pb2.GetPreviousMessagesResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    user_id=result['data']['user_id'],
                    other_user_id=result['data']['other_user_id'],
                    messages=[chat_pb2.ChatMessage(
                        message_id=str(msg['message_id']),
                        content=msg['content'],
                        timestamp=msg['timestamp'],
                        is_from_me=msg['is_from_me'],
                        sender=chat_pb2.MessageSender(
                            user_id=str(msg['sender']['user_id']),
                            username=msg['sender']['username']
                        )
                    ) for msg in result['data']['messages']],
                    total_pages=result['data']['total_pages']
                )
            return chat_pb2.GetPreviousMessagesResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in GetPreviousMessages: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.GetPreviousMessagesResponse()

    def GetChatUnreadCount(self, request, context):
        try:
            result = self.message_handler.get_chat_unread_count({
                'user_id': request.user_id,
                'other_user_id': request.other_user_id
            })
            if result['code'] == SUCCESS:
                return chat_pb2.GetChatUnreadCountResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    user_id=result['data']['user_id'],
                    other_user_id=result['data']['other_user_id'],
                    count=result['data']['count']
                )
            return chat_pb2.GetChatUnreadCountResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in GetChatUnreadCount: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.GetChatUnreadCountResponse()

    def GetUnreadMessages(self, request, context):
        try:
            result = self.message_handler.get_chat_unread_messages({
                'user_id': request.user_id,
                'other_user_id': request.other_user_id,
                'num_messages': request.num_messages
            })
            if result['code'] == SUCCESS:
                return chat_pb2.GetUnreadMessagesResponse(
                    code=SUCCESS,
                    message=MESSAGE_OK,
                    messages=[chat_pb2.UnreadMessage(
                        message_id=str(msg['message_id']),
                        sender_id=msg['sender_id'],
                        recipient_id=msg['recipient_id'],
                        content=msg['content'],
                        timestamp=msg['timestamp'],
                        is_read=msg['is_read'],
                        is_from_me=msg['is_from_me']
                    ) for msg in result['data']['messages']]
                )
            return chat_pb2.GetUnreadMessagesResponse(code=result['code'], message=result['message'])
        except Exception as e:  
            self.logger.error(f"Error in GetUnreadMessages: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.GetUnreadMessagesResponse()

    def DeleteMessages(self, request, context):
        try:
            result = self.message_handler.delete_messages({
                'message_ids': list(request.message_ids)
            })
            return chat_pb2.BasicResponse(
                code=result['code'],
                message=result.get('message', MESSAGE_OK)
            )
        except Exception as e:  
            self.logger.error(f"Error in DeleteMessages: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.BasicResponse()

class GRPCServer:
    def __init__(self, host, port, logger):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.logger = logger
        self.host = host
        self.port = port
        chat_pb2_grpc.add_ChatServiceServicer_to_server(
            ChatServiceServicer(logger), self.server)

    def start(self):
        self.server.add_insecure_port(f'{self.host}:{self.port}')
        self.server.start()
        self.logger.info(f"gRPC server started on {self.host}:{self.port}")
        
    def stop(self, grace=None):
        self.server.stop(grace)
        self.logger.info("gRPC server stopped")