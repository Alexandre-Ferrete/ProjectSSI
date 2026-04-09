"""
CLI (Command Line Interface)
===========================
User interface for the chat client.
"""

import sys
import getpass
import logging
from typing import Optional, List, Dict, Any

from src.protocol.commands import parse_command, format_error, format_success, format_users, format_rooms

logger = logging.getLogger(__name__)


class CLI:
    """
    Command-line interface for the chat client.
    """
    
    def __init__(self, client):
        self.client = client
        self.authenticated = False
        self.current_room = None
        self.running = False
    
    def display_welcome(self):
        """Display welcome message."""
        print("""
===============================================
  Secure E2EE Chat Client
  System Security Project 2025/2026
===============================================

Please login or register to start chatting.

Commands (before login):
  register <username> <password>    - Create new account
  login <username> <password>       - Login to existing account
  help                              - Show this help message
  exit                              - Exit the program
""")
    
    def display_help(self):
        """Display help message."""
        if self.authenticated:
            print("""
Available commands:
  msg <username> <message>          - Send private message
  users                             - List online users
  rooms                             - List available rooms
  create_room <name>                - Create new room
  join <room_name>                  - Join a room
  leave <room_name>                 - Leave a room
  history                           - View message history
  whoami                            - Show current user
  logout                            - Logout
  help                              - Show this help
  exit                              - Exit the program
""")
        else:
            self.display_welcome()
    
    def display_error(self, message: str):
        """Display error message."""
        print(format_error(message))
    
    def display_success(self, message: str):
        """Display success message."""
        print(format_success(message))
    
    def display_message(self, sender: str, content: str):
        """Display incoming message."""
        print(f"\n[New message from {sender}]: {content}")
        if self.client.running:
            print("> ", end="", flush=True)
    
    def display_room_message(self, room: str, sender: str, content: str):
        """Display incoming room message."""
        print(f"\n[{room}] {sender}: {content}")
        if self.client.running:
            print("> ", end="", flush=True)
    
    def display_notification(self, message: str):
        """Display notification."""
        print(f"\n[NOTIFICATION] {message}")
        if self.client.running:
            print("> ", end="", flush=True)
    
    def display_users(self, users: List[str]):
        """Display list of users."""
        print(format_users(users, self.client.username or ""))
    
    def display_rooms(self, rooms: List[Dict[str, Any]]):
        """Display list of rooms."""
        print(format_rooms(rooms))
    
    def display_status(self, message: str):
        """Display status message."""
        print(f"[STATUS] {message}")
    
    def display_connection_status(self, connected: bool):
        """Display connection status."""
        if connected:
            print("[+] Connected to server")
        else:
            print("[-] Disconnected from server")
    
    def get_command(self) -> str:
        """
        Get command from user.
        
        Returns:
            Command string
        """
        try:
            if self.current_room:
                return input(f"[{self.current_room}]> ").strip()
            return input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return "exit"
    
    def get_password(self, prompt: str = "Password: ") -> str:
        """
        Get password (hidden input).
        
        Returns:
            Password string
        """
        try:
            return getpass.getpass(prompt)
        except (EOFError, KeyboardInterrupt):
            return ""
    
    def get_input(self, prompt: str) -> str:
        """
        Get general input.
        
        Args:
            prompt: Prompt to display
            
        Returns:
            User input
        """
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return ""
    
    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        Parse command into action and arguments.
        
        Args:
            command: Raw command string
            
        Returns:
            {"action": str, "args": dict}
        """
        cmd, error = parse_command(command)
        
        if error:
            return {"action": "error", "args": {"message": error}}
        
        if cmd is None:
            return {"action": "error", "args": {"message": "Empty command"}}
        
        action = cmd.name
        args = {}
        
        if action in ("register", "login", "msg"):
            if len(cmd.args) >= 2:
                args["username"] = cmd.args[0]
                if action == "msg":
                    args["recipient"] = cmd.args[0]
                    args["message"] = " ".join(cmd.args[1:])
                elif action == "register":
                    args["password"] = cmd.args[1]
                else:
                    args["password"] = cmd.args[1]
        elif action in ("create_room", "join", "leave"):
            if cmd.args:
                args["room_name"] = cmd.args[0]
        
        return {"action": action, "args": args}
    
    def execute_command(self, command: Dict[str, Any]) -> bool:
        """
        Execute parsed command.
        
        Args:
            command: Parsed command
            
        Returns:
            True if executed successfully
        """
        action = command["action"]
        args = command["args"]
        
        handlers = {
            "register": self.handle_register,
            "login": self.handle_login,
            "logout": self.handle_logout,
            "msg": self.handle_msg,
            "users": self.handle_users,
            "rooms": self.handle_rooms,
            "create_room": self.handle_create_room,
            "join": self.handle_join_room,
            "leave": self.handle_leave_room,
            "history": self.handle_history,
            "whoami": self.handle_whoami,
            "help": self.handle_help,
            "exit": self.handle_exit,
        }
        
        handler = handlers.get(action)
        if handler:
            return handler(args)
        
        self.display_error(f"Unknown command: {action}")
        return True
    
    def handle_register(self, args: Dict[str, Any]) -> bool:
        """Handle register command."""
        username = args.get("username", "")
        password = args.get("password", "")
        
        if not username or not password:
            self.display_error("Usage: register <username> <password>")
            return True
        
        return self.client.register(username, password)
    
    def handle_login(self, args: Dict[str, Any]) -> bool:
        """Handle login command."""
        username = args.get("username", "")
        password = args.get("password", "")
        
        if not username or not password:
            self.display_error("Usage: login <username> <password>")
            return True
        
        return self.client.login(username, password)
    
    def handle_logout(self, args: Dict[str, Any]) -> bool:
        """Handle logout command."""
        self.client.logout()
        self.authenticated = False
        self.current_room = None
        self.display_success("Logged out successfully")
        return True
    
    def handle_msg(self, args: Dict[str, Any]) -> bool:
        """Handle msg (private message) command."""
        recipient = args.get("recipient", "")
        message = args.get("message", "")
        
        if not recipient or not message:
            self.display_error("Usage: msg <username> <message>")
            return True
        
        if recipient == self.client.username:
            self.display_error("Cannot send message to yourself")
            return True
        
        return self.client.send_chat(recipient, message)
    
    def handle_users(self, args: Dict[str, Any]) -> bool:
        """Handle users command."""
        self.client.get_online_users()
        return True
    
    def handle_rooms(self, args: Dict[str, Any]) -> bool:
        """Handle rooms command."""
        self.client.get_rooms()
        return True
    
    def handle_create_room(self, args: Dict[str, Any]) -> bool:
        """Handle create_room command."""
        room_name = args.get("room_name", "")
        
        if not room_name:
            self.display_error("Usage: create_room <name>")
            return True
        
        return self.client.create_room(room_name)
    
    def handle_join_room(self, args: Dict[str, Any]) -> bool:
        """Handle join room command."""
        room_name = args.get("room_name", "")
        
        if not room_name:
            self.display_error("Usage: join <room_name>")
            return True
        
        return self.client.join_room(room_name)
    
    def handle_leave_room(self, args: Dict[str, Any]) -> bool:
        """Handle leave room command."""
        room_name = args.get("room_name", "")
        
        if not room_name:
            if self.current_room:
                room_name = self.current_room
            else:
                self.display_error("Usage: leave <room_name>")
                return True
        
        return self.client.leave_room(room_name)
    
    def handle_room_message(self, message: str) -> bool:
        """Handle message in a room context."""
        if not self.current_room:
            self.display_error("Not in a room")
            return True
        
        return self.client.send_room_message(self.current_room, message)
    
    def handle_history(self, args: Dict[str, Any]) -> bool:
        """Handle history command."""
        self.display_notification("Message history not yet implemented")
        return True
    
    def handle_whoami(self, args: Dict[str, Any]) -> bool:
        """Handle whoami command."""
        if self.client.username:
            print(f"Logged in as: {self.client.username}")
        else:
            print("Not logged in")
        return True
    
    def handle_help(self, args: Dict[str, Any]) -> bool:
        """Handle help command."""
        self.display_help()
        return True
    
    def handle_exit(self, args: Dict[str, Any]) -> bool:
        """Handle exit command."""
        self.client.disconnect()
        self.running = False
        self.display_success("Goodbye!")
        return False
    
    def on_message_received(self, sender: str, content: str):
        """Handle incoming message notification."""
        self.display_message(sender, content)
    
    def on_room_message(self, room: str, sender: str, content: str):
        """Handle incoming room message."""
        self.display_room_message(room, sender, content)
    
    def on_user_online(self, username: str):
        """Handle user came online notification."""
        self.display_notification(f"{username} is now online")
    
    def on_user_offline(self, username: str):
        """Handle user went offline notification."""
        self.display_notification(f"{username} is now offline")
    
    def on_room_joined(self, room_name: str, members: List[str]):
        """Handle room joined notification."""
        self.current_room = room_name
        self.display_success(f"Joined room '{room_name}'")
        print(f"Members ({len(members)}): {', '.join(members)}")
    
    def on_room_left(self, room_name: str):
        """Handle room left notification."""
        if self.current_room == room_name:
            self.current_room = None
        self.display_success(f"Left room '{room_name}'")
    
    def on_error(self, error_message: str):
        """Handle error from server."""
        self.display_error(error_message)
    
    def on_success(self, message: str):
        """Handle success from server."""
        self.display_success(message)
    
    def on_auth_success(self):
        """Handle successful authentication."""
        self.authenticated = True
        self.display_success("Login successful!")
    
    def on_disconnected(self):
        """Handle disconnection."""
        self.authenticated = False
        self.current_room = None
        self.display_status("Disconnected from server")
    
    def run(self):
        """Main CLI loop."""
        self.running = True
        self.display_welcome()
        
        while self.running and self.client.running:
            try:
                command = self.get_command()
                
                if not command:
                    continue
                
                if self.current_room and not command.startswith("/"):
                    if command.lower() in ("leave", "exit", "quit"):
                        self.handle_leave_room({"room_name": self.current_room})
                    else:
                        self.handle_room_message(command)
                    continue
                
                if command.startswith("/"):
                    command = command[1:]
                
                parsed = self.parse_command(command)
                
                if parsed["action"] == "error":
                    self.display_error(parsed["args"].get("message", "Unknown error"))
                    continue
                
                self.execute_command(parsed)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
                continue
            except Exception as e:
                self.display_error(f"Error: {e}")
                logger.error(f"CLI error: {e}")
        
        self.display_status("CLI terminated")
