"""
User Manager
============
Handles user registration, authentication, and online user tracking.
"""

import threading
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.utils.helpers import hash_password, verify_password, validate_username, validate_password

logger = logging.getLogger(__name__)


class UserManager:
    """
    Manages user accounts and authentication.
    """
    
    def __init__(self, storage):
        self.storage = storage
        self.online_users = {}
        self.online_lock = threading.Lock()
    
    def register_user(
        self,
        username: str,
        password: str,
        public_key: bytes,
        certificate: bytes = None
    ) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: Unique username
            password: User's password
            public_key: User's public key for encryption
            certificate: User's certificate signed by CA
            
        Returns:
            {"success": bool, "error": str or None, "certificate": bytes or None}
        """
        if not validate_username(username):
            return {"success": False, "error": "Invalid username format", "certificate": None}
        
        if not validate_password(password):
            return {"success": False, "error": "Password must be at least 8 chars with letters and digits", "certificate": None}
        
        if self.user_exists(username):
            return {"success": False, "error": "Username already exists", "certificate": None}
        
        password_hash, password_salt = hash_password(password)
        
        user_data = {
            "password_hash": password_hash,
            "password_salt": password_salt,
            "public_key": public_key,
            "certificate": certificate,
            "registered_at": datetime.utcnow().isoformat(),
            "banned": False
        }
        
        self.storage.save_user(username, user_data)
        logger.info(f"User registered: {username}")
        
        return {"success": True, "error": None, "certificate": certificate}
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        return self.storage.get_user(username) is not None
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username and password.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            User data if authenticated, None otherwise
        """
        user = self.storage.get_user(username)
        
        if user is None:
            logger.warning(f"Authentication failed: user not found - {username}")
            return None
        
        if user.get("banned", False):
            logger.warning(f"Authentication failed: user banned - {username}")
            return None
        
        if not verify_password(password, user["password_hash"], user["password_salt"]):
            logger.warning(f"Authentication failed: invalid password - {username}")
            return None
        
        self.storage.update_last_login(username)
        logger.info(f"User authenticated: {username}")
        
        return user
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user data by username."""
        return self.storage.get_user(username)
    
    def add_online(self, username: str, handler):
        """Mark user as online."""
        with self.online_lock:
            self.online_users[username] = handler
        logger.info(f"User online: {username}")
    
    def remove_online(self, username: str):
        """Mark user as offline."""
        with self.online_lock:
            if username in self.online_users:
                del self.online_users[username]
        logger.info(f"User offline: {username}")
    
    def is_online(self, username: str) -> bool:
        """Check if user is online."""
        with self.online_lock:
            return username in self.online_users
    
    def get_online_users(self) -> List[str]:
        """Get list of all online users."""
        with self.online_lock:
            return list(self.online_users.keys())
    
    def get_handler(self, username: str):
        """Get handler for online user."""
        with self.online_lock:
            return self.online_users.get(username)
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all registered users."""
        users = self.storage.get_all_users()
        online = self.get_online_users()
        
        for user in users:
            user["online"] = user["username"] in online
        
        return users
    
    def ban_user(self, username: str) -> bool:
        """Ban a user."""
        user = self.storage.get_user(username)
        if user:
            user["banned"] = True
            self.storage.save_user(username, user)
            
            if self.is_online(username):
                self.remove_online(username)
            
            logger.info(f"User banned: {username}")
            return True
        return False
    
    def unban_user(self, username: str) -> bool:
        """Unban a user."""
        user = self.storage.get_user(username)
        if user:
            user["banned"] = False
            self.storage.save_user(username, user)
            logger.info(f"User unbanned: {username}")
            return True
        return False
    
    def is_banned(self, username: str) -> bool:
        """Check if user is banned."""
        user = self.storage.get_user(username)
        return user is not None and user.get("banned", False)
    
    def get_user_count(self) -> int:
        """Get total number of registered users."""
        return len(self.storage.get_all_users())
    
    def get_online_count(self) -> int:
        """Get number of online users."""
        with self.online_lock:
            return len(self.online_users)
