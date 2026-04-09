"""
Chat Commands
=============
Command parsing for the chat CLI.
"""

from typing import Dict, Any, List, Optional, Tuple


class Command:
    """Represents a parsed command."""
    
    def __init__(self, name: str, args: List[str], raw: str):
        self.name = name
        self.args = args
        self.raw = raw


COMMANDS = {
    "register": {"min_args": 2, "max_args": 2, "usage": "register <username> <password>"},
    "login": {"min_args": 2, "max_args": 2, "usage": "login <username> <password>"},
    "help": {"min_args": 0, "max_args": 0, "usage": "help"},
    "exit": {"min_args": 0, "max_args": 0, "usage": "exit"},
    "msg": {"min_args": 2, "max_args": None, "usage": "msg <username> <message>"},
    "users": {"min_args": 0, "max_args": 0, "usage": "users"},
    "rooms": {"min_args": 0, "max_args": 0, "usage": "rooms"},
    "create_room": {"min_args": 1, "max_args": 1, "usage": "create_room <room_name>"},
    "join": {"min_args": 1, "max_args": 1, "usage": "join <room_name>"},
    "leave": {"min_args": 1, "max_args": 1, "usage": "leave <room_name>"},
    "history": {"min_args": 0, "max_args": 0, "usage": "history"},
    "whoami": {"min_args": 0, "max_args": 0, "usage": "whoami"},
    "logout": {"min_args": 0, "max_args": 0, "usage": "logout"},
}


def parse_command(line: str) -> Tuple[Optional[Command], Optional[str]]:
    """
    Parse a command line.
    
    Args:
        line: Raw command line
        
    Returns:
        (Command, error_message)
    """
    if not line or not line.strip():
        return None, "Empty command"
    
    parts = line.strip().split()
    name = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    if name not in COMMANDS:
        return None, f"Unknown command: {name}"
    
    error = validate_command(name, args)
    if error:
        return None, error
    
    return Command(name, args, line), None


def validate_command(name: str, args: List[str]) -> Optional[str]:
    """
    Validate command arguments.
    
    Args:
        name: Command name
        args: Command arguments
        
    Returns:
        Error message if invalid, None if valid
    """
    if name not in COMMANDS:
        return f"Unknown command: {name}"
    
    cmd_info = COMMANDS[name]
    min_args = cmd_info["min_args"]
    max_args = cmd_info["max_args"]
    
    if len(args) < min_args:
        return f"{name}: missing arguments. Usage: {cmd_info['usage']}"
    
    if max_args is not None and len(args) > max_args:
        return f"{name}: too many arguments. Usage: {cmd_info['usage']}"
    
    return None


def format_error(message: str) -> str:
    """Format error message for display."""
    return f"[ERROR] {message}"


def format_success(message: str) -> str:
    """Format success message for display."""
    return f"[OK] {message}"


def format_users(users: List[str], current_user: str) -> str:
    """Format user list for display."""
    if not users:
        return "No online users."
    
    formatted = []
    for user in users:
        if user == current_user:
            formatted.append(f"  - {user} (you)")
        else:
            formatted.append(f"  - {user}")
    
    return "Online users:\n" + "\n".join(formatted)


def format_rooms(rooms: List[Dict[str, Any]]) -> str:
    """Format room list for display."""
    if not rooms:
        return "No active rooms."
    
    formatted = []
    for room in rooms:
        name = room.get("name", "unknown")
        members = room.get("members", 0)
        created_by = room.get("created_by", "unknown")
        formatted.append(f"  - {name} ({members} members, created by {created_by})")
    
    return "Active rooms:\n" + "\n".join(formatted)


# =========================================================================
# COMMAND EXAMPLES
# =========================================================================
#
# Pre-login:
#   register alice secret123
#   login alice secret123
#   help
#   exit
#
# Post-login:
#   msg bob Hello!
#   users
#   rooms
#   create_room myroom
#   join myroom
#   leave myroom
#   history
#   whoami
#   logout
#
# In-room:
#   Hello room!
#   leave
#   members
#
# =========================================================================
