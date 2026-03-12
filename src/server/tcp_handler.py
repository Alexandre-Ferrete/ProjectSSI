"""
TCP Handler
===========
Handles individual client connections - reads/writes messages on the wire.

TODO:
- Define communication protocol (JSON over TCP with length prefix)
- Handle incoming messages
- Send outgoing messages
- Manage connection lifecycle
"""

import socket
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ClientHandler:
    """
    Handles communication with a single client.
    
    TODO:
    - Read bytes from socket using defined protocol
    - Parse messages
    - Write messages to socket
    - Manage connection state
    - Handle timeouts and disconnects
    """
    
    def __init__(self, client_socket: socket.socket, address: tuple, server):
        self.socket = client_socket
        self.address = address
        self.server = server
        
        self.username = None
        self.authenticated = False
        self.running = False
        self.buffer_size = 4096
    
    def handle(self):
        """TODO: Main handling loop - runs in separate thread."""
        pass
    
    def _receive(self) -> Optional[bytes]:
        """
        TODO: Receive data from socket.
        
        Protocol: [4 bytes length][JSON payload]
        """
        pass
    
    def _recv_exact(self, n: int) -> Optional[bytes]:
        """TODO: Receive exactly n bytes."""
        pass
    
    def _process_message(self, data: bytes):
        """TODO: Parse and route incoming message."""
        pass
    
    # =========================================================================
    # Message Handlers (to be implemented)
    # =========================================================================
    
    def _handle_register(self, message: Dict[str, Any]):
        """
        TODO: Handle user registration request.
        
        Expected message format:
        {
            'type': 'register',
            'username': '...',
            'password_hash': '...',
            'public_key': '...',
            'certificate_request': '...'
        }
        
        Response:
        {
            'type': 'register_response',
            'success': true/false,
            'certificate': '...' // if successful
            'error': '...'       // if failed
        }
        """
        pass
    
    def _handle_auth(self, message: Dict[str, Any]):
        """
        TODO: Handle user authentication request.
        
        Expected message format:
        {
            'type': 'auth',
            'username': '...',
            'password_hash': '...'
        }
        
        Response:
        {
            'type': 'auth_response',
            'success': true/false,
            'certificate': '...',
            'error': '...'
        }
        """
        pass
    
    def _handle_chat(self, message: Dict[str, Any]):
        """
        TODO: Handle chat message.
        
        Expected message format:
        {
            'type': 'chat',
            'recipient': '...',
            'encrypted_content': '...',
            'message_id': '...'
        }
        """
        pass
    
    def _handle_disconnect(self):
        """TODO: Handle client disconnect."""
        pass
    
    # =========================================================================
    # Send Methods
    # =========================================================================
    
    def send_message(self, message: Dict[str, Any]):
        """
        TODO: Send message to client.
        
        Protocol: [4 bytes length][JSON payload]
        """
        pass
    
    def send_error(self, error_message: str):
        """TODO: Send error response."""
        pass
    
    def send_success(self, data: Dict[str, Any]):
        """TODO: Send success response."""
        pass
    
    def close(self):
        """TODO: Close connection and cleanup."""
        pass


# ============================================================================
# CLIENT-SERVER MESSAGE PROTOCOL
# ============================================================================
#
# All messages follow: [4 bytes length (big-endian)][JSON payload]
#
# Message Types:
# -------------
# CLIENT -> SERVER:
#   - register     : Register new user
#   - auth         : Authenticate user
#   - chat         : Send encrypted message
#   - join_room    : Join a group chat
#   - leave_room   : Leave a group chat
#   - create_room  : Create new group chat
#   - get_offline  : Request offline messages
#   - disconnect   : Clean disconnect
#
# SERVER -> CLIENT:
#   - register_response
#   - auth_response
#   - chat_response
#   - message       : Incoming chat message
#   - room_message  : Incoming group message
#   - user_online   : Notification when user comes online
#   - user_offline  : Notification when user goes offline
#   - error         : Error response
#   - success       : Generic success response
#
# ============================================================================
