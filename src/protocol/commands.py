"""
Chat Commands
=============
Command parsing for the chat CLI.

TODO:
- Parse user commands
- Validate arguments
- Execute commands
"""

from typing import Dict, Any, List, Optional, Tuple


class Command:
    """TODO: Represents a parsed command."""
    
    def __init__(self, name: str, args: List[str], raw: str):
        self.name = name
        self.args = args
        self.raw = raw


# Command definitions
COMMANDS = {
    # Pre-login commands
    "register": {"min_args": 2, "max_args": 2, "usage": "register <username> <password>"},
    "login": {"min_args": 2, "max_args": 2, "usage": "login <username> <password>"},
    "help": {"min_args": 0, "max_args": 0, "usage": "help"},
    "exit": {"min_args": 0, "max_args": 0, "usage": "exit"},
    
    # Post-login commands
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
    TODO: Parse a command line.
    
    Args:
        line: Raw command line
        
    Returns:
        (Command, error_message)
    """
    pass


def validate_command(name: str, args: List[str]) -> Optional[str]:
    """
    TODO: Validate command arguments.
    
    Args:
        name: Command name
        args: Command arguments
        
    Returns:
        Error message if invalid, None if valid
    """
    pass


def format_error(message: str) -> str:
    """TODO: Format error message for display."""
    pass


def format_success(message: str) -> str:
    """TODO: Format success message for display."""
    pass


def format_users(users: List[str], current_user: str) -> str:
    """TODO: Format user list for display."""
    pass


def format_rooms(rooms: List[Dict[str, Any]]) -> str:
    """TODO: Format room list for display."""
    pass


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
