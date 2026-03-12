"""
CLI (Command Line Interface)
============================
User interface for the chat client.

TODO:
- Parse user commands
- Display messages and notifications
- Handle input/output
"""

import sys
import getpass
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class CLI:
    """
    Command-line interface for the chat client.
    
    TODO:
    - Display welcome/header
    - Parse user commands
    - Display messages
    - Display notifications
    - Handle user input
    """
    
    def __init__(self, client):
        self.client = client
        self.authenticated = False
        self.current_room = None
    
    # =========================================================================
    # Display Methods
    # =========================================================================
    
    def display_welcome(self):
        """TODO: Display welcome message."""
        pass
    
    def display_help(self):
        """TODO: Display help message."""
        pass
    
    def display_error(self, message: str):
        """TODO: Display error message."""
        pass
    
    def display_success(self, message: str):
        """TODO: Display success message."""
        pass
    
    def display_message(self, sender: str, content: str):
        """TODO: Display incoming message."""
        pass
    
    def display_notification(self, message: str):
        """TODO: Display notification."""
        pass
    
    def display_users(self, users: List[str]):
        """TODO: Display list of users."""
        pass
    
    def display_rooms(self, rooms: List[Dict[str, Any]]):
        """TODO: Display list of rooms."""
        pass
    
    def display_status(self, message: str):
        """TODO: Display status message."""
        pass
    
    # =========================================================================
    # Input Methods
    # =========================================================================
    
    def get_command(self) -> str:
        """
        TODO: Get command from user.
        
        Returns:
            Command string
        """
        pass
    
    def get_password(self) -> str:
        """
        TODO: Get password (hidden input).
        
        Returns:
            Password string
        """
        pass
    
    def get_input(self, prompt: str) -> str:
        """
        TODO: Get general input.
        
        Args:
            prompt: Prompt to display
            
        Returns:
            User input
        """
        pass
    
    # =========================================================================
    # Command Parsing
    # =========================================================================
    
    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        TODO: Parse command into action and arguments.
        
        Args:
            command: Raw command string
            
        Returns:
            {
                "action": "register" | "login" | "msg" | ...,
                "args": {...}
            }
        """
        pass
    
    def execute_command(self, command: Dict[str, Any]) -> bool:
        """
        TODO: Execute parsed command.
        
        Args:
            command: Parsed command
            
        Returns:
            True if executed successfully
        """
        pass
    
    # =========================================================================
    # Command Handlers
    # =========================================================================
    
    def handle_register(self, args: Dict[str, Any]):
        """
        TODO: Handle register command.
        
        Args:
            args: {username, password}
        """
        pass
    
    def handle_login(self, args: Dict[str, Any]):
        """
        TODO: Handle login command.
        
        Args:
            args: {username, password}
        """
        pass
    
    def handle_logout(self):
        """TODO: Handle logout command."""
        pass
    
    def handle_msg(self, args: Dict[str, Any]):
        """
        TODO: Handle msg (private message) command.
        
        Args:
            args: {recipient, message}
        """
        pass
    
    def handle_users(self):
        """TODO: Handle users command."""
        pass
    
    def handle_rooms(self):
        """TODO: Handle rooms command."""
        pass
    
    def handle_create_room(self, args: Dict[str, Any]):
        """
        TODO: Handle create_room command.
        
        Args:
            args: {room_name}
        """
        pass
    
    def handle_join_room(self, args: Dict[str, Any]):
        """
        TODO: Handle join room command.
        
        Args:
            args: {room_name}
        """
        pass
    
    def handle_leave_room(self, args: Dict[str, Any]):
        """
        TODO: Handle leave room command.
        
        Args:
            args: {room_name}
        """
        pass
    
    def handle_room_message(self, message: str):
        """
        TODO: Handle message in a room context.
        
        Args:
            message: Message to send to room
        """
        pass
    
    def handle_history(self):
        """TODO: Handle history command."""
        pass
    
    def handle_whoami(self):
        """TODO: Handle whoami command."""
        pass
    
    def handle_exit(self):
        """TODO: Handle exit command."""
        pass
    
    def handle_help(self):
        """TODO: Handle help command."""
        pass
    
    # =========================================================================
    # Message Handling
    # =========================================================================
    
    def on_message_received(self, sender: str, encrypted_content: bytes):
        """
        TODO: Handle incoming message notification.
        
        Args:
            sender: Sender's username
            encrypted_content: Encrypted message content
        """
        pass
    
    def on_room_message(self, room: str, sender: str, content: str):
        """
        TODO: Handle incoming room message.
        
        Args:
            room: Room name
            sender: Sender's username
            content: Message content
        """
        pass
    
    def on_user_online(self, username: str):
        """
        TODO: Handle user came online notification.
        
        Args:
            username: User who came online
        """
        pass
    
    def on_user_offline(self, username: str):
        """
        TODO: Handle user went offline notification.
        
        Args:
            username: User who went offline
        """
        pass
    
    # =========================================================================
    # Main Loop
    # =========================================================================
    
    def run(self):
        """TODO: Main CLI loop."""
        pass


# ============================================================================
# COMMAND SYNTAX
# ============================================================================
#
# Before Login:
# -------------
# register <username> <password>
# login <username> <password>
# help
# exit
#
# After Login:
# ------------
# msg <username> <message>           - Send private message
# users                              - List online users
# rooms                              - List available rooms
# create_room <name>                  - Create new room
# join <room_name>                    - Join a room
# leave <room_name>                   - Leave a room
# history                             - View message history
# whoami                              - Show current user info
# logout                              - Logout
# help                               - Show help
# exit                               - Exit
#
# In Room:
# --------
# <message>                          - Send to room
# leave                              - Leave room
# members                            - Show room members
#
# ============================================================================
