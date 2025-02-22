import grpc
from generated import chat_pb2, chat_pb2_grpc

class GRPCClient:
    def __init__(self, host, port, logger):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = chat_pb2_grpc.ChatServiceStub(self.channel)
        self.logger = logger

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
            self.logger.error(f"RPC failed: {str(e)}")
            return {
                'code': -1,
                'message': str(e)
            }
