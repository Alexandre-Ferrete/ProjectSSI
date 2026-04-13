"""
Storage
======
Persistent storage for users, messages, and server data.

IMPLEMENTAÇÃO:
- SQLite para persistência (ficheiro server.db)
- Tabelas: users, offline_messages, rooms, room_members
- Conexão com check_same_thread=False para threading
"""

import os
import json
import sqlite3
import logging
from typing import Optional, Dict, Any, List


class Storage:
    """
    Persistent storage layer.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Inicializa storage com diretório de dados."""
        # self.data_dir = data_dir
        # self.db_path = os.path.join(data_dir, "server.db")
        # self.conn = None
        pass
    
    def initialize(self):
        """Inicializa storage - cria base de dados e tabelas."""
        # 1. os.makedirs(data_dir, exist_ok=True)
        # 2. Conectar SQLite: sqlite3.connect(db_path)
        # 3. _create_tables()
        pass
    
    def _create_tables(self):
        """Cria tabelas SQLite."""
        # users: username PK, password, public_key, certificate
        # offline_messages: id PK, recipient, sender, encrypted_content, etc.
        # rooms: name PK, created_by
        # room_members: room_name, username (PK composta)
        pass
    
    def save_user(self, username: str, user_data: Dict[str, Any]):
        """Guarda ou atualiza dados do utilizador."""
        # INSERT OR REPLACE INTO users
        pass
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retorna dados do utilizador por username."""
        # SELECT * FROM users WHERE username = ?
        pass
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Retorna todos os utilizadores registados."""
        # SELECT * FROM users
        pass
    
    def update_last_login(self, username: str):
        """Atualiza último login do utilizador."""
        pass
    
    def delete_user(self, username: str):
        """Apaga utilizador e dados associados."""
        # DELETE FROM users WHERE username = ?
        pass
    
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
        """Guarda mensagem para destinatário offline."""
        # INSERT INTO offline_messages
        pass
    
    def get_offline_messages(self, recipient: str) -> List[Dict[str, Any]]:
        """Retorna mensagens offline para um utilizador."""
        # SELECT * FROM offline_messages WHERE recipient = ? AND delivered = 0
        pass
    
    def mark_offline_message_delivered(self, message_id: str):
        """Marca mensagem offline como entregue."""
        # UPDATE offline_messages SET delivered = 1 WHERE id = ?
        pass
    
    def delete_offline_message(self, message_id: str):
        """Apaga mensagem offline após entrega."""
        # DELETE FROM offline_messages WHERE id = ?
        pass
    
    def delete_all_offline_messages(self, recipient: str):
        """Apaga todas as mensagens offline para um utilizador."""
        # DELETE FROM offline_messages WHERE recipient = ?
        pass
    
    def create_room(self, room_name: str, created_by: str) -> bool:
        """Cria novo room de chat."""
        # INSERT INTO rooms + INSERT INTO room_members (criador)
        pass
    
    def delete_room(self, room_name: str):
        """Elimina room de chat."""
        # DELETE FROM room_members + DELETE FROM rooms
        pass
    
    def room_exists(self, room_name: str) -> bool:
        """Verifica se room existe."""
        # SELECT 1 FROM rooms WHERE name = ?
        pass
    
    def add_room_member(self, room_name: str, username: str) -> bool:
        """Adiciona membro ao room."""
        # INSERT INTO room_members (ignorar se já existe)
        pass
    
    def remove_room_member(self, room_name: str, username: str):
        """Remove membro do room."""
        # DELETE FROM room_members
        pass
    
    def get_room_members(self, room_name: str) -> List[str]:
        """Retorna membros de um room."""
        # SELECT username FROM room_members WHERE room_name = ?
        pass
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Retorna todos os rooms."""
        # SELECT name, created_by FROM rooms
        pass
    
    def is_room_member(self, room_name: str, username: str) -> bool:
        """Verifica se utilizador é membro do room."""
        # SELECT 1 FROM room_members WHERE room_name = ? AND username = ?
        pass
    
    def save_certificate(self, username: str, certificate: bytes):
        """Guarda certificado do utilizador."""
        # UPDATE users SET certificate = ? WHERE username = ?
        pass
    
    def get_certificate(self, username: str) -> Optional[bytes]:
        """Retorna certificado do utilizador."""
        # SELECT certificate FROM users WHERE username = ?
        pass
    
    def get_public_key(self, username: str) -> Optional[bytes]:
        """Retorna chave pública do utilizador."""
        # SELECT public_key FROM users WHERE username = ?
        pass
    
    def save_public_key(self, username: str, public_key: bytes):
        """Guarda chave pública do utilizador."""
        # UPDATE users SET public_key = ? WHERE username = ?
        pass
    
    def increment_message_count(self):
        """Incrementa contador de mensagens."""
        pass
    
    def get_message_count(self) -> int:
        """Retorna número total de mensagens enviadas."""
        pass
    
    def get_offline_message_count(self) -> int:
        """Retorna número de mensagens offline em queue."""
        # SELECT COUNT(*) FROM offline_messages WHERE delivered = 0
        pass
    
    def close(self):
        """Fecha conexão com base de dados."""
        # conn.close()
        pass
