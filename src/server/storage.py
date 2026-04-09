"""
Storage
=======
Persistent storage for users, messages, and server data.
"""

import os
import json
import sqlite3
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Storage:
    """
    Persistent storage layer.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "server.db")
        self.conn = None
    
    def initialize(self):
        """Initialize storage - create database and tables."""
        os.makedirs(self.data_dir, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Storage initialized at {self.db_path}")
    
    def _create_tables(self):
        """Create database tables if not exist."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                public_key BLOB,
                certificate BLOB,
                registered_at TEXT NOT NULL,
                last_login TEXT,
                banned INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offline_messages (
                id TEXT PRIMARY KEY,
                recipient TEXT NOT NULL,
                sender TEXT NOT NULL,
                encrypted_content BLOB NOT NULL,
                ephemeral_public_key BLOB,
                nonce BLOB,
                tag BLOB,
                timestamp TEXT NOT NULL,
                delivered INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                name TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS room_members (
                room_name TEXT NOT NULL,
                username TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                PRIMARY KEY (room_name, username)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_stats (
                id INTEGER PRIMARY KEY,
                total_messages INTEGER DEFAULT 0,
                total_offline_messages INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("SELECT COUNT(*) FROM message_stats")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO message_stats (total_messages, total_offline_messages) VALUES (0, 0)")
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
    def save_user(self, username: str, user_data: Dict[str, Any]):
        """Save or update user data."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (username, password_hash, password_salt, public_key, certificate, registered_at, last_login, banned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            user_data.get("password_hash", ""),
            user_data.get("password_salt", ""),
            user_data.get("public_key"),
            user_data.get("certificate"),
            user_data.get("registered_at", datetime.utcnow().isoformat()),
            user_data.get("last_login"),
            1 if user_data.get("banned", False) else 0
        ))
        self.conn.commit()
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user data by username."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return {
            "username": row["username"],
            "password_hash": row["password_hash"],
            "password_salt": row["password_salt"],
            "public_key": row["public_key"],
            "certificate": row["certificate"],
            "registered_at": row["registered_at"],
            "last_login": row["last_login"],
            "banned": bool(row["banned"])
        }
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all registered users."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY registered_at DESC")
        rows = cursor.fetchall()
        
        return [
            {
                "username": row["username"],
                "password_hash": row["password_hash"],
                "password_salt": row["password_salt"],
                "public_key": row["public_key"],
                "certificate": row["certificate"],
                "registered_at": row["registered_at"],
                "last_login": row["last_login"],
                "banned": bool(row["banned"])
            }
            for row in rows
        ]
    
    def update_last_login(self, username: str):
        """Update user's last login time."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE username = ?",
            (datetime.utcnow().isoformat(), username)
        )
        self.conn.commit()
    
    def delete_user(self, username: str):
        """Delete user and associated data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        cursor.execute("DELETE FROM room_members WHERE username = ?", (username,))
        cursor.execute("DELETE FROM offline_messages WHERE recipient = ? OR sender = ?", (username, username))
        self.conn.commit()
    
    def store_offline_message(
        self,
        recipient: str,
        sender: str,
        encrypted_content: bytes,
        message_id: str,
        ephemeral_public_key: bytes = None,
        nonce: bytes = None,
        tag: bytes = None
    ):
        """Store message for offline recipient."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO offline_messages 
            (id, recipient, sender, encrypted_content, ephemeral_public_key, nonce, tag, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            recipient,
            sender,
            encrypted_content,
            ephemeral_public_key,
            nonce,
            tag,
            datetime.utcnow().isoformat()
        ))
        
        cursor.execute("UPDATE message_stats SET total_offline_messages = total_offline_messages + 1")
        self.conn.commit()
        logger.info(f"Stored offline message from {sender} to {recipient}")
    
    def get_offline_messages(self, recipient: str) -> List[Dict[str, Any]]:
        """Get all offline messages for a user."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM offline_messages 
            WHERE recipient = ? AND delivered = 0
            ORDER BY timestamp ASC
        """, (recipient,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": row["id"],
                "recipient": row["recipient"],
                "sender": row["sender"],
                "encrypted_content": row["encrypted_content"],
                "ephemeral_public_key": row["ephemeral_public_key"],
                "nonce": row["nonce"],
                "tag": row["tag"],
                "timestamp": row["timestamp"]
            }
            for row in rows
        ]
    
    def mark_offline_message_delivered(self, message_id: str):
        """Mark offline message as delivered."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE offline_messages SET delivered = 1 WHERE id = ?",
            (message_id,)
        )
        self.conn.commit()
    
    def delete_offline_message(self, message_id: str):
        """Delete offline message after delivery."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM offline_messages WHERE id = ?", (message_id,))
        self.conn.commit()
    
    def delete_all_offline_messages(self, recipient: str):
        """Delete all offline messages for a user."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM offline_messages WHERE recipient = ?", (recipient,))
        self.conn.commit()
    
    def create_room(self, room_name: str, created_by: str) -> bool:
        """Create a new chat room."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO rooms (name, created_at, created_by)
                VALUES (?, ?, ?)
            """, (room_name, datetime.utcnow().isoformat(), created_by))
            
            cursor.execute("""
                INSERT INTO room_members (room_name, username, joined_at)
                VALUES (?, ?, ?)
            """, (room_name, created_by, datetime.utcnow().isoformat()))
            
            self.conn.commit()
            logger.info(f"Room '{room_name}' created by {created_by}")
            return True
        except sqlite3.IntegrityError:
            return False
    
    def delete_room(self, room_name: str):
        """Delete a chat room."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM rooms WHERE name = ?", (room_name,))
        cursor.execute("DELETE FROM room_members WHERE room_name = ?", (room_name,))
        self.conn.commit()
    
    def room_exists(self, room_name: str) -> bool:
        """Check if room exists."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM rooms WHERE name = ?", (room_name,))
        return cursor.fetchone() is not None
    
    def add_room_member(self, room_name: str, username: str) -> bool:
        """Add user to room."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO room_members (room_name, username, joined_at)
                VALUES (?, ?, ?)
            """, (room_name, username, datetime.utcnow().isoformat()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_room_member(self, room_name: str, username: str):
        """Remove user from room."""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM room_members WHERE room_name = ? AND username = ?",
            (room_name, username)
        )
        
        cursor.execute("SELECT COUNT(*) FROM room_members WHERE room_name = ?", (room_name,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("DELETE FROM rooms WHERE name = ?", (room_name,))
        
        self.conn.commit()
    
    def get_room_members(self, room_name: str) -> List[str]:
        """Get all members of a room."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT username FROM room_members WHERE room_name = ?
        """, (room_name,))
        rows = cursor.fetchall()
        return [row["username"] for row in rows]
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Get all rooms."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.name, r.created_at, r.created_by, 
                   COUNT(m.username) as member_count
            FROM rooms r
            LEFT JOIN room_members m ON r.name = m.room_name
            GROUP BY r.name
            ORDER BY r.created_at DESC
        """)
        rows = cursor.fetchall()
        
        return [
            {
                "name": row["name"],
                "created_at": row["created_at"],
                "created_by": row["created_by"],
                "members": row["member_count"]
            }
            for row in rows
        ]
    
    def is_room_member(self, room_name: str, username: str) -> bool:
        """Check if user is a member of a room."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 1 FROM room_members WHERE room_name = ? AND username = ?
        """, (room_name, username))
        return cursor.fetchone() is not None
    
    def save_certificate(self, username: str, certificate: bytes):
        """Save user's certificate."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET certificate = ? WHERE username = ?",
            (certificate, username)
        )
        self.conn.commit()
    
    def get_certificate(self, username: str) -> Optional[bytes]:
        """Get user's certificate."""
        user = self.get_user(username)
        if user:
            return user.get("certificate")
        return None
    
    def get_public_key(self, username: str) -> Optional[bytes]:
        """Get user's public key."""
        user = self.get_user(username)
        if user:
            return user.get("public_key")
        return None
    
    def save_public_key(self, username: str, public_key: bytes):
        """Save user's public key."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET public_key = ? WHERE username = ?",
            (public_key, username)
        )
        self.conn.commit()
    
    def increment_message_count(self):
        """Increment total message count."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE message_stats SET total_messages = total_messages + 1")
        self.conn.commit()
    
    def get_message_count(self) -> int:
        """Get total number of messages sent."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT total_messages FROM message_stats")
        row = cursor.fetchone()
        return row["total_messages"] if row else 0
    
    def get_offline_message_count(self) -> int:
        """Get number of queued offline messages."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM offline_messages WHERE delivered = 0")
        row = cursor.fetchone()
        return row["COUNT(*)"] if row else 0
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Storage connection closed")
