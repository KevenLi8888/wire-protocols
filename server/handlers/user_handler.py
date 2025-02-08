from datetime import datetime
from database.collections import UsersCollection
from shared.constants import *
from shared.models import User

class UserHandler:
    def __init__(self):
        self.users = UsersCollection()

    def create_account(self, data):
        user = self.users.find_by_email(data['email'])
        if user:
            return {"code": ERROR_USER_EXISTS, "message": MESSAGE_USER_EXISTS}
        # TODO: password should be hashed
        self.users.insert_one(User(username=data['username'], email=data['email'], password_hash=data['password'], created_at=datetime.now()))
        return {"code": SUCCESS, "message": MESSAGE_OK}

    def login(self, data):
        user = self.users.find_by_email(data['email'])
        if not user or user.password_hash != data['password']:
            return {"code": ERROR_INVALID_CREDENTIALS, "message": MESSAGE_INVALID_CREDENTIALS}
        self.users.update_last_login(str(user._id))
        return {"code": SUCCESS, "message": MESSAGE_OK}
