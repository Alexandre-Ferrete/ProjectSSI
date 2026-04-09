"""
Client Main Entry Point
=======================
TCP client that connects to the chat server.
"""

import socket
import threading
import logging
import struct
import json
from typing import Optional

from src.client.session_manager import SessionManager
from src.client.cli import CLI
from src.utils.helpers import encode_base64, decode_base64, generate_message_id, setup_logging

logger = logging.getLogger(__name__)


class ChatClient:
    """
    Main client class that connects to the server.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 5555):
        self.host = host
        self.port = port
        self.socket = None
        
        self.username = None
        self.authenticated = False
        self.running = False
        self.connected = False
        
        self.session_manager = SessionManager()
        self.cli = CLI(self)
        
        self.receive_thread = None
        self._recv_buffer = b""
        
        self._message_callbacks = []
        
        self.current_room = None
    
    def connect(self) -> bool:
        """
        Connect to server.
        
        Returns:
            True if connected successfully
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True
            
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            logger.info(f"Connected to server at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from server gracefully."""
        self.running = False
        
        if self.authenticated:
            try:
                self.send_message({"type": "disconnect"})
            except Exception:
                pass
        
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        
        self.connected = False
        self.authenticated = False
        self.username = None
        
        logger.info("Disconnected from server")
    
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self.connected and self.socket is not None
    
    def send_message(self, message: dict):
        """
        Send message to server.
        Protocol: [4 bytes length][JSON payload]
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to server")
        
        try:
            data = json.dumps(message, ensure_ascii=False).encode('utf-8')
            length = struct.pack("!I", len(data))
            self.socket.sendall(length + data)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    def _receive_loop(self):
        """Continuously receive messages from server."""
        while self.running and self.connected:
            try:
                data = self._receive()
                if data is None:
                    break
                
                if data:
                    self._process_message(data)
                    
            except Exception as e:
                logger.error(f"Receive error: {e}")
                break
        
        self._handle_disconnection()
    
    def _receive(self) -> Optional[bytes]:
        """
        Receive data from server.
        Protocol: [4 bytes length][JSON payload]
        """
        try:
            length_data = self._recv_exact(4)
            if length_data is None:
                return None
            
            length = struct.unpack("!I", length_data)[0]
            
            if length > 10 * 1024 * 1024:
                logger.warning(f"Message too large: {length}")
                return None
            
            data = self._recv_exact(length)
            if data is None:
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def _recv_exact(self, n: int) -> Optional[bytes]:
        """Receive exactly n bytes."""
        while len(self._recv_buffer) < n:
            try:
                chunk = self.socket.recv(max(4096, n - len(self._recv_buffer)))
                if not chunk:
                    return None
                self._recv_buffer += chunk
            except socket.timeout:
                if len(self._recv_buffer) >= n:
                    break
                continue
            except Exception:
                return None
        
        result = self._recv_buffer[:n]
        self._recv_buffer = self._recv_buffer[n:]
        return result
    
    def _process_message(self, data: bytes):
        """Parse and handle incoming message."""
        try:
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get("type", "")
            
            logger.debug(f"Received: {msg_type}")
            
            handlers = {
                "register_response": self._handle_register_response,
                "auth_response": self._handle_auth_response,
                "chat_response": self._handle_chat_response,
                "message": self._handle_incoming_message,
                "room_message": self._handle_room_message,
                "room_created": self._handle_room_created,
                "room_joined": self._handle_room_joined,
                "room_left": self._handle_room_left,
                "user_joined": self._handle_user_joined,
                "user_left": self._handle_user_left,
                "users_list": self._handle_users_list,
                "rooms_list": self._handle_rooms_list,
                "offline_messages": self._handle_offline_messages,
                "public_key_response": self._handle_public_key_response,
                "user_online": self._handle_user_online,
                "user_offline": self._handle_user_offline,
                "ca_certificate": self._handle_ca_certificate,
                "error": self._handle_error,
                "success": self._handle_success,
            }
            
            handler = handlers.get(msg_type)
            if handler:
                handler(message)
            else:
                logger.debug(f"Unhandled message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_disconnection(self):
        """Handle disconnection from server."""
        self.connected = False
        self.running = False
        
        if hasattr(self.cli, 'on_disconnected'):
            self.cli.on_disconnected()
    
    def register(self, username: str, password: str) -> bool:
        """
        Register new user account.
        
        Args:
            username: Desired username
            password: User's password
            
        Returns:
            True if registration request sent
        """
        if not self.is_connected():
            self.cli.display_error("Not connected to server")
            return False
        
        self.session_manager.set_username(username)
        
        if not self.session_manager.has_keys():
            self.session_manager.generate_keypair()
        
        public_key_b64 = self.session_manager.get_public_key_b64()
        
        message = {
            "type": "register",
            "username": username,
            "password": password,
            "public_key": public_key_b64
        }
        
        try:
            self.send_message(message)
            return True
        except Exception as e:
            self.cli.display_error(f"Registration failed: {e}")
            return False
    
    def login(self, username: str, password: str) -> bool:
        """
        Authenticate with server.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if authentication request sent
        """
        if not self.is_connected():
            self.cli.display_error("Not connected to server")
            return False
        
        self.session_manager.set_username(username)
        
        self.session_manager.load_keys()
        
        message = {
            "type": "auth",
            "username": username,
            "password": password
        }
        
        try:
            self.send_message(message)
            return True
        except Exception as e:
            self.cli.display_error(f"Login failed: {e}")
            return False
    
    def logout(self):
        """Logout from server."""
        self.session_manager.clear_all_session_keys()
        self.current_room = None
        
        if self.is_connected():
            try:
                self.send_message({"type": "disconnect"})
            except Exception:
                pass
        
        self.authenticated = False
        self.username = None
    
    def send_chat(self, recipient: str, plaintext: str) -> bool:
        """
        Send encrypted chat message to recipient.
        
        Args:
            recipient: Recipient's username
            plaintext: Message to send
            
        Returns:
            True if message sent successfully
        """
        if not self.authenticated:
            self.cli.display_error("Not authenticated")
            return False
        
        try:
            recipient_key = self.session_manager.get_recipient_key(recipient)
            
            if not recipient_key:
                self.cli.display_status("Fetching recipient's public key...")
                self.send_message({
                    "type": "get_public_key",
                    "username": recipient
                })
                return False
            
            encrypted = self.session_manager.encrypt_message(
                recipient,
                plaintext.encode('utf-8')
            )
            
            message = {
                "type": "chat",
                "recipient": recipient,
                "encrypted_content": encrypted["encrypted_content"],
                "ephemeral_public_key": encrypted["ephemeral_public_key"],
                "nonce": encrypted["nonce"],
                "tag": encrypted["tag"],
                "message_id": generate_message_id()
            }
            
            self.send_message(message)
            return True
            
        except Exception as e:
            self.cli.display_error(f"Failed to send message: {e}")
            return False
    
    def send_room_message(self, room_name: str, plaintext: str) -> bool:
        """Send message to room."""
        if not self.authenticated:
            self.cli.display_error("Not authenticated")
            return False
        
        try:
            encrypted = self._encrypt_for_all_members(room_name, plaintext.encode('utf-8'))
            
            message = {
                "type": "room_message",
                "room_name": room_name,
                "encrypted_content": encrypted["encrypted_content"],
                "ephemeral_public_key": encrypted["ephemeral_public_key"],
                "nonce": encrypted["nonce"],
                "tag": encrypted["tag"],
                "message_id": generate_message_id()
            }
            
            self.send_message(message)
            return True
            
        except Exception as e:
            self.cli.display_error(f"Failed to send room message: {e}")
            return False
    
    def _encrypt_for_all_members(self, room_name: str, plaintext: bytes) -> dict:
        """Encrypt message for all room members (simplified - uses recipient's key)."""
        members = self._room_members.get(room_name, [])
        
        if not members:
            raise ValueError("Room has no members")
        
        recipient = members[0]
        return self.session_manager.encrypt_message(recipient, plaintext)
    
    def create_room(self, room_name: str) -> bool:
        """Create a new chat room."""
        if not self.authenticated:
            self.cli.display_error("Not authenticated")
            return False
        
        try:
            self.send_message({
                "type": "create_room",
                "room_name": room_name
            })
            return True
        except Exception as e:
            self.cli.display_error(f"Failed to create room: {e}")
            return False
    
    def join_room(self, room_name: str) -> bool:
        """Join an existing chat room."""
        if not self.authenticated:
            self.cli.display_error("Not authenticated")
            return False
        
        try:
            self.send_message({
                "type": "join_room",
                "room_name": room_name
            })
            return True
        except Exception as e:
            self.cli.display_error(f"Failed to join room: {e}")
            return False
    
    def leave_room(self, room_name: str) -> bool:
        """Leave a chat room."""
        if not self.authenticated:
            self.cli.display_error("Not authenticated")
            return False
        
        try:
            self.send_message({
                "type": "leave_room",
                "room_name": room_name
            })
            
            if self.current_room == room_name:
                self.current_room = None
            
            return True
        except Exception as e:
            self.cli.display_error(f"Failed to leave room: {e}")
            return False
    
    def get_online_users(self):
        """Request list of online users."""
        if not self.authenticated:
            return
        
        try:
            self.send_message({"type": "get_users"})
        except Exception as e:
            self.cli.display_error(f"Failed to get users: {e}")
    
    def get_rooms(self):
        """Request list of available rooms."""
        if not self.authenticated:
            return
        
        try:
            self.send_message({"type": "get_rooms"})
        except Exception as e:
            self.cli.display_error(f"Failed to get rooms: {e}")
    
    def _handle_register_response(self, message: dict):
        """Handle registration response."""
        if message.get("success"):
            cert_b64 = message.get("certificate")
            ca_cert_b64 = message.get("ca_certificate")
            
            if cert_b64:
                self.session_manager.set_certificate(decode_base64(cert_b64))
            if ca_cert_b64:
                self.session_manager.set_ca_certificate(decode_base64(ca_cert_b64))
            
            self.cli.on_success("Registration successful! Certificate issued.")
        else:
            self.cli.on_error(message.get("error", "Registration failed"))
    
    def _handle_auth_response(self, message: dict):
        """Handle authentication response."""
        if message.get("success"):
            self.username = message.get("username")
            self.authenticated = True
            
            cert_b64 = message.get("certificate")
            ca_cert_b64 = message.get("ca_certificate")
            pub_key_b64 = message.get("public_key")
            
            if cert_b64:
                self.session_manager.set_certificate(decode_base64(cert_b64))
            if ca_cert_b64:
                self.session_manager.set_ca_certificate(decode_base64(ca_cert_b64))
            
            self.session_manager.load_keys()
            
            self.cli.on_auth_success()
        else:
            self.cli.on_error(message.get("error", "Authentication failed"))
    
    def _handle_chat_response(self, message: dict):
        """Handle chat response."""
        if message.get("success"):
            self.cli.display_status("Message sent")
        else:
            status = message.get("status", "error")
            if status == "offline":
                self.cli.display_status("Message stored for offline delivery")
            else:
                self.cli.on_error(message.get("error", "Failed to send message"))
    
    def _handle_incoming_message(self, message: dict):
        """Handle incoming message."""
        sender = message.get("sender", "unknown")
        encrypted_content = message.get("encrypted_content")
        ephemeral_pub = message.get("ephemeral_public_key")
        nonce = message.get("nonce")
        tag = message.get("tag")
        
        try:
            if encrypted_content and ephemeral_pub and nonce and tag:
                plaintext = self.session_manager.decrypt_message(
                    sender, encrypted_content, ephemeral_pub, nonce, tag
                )
                content = plaintext.decode('utf-8')
            else:
                content = "[Encrypted message - decryption failed]"
            
            self.cli.on_message_received(sender, content)
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            self.cli.on_message_received(sender, "[Decryption failed]")
    
    def _handle_room_message(self, message: dict):
        """Handle room message."""
        room = message.get("room", "unknown")
        sender = message.get("sender", "unknown")
        encrypted_content = message.get("encrypted_content")
        ephemeral_pub = message.get("ephemeral_public_key")
        nonce = message.get("nonce")
        tag = message.get("tag")
        
        try:
            if encrypted_content and ephemeral_pub and nonce and tag:
                plaintext = self.session_manager.decrypt_message(
                    sender, encrypted_content, ephemeral_pub, nonce, tag
                )
                content = plaintext.decode('utf-8')
            else:
                content = "[Encrypted message]"
            
            self.cli.on_room_message(room, sender, content)
        except Exception as e:
            logger.error(f"Room message decryption error: {e}")
            self.cli.on_room_message(room, sender, "[Decryption failed]")
    
    def _handle_room_created(self, message: dict):
        """Handle room created response."""
        if message.get("success"):
            self.cli.on_success(f"Room '{message.get('room_name')}' created")
        else:
            self.cli.on_error("Failed to create room")
    
    def _handle_room_joined(self, message: dict):
        """Handle room joined response."""
        if message.get("success"):
            room_name = message.get("room_name")
            members = message.get("members", [])
            self.current_room = room_name
            self.cli.on_room_joined(room_name, members)
        else:
            self.cli.on_error("Failed to join room")
    
    def _handle_room_left(self, message: dict):
        """Handle room left response."""
        if message.get("success"):
            room_name = message.get("room_name")
            self.cli.on_room_left(room_name)
        else:
            self.cli.on_error("Failed to leave room")
    
    def _handle_user_joined(self, message: dict):
        """Handle user joined room notification."""
        username = message.get("username")
        room = message.get("room")
        self.cli.display_notification(f"{username} joined {room}")
    
    def _handle_user_left(self, message: dict):
        """Handle user left room notification."""
        username = message.get("username")
        room = message.get("room")
        self.cli.display_notification(f"{username} left {room}")
    
    def _handle_users_list(self, message: dict):
        """Handle users list response."""
        users = message.get("users", [])
        self.cli.display_users(users)
    
    def _handle_rooms_list(self, message: dict):
        """Handle rooms list response."""
        rooms = message.get("rooms", [])
        self._rooms = rooms
        self.cli.display_rooms(rooms)
    
    def _handle_offline_messages(self, message: dict):
        """Handle offline messages."""
        count = message.get("count", 0)
        messages = message.get("messages", [])
        
        if count > 0:
            self.cli.display_status(f"You have {count} offline messages")
            for msg in messages:
                self._handle_incoming_message({
                    "sender": msg.get("sender"),
                    "encrypted_content": msg.get("encrypted_content"),
                    "ephemeral_public_key": msg.get("ephemeral_public_key"),
                    "nonce": msg.get("nonce"),
                    "tag": msg.get("tag")
                })
        else:
            self.cli.display_status("No offline messages")
    
    def _handle_public_key_response(self, message: dict):
        """Handle public key response."""
        username = message.get("username")
        pub_key_b64 = message.get("public_key")
        
        if pub_key_b64:
            pub_key = decode_base64(pub_key_b64)
            self.session_manager.add_recipient_key(username, pub_key)
            logger.info(f"Received public key for {username}")
    
    def _handle_user_online(self, message: dict):
        """Handle user online notification."""
        username = message.get("username")
        self.cli.on_user_online(username)
    
    def _handle_user_offline(self, message: dict):
        """Handle user offline notification."""
        username = message.get("username")
        self.cli.on_user_offline(username)
    
    def _handle_ca_certificate(self, message: dict):
        """Handle CA certificate."""
        cert_b64 = message.get("certificate")
        if cert_b64:
            self.session_manager.set_ca_certificate(decode_base64(cert_b64))
    
    def _handle_error(self, message: dict):
        """Handle error message."""
        self.cli.on_error(message.get("error", "Unknown error"))
    
    def _handle_success(self, message: dict):
        """Handle success message."""
        self.cli.on_success(message.get("message", "Success"))
    
    def start(self):
        """Start client - connect and start CLI."""
        setup_logging(level="INFO")
        
        if not self.connect():
            print("Failed to connect to server. Please try again.")
            return
        
        self.cli.display_connection_status(True)
        self.cli.run()
    
    def run(self):
        """Main client loop."""
        self.start()


_client_instance = None


def main():
    """Client entry point."""
    global _client_instance
    
    setup_logging(level="INFO")
    
    print("""
===============================================
  Secure E2EE Chat Client
  System Security Project 2025/2026
===============================================
""")
    
    host = input("Server host [localhost]: ").strip() or "localhost"
    port_str = input("Server port [5555]: ").strip() or "5555"
    
    try:
        port = int(port_str)
    except ValueError:
        print("Invalid port. Using default 5555.")
        port = 5555
    
    _client_instance = ChatClient(host=host, port=port)
    _client_instance.run()


if __name__ == "__main__":
    main()
