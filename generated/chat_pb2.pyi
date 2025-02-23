from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BasicResponse(_message.Message):
    __slots__ = ("code", "message")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class CreateAccountRequest(_message.Message):
    __slots__ = ("email", "username", "password")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    email: str
    username: str
    password: str
    def __init__(self, email: _Optional[str] = ..., username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class CreateAccountResponse(_message.Message):
    __slots__ = ("code", "message")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ("email", "password")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    email: str
    password: str
    def __init__(self, email: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class UserData(_message.Message):
    __slots__ = ("id", "username", "email")
    ID_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    id: str
    username: str
    email: str
    def __init__(self, id: _Optional[str] = ..., username: _Optional[str] = ..., email: _Optional[str] = ...) -> None: ...

class LoginResponse(_message.Message):
    __slots__ = ("code", "message", "user")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    user: UserData
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., user: _Optional[_Union[UserData, _Mapping]] = ...) -> None: ...

class DeleteAccountRequest(_message.Message):
    __slots__ = ("email", "password")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    email: str
    password: str
    def __init__(self, email: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class GetUsersRequest(_message.Message):
    __slots__ = ("page",)
    PAGE_FIELD_NUMBER: _ClassVar[int]
    page: int
    def __init__(self, page: _Optional[int] = ...) -> None: ...

class GetUsersResponse(_message.Message):
    __slots__ = ("code", "message", "users")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USERS_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    users: _containers.RepeatedCompositeFieldContainer[UserData]
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., users: _Optional[_Iterable[_Union[UserData, _Mapping]]] = ...) -> None: ...

class SearchUsersRequest(_message.Message):
    __slots__ = ("pattern", "page", "current_user_id")
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_USER_ID_FIELD_NUMBER: _ClassVar[int]
    pattern: str
    page: int
    current_user_id: str
    def __init__(self, pattern: _Optional[str] = ..., page: _Optional[int] = ..., current_user_id: _Optional[str] = ...) -> None: ...

class SearchUsersResponse(_message.Message):
    __slots__ = ("code", "message", "users", "total_pages")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USERS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PAGES_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    users: _containers.RepeatedCompositeFieldContainer[UserData]
    total_pages: int
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., users: _Optional[_Iterable[_Union[UserData, _Mapping]]] = ..., total_pages: _Optional[int] = ...) -> None: ...

class SendMessageRequest(_message.Message):
    __slots__ = ("content", "recipient_id", "sender_id")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    content: str
    recipient_id: str
    sender_id: str
    def __init__(self, content: _Optional[str] = ..., recipient_id: _Optional[str] = ..., sender_id: _Optional[str] = ...) -> None: ...

class MessageData(_message.Message):
    __slots__ = ("message_id", "sender_id", "recipient_id", "content", "timestamp")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    message_id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: str
    def __init__(self, message_id: _Optional[str] = ..., sender_id: _Optional[str] = ..., recipient_id: _Optional[str] = ..., content: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class SendMessageResponse(_message.Message):
    __slots__ = ("code", "message", "data")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    data: MessageData
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., data: _Optional[_Union[MessageData, _Mapping]] = ...) -> None: ...

class DeleteMessagesRequest(_message.Message):
    __slots__ = ("message_ids",)
    MESSAGE_IDS_FIELD_NUMBER: _ClassVar[int]
    message_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, message_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class GetRecentChatsRequest(_message.Message):
    __slots__ = ("user_id", "page")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    page: int
    def __init__(self, user_id: _Optional[str] = ..., page: _Optional[int] = ...) -> None: ...

class LastMessage(_message.Message):
    __slots__ = ("content", "timestamp", "is_from_me")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    IS_FROM_ME_FIELD_NUMBER: _ClassVar[int]
    content: str
    timestamp: str
    is_from_me: bool
    def __init__(self, content: _Optional[str] = ..., timestamp: _Optional[str] = ..., is_from_me: bool = ...) -> None: ...

