"""
Message Types
=============
Defines all message types for client-server communication.

TODO:
- Define message structure
- Define message types (enum)
- Serialization/deserialization
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class MessageType(Enum):
    """TODO: All message types in the protocol."""
    
    # Client -> Server
    REGISTER = "register"
    AUTH = "auth"
    CHAT = "chat"
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    GET_USERS = "get_users"
    GET_ROOMS = "get_rooms"
    GET_OFFLINE = "get_offline"
    DISCONNECT = "disconnect"
    
    # Server -> Client
    REGISTER_RESPONSE = "register_response"
    AUTH_RESPONSE = "auth_response"
    CHAT_RESPONSE = "chat_response"
    MESSAGE = "message"
    ROOM_MESSAGE = "room_message"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    ROOM_CREATED = "room_created"
    ROOM_JOINED = "room_joined"
    ROOM_LEFT = "room_left"
    USERS_LIST = "users_list"
    ROOMS_LIST = "rooms_list"
    OFFLINE_MESSAGES = "offline_messages"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class Message:
    """TODO: Base message structure."""
    type: MessageType
    payload: Dict[str, Any]
    timestamp: Optional[int] = None


@dataclass
class RegisterMessage:
    """TODO: Registration request."""
    username: str
    password_hash: str
    public_key: str  # Base64 encoded


@dataclass
class AuthMessage:
    """TODO: Authentication request."""
    username: str
    password_hash: str


@dataclass
class ChatMessage:
    """TODO: Chat message."""
    recipient: str
    encrypted_content: str  # Base64 encoded
    ephemeral_public_key: Optional[str] = None  # Base64 for ECDH
    nonce: Optional[str] = None  # Base64
    tag: Optional[str] = None  # Base64


@dataclass
class RoomMessage:
    """TODO: Room chat message."""
    room_name: str
    encrypted_content: str


# =========================================================================
# MESSAGE FORMATS
# =========================================================================
#
# All messages are JSON with this structure:
# {
#     "type": "message_type",
#     "payload": {...},
#     "timestamp": 1234567890  // optional
# }
#
# =========================================================================
