"""
Client Main Entry Point
======================
TCP client that connects to the chat server.
Handles P2P connections for direct messaging between users.

IMPLEMENTAÇÃO:
- Socket TCP para conectar ao servidor
- Socket P2P separado para listening (porta dinâmica)
- Thread para receber mensagens do servidor
- Thread para aceitar conexões P2P
- Dicionário para guardar conexões P2P ativas
"""

import socket
import threading
import logging
import struct
import json
from typing import Optional, Callable


class ChatClient:
    """
    Main client class that connects to the server.
    Handles P2P connections for E2EE messaging.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 5555):
        """Inicializa cliente com host e porta do servidor."""
        # self.host = host
        # self.port = port
        # self.server_socket = None
        # self.username = None
        # self.connected = False
        # self.running = False
        # self.p2p_socket = None
        # self.p2p_port = 0
        # self.p2p_connections = {}  # ip -> socket
        # self.message_callback = None
        pass
    
    def connect(self) -> bool:
        """Conecta ao servidor."""
        # 1. Criar socket TCP
        # 2. connect((host, port))
        # 3. connected = True
        # 4. Iniciar thread _receive_loop()
        # 5. Retornar True/False
        pass
    
    def start_p2p_listener(self, port: int = 0) -> int:
        """Inicia listener P2P na porta disponível."""
        # 1. Criar socket TCP
        # 2. bind(('0.0.0.0', port)) - se port=0, escolhe disponível
        # 3. listen(5)
        # 4. Obter porta real: getsockname()[1]
        # 5. Iniciar thread _p2p_accept_loop()
        # 6. Retornar porta
        pass
    
    def _p2p_accept_loop(self):
        """Aceita conexões P2P recebidas em thread separada."""
        # Loop while running:
        #   client_socket, address = p2p_socket.accept()
        #   Iniciar thread _handle_p2p_client()
        pass
    
    def _handle_p2p_client(self, client_socket, address):
        """Handle conexão P2P recebida de peer."""
        # Loop: receber mensagens (mesmo protocolo length+JSON)
        # Se callback configurado, chamar callback(mensagem, "p2p")
        pass
    
    def disconnect(self):
        """Desconecta do servidor e fecha conexões P2P."""
        # 1. running = False
        # 2. Fechar server_socket
        # 3. Fechar p2p_socket
        # 4. Fechar todas as conexões em p2p_connections
        # 5. connected = False
        pass
    
    def is_connected(self) -> bool:
        """Verifica se está conectado ao servidor."""
        # return self.connected
        pass
    
    def send_message(self, message: dict):
        """Envia mensagem ao servidor."""
        # 1. json.dumps(message).encode()
        # 2. struct.pack("!I", len(data))
        # 3. server_socket.sendall(length + data)
        pass
    
    def register(self, username: str, password: str) -> bool:
        """Regista nova conta de utilizador."""
        # send_message({"type": "register", "username": ..., "password": ..., "public_key": ...})
        pass
    
    def login(self, username: str, password: str) -> bool:
        """Autentica-se no servidor."""
        # send_message({"type": "auth", "username": ..., "password": ...})
        # Guardar username
        pass
    
    def logout(self):
        """ Faz logout do servidor. """
        # send_message({"type": "disconnect"})
        # disconnect()
        pass
    
    def request_user_ip(self, username: str) -> Optional[str]:
        """ Request IP do utilizador ao servidor para conexão P2P. """
        # send_message({"type": "get_ip", "username": username})
        # Retornar None (resposta vem de forma assíncrona)
        pass
    
    def connect_to_peer(self, ip: str) -> bool:
        """Estabelece conexão direta P2P ao peer."""
        # 1. Parse ip (host:port)
        # 2. Criar socket TCP
        # 3. connect((host, port))
        # 4. Guardar em p2p_connections[ip] = socket
        pass
    
    def send_p2p_message(self, ip: str, message: dict) -> bool:
        """Envia mensagem encriptada diretamente ao peer via P2P."""
        # 1. Obter socket de p2p_connections[ip]
        # 2. Se não existir: connect_to_peer(ip) primeiro
        # 3. Enviar com protocolo length+JSON
        pass
    
    def send_chat(self, recipient: str, plaintext: str) -> bool:
        """Encripta mensagem com E2EE e envia via P2P."""
        # 1. request_user_ip(recipient) para obter IP
        # 2. Quando IP recebido: conectar P2P
        # 3. Encriptar mensagem (session_manager.encrypt_message)
        # 4. send_p2p_message(ip, msg_encriptada)
        pass
    
    def send_room_message(self, room_name: str, plaintext: str) -> bool:
        """Envia mensagem para room."""
        pass
    
    def create_room(self, room_name: str) -> bool:
        """Cria novo room de chat."""
        pass
    
    def join_room(self, room_name: str) -> bool:
        """Entra num room existente."""
        pass
    
    def leave_room(self, room_name: str) -> bool:
        """Sai de um room."""
        pass
    
    def get_online_users(self):
        """Request lista de utilizadores online."""
        pass
    
    def get_rooms(self):
        """Request lista de rooms disponíveis."""
        pass
    
    def start(self):
        """Inicia cliente - conecta e inicia CLI."""
        # 1. connect()
        # 2. run()
        pass
    
    def run(self):
        """Loop principal do cliente - processa input do utilizador."""
        # Loop: input() → parse_command() → execute_command()
        # Comandos: msg, users, rooms, create_room, join, leave, etc.
        pass
    
    def _receive_loop(self):
        """Recebe mensagens do servidor em thread separada."""
        # Loop while running:
        #   Receber 4 bytes (length)
        #   Receber N bytes (JSON)
        #   json.loads()
        #   _handle_server_message()
        pass
    
    def _handle_server_message(self, message: dict):
        """Handle mensagens do servidor (respostas auth, IP, etc)."""
        # 1. message.get("type")
        # 2. Se "ip_response" + success:
        #      - Guardar IP
        #      - connect_to_peer(ip)
        # 3. Se "auth_response" + success:
        #      - username = message["username"]
        #      - start_p2p_listener()
        pass
    
    def set_message_callback(self, callback: Callable):
        """Define callback para mensagens P2P recebidas."""
        # self.message_callback = callback
        pass


def main():
    """Ponto de entrada do cliente."""
    # 1. Criar ChatClient
    # 2. client.start()
    pass


if __name__ == "__main__":
    main()
