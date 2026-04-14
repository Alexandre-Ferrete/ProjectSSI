import os
import sqlite3
from typing import Optional, List, Dict, Any


class Storage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "server.db")
        self.conn: Optional[sqlite3.Connection] = None

    def initialize(self):
        os.makedirs(self.data_dir, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                public_key BLOB,
                certificate BLOB
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS offline_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                sender TEXT NOT NULL,
                encrypted_content BLOB NOT NULL,
                nonce BLOB,
                tag BLOB
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                name TEXT PRIMARY KEY,
                created_by TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(username)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS room_members (
                room_name TEXT NOT NULL,
                username TEXT NOT NULL,
                PRIMARY KEY (room_name, username),
                FOREIGN KEY (room_name) REFERENCES rooms(name),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)

        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    # USER FUNCTIONS
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        # Retorna utilizador pelo username
        cursor = self.conn.execute(
            "SELECT username, password_hash, public_key, certificate FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def create_user(self, username: str, password_hash: str, public_key: Optional[bytes] = None,
                    certificate: Optional[bytes] = None) -> bool:
        # Cria novo utilizador
        try:
            self.conn.execute(
                "INSERT INTO users (username, password_hash, public_key, certificate) VALUES (?, ?, ?, ?)",
                (username, password_hash, public_key, certificate)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_user(self, username: str) -> bool:
        # Apaga utilizador
        cursor = self.conn.execute("DELETE FROM users WHERE username = ?", (username,))
        self.conn.commit()
        return cursor.rowcount > 0

    def list_users(self) -> List[Dict[str, Any]]:
        # Lista todos os utilizadores
        cursor = self.conn.execute("SELECT username FROM users")
        return [{"username": row[0]} for row in cursor.fetchall()]

    # OFFLINE MESSAGE FUNCTIONS
    def store_offline_message(self, recipient: str, sender: str, encrypted_content: bytes,
                               nonce: Optional[bytes] = None, tag: Optional[bytes] = None) -> int:
        # Guarda mensagem offline
        cursor = self.conn.execute(
            "INSERT INTO offline_messages (recipient, sender, encrypted_content, nonce, tag) VALUES (?, ?, ?, ?, ?)",
            (recipient, sender, encrypted_content, nonce, tag)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_offline_messages(self, recipient: str) -> List[Dict[str, Any]]:
        # Retorna mensagens offline de um destinatário
        cursor = self.conn.execute(
            "SELECT id, recipient, sender, encrypted_content, nonce, tag FROM offline_messages WHERE recipient = ?",
            (recipient,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def delete_offline_message(self, message_id: int) -> bool:
        # Apaga uma mensagem offline
        cursor = self.conn.execute("DELETE FROM offline_messages WHERE id = ?", (message_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def clear_offline_messages(self, recipient: str) -> int:
        # Apaga todas as mensagens offline de um utilizador
        cursor = self.conn.execute("DELETE FROM offline_messages WHERE recipient = ?", (recipient,))
        self.conn.commit()
        return cursor.rowcount

    # ROOM FUNCTIONS
    def create_room(self, name: str, created_by: str) -> bool:
        # Cria nova sala
        try:
            self.conn.execute("INSERT INTO rooms (name, created_by) VALUES (?, ?)", (name, created_by))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_room(self, name: str) -> bool:
        # Apaga sala e os seus membros
        self.conn.execute("DELETE FROM room_members WHERE room_name = ?", (name,))
        cursor = self.conn.execute("DELETE FROM rooms WHERE name = ?", (name,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_room(self, name: str) -> Optional[Dict[str, Any]]:
        # Retorna sala pelo nome
        cursor = self.conn.execute("SELECT name, created_by FROM rooms WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def list_rooms(self) -> List[Dict[str, Any]]:
        # Lista todas as salas
        cursor = self.conn.execute("SELECT name, created_by FROM rooms")
        return [dict(row) for row in cursor.fetchall()]

    # ROOM MEMBER FUNCTIONS
    def add_room_member(self, room_name: str, username: str) -> bool:
        # Adiciona membro a uma sala
        try:
            self.conn.execute(
                "INSERT INTO room_members (room_name, username) VALUES (?, ?)",
                (room_name, username)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_room_member(self, room_name: str, username: str) -> bool:
        # Remove membro de uma sala
        cursor = self.conn.execute(
            "DELETE FROM room_members WHERE room_name = ? AND username = ?",
            (room_name, username)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_room_members(self, room_name: str) -> List[str]:
        # Retorna membros de uma sala
        cursor = self.conn.execute(
            "SELECT username FROM room_members WHERE room_name = ?",
            (room_name,)
        )
        return [row[0] for row in cursor.fetchall()]

    def is_room_member(self, room_name: str, username: str) -> bool:
        # Verifica se utilizador é membro de uma sala
        cursor = self.conn.execute(
            "SELECT 1 FROM room_members WHERE room_name = ? AND username = ?",
            (room_name, username)
        )
        return cursor.fetchone() is not None

    def get_user_rooms(self, username: str) -> List[str]:
        # Retorna salas de um utilizador
        cursor = self.conn.execute(
            "SELECT room_name FROM room_members WHERE username = ?",
            (username,)
        )
        return [row[0] for row in cursor.fetchall()]
