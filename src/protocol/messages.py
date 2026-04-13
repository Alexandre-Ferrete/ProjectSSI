"""
Message Types
===========
Defines all message types for client-server communication.

IMPLEMENTAÇÃO:
- Enum para tipos de mensagens
- Dataclasses para estruturas de mensagens
- JSON como formato de serialização
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class MessageType(Enum):
    """Tipos de mensagens do protocolo."""
    # Client → Server
    REGISTER = "register"
    AUTH = "auth"
    GET_IP = "get_ip"
    CHAT = "chat"
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_MESSAGE = "room_message"
    GET_USERS = "get_users"
    GET_ROOMS = "get_rooms"
    GET_OFFLINE = "get_offline"
    GET_PUBLIC_KEY = "get_public_key"
    DISCONNECT = "disconnect"
    
    # Server → Client
    REGISTER_RESPONSE = "register_response"
    AUTH_RESPONSE = "auth_response"
    IP_RESPONSE = "ip_response"
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
    """Estrutura base de mensagem."""
    type: MessageType
    payload: Dict[str, Any]
    timestamp: Optional[int] = None


@dataclass
class RegisterMessage:
    """Pedido de registo de novo utilizador."""
    username: str
    password_hash: str
    public_key: str


@dataclass
class AuthMessage:
    """Pedido de autenticação."""
    username: str
    password_hash: str


@dataclass
class ChatMessage:
    """Mensagem de chat encriptada."""
    recipient: str
    encrypted_content: str
    ephemeral_public_key: Optional[str] = None
    nonce: Optional[str] = None
    tag: Optional[str] = None


@dataclass
class RoomMessage:
    """Mensagem de room de chat."""
    room_name: str
    encrypted_content: str
