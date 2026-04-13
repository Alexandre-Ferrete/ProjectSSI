"""
Message Types
============
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
    pass


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
    public_key: str


@dataclass
class AuthMessage:
    """TODO: Authentication request."""
    username: str
    password_hash: str


@dataclass
class ChatMessage:
    """TODO: Chat message."""
    recipient: str
    encrypted_content: str
    ephemeral_public_key: Optional[str] = None
    nonce: Optional[str] = None
    tag: Optional[str] = None


@dataclass
class RoomMessage:
    """TODO: Room chat message."""
    room_name: str
    encrypted_content: str