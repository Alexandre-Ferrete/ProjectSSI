"""
Storage
=======
Persistent storage for users, messages, and server data.

TODO:
- Store user data (encrypted)
- Store offline messages
- Store certificates
- Store CA keys
"""

import os
import json
import sqlite3
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class Storage:
    """
    Persistent storage layer.
    
    TODO:
    - Initialize database
    - CRUD operations for users
    - Offline message queue
    - Certificate storage
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "server.db")
        self.conn = None
    
    # =========================================================================
    # Initialization
    # =========================================================================
    
    def initialize(self):
        """
        TODO: Initialize storage - create database and tables.
        
        Database schema:
        - users: username, password_hash, public_key, certificate, registered_at, last_login, banned
        - offline_messages: id, recipient, sender, encrypted_content, timestamp
        - rooms: name, created_at, created_by
        - room_members: room_name, username, joined_at
        """
        pass
    
    def _create_tables(self):
        """TODO: Create database tables if not exist."""
        pass
    
    # =========================================================================
    # User Operations
    # =========================================================================
    
    def save_user(self, username: str, user_data: Dict[str, Any]):
        """
        TODO: Save or update user data.
        
        Args:
            username: User's unique identifier
            user_data: {
                "password_hash": "...",
                "public_key": "...",
                "certificate": "...",
                "registered_at": "...",
                "last_login": "...",
                "banned": false
            }
        """
        pass
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """TODO: Get user data by username."""
        pass
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """TODO: Get all registered users."""
        pass
    
    def delete_user(self, username: str):
        """TODO: Delete user and associated data."""
        pass
    
    # =========================================================================
    # Offline Messages
    # =========================================================================
    
    def store_offline_message(
        self,
        recipient: str,
        sender: str,
        encrypted_content: bytes,
        message_id: str
    ):
        """
        TODO: Store message for offline recipient.
        
        Args:
            recipient: Username of message recipient
            sender: Username of message sender
            encrypted_content: Encrypted message payload
            message_id: Unique message identifier
        """
        pass
    
    def get_offline_messages(self, recipient: str) -> List[Dict[str, Any]]:
        """
        TODO: Get all offline messages for a user.
        
        Returns:
            List of messages (should be deleted after retrieval)
        """
        pass
    
    def delete_offline_message(self, message_id: str):
        """TODO: Delete offline message after delivery."""
        pass
    
    def delete_all_offline_messages(self, recipient: str):
        """TODO: Delete all offline messages for a user."""
        pass
    
    # =========================================================================
    # Room/Group Chat Operations
    # =========================================================================
    
    def create_room(self, room_name: str, created_by: str):
        """TODO: Create a new chat room."""
        pass
    
    def delete_room(self, room_name: str):
        """TODO: Delete a chat room."""
        pass
    
    def room_exists(self, room_name: str) -> bool:
        """TODO: Check if room exists."""
        pass
    
    def add_room_member(self, room_name: str, username: str):
        """TODO: Add user to room."""
        pass
    
    def remove_room_member(self, room_name: str, username: str):
        """TODO: Remove user from room."""
        pass
    
    def get_room_members(self, room_name: str) -> List[str]:
        """TODO: Get all members of a room."""
        pass
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """TODO: Get all rooms."""
        pass
    
    # =========================================================================
    # Certificate Storage
    # =========================================================================
    
    def save_certificate(self, username: str, certificate: bytes):
        """TODO: Save user's certificate."""
        pass
    
    def get_certificate(self, username: str) -> Optional[bytes]:
        """TODO: Get user's certificate."""
        pass
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_message_count(self) -> int:
        """TODO: Get total number of messages sent."""
        pass
    
    def get_offline_message_count(self) -> int:
        """TODO: Get number of queued offline messages."""
        pass


# ============================================================================
# STORAGE SECURITY CONSIDERATIONS
# ============================================================================
#
# - User passwords stored as salted hashes (Argon2 or PBKDF2)
# - Database file should be encrypted (SQLCipher or OS-level encryption)
# - Private keys stored with encryption at rest
# - Certificate files should have restricted permissions
#
# ============================================================================
