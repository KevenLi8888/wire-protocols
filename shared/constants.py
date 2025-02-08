# Message Types
MSG_CREATE_ACCOUNT_REQUEST = 1
MSG_CREATE_ACCOUNT_RESPONSE = 2
MSG_LOGIN_REQUEST = 3
MSG_LOGIN_RESPONSE = 4
MSG_DELETE_ACCOUNT_REQUEST = 5
MSG_DELETE_ACCOUNT_RESPONSE = 6
MSG_ERROR_RESPONSE = 99

# Error Codes
SUCCESS = 0
ERROR_INVALID_MESSAGE = -1
ERROR_USER_EXISTS = -2
ERROR_INVALID_CREDENTIALS = -3
ERROR_USER_NOT_FOUND = -4
ERROR_SERVER_ERROR = -500

# Messages
MESSAGE_OK = "OK"
MESSAGE_INVALID_MESSAGE = "Invalid message type"
MESSAGE_USER_EXISTS = "User already exists"
MESSAGE_INVALID_CREDENTIALS = "Invalid credentials"
MESSAGE_USER_NOT_FOUND = "User not found"
MESSAGE_SERVER_ERROR = "Internal server error"

# Message Format Mapping
MESSAGE_FORMATS = {
    MSG_CREATE_ACCOUNT_REQUEST: 'CREATE_ACCOUNT_REQUEST',
    MSG_CREATE_ACCOUNT_RESPONSE: 'RESPONSE_FORMAT',
    MSG_LOGIN_REQUEST: 'LOGIN_REQUEST',
    MSG_LOGIN_RESPONSE: 'RESPONSE_FORMAT',
    MSG_DELETE_ACCOUNT_REQUEST: 'DELETE_ACCOUNT_REQUEST',
    MSG_DELETE_ACCOUNT_RESPONSE: 'RESPONSE_FORMAT',
    MSG_ERROR_RESPONSE: 'RESPONSE_FORMAT'
}
