import grpc
from concurrent import futures
from generated import chat_pb2, chat_pb2_grpc
from server.handlers.user_handler import UserHandler
from shared.constants import SUCCESS, MESSAGE_OK

class ChatServiceServicer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, logger):
        self.user_handler = UserHandler()
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
