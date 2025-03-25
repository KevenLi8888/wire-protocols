import math
from typing import Optional, List
from datetime import datetime
from shared.models import User, Server
from database.connection import DatabaseManager
from bson import ObjectId
import uuid

class UsersCollection:
    """
    Handles all database operations related to users.
    Provides methods for CRUD operations, user searches, and authentication updates.
    Collection schema:
    ```
    {
    "_id": "ObjectId",          // Unique identifier for each user (MongoDB internal)
    "user_id": "string",        // Unique user ID (UUID) consistent across replicas
    "username": "string",       // Username (not unique)
    "email": "string",          // Unique email address
    "password_hash": "string",  // Hashed password
    "created_at": "Date",       // Account creation timestamp
    "last_login": "Date",       // Last login timestamp
    }
    ```
    """
    def __init__(self, db_type: str = 'database'):
        """Initialize UsersCollection with database connection
        
        Args:
            db_type: Type of database to connect to ('database' or 'registry')
        """
        self.db = DatabaseManager.get_instance(db_type).db
        self.db_type = db_type 
        self.collection = self.db['users']

    def insert_one(self, user: User) -> Optional[str]:
        """Insert a new user into the database and return their ID"""
        # Generate UUID for user_id if not provided
        if not user.user_id:
            user.user_id = str(uuid.uuid4())
            
        user_dict = user.to_dict()
        result = self.collection.insert_one(user_dict)
        return user.user_id if result else None

    def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by their username"""
        data = self.collection.find_one({"username": username})
        return User.from_dict(data) if data else None

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address"""
        data = self.collection.find_one({"email": email})
        return User.from_dict(data) if data else None
    
    def delete_one(self, user_id: str) -> bool:
        """Delete a user by their ID and return success status"""
        result = self.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp and return success status"""
        result = self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_login": datetime.now()}}
        )
        return result.modified_count > 0

    def get_all_users(self) -> list[User]:
        """Retrieve all users from the database"""
        # users = self.collection.find({}, {'user_id': 1, 'username': 1, 'email': 1})
        users = self.collection.find()
        return [u for u in (User.from_dict(user) for user in users) if u is not None]
    
    def search_users_by_username(self, current_user_id: str, filter_str: str) -> list[User]:
        '''Search users by username, filter_string is regex, excluding the current user'''
        users = self.collection.find({
            'username': {'$regex': filter_str, '$options': 'i'},
            'user_id': {'$ne': current_user_id}
        }, {'user_id': 1, 'username': 1, 'email': 1})
        return [u for u in (User.from_dict(user) for user in users) if u is not None]

    def search_users_by_username_paginated(self, current_user_id: str, pattern: str, page: int, per_page: int = 10) -> tuple[list[User], int]:
        """Search users by username pattern with pagination"""
        skip = (page - 1) * per_page
        
        query = {
            'username': {'$regex': pattern, '$options': 'i'},
            'user_id': {'$ne': current_user_id}
        }
        
        total = self.collection.count_documents(query)
        total_pages = math.ceil(total / per_page)
        
        users = self.collection.find(
            query,
            {'user_id': 1, 'username': 1, 'email': 1, 'password_hash': 1}
        ).skip(skip).limit(per_page)
        
        return [u for u in (User.from_dict(user) for user in users) if u is not None], total_pages

    def find_by_id(self, user_id: str) -> Optional[User]:
        try:
            data = self.collection.find_one({"user_id": user_id})
            return User.from_dict(data) if data else None
        except:
            return None

    def clear_all_users(self) -> bool:
        """Delete all users from the collection
        
        Returns:
            bool: True if deletion was successful
        """
        try:
            result = self.collection.delete_many({})
            return result.acknowledged
        except Exception as e:
            import logging
            logging.error(f"Failed to clear users collection: {str(e)}")
            return False

class MessagesCollection:
    """
    Handles all database operations related to messages between users.
    Provides methods for message management, chat history, and read/unread status.
    Collection schema:
    - _id: ObjectId (MongoDB internal)
    - message_id: str (UUID - consistent across replicas)
    - sender_id: str (user_id, not ObjectId)
    - recipient_id: str (user_id, not ObjectId)
    - content: str
    - timestamp: datetime
    - is_read: bool
    """
    def __init__(self, db_type: str = 'database'):
        """Initialize MessagesCollection with database connection
        
        Args:
            db_type: Type of database to connect to ('database' or 'registry')
        """
        self.db_type = db_type  # Store db_type as instance variable
        self.db = DatabaseManager.get_instance(db_type).db
        self.collection = self.db['messages']

    def insert_message(self, sender_id: str, recipient_id: str, content: str, message_id: Optional[str] = None, time: Optional[datetime] = None, is_read: bool = False) -> Optional[str]:
        """Insert a new message and return its ID"""
        # Generate UUID for message_id if not provided
        if not message_id:
            message_id = str(uuid.uuid4())
        

        if time is None:
            time = datetime.now()
            
        message = {
            'message_id': message_id,
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'content': content,
            'timestamp': time,
            'is_read': is_read
        }
        result = self.collection.insert_one(message)
        return message_id if result else None

    def get_unread_messages(self, user_id: str, other_user_id: str, num_messages: int) -> list:
        """Get unread messages between two users with a limit"""
        messages = self.collection.find({
            'recipient_id': user_id,
            'sender_id': other_user_id,
            'is_read': False
        }).sort('timestamp', 1).limit(num_messages)
        return [msg for msg in messages]

    def mark_as_read(self, message_ids: list[str]) -> bool:
        """Mark multiple messages as read and return success status"""
        result = self.collection.update_many(
            {'message_id': {'$in': message_ids}},
            {'$set': {'is_read': True}}
        )
        return result.modified_count > 0
    
    def delete_messages(self, message_ids: list[str]) -> bool:
        """Delete multiple messages by their IDs and return success status"""
        result = self.collection.delete_many(
            {'message_id': {'$in': message_ids}}
        )
        return result.deleted_count > 0

    def get_recent_chats(self, user_id: str, page: int = 1, per_page: int = 12):
        """
        Get recent chats for a user with pagination.
        
        The MongoDB aggregation pipeline:
        1. Matches messages where the user is either sender or recipient
        2. Sorts messages by timestamp (newest first)
        3. Groups messages by the other participant in the conversation
        4. Calculates unread message count for each chat
        5. Applies pagination
        
        Returns:
        - List of formatted chat objects with last message and unread count
        - Total number of pages
        """
        skip = (page - 1) * per_page
        
        # Pipeline to get the most recent message for each chat
        pipeline = [
            # Match messages where user is either sender or recipient
            {'$match': {
                '$or': [
                    {'sender_id': user_id},
                    {'recipient_id': user_id}
                ]
            }},
            # Sort by timestamp descending
            {'$sort': {'timestamp': -1}},
            # Group by the other user in the conversation
            {'$group': {
                '_id': {
                    '$cond': [
                        {'$eq': ['$sender_id', user_id]},
                        '$recipient_id',
                        '$sender_id'
                    ]
                },
                'last_message': {'$first': '$$ROOT'},
                'unread_count': {
                    '$sum': {
                        '$cond': [
                            {'$and': [
                                {'$eq': ['$recipient_id', user_id]},
                                {'$eq': ['$is_read', False]}
                            ]},
                            1,
                            0
                        ]
                    }
                }
            }},
            # Skip and limit for pagination
            {'$skip': skip},
            {'$limit': per_page}
        ]
        
        # Execute pipeline
        chats = list(self.collection.aggregate(pipeline))
        
        # Get total count for pagination
        total_chats = len(list(self.collection.aggregate(pipeline[:-2])))
        total_pages = math.ceil(total_chats / per_page)
        
        # Look up usernames for the other users in the chats
        users_collection = UsersCollection(db_type=self.db_type)
        formatted_chats = []
        for chat in chats:
            other_user = users_collection.find_by_id(str(chat['_id']))
            formatted_chat = {
                'user_id': str(chat['_id']),
                'username': other_user.username if other_user else 'Unknown User',
                'unread_count': chat['unread_count']
            }
            
            # Format the last message
            msg = chat['last_message']
            formatted_chat['last_message'] = {
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat(),
                'is_from_me': msg['sender_id'] == user_id
            }
            # Store original timestamp for sorting
            formatted_chat['sort_timestamp'] = msg['timestamp']
            formatted_chats.append(formatted_chat)
        
        # Sort chats by timestamp before returning
        formatted_chats.sort(key=lambda x: x['sort_timestamp'], reverse=True)
        # Remove the sorting timestamp
        for chat in formatted_chats:
            del chat['sort_timestamp']
        
        return formatted_chats, total_pages

    def get_previous_messages_between_users(self, user_id: str, other_user_id: str, page: int = 1, per_page: int = 6):
        """
        Get previous messages between two users with pagination.
        
        Query conditions:
        - Messages between the two specified users
        - Messages that are either:
          a) Already marked as read
          b) Sent by the current user
        
        Special cases:
        - If page == -1, returns the last page
        - Uses user caching to minimize database lookups
        
        Returns:
        - List of formatted messages with sender information
        - Total number of pages
        """
        # Query to match read messages or messages sent by current user
        query = {
            '$and': [
                {
                    '$or': [
                        {'sender_id': user_id, 'recipient_id': other_user_id},
                        {'sender_id': other_user_id, 'recipient_id': user_id}
                    ]
                },
                {
                    '$or': [
                        {'is_read': True},
                        {'sender_id': user_id}  # Include all messages sent by current user
                    ]
                }
            ]
        }

        # Get total count for pagination
        total_messages = self.collection.count_documents(query)
        total_pages = math.ceil(total_messages / per_page)

        # Handle last page request
        if page == -1:
            page = total_pages
        
        skip = (page - 1) * per_page if page > 0 else 0

        # Get messages with pagination
        messages = self.collection.find(query)\
            .sort('timestamp')\
            .skip(skip)\
            .limit(per_page)

        # Create users collection instance to look up usernames
        users_collection = UsersCollection(db_type=self.db_type)
        
        # Cache user info to avoid multiple DB lookups
        user_cache = {}
        
        # Format messages
        formatted_messages = []
        for msg in messages:
            sender_id = str(msg['sender_id'])
            
            # Get sender info from cache or database
            if sender_id not in user_cache:
                sender = users_collection.find_by_id(sender_id)
                user_cache[sender_id] = {
                    'user_id': sender_id,
                    'username': sender.username if sender else 'Unknown User'
                }
            
            formatted_messages.append({
                'message_id': str(msg['message_id']),
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat(),
                'is_from_me': msg['sender_id'] == user_id,
                'sender': user_cache[sender_id]
            })

        return formatted_messages, total_pages
    
    def get_chat_unread_count(self, user_id: str, other_user_id: str) -> int:
        """Get the unread message count between two users"""
        count = self.collection.count_documents({
            'sender_id': other_user_id,
            'recipient_id': user_id,
            'is_read': False
        })
        
        return count
    
    def delete_user_messages(self, user_id: str):
        """Delete all messages for a user"""
        result = self.collection.delete_many({
            '$or': [
                {'sender_id': user_id},
                {'recipient_id': user_id}
            ]
        })
        return result.deleted_count

    def find_message_by_id(self, message_id: str) -> Optional[dict]:
        """根据消息ID查找消息"""
        return self.collection.find_one({"message_id": message_id})

    def get_all_messages(self) -> list[dict]:
        """Get all messages from the database
        
        Returns:
            list[dict]: List of all messages in the database
        """
        messages = self.collection.find({})
        return [msg for msg in messages]

    def clear_all_messages(self) -> bool:
        """Delete all messages from the collection
        
        Returns:
            bool: True if deletion was successful
        """
        try:
            result = self.collection.delete_many({})
            return result.acknowledged
        except Exception as e:
            import logging
            logging.error(f"Failed to clear messages collection: {str(e)}")
            return False

class ServersCollection:
    """
    Handles all database operations related to server registry.
    Provides methods for server registration, discovery, and status management.
    Collection schema:
    - _id: ObjectId
    - server_id: str (unique identifier for each server)
    - host: str
    - port: int
    - status: str (ONLINE, STOPPED, OFFLINE)
    - created_at: datetime
    - updated_at: datetime
    - is_leader: bool (identifies the leader server in a distributed setup)
    """
    def __init__(self, db_type: str = 'registry'):
        """Initialize ServersCollection with database connection
        
        Args:
            db_type: Type of database to connect to (should be 'registry')
        """
        self.db = DatabaseManager.get_instance(db_type).db
        self.collection = self.db['servers']
        
    def register_server(self, server: Server) -> Optional[str]:
        """Register a server in the registry or update its status if already exists
        
        Args:
            server: Server object containing server details
            
        Returns:
            str: ID of the registered server record
        """
        # Check if server with this ID already exists
        existing = self.collection.find_one({"server_id": server.server_id})
        
        if existing:
            # Update existing server entry
            server_dict = server.to_dict()
            server_dict['updated_at'] = datetime.now()
            self.collection.update_one(
                {"server_id": server.server_id},
                {"$set": server_dict}
            )
            return str(existing['_id'])
        else:
            # Insert new server entry
            server_dict = server.to_dict()
            if 'created_at' not in server_dict or not server_dict['created_at']:
                server_dict['created_at'] = datetime.now()
            server_dict['updated_at'] = datetime.now()
            
            result = self.collection.insert_one(server_dict)
            return str(result.inserted_id) if result else None
    
    def get_all_servers(self, include_terminated: bool = False) -> List[Server]:
        """Get all registered servers
        
        Args:
            include_terminated: Whether to include terminated servers in the results (OFFLINE or STOPPED)
            
        Returns:
            List[Server]: List of server objects
        """
        query = {} if include_terminated else {"status": {"$nin": ["OFFLINE", "STOPPED"]}}
        servers_data = self.collection.find(query)
        
        return [Server.from_dict(server_data) for server_data in servers_data]
    
    def get_server_by_id(self, server_id: str) -> Optional[Server]:
        """Find a server by its ID
        
        Args:
            server_id: Unique ID of the server
            
        Returns:
            Server: Server object if found, None otherwise
        """
        data = self.collection.find_one({"server_id": server_id})
        return Server.from_dict(data) if data else None
    
    def update_server_status(self, server_id: str, status: str) -> bool:
        """Update server status
        
        Args:
            server_id: ID of the server to update
            status: New status (ONLINE, STOPPED, OFFLINE)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        result = self.collection.update_one(
            {"server_id": server_id},
            {"$set": {"status": status, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0
    
    def update_server_leader_status(self, server_id: str, is_leader: bool) -> bool:
        """Update the leader status of a server
        
        Args:
            server_id: ID of the server to update
            is_leader: Boolean indicating if the server is leader
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"server_id": server_id},
                {"$set": {"is_leader": is_leader, "updated_at": datetime.now()}}
            )
            return result.acknowledged and result.modified_count > 0
        except Exception as e:
            import logging
            logging.error(f"Failed to update server leader status: {str(e)}")
            return False
    
    def set_leader(self, server_id: str) -> bool:
        """Set a server as the leader and ensure all others are not leaders
        
        Args:
            server_id: ID of the server to set as leader
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # First, unset leader status for all servers
        self.collection.update_many({}, {"$set": {"is_leader": False}})
        
        # Then set the specified server as leader
        result = self.collection.update_one(
            {"server_id": server_id},
            {"$set": {"is_leader": True, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0
    
    def get_leader(self) -> Optional[Server]:
        """Get the current leader server
        
        Returns:
            Server: Leader server object if found, None otherwise
        """
        data = self.collection.find_one({"is_leader": True})
        return Server.from_dict(data) if data else None
    
    def reset_all_leader_status(self) -> bool:
        """Reset leader status for all servers to False
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            result = self.collection.update_many(
                {},  # Match all documents
                {"$set": {"is_leader": False}}
            )
            return result.acknowledged
        except Exception as e:
            import logging
            logging.error(f"Failed to reset all server leader statuses: {str(e)}")
            return False
