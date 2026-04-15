"""
Message Types
===========
Defines all message types for client-server communication.

IMPLEMENTAÇÃO:
- Enum para tipos de mensagens
- Dataclasses para estruturas de mensagens
- JSON como formato de serialização
"""

import time
import json
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


class MessageType(Enum):
    # Fluxo de Sistema (Client <-> Server)
    REGISTER = "register"
    AUTH = "auth"
    GET_IP = "get_ip"
    DISCONNECT = "disconnect"
    RESPONSE = "response"  # Resposta genérica (Sucesso/Erro)
    
    # Fluxo P2P (Client <-> Client)
    P2P_HELLO = "p2p_hello"       # Início do ECDH Handshake
    P2P_MSG = "p2p_msg"           # Mensagem de chat real
    
    # Grupos e Offline
    ROOM_ACTION = "room_action"   # Join/Leave/Create
    OFFLINE_FETCH = "off_fetch"   # Pedir mensagens guardadas
    OFFLINE_STORE = "off_store"   # Servidor a entregar mensagens


@dataclass
class Message:
    msg_type: str 
    sender: str
    payload: Dict[str, Any]
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(**data)



def create_register_msg(username, pwd_hash, pub_key) -> Message:
    return Message(
        msg_type=MessageType.REGISTER.value,
        sender=username,
        payload={
            "password": pwd_hash,
            "public_key": pub_key  # Para a PKI da Pessoa 1
        }
    )

def create_p2p_chat_msg(sender, recipient, encrypted_content, nonce, tag) -> Message:
    """A estrutura que a Pessoa 3 vai precisar para o AES-GCM"""
    return Message(
        msg_type=MessageType.P2P_MSG.value,
        sender=sender,
        payload={
            "recipient": recipient,
            "content": encrypted_content,
            "nonce": nonce,
            "tag": tag
        }
    )