"""
Message Router
=============
Routes messages between users, handles online/offline delivery.
"""

import logging
import threading
from typing import Optional, List, Dict, Any

from src.utils.helpers import generate_message_id

logger = logging.getLogger(__name__)


class MessageRouter:
    """
    Routes messages between users.
    """
    
    def __init__(self, user_manager, storage):
        self.user_manager = user_manager
        self.storage = storage
        
        self.rooms = {}
        self.rooms_lock = threading.Lock()
    
    def route_message(
        self,
        sender: str,
        recipient: str,
        encrypted_content: bytes,
        message_id: str,
        ephemeral_public_key: bytes = None,
        nonce: bytes = None,
        tag: bytes = None
    ) -> Dict[str, Any]:
        """
        Route a message to recipient.
        
        Args:
            sender: Username of sender
            recipient: Username of recipient
            encrypted_content: Encrypted message payload
            message_id: Unique message identifier
            ephemeral_public_key: Ephemeral public key for ECDH
            nonce: AES-GCM nonce
            tag: AES-GCM tag
            
        Returns:
            {"delivered": bool, "status": str, "error": str or None}
        """
        if sender == recipient:
            return {"delivered": False, "status": "error", "error": "Cannot send to yourself"}
        
        recipient_user = self.user_manager.get_user(recipient)
        if recipient_user is None:
            return {"delivered": False, "status": "error", "error": "Recipient not found"}
        
        self.storage.increment_message_count()
        
        if self.user_manager.is_online(recipient):
            handler = self.user_manager.get_handler(recipient)
            message = {
                "type": "message",
                "sender": sender,
                "encrypted_content": encrypted_content,
                "ephemeral_public_key": ephemeral_public_key,
                "nonce": nonce,
                "tag": tag,
                "message_id": message_id
            }
            handler.send_message(message)
            
            logger.info(f"Message delivered from {sender} to {recipient}")
            return {"delivered": True, "status": "delivered", "error": None}
        else:
            self.store_offline(
                recipient, sender, encrypted_content, message_id,
                ephemeral_public_key, nonce, tag
            )
            
            logger.info(f"Message stored offline from {sender} to {recipient}")
            return {"delivered": False, "status": "offline", "error": None}
    
    def deliver_to_online(self, recipient: str, message: Dict[str, Any]) -> bool:
        """
        Deliver message to online user.
        
        Args:
            recipient: Username
            message: Message to deliver
            
        Returns:
            True if delivered successfully
        """
        handler = self.user_manager.get_handler(recipient)
        if handler:
            handler.send_message(message)
            return True
        return False
    
    def store_offline(
        self,
        recipient: str,
        sender: str,
        encrypted_content: bytes,
        message_id: str,
        ephemeral_public_key: bytes = None,
        nonce: bytes = None,
        tag: bytes = None
    ):
        """
        Store message for offline delivery.
        """
        self.storage.store_offline_message(
            recipient=recipient,
            sender=sender,
            encrypted_content=encrypted_content,
            message_id=message_id,
            ephemeral_public_key=ephemeral_public_key,
            nonce=nonce,
            tag=tag
        )
    
    def deliver_pending_offline_messages(self, username: str, handler):
        """
        Deliver all pending offline messages to user on login.
        """
        messages = self.storage.get_offline_messages(username)
        
        if messages:
            offline_msg = {
                "type": "offline_messages",
                "count": len(messages),
                "messages": [
                    {
                        "sender": msg["sender"],
                        "encrypted_content": msg["encrypted_content"],
                        "ephemeral_public_key": msg["ephemeral_public_key"],
                        "nonce": msg["nonce"],
                        "tag": msg["tag"],
                        "message_id": msg["id"],
                        "timestamp": msg["timestamp"]
                    }
                    for msg in messages
                ]
            }
            handler.send_message(offline_msg)
            
            for msg in messages:
                self.storage.mark_offline_message_delivered(msg["id"])
            
            logger.info(f"Delivered {len(messages)} offline messages to {username}")
    
    def create_room(self, room_name: str, created_by: str) -> Dict[str, Any]:
        """
        Create a new chat room.
        
        Args:
            room_name: Name of the room
            created_by: Username of creator
            
        Returns:
            {"success": bool, "error": str or None}
        """
        if self.storage.room_exists(room_name):
            return {"success": False, "error": "Room already exists"}
        
        if self.storage.create_room(room_name, created_by):
            with self.rooms_lock:
                self.rooms[room_name] = {
                    "members": {created_by},
                    "created_by": created_by
                }
            logger.info(f"Room '{room_name}' created by {created_by}")
            return {"success": True, "error": None}
        
        return {"success": False, "error": "Failed to create room"}
    
    def delete_room(self, room_name: str) -> bool:
        """Delete a chat room."""
        members = self.storage.get_room_members(room_name)
        
        for member in members:
            self.leave_room(room_name, member)
        
        self.storage.delete_room(room_name)
        
        with self.rooms_lock:
            if room_name in self.rooms:
                del self.rooms[room_name]
        
        logger.info(f"Room '{room_name}' deleted")
        return True
    
    def join_room(self, room_name: str, username: str) -> Dict[str, Any]:
        """
        Add user to a room.
        
        Args:
            room_name: Name of room
            username: User to add
            
        Returns:
            {"success": bool, "error": str or None}
        """
        if not self.storage.room_exists(room_name):
            return {"success": False, "error": "Room does not exist"}
        
        if self.storage.is_room_member(room_name, username):
            return {"success": False, "error": "Already a member"}
        
        if self.storage.add_room_member(room_name, username):
            with self.rooms_lock:
                if room_name not in self.rooms:
                    self.rooms[room_name] = {"members": set(), "created_by": None}
                self.rooms[room_name]["members"].add(username)
            
            self._notify_room_members(
                room_name,
                {
                    "type": "user_joined",
                    "room": room_name,
                    "username": username
                },
                exclude=[username]
            )
            
            logger.info(f"{username} joined room '{room_name}'")
            return {"success": True, "error": None}
        
        return {"success": False, "error": "Failed to join room"}
    
    def leave_room(self, room_name: str, username: str) -> bool:
        """Remove user from a room."""
        if not self.storage.is_room_member(room_name, username):
            return False
        
        self.storage.remove_room_member(room_name, username)
        
        with self.rooms_lock:
            if room_name in self.rooms:
                self.rooms[room_name]["members"].discard(username)
        
        self._notify_room_members(
            room_name,
            {
                "type": "user_left",
                "room": room_name,
                "username": username
            }
        )
        
        logger.info(f"{username} left room '{room_name}'")
        return True
    
    def broadcast_to_room(
        self,
        room_name: str,
        sender: str,
        encrypted_content: bytes,
        message_id: str,
        ephemeral_public_key: bytes = None,
        nonce: bytes = None,
        tag: bytes = None
    ) -> Dict[str, Any]:
        """
        Broadcast message to all room members.
        """
        if not self.storage.room_exists(room_name):
            return {"success": False, "error": "Room does not exist"}
        
        if not self.storage.is_room_member(room_name, sender):
            return {"success": False, "error": "Not a member of this room"}
        
        members = self.storage.get_room_members(room_name)
        
        message = {
            "type": "room_message",
            "room": room_name,
            "sender": sender,
            "encrypted_content": encrypted_content,
            "ephemeral_public_key": ephemeral_public_key,
            "nonce": nonce,
            "tag": tag,
            "message_id": message_id
        }
        
        for member in members:
            if member != sender and self.user_manager.is_online(member):
                handler = self.user_manager.get_handler(member)
                handler.send_message(message)
        
        self.storage.increment_message_count()
        logger.info(f"Message broadcasted to room '{room_name}' by {sender}")
        
        return {"success": True, "error": None}
    
    def get_room_members(self, room_name: str) -> List[str]:
        """Get all members of a room."""
        return self.storage.get_room_members(room_name)
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Get all active rooms."""
        return self.storage.get_all_rooms()
    
    def _notify_room_members(self, room_name: str, message: Dict[str, Any], exclude: List[str] = None):
        """Send notification to all room members."""
        exclude = exclude or []
        members = self.storage.get_room_members(room_name)
        
        for member in members:
            if member not in exclude and self.user_manager.is_online(member):
                handler = self.user_manager.get_handler(member)
                handler.send_message(message)
    
    def notify_user_online(self, username: str, handler):
        """Notify user's contacts that they came online."""
        pass
    
    def notify_user_offline(self, username: str):
        """Notify user's contacts that they went offline."""
        pass
    
    def get_room_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        """Get room information."""
        if not self.storage.room_exists(room_name):
            return None
        
        rooms = self.storage.get_all_rooms()
        for room in rooms:
            if room["name"] == room_name:
                members = self.storage.get_room_members(room_name)
                return {
                    "name": room["name"],
                    "created_by": room["created_by"],
                    "created_at": room["created_at"],
                    "members": members,
                    "member_count": len(members)
                }
        
        return None
