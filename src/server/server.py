"""
Server Main Entry Point
=======================
TCP server that accepts client connections, manages users, and routes messages.
"""

import socket
import threading
import signal
import sys
import logging

from src.server.storage import Storage
from src.server.ca import CertificateAuthority
from src.server.user_manager import UserManager
from src.server.message_router import MessageRouter
from src.server.tcp_handler import ClientHandler
from src.utils.helpers import setup_logging, get_logger

logger = get_logger(__name__)


class ChatServer:
    """
    Main server class that coordinates all components.
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.accept_thread = None
        
        self.storage = Storage()
        self.ca = CertificateAuthority(self.storage)
        self.user_manager = UserManager(self.storage)
        self.message_router = MessageRouter(self.user_manager, self.storage)
        
        self.clients = {}
        self.clients_lock = threading.Lock()
    
    def start(self):
        """Initialize and start the server."""
        self.storage.initialize()
        self.ca.initialize()
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(50)
        
        self.running = True
        
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()
        
        logger.info(f"Server started on {self.host}:{self.port}")
        print(f"Server started on {self.host}:{self.port}")
    
    def _accept_loop(self):
        """Accept incoming client connections."""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                handler = ClientHandler(client_socket, address, self)
                thread = threading.Thread(target=handler.handle, daemon=True)
                thread.start()
            except Exception as e:
                if self.running:
                    logger.error(f"Accept error: {e}")
    
    def register_client(self, username: str, handler: ClientHandler):
        """Register authenticated client."""
        with self.clients_lock:
            self.clients[username] = handler
        self.user_manager.add_online(username, handler)
        logger.info(f"Client registered: {username}")
    
    def unregister_client(self, username: str):
        """Unregister disconnected client."""
        with self.clients_lock:
            if username in self.clients:
                del self.clients[username]
        self.user_manager.remove_online(username)
        logger.info(f"Client unregistered: {username}")
    
    def get_online_users(self):
        """Get list of online users."""
        return self.user_manager.get_online_users()
    
    def shutdown(self):
        """Graceful shutdown."""
        logger.info("Server shutting down...")
        print("Server shutting down...")
        
        self.running = False
        
        with self.clients_lock:
            for username, handler in list(self.clients.items()):
                try:
                    handler.send_message({"type": "server_shutdown"})
                    handler.close()
                except Exception:
                    pass
            self.clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        
        self.storage.close()
        
        logger.info("Server shutdown complete")
        print("Server shutdown complete")
    
    def get_status(self) -> dict:
        """Get server status."""
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "online_users": self.user_manager.get_online_count(),
            "total_users": self.user_manager.get_user_count(),
            "active_rooms": len(self.message_router.get_all_rooms()),
            "offline_messages": self.storage.get_offline_message_count()
        }
    
    def ban_user(self, username: str) -> bool:
        """Ban a user."""
        return self.user_manager.ban_user(username)
    
    def unban_user(self, username: str) -> bool:
        """Unban a user."""
        return self.user_manager.unban_user(username)


_server_instance = None


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global _server_instance
    if _server_instance:
        _server_instance.shutdown()
    sys.exit(0)


def admin_cli(server: ChatServer):
    """Admin CLI interface."""
    print("\n" + "=" * 50)
    print("Secure E2EE Chat Server - Admin Console")
    print("=" * 50)
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == "help":
                print("""
Available commands:
  start              - Start the server
  status             - Show server status
  users              - List all registered users
  online             - List online users
  rooms              - List active rooms
  stats              - Show statistics
  ban <username>     - Ban a user
  unban <username>   - Unban a user
  shutdown           - Shutdown the server
  help               - Show this help
  exit               - Exit admin console
""")
            
            elif cmd == "start":
                if server.running:
                    print("Server is already running!")
                else:
                    server.start()
            
            elif cmd == "status":
                status = server.get_status()
                print(f"""
Server Status: {'RUNNING' if status['running'] else 'STOPPED'}
Host: {status['host']}
Port: {status['port']}
Online Users: {status['online_users']}
Total Users: {status['total_users']}
Active Rooms: {status['active_rooms']}
Offline Messages Queued: {status['offline_messages']}
""")
            
            elif cmd == "users":
                users = server.user_manager.get_all_users()
                print("\nRegistered Users:")
                for user in users:
                    status = "online" if user.get("online", False) else "offline"
                    banned = " [BANNED]" if user.get("banned", False) else ""
                    print(f"  - {user['username']} ({status}){banned}")
                print(f"Total: {len(users)} users")
            
            elif cmd == "online":
                users = server.get_online_users()
                print("\nOnline Users:")
                if users:
                    for user in users:
                        print(f"  - {user}")
                else:
                    print("  No users online")
                print(f"Total: {len(users)} users")
            
            elif cmd == "rooms":
                rooms = server.message_router.get_all_rooms()
                print("\nActive Rooms:")
                if rooms:
                    for room in rooms:
                        print(f"  - {room['name']} ({room['members']} members, created by {room['created_by']})")
                else:
                    print("  No active rooms")
            
            elif cmd == "stats":
                status = server.get_status()
                print(f"""
Statistics:
  Total Messages Sent: {server.storage.get_message_count()}
  Offline Messages: {status['offline_messages']}
  Online Users: {status['online_users']}
  Registered Users: {status['total_users']}
  Active Rooms: {status['active_rooms']}
""")
            
            elif cmd.startswith("ban "):
                username = cmd[4:].strip()
                if server.ban_user(username):
                    print(f"User '{username}' has been banned")
                else:
                    print(f"Failed to ban user '{username}'")
            
            elif cmd.startswith("unban "):
                username = cmd[6:].strip()
                if server.unban_user(username):
                    print(f"User '{username}' has been unbanned")
                else:
                    print(f"Failed to unban user '{username}'")
            
            elif cmd == "shutdown":
                server.shutdown()
                print("Server has been shut down")
                break
            
            elif cmd == "exit":
                print("Exiting admin console (server still running)")
                break
            
            elif cmd == "":
                continue
            
            else:
                print(f"Unknown command: {cmd}. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\nUse 'shutdown' to stop the server or 'exit' to exit console")
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Server entry point."""
    global _server_instance
    
    setup_logging(level="INFO")
    
    _server_instance = ChatServer()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("""
===============================================
  Secure E2EE Chat Server
  System Security Project 2025/2026
===============================================
""")
    
    _server_instance.start()
    
    admin_cli(_server_instance)


if __name__ == "__main__":
    main()