class ChatData(_message.Message):
    __slots__ = ("user_id", "username", "unread_count", "last_message")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    UNREAD_COUNT_FIELD_NUMBER: _ClassVar[int]
    LAST_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    username: str
    unread_count: int
    last_message: LastMessage
    def __init__(self, user_id: _Optional[str] = ..., username: _Optional[str] = ..., unread_count: _Optional[int] = ..., last_message: _Optional[_Union[LastMessage, _Mapping]] = ...) -> None: ...

class GetRecentChatsResponse(_message.Message):
    __slots__ = ("code", "message", "chats", "total_pages")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CHATS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PAGES_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    chats: _containers.RepeatedCompositeFieldContainer[ChatData]
    total_pages: int
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., chats: _Optional[_Iterable[_Union[ChatData, _Mapping]]] = ..., total_pages: _Optional[int] = ...) -> None: ...

class GetPreviousMessagesRequest(_message.Message):
    __slots__ = ("user_id", "other_user_id", "page")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    OTHER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    other_user_id: str
    page: int
    def __init__(self, user_id: _Optional[str] = ..., other_user_id: _Optional[str] = ..., page: _Optional[int] = ...) -> None: ...

class MessageSender(_message.Message):
    __slots__ = ("user_id", "username")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    username: str
    def __init__(self, user_id: _Optional[str] = ..., username: _Optional[str] = ...) -> None: ...

class ChatMessage(_message.Message):
    __slots__ = ("message_id", "content", "timestamp", "is_from_me", "sender")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    IS_FROM_ME_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    message_id: str
    content: str
    timestamp: str
    is_from_me: bool
    sender: MessageSender
    def __init__(self, message_id: _Optional[str] = ..., content: _Optional[str] = ..., timestamp: _Optional[str] = ..., is_from_me: bool = ..., sender: _Optional[_Union[MessageSender, _Mapping]] = ...) -> None: ...

class GetPreviousMessagesResponse(_message.Message):
    __slots__ = ("code", "message", "user_id", "other_user_id", "messages", "total_pages")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    OTHER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PAGES_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    user_id: str
    other_user_id: str
    messages: _containers.RepeatedCompositeFieldContainer[ChatMessage]
    total_pages: int
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., user_id: _Optional[str] = ..., other_user_id: _Optional[str] = ..., messages: _Optional[_Iterable[_Union[ChatMessage, _Mapping]]] = ..., total_pages: _Optional[int] = ...) -> None: ...

class GetChatUnreadCountRequest(_message.Message):
    __slots__ = ("user_id", "other_user_id")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    OTHER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    other_user_id: str
    def __init__(self, user_id: _Optional[str] = ..., other_user_id: _Optional[str] = ...) -> None: ...

class GetChatUnreadCountResponse(_message.Message):
    __slots__ = ("code", "message", "user_id", "other_user_id", "count")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    OTHER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    user_id: str
    other_user_id: str
    count: int
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., user_id: _Optional[str] = ..., other_user_id: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class GetUnreadMessagesRequest(_message.Message):
    __slots__ = ("user_id", "other_user_id", "num_messages")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    OTHER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    NUM_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    other_user_id: str
    num_messages: int
    def __init__(self, user_id: _Optional[str] = ..., other_user_id: _Optional[str] = ..., num_messages: _Optional[int] = ...) -> None: ...

class UnreadMessage(_message.Message):
    __slots__ = ("message_id", "sender_id", "recipient_id", "content", "timestamp", "is_read", "is_from_me")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    IS_READ_FIELD_NUMBER: _ClassVar[int]
    IS_FROM_ME_FIELD_NUMBER: _ClassVar[int]
    message_id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: str
    is_read: bool
    is_from_me: bool
    def __init__(self, message_id: _Optional[str] = ..., sender_id: _Optional[str] = ..., recipient_id: _Optional[str] = ..., content: _Optional[str] = ..., timestamp: _Optional[str] = ..., is_read: bool = ..., is_from_me: bool = ...) -> None: ...

class GetUnreadMessagesResponse(_message.Message):
    __slots__ = ("code", "message", "messages")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    messages: _containers.RepeatedCompositeFieldContainer[UnreadMessage]
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ..., messages: _Optional[_Iterable[_Union[UnreadMessage, _Mapping]]] = ...) -> None: ...
