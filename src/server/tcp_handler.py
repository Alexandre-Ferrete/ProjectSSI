"""
TCP Handler
==========
Handles individual client connections - reads/writes messages on the wire.
"""

import socket
import json
import logging
import struct
import threading
from typing import Optional, Dict, Any

from src.utils.helpers import encode_base64, decode_base64, generate_message_id

logger = logging.getLogger(__name__)


class ClientHandler:
    """
    Handles communication with a single client.
    """
    
    def __init__(self, client_socket: socket.socket, address: tuple, server):
        self.socket = client_socket
        self.address = address
        self.server = server
        
        self.username = None
        self.authenticated = False
        self.running = False
        self.buffer_size = 4096
        self._recv_buffer = b""
        
        self.socket.settimeout(300)
    
    def handle(self):
        """Main handling loop - runs in separate thread."""
        self.running = True
        logger.info(f"Client connected: {self.address}")
        
        try:
            while self.running:
                try:
                    data = self._receive()
                    if data is None:
                        break
                    
                    if data:
                        self._process_message(data)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error handling client {self.address}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            self._handle_disconnect()
    
    def _receive(self) -> Optional[bytes]:
        """
        Receive data from socket.
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
                return None
            except Exception as e:
                logger.error(f"Socket recv error: {e}")
                return None
        
        result = self._recv_buffer[:n]
        self._recv_buffer = self._recv_buffer[n:]
        return result
    
    def _process_message(self, data: bytes):
        """Parse and route incoming message."""
        try:
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get("type", "")
            
            logger.debug(f"Received message type: {msg_type} from {self.address}")
            
            handlers = {
                "register": self._handle_register,
                "auth": self._handle_auth,
                "chat": self._handle_chat,
                "create_room": self._handle_create_room,
                "join_room": self._handle_join_room,
                "leave_room": self._handle_leave_room,
                "get_users": self._handle_get_users,
                "get_rooms": self._handle_get_rooms,
                "get_offline": self._handle_get_offline,
                "get_public_key": self._handle_get_public_key,
                "disconnect": self._handle_disconnect_request,
            }
            
            handler = handlers.get(msg_type)
            if handler:
                handler(message)
            else:
                self.send_error(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            self.send_error("Invalid message format")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.send_error(f"Server error: {str(e)}")
    
    def _handle_register(self, message: Dict[str, Any]):
        """Handle user registration request."""
        username = message.get("username", "")
        password = message.get("password", "")
        public_key_b64 = message.get("public_key", "")
        
        if not username or not password:
            self.send_error("Missing username or password")
            return
        
        try:
            public_key = decode_base64(public_key_b64) if public_key_b64 else None
        except Exception:
            self.send_error("Invalid public key format")
            return
        
        result = self.server.user_manager.register_user(
            username=username,
            password=password,
            public_key=public_key
        )
        
        if result["success"]:
            certificate = self.server.ca.sign_user_certificate(
                username=username,
                public_key=public_key
            )
            
            cert_b64 = encode_base64(certificate) if certificate else None
            ca_cert_b64 = encode_base64(self.server.ca.get_ca_certificate())
            
            self.send_message({
                "type": "register_response",
                "success": True,
                "certificate": cert_b64,
                "ca_certificate": ca_cert_b64,
                "message": "Registration successful"
            })
            
            self.send_message({
                "type": "ca_certificate",
                "certificate": ca_cert_b64
            })
        else:
            self.send_error(result["error"])
    
    def _handle_auth(self, message: Dict[str, Any]):
        """Handle user authentication request."""
        username = message.get("username", "")
        password = message.get("password", "")
        
        if not username or not password:
            self.send_error("Missing username or password")
            return
        
        if self.server.user_manager.is_banned(username):
            self.send_error("User is banned")
            return
        
        user = self.server.user_manager.authenticate(username, password)
        
        if user:
            self.username = username
            self.authenticated = True
            
            self.server.register_client(username, self)
            
            certificate = self.server.ca.get_user_certificate(username)
            ca_certificate = self.server.ca.get_ca_certificate()
            public_key = self.server.ca.get_user_public_key(username)
            
            cert_b64 = encode_base64(certificate) if certificate else None
            ca_cert_b64 = encode_base64(ca_certificate) if ca_certificate else None
            pub_key_b64 = encode_base64(public_key) if public_key else None
            
            self.send_message({
                "type": "auth_response",
                "success": True,
                "username": username,
                "certificate": cert_b64,
                "ca_certificate": ca_cert_b64,
                "public_key": pub_key_b64,
                "message": "Authentication successful"
            })
            
            self.server.message_router.deliver_pending_offline_messages(username, self)
            
            self._broadcast_user_status(username, True)
        else:
            self.send_error("Invalid credentials")
    
    def _handle_chat(self, message: Dict[str, Any]):
        """Handle chat message."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        recipient = message.get("recipient", "")
        encrypted_content_b64 = message.get("encrypted_content", "")
        ephemeral_pub_b64 = message.get("ephemeral_public_key")
        nonce_b64 = message.get("nonce")
        tag_b64 = message.get("tag")
        message_id = message.get("message_id") or generate_message_id()
        
        if not recipient or not encrypted_content_b64:
            self.send_error("Missing recipient or content")
            return
        
        try:
            encrypted_content = decode_base64(encrypted_content_b64)
            ephemeral_pub = decode_base64(ephemeral_pub_b64) if ephemeral_pub_b64 else None
            nonce = decode_base64(nonce_b64) if nonce_b64 else None
            tag = decode_base64(tag_b64) if tag_b64 else None
        except Exception:
            self.send_error("Invalid message format")
            return
        
        result = self.server.message_router.route_message(
            sender=self.username,
            recipient=recipient,
            encrypted_content=encrypted_content,
            message_id=message_id,
            ephemeral_public_key=ephemeral_pub,
            nonce=nonce,
            tag=tag
        )
        
        self.send_message({
            "type": "chat_response",
            "success": result["delivered"],
            "status": result["status"],
            "message_id": message_id,
            "error": result.get("error")
        })
    
    def _handle_create_room(self, message: Dict[str, Any]):
        """Handle create room request."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        room_name = message.get("room_name", "")
        
        if not room_name:
            self.send_error("Room name required")
            return
        
        result = self.server.message_router.create_room(room_name, self.username)
        
        if result["success"]:
            self.send_message({
                "type": "room_created",
                "room_name": room_name,
                "success": True
            })
        else:
            self.send_error(result["error"])
    
    def _handle_join_room(self, message: Dict[str, Any]):
        """Handle join room request."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        room_name = message.get("room_name", "")
        
        if not room_name:
            self.send_error("Room name required")
            return
        
        result = self.server.message_router.join_room(room_name, self.username)
        
        if result["success"]:
            members = self.server.message_router.get_room_members(room_name)
            self.send_message({
                "type": "room_joined",
                "room_name": room_name,
                "members": members,
                "success": True
            })
        else:
            self.send_error(result["error"])
    
    def _handle_leave_room(self, message: Dict[str, Any]):
        """Handle leave room request."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        room_name = message.get("room_name", "")
        
        if not room_name:
            self.send_error("Room name required")
            return
        
        if self.server.message_router.leave_room(room_name, self.username):
            self.send_message({
                "type": "room_left",
                "room_name": room_name,
                "success": True
            })
        else:
            self.send_error("Failed to leave room")
    
    def _handle_room_message(self, message: Dict[str, Any]):
        """Handle room message."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        room_name = message.get("room_name", "")
        encrypted_content_b64 = message.get("encrypted_content", "")
        ephemeral_pub_b64 = message.get("ephemeral_public_key")
        nonce_b64 = message.get("nonce")
        tag_b64 = message.get("tag")
        message_id = message.get("message_id") or generate_message_id()
        
        if not room_name or not encrypted_content_b64:
            self.send_error("Missing room or content")
            return
        
        try:
            encrypted_content = decode_base64(encrypted_content_b64)
            ephemeral_pub = decode_base64(ephemeral_pub_b64) if ephemeral_pub_b64 else None
            nonce = decode_base64(nonce_b64) if nonce_b64 else None
            tag = decode_base64(tag_b64) if tag_b64 else None
        except Exception:
            self.send_error("Invalid message format")
            return
        
        result = self.server.message_router.broadcast_to_room(
            room_name=room_name,
            sender=self.username,
            encrypted_content=encrypted_content,
            message_id=message_id,
            ephemeral_public_key=ephemeral_pub,
            nonce=nonce,
            tag=tag
        )
        
        if result["success"]:
            self.send_message({
                "type": "room_message_response",
                "success": True,
                "message_id": message_id
            })
        else:
            self.send_error(result["error"])
    
    def _handle_get_users(self, message: Dict[str, Any]):
        """Handle get users request."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        users = self.server.user_manager.get_online_users()
        self.send_message({
            "type": "users_list",
            "users": users
        })
    
    def _handle_get_rooms(self, message: Dict[str, Any]):
        """Handle get rooms request."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        rooms = self.server.message_router.get_all_rooms()
        self.send_message({
            "type": "rooms_list",
            "rooms": rooms
        })
    
    def _handle_get_offline(self, message: Dict[str, Any]):
        """Handle get offline messages request."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        self.server.message_router.deliver_pending_offline_messages(self.username, self)
    
    def _handle_get_public_key(self, message: Dict[str, Any]):
        """Handle get public key request."""
        if not self.authenticated:
            self.send_error("Not authenticated")
            return
        
        target_username = message.get("username", "")
        
        if not target_username:
            self.send_error("Username required")
            return
        
        public_key = self.server.ca.get_user_public_key(target_username)
        
        if public_key:
            self.send_message({
                "type": "public_key_response",
                "username": target_username,
                "public_key": encode_base64(public_key)
            })
        else:
            self.send_error("User not found or no public key")
    
    def _handle_disconnect_request(self, message: Dict[str, Any]):
        """Handle disconnect request."""
        self.running = False
    
    def _handle_disconnect(self):
        """Handle client disconnect."""
        logger.info(f"Client disconnected: {self.address}")
        
        if self.username:
            self.server.unregister_client(self.username)
            self._broadcast_user_status(self.username, False)
        
        self.close()
    
    def _broadcast_user_status(self, username: str, online: bool):
        """Broadcast user online/offline status."""
        msg_type = "user_online" if online else "user_offline"
        message = {"type": msg_type, "username": username}
        
        for user in self.server.user_manager.get_online_users():
            if user != username:
                handler = self.server.user_manager.get_handler(user)
                if handler:
                    try:
                        handler.send_message(message)
                    except Exception:
                        pass
    
    def send_message(self, message: Dict[str, Any]):
        """
        Send message to client.
        Protocol: [4 bytes length][JSON payload]
        """
        try:
            data = json.dumps(message, ensure_ascii=False).encode('utf-8')
            length = struct.pack("!I", len(data))
            self.socket.sendall(length + data)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.running = False
    
    def send_error(self, error_message: str):
        """Send error response."""
        self.send_message({
            "type": "error",
            "error": error_message
        })
    
    def send_success(self, data: Dict[str, Any]):
        """Send success response."""
        response = {"type": "success"}
        response.update(data)
        self.send_message(response)
    
    def close(self):
        """Close connection and cleanup."""
        self.running = False
        try:
            self.socket.close()
        except Exception:
            pass
