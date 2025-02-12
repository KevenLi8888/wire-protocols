import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import MagicMock, patch
from database.collections import UsersCollection, MessagesCollection
from shared.models import User

@pytest.fixture
def mock_db_manager():
    with patch('database.collections.DatabaseManager') as mock_manager:
        mock_db = MagicMock()
        mock_manager.get_instance.return_value.db = mock_db
        yield mock_db

@pytest.fixture
def users_collection(mock_db_manager):
    collection = UsersCollection()
    collection.collection = MagicMock()
    return collection

@pytest.fixture
def messages_collection(mock_db_manager):
    collection = MessagesCollection()
    collection.collection = MagicMock()
    return collection

class TestUsersCollection:
    def test_insert_one(self, users_collection):
        """Test inserting a user"""
        mock_user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password"
        )
        users_collection.collection.insert_one.return_value.inserted_id = ObjectId()
        
        result = users_collection.insert_one(mock_user)
        assert result is not None
        users_collection.collection.insert_one.assert_called_once()

    def test_find_by_username(self, users_collection):
        """Test finding a user by username"""
        mock_data = {
            "_id": ObjectId(),
            "username": "test_user",
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        users_collection.collection.find_one.return_value = mock_data
        
        user = users_collection.find_by_username("test_user")
        assert user is not None
        assert user.username == "test_user"
        users_collection.collection.find_one.assert_called_with({"username": "test_user"})

    def test_search_users_by_username_paginated(self, users_collection):
        """Test paginated user search"""
        mock_users = [
            {
                "_id": ObjectId(),
                "username": "user1",
                "email": "user1@example.com"
            },
            {
                "_id": ObjectId(),
                "username": "user2",
                "email": "user2@example.com"
            }
        ]
        
        # using valid ObjectId string
        current_user_id = str(ObjectId())
        users_collection.collection.count_documents.return_value = 2
        users_collection.collection.find.return_value.skip.return_value.limit.return_value = mock_users
        
        users, total_pages = users_collection.search_users_by_username_paginated(
            current_user_id,
            "user",
            page=1,
            per_page=10
        )
        
        assert len(users) == 2
        assert total_pages == 1

    def test_find_by_email(self, users_collection):
        """Test finding a user by email"""
        mock_data = {
            "_id": ObjectId(),
            "username": "test_user",
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        users_collection.collection.find_one.return_value = mock_data
        
        user = users_collection.find_by_email("test@example.com")
        assert user is not None
        assert user.email == "test@example.com"
        users_collection.collection.find_one.assert_called_with({"email": "test@example.com"})

    def test_update_last_login(self, users_collection):
        """Test updating user's last login time"""
        user_id = str(ObjectId())
        users_collection.collection.update_one.return_value.modified_count = 1
        
        result = users_collection.update_last_login(user_id)
        assert result is True
        users_collection.collection.update_one.assert_called_once()

    def test_get_all_users(self, users_collection):
        """Test getting all users"""
        mock_users = [
            {
                "_id": ObjectId(),
                "username": "user1",
                "email": "user1@example.com"
            },
            {
                "_id": ObjectId(),
                "username": "user2",
                "email": "user2@example.com"
            }
        ]
        users_collection.collection.find.return_value = mock_users
        
        users = users_collection.get_all_users()
        assert len(users) == 2
        users_collection.collection.find.assert_called_once()

    def test_find_by_id(self, users_collection):
        """Test finding a user by ID"""
        mock_id = ObjectId()
        mock_data = {
            "_id": mock_id,
            "username": "test_user",
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        users_collection.collection.find_one.return_value = mock_data
        
        # Test with valid ID
        user = users_collection.find_by_id(str(mock_id))
        assert user is not None
        assert user.username == "test_user"
        users_collection.collection.find_one.assert_called_with({"_id": mock_id})
        
        # Test with invalid ID
        user = users_collection.find_by_id("invalid_id")
        assert user is None

    def test_search_users_by_username(self, users_collection):
        """Test searching users by username"""
        mock_users = [
            {
                "_id": ObjectId(),
                "username": "user1",
                "email": "user1@example.com"
            },
            {
                "_id": ObjectId(),
                "username": "user2",
                "email": "user2@example.com"
            }
        ]
        users_collection.collection.find.return_value = mock_users
        
        current_user_id = str(ObjectId())
        users = users_collection.search_users_by_username(current_user_id, "user")
        
        assert len(users) == 2
        users_collection.collection.find.assert_called_with({
            'username': {'$regex': 'user', '$options': 'i'},
            '_id': {'$ne': ObjectId(current_user_id)}
        }, {'_id': 1, 'username': 1, 'email': 1})

class TestMessagesCollection:
    def test_insert_message(self, messages_collection):
        """Test inserting a message"""
        messages_collection.collection.insert_one.return_value.inserted_id = ObjectId()
        
        # using valid ObjectId string
        sender_id = str(ObjectId())
        recipient_id = str(ObjectId())
        
        result = messages_collection.insert_message(
            sender_id,
            recipient_id,
            "Hello!"
        )
        
        assert result is not None
        messages_collection.collection.insert_one.assert_called_once()

    def test_get_unread_messages(self, messages_collection):
        """Test getting unread messages"""
        mock_messages = [
            {
                "_id": ObjectId(),
                "sender_id": ObjectId(),
                "content": "Hello",
                "timestamp": datetime.now()
            }
        ]
        
        # Correctly set up chained mock calls
        mock_find = MagicMock()
        mock_sort = MagicMock()
        mock_limit = MagicMock()
        
        mock_find.sort.return_value = mock_sort
        mock_sort.limit.return_value = mock_messages
        messages_collection.collection.find.return_value = mock_find
        
        # using valid ObjectId strings
        user_id = str(ObjectId())
        other_user_id = str(ObjectId())
        num_messages = 10
        
        messages = messages_collection.get_unread_messages(user_id, other_user_id, num_messages)
        assert len(messages) == 1
        messages_collection.collection.find.assert_called_once()

    def test_mark_as_read(self, messages_collection):
        """Test marking messages as read"""
        messages_collection.collection.update_many.return_value.modified_count = 1
        
        # using valid ObjectId string
        message_ids = [str(ObjectId()), str(ObjectId())]
        result = messages_collection.mark_as_read(message_ids)
        assert result is True
        messages_collection.collection.update_many.assert_called_once()

    def test_get_recent_chats(self, messages_collection):
        """Test getting recent chats"""
        mock_pipeline_result = [
            {
                "_id": ObjectId(),
                "last_message": {
                    "content": "Hello",
                    "timestamp": datetime.now(),
                    "sender_id": ObjectId(),
                    "recipient_id": ObjectId()
                },
                "unread_count": 1
            }
        ]
        
        messages_collection.collection.aggregate.return_value = mock_pipeline_result
        
        with patch('database.collections.UsersCollection') as mock_users_collection:
            mock_users_collection.return_value.find_by_id.return_value = User(
                username="test_user",
                email="test@example.com",
                password_hash="hash"
            )
            
            # using valid ObjectId string
            user_id = str(ObjectId())
            chats, total_pages = messages_collection.get_recent_chats(user_id)
            assert len(chats) == 1
            assert total_pages >= 1

    def test_get_previous_messages_between_users(self, messages_collection):
        """Test getting previous messages between users"""
        mock_messages = [
            {
                "_id": ObjectId(),
                "sender_id": ObjectId(),
                "recipient_id": ObjectId(),
                "content": "Hello",
                "timestamp": datetime.now(),
                "is_read": True
            }
        ]
        
        messages_collection.collection.count_documents.return_value = 1
        messages_collection.collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_messages
        
        with patch('database.collections.UsersCollection') as mock_users_collection:
            mock_users_collection.return_value.find_by_id.return_value = User(
                username="test_user",
                email="test@example.com",
                password_hash="hash"
            )
            
            user_id = str(ObjectId())
            other_user_id = str(ObjectId())
            messages, total_pages = messages_collection.get_previous_messages_between_users(
                user_id,
                other_user_id
            )
            
            assert len(messages) == 1
            assert total_pages == 1
