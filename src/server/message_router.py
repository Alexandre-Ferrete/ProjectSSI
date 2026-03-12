"""
Message Router
==============
Routes messages between users, handles online/offline delivery.

TODO:
- Route messages to online users directly
- Store offline messages for later delivery
- Handle group chat messages
- Deliver pending offline messages on login
"""

import logging
import threading
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class MessageRouter:
    """
    Routes messages between users.
    
    TODO:
    - Route to online users (deliver immediately)
    - Store for offline users (queue for later)
    - Handle group messages
    - Notify about online/offline status
    """
    
    def __init__(self, user_manager, storage):
        self.user_manager = user_manager
        self.storage = storage
        
        # Active rooms: room_name -> {members: set, created_by: str}
        self.rooms = {}
        self.rooms_lock = threading.Lock()
    
    # =========================================================================
    # Direct Messages
    # =========================================================================
    
    def route_message(
        self,
        sender: str,
        recipient: str,
        encrypted_content: bytes,
        message_id: str
    ) -> Dict[str, Any]:
        """
        TODO: Route a message to recipient.
        
        Args:
            sender: Username of sender
            recipient: Username of recipient
            encrypted_content: Encrypted message payload
            message_id: Unique message identifier
            
        Returns:
            {
                "delivered": true/false,
                "status": "delivered" | "offline" | "error",
                "error": "..." (if error)
            }
        
        Logic:
        1. Check if recipient is online
        2. If online -> deliver immediately
        3. If offline -> store for later delivery
        4. Return delivery status
        """
        pass
    
    def deliver_to_online(self, recipient: str, message: Dict[str, Any]) -> bool:
        """
        TODO: Deliver message to online user.
        
        Args:
            recipient: Username
            message: Message to deliver
            
        Returns:
            True if delivered successfully
        """
        pass
    
    def store_offline(self, recipient: str, sender: str, encrypted_content: bytes, message_id: str):
        """
        TODO: Store message for offline delivery.
        
        - Save to storage
        - Will be delivered on user's next login
        """
        pass
    
    def deliver_pending_offline_messages(self, username: str, handler):
        """
        TODO: Deliver all pending offline messages to user on login.
        
        Called when user authenticates successfully.
        
        Args:
            username: Username of logged-in user
            handler: ClientHandler to send messages to
        """
        pass
    
    # =========================================================================
    # Group Chat / Rooms
    # =========================================================================
    
    def create_room(self, room_name: str, created_by: str) -> bool:
        """
        TODO: Create a new chat room.
        
        Args:
            room_name: Name of the room
            created_by: Username of creator
            
        Returns:
            True if created successfully
        """
        pass
    
    def delete_room(self, room_name: str):
        """TODO: Delete a chat room."""
        pass
    
    def join_room(self, room_name: str, username: str) -> bool:
        """
        TODO: Add user to a room.
        
        Args:
            room_name: Name of room
            username: User to add
            
        Returns:
            True if joined successfully
        """
        pass
    
    def leave_room(self, room_name: str, username: str):
        """TODO: Remove user from a room."""
        pass
    
    def broadcast_to_room(
        self,
        room_name: str,
        sender: str,
        encrypted_content: bytes,
        message_id: str
    ):
        """
        TODO: Broadcast message to all room members.
        
        Args:
            room_name: Name of room
            sender: Username of sender
            encrypted_content: Encrypted message
            message_id: Unique message identifier
        """
        pass
    
    def get_room_members(self, room_name: str) -> List[str]:
        """TODO: Get all members of a room."""
        pass
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """TODO: Get all active rooms."""
        pass
    
    # =========================================================================
    # Online/Offline Notifications
    # =========================================================================
    
    def notify_user_online(self, username: str, handler):
        """
        TODO: Notify user's contacts that they came online.
        
        Optional feature - could notify friends/contacts.
        """
        pass
    
    def notify_user_offline(self, username: str):
        """
        TODO: Notify user's contacts that they went offline.
        
        Optional feature.
        """
        pass


# ============================================================================
# MESSAGE DELIVERY FLOW
# ============================================================================
#
# 1. Client A sends encrypted message to Client B
# 2. Server receives message via TCP
# 3. Server checks if B is online
# 4. If ONLINE:
#    - Server delivers to B's handler immediately
#    - Returns "delivered" status to A
# 5. If OFFLINE:
#    - Server stores message in offline queue
#    - Returns "stored" status to A
# 6. When B logs in:
#    - Server delivers all pending offline messages
#    - B decrypts and displays messages
#
# GROUP CHAT FLOW:
# 1. Client creates/joins room
# 2. Client sends message to room
# 3. Server broadcasts to all room members
# 4. Each member receives and decrypts
#
# ============================================================================
