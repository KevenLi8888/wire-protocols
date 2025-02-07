from database.collections import UsersCollection
from shared.constants import *

class UserHandler:
    def __init__(self):
        self.users = UsersCollection()

    def create_account(self, data):
        user = self.users.find_by_email(data['email'])
        if user:
            return {"code": ERROR_USER_EXISTS, "message": MESSAGE_USER_EXISTS}
        # Hash password and create user
        # ...
        return {"code": SUCCESS, "message": MESSAGE_OK}

    def login(self, data):
        user = self.users.find_by_email(data['email'])
        if not user or user.password_hash != data['password']:
            return {"code": ERROR_INVALID_CREDENTIALS, "message": MESSAGE_INVALID_CREDENTIALS}
        self.users.update_last_login(str(user._id))
        return {"code": SUCCESS, "message": MESSAGE_OK}
