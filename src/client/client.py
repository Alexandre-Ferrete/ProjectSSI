import base64
import socket
import threading
import struct
import json
import time
from crypto.signatures import generate_keypair_Ed25519
from crypto.kdf import derive_key_PBKDF2HMAC
from typing import Optional, Dict
from protocol.messages import Message, MessageType
from client.session_manager import SessionManager

# Nota: importar as funções da Pessoa 3 aqui quando estiverem prontas
# from crypto.hybrid import encrypt_content, decrypt_content

class ChatClient:
    def __init__(self, server_host: str = 'localhost', server_port: int = 5555, username: str = None):
        self.server_addr = (server_host, server_port)
        self.server_socket = None

        self.session_manager = SessionManager(username=username)
        
        self.username = None
        self.running = False
        
        # P2P Listener
        self.p2p_socket = None
        self.p2p_port = 0
        
        # Sessões Ativas: { "username": {"socket": sock, "shared_key": key} }
        self.peer_sessions: Dict[str, dict] = {}
        
        # Pendente: { "username": "mensagem_para_enviar_depois_de_conectar" }
        self.pending_chats = {}

    # --- Utilitários de Comunicação (O "Framer") ---
    
    def _send_packet(self, sock: socket.socket, message: Message):
        """Envia qualquer mensagem no formato [Tamanho][JSON]."""
        try:
            data = message.to_json().encode('utf-8')
            header = struct.pack('!I', len(data))
            sock.sendall(header + data)
        except Exception as e:
            print(f"Erro ao enviar: {e}")

    def _recv_packet(self, sock: socket.socket) -> Optional[Message]:
        """Lê do socket seguindo o protocolo de tamanho."""
        try:
            header = sock.recv(4)
            if not header: return None
            length = struct.unpack('!I', header)[0]
            
            data = b""
            while len(data) < length:
                chunk = sock.recv(min(length - len(data), 4096))
                if not chunk: break
                data += chunk
            
            return Message.from_json(data.decode('utf-8'))
        except:
            return None

    # --- Gestão de Conexão com Servidor ---

    def connect(self) -> bool:
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect(self.server_addr)
            self.running = True
            
            # Iniciar escuta do servidor
            threading.Thread(target=self._server_receive_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"Falha ao ligar ao servidor: {e}")
            return False

    def login(self, username, password):
        # Primeiro, iniciamos o nosso "ouvido" P2P para saber que porta enviar ao servidor
        if not self.p2p_socket:
            self.start_p2p_listener()
        
        payload = {
            "username": username,
            "password": password,
            "p2p_port": self.p2p_port # CRÍTICO: Pessoa 1 precisa disto
        }
        msg = Message(MessageType.AUTH.value, username, payload)
        self._send_packet(self.server_socket, msg)

    # --- Lógica P2P (Onde a magia acontece) ---

    def start_p2p_listener(self):
        """Abre uma porta para receber outros utilizadores."""
        self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p2p_socket.bind(('0.0.0.0', 0)) # Porta dinâmica
        self.p2p_port = self.p2p_socket.getsockname()[1]
        self.p2p_socket.listen(5)
        
        threading.Thread(target=self._p2p_accept_loop, daemon=True).start()

    def _p2p_accept_loop(self):
        while self.running:
            client_sock, addr = self.p2p_socket.accept()
            threading.Thread(target=self._handle_peer_connection, args=(client_sock, addr)).start()

    def _handle_peer_connection(self, sock, addr):
        peer_user = None
        while self.running:
            msg = self._recv_packet(sock)
            if not msg: break
            
            peer_user = msg.sender
            
            if msg.msg_type == MessageType.P2P_HELLO.value:
                peer_pub_key = msg.payload.get("pub_key")
                
                # --- CORREÇÃO AQUI ---
                # Garante que o trane (receptor) também gera a sua chave efémera para o bob
                if peer_user not in self.peer_sessions:
                    print(f"[*] A processar handshake inicial de {peer_user}...")
                    # Esta linha gera a chave privada efémera se ela não existir!
                    my_pub = self.session_manager.get_handshake_data(peer_user)
                    
                    # Agora sim, processamos a chave do outro
                    self.session_manager.process_peer_handshake(peer_user, peer_pub_key)
                    
                    # Respondemos com a nossa chave pública
                    reply = Message(MessageType.P2P_HELLO.value, self.username, {"pub_key": my_pub})
                    self._send_packet(sock, reply)
                    
                    # Guardamos o socket
                    self.peer_sessions[peer_user] = {"socket": sock}
                else:
                    # Se já conhecemos, apenas processamos o handshake
                    self.session_manager.process_peer_handshake(peer_user, peer_pub_key)
                # ----------------------

                # Enviar mensagens pendentes (se existirem)
                if peer_user in self.pending_chats:
                    content = self.pending_chats.pop(peer_user)
                    encrypted_payload = self.session_manager.encrypt_for_peer(peer_user, content)
                    if encrypted_payload:
                        p2p_msg = Message(MessageType.P2P_MSG.value, self.username, encrypted_payload)
                        self._send_packet(sock, p2p_msg)

            elif msg.msg_type == MessageType.P2P_MSG.value:
                # Se chegar aqui e der erro, é porque o process_peer_handshake falhou antes
                texto_limpo = self.session_manager.decrypt_from_peer(peer_user, msg.payload)
                if texto_limpo:
                    print(f"\n[{peer_user}]: {texto_limpo}")
                else:
                    print(f"\n[!] Erro de desencriptação com {peer_user}. Sessão corrompida.")

    def connect_to_peer(self, username, ip, port):
        """Inicia uma conexão direta com outro user."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, int(port)))
            
            # CORREÇÃO: Usar o SessionManager para gerar a chave efémera real
            my_pub_b64 = self.session_manager.get_handshake_data(username)
            handshake = Message(MessageType.P2P_HELLO.value, self.username, {"pub_key": my_pub_b64})
            self._send_packet(sock, handshake)
            
            # Guardar socket na sessão
            self.peer_sessions[username] = {"socket": sock}
            
            threading.Thread(target=self._handle_peer_connection, args=(sock, (ip, port)), daemon=True).start()
            
        except Exception as e:
            print(f"Erro ao ligar a {username}: {e}")

    # --- Loops de Receção e CLI ---

    def _server_receive_loop(self):
        while self.running:
            msg = self._recv_packet(self.server_socket)
            if not msg: break
            
            if msg.msg_type == MessageType.RESPONSE.value:
                status = msg.payload.get("status")
                texto = msg.payload.get("message")
                
                if status == "success":
                    print(f"\n[Servidor] SUCESSO: {texto}")
                    
                    if "Login OK" in texto:
                        print(f"[*] Listening para P2P na porta {self.p2p_port}")
                        salt = msg.payload.get("salt")
                        self.session_manager.set_salt(salt)
                        self.username = msg.payload.get("username")
                        self.session_manager.set_username(self.username)
                        
                        # 👇 NOVO: pedir mensagens offline ao fazer login
                        req = Message(MessageType.OFFLINE_STORE.value, self.username, {
                            "action": "get"
                        })
                        self._send_packet(self.server_socket, req)
                        
                elif status == "error":
                    print(f"\n[Servidor] ERRO: {texto}")
                    
            elif msg.msg_type == MessageType.IP_RESPONSE.value:
                dest_user = msg.payload.get('target_user')
                ip = msg.payload.get('ip')
                port = msg.payload.get('port')
                
                if ip:
                    print(f"[*] {dest_user} encontrado em {ip}:{port}. A conectar...")
                    self.connect_to_peer(dest_user, ip, port)
                else:
                    print(f"[!] {dest_user} está offline. A guardar mensagem no servidor...")

                    # 👇 NOVO: enviar mensagem offline para o servidor
                    if dest_user in self.pending_chats:
                        content = self.pending_chats.pop(dest_user)
                        pub_key = msg.payload.get("public_key")
                        encrypted_data = self.session_manager.encrypt_offline(pub_key, content)

                        msg_off = Message(MessageType.OFFLINE_STORE.value, self.username, {
                            "action": "store",
                            "recipient": dest_user,
                            "content": encrypted_data["content"],
                            "nonce": encrypted_data["nonce"],
                            "tag": encrypted_data["tag"]
                        })
                        self._send_packet(self.server_socket, msg_off)

            elif msg.msg_type == MessageType.USERS_LIST.value:
                print(f"[*] Utilizadores Online: {msg.payload.get('users')}")

            # 👇 NOVO: receber mensagens offline do servidor
            elif msg.msg_type == "offline_messages":
                mensagens = msg.payload.get("messages", [])
                
                if not mensagens:
                    print("\n[*] Não tens mensagens offline pendentes.")
                
                for m in mensagens:
                    sender = m.get("sender")
                    # Passamos o dicionário 'm' inteiro porque o decrypt_offline 
                    # precisa do content, nonce e tag
                    try:
                        texto_limpo = self.session_manager.decrypt_offline(m)
                        print(f"\n[OFFLINE][{sender}]: {texto_limpo}")
                    except Exception as e:
                        print(f"\n[OFFLINE][{sender}]: (Erro ao desencriptar: {e})")


    def stop(self):
        self.running = False
        if self.server_socket: self.server_socket.close()
        print("Desconectado.")

    def run_cli(self):
            print("\n=== BEM-VINDO AO SECURE P2P CHAT ===")
            print("Comandos disponíveis:")
            print("  /register <user> <pass>  - Criar nova conta")
            print("  /login <user> <pass>     - Entrar na conta")
            print("  /chat <user> <msg>       - Enviar mensagem (P2P)")
            print("  /list                    - Ver quem está online")
            print("  /exit                    - Sair do programa")
            print("===================================\n")

            while self.running:
                raw_input = input(f"[{self.username or 'Anonimo'}] > ").strip()
                if not raw_input: continue
                
                parts = raw_input.split(" ", 2)
                cmd = parts[0].lower()

                # --- REGISTAR ---
                if cmd == "/register" and len(parts) == 3:
                    user, pwd = parts[1], parts[2]
                    pwd_kdf, salt = derive_key_PBKDF2HMAC(pwd)
                    pub_key_b64 = self.session_manager.load_or_generate_identity_keys(pwd_kdf, user)
                    # Cria a mensagem com o formato que a Pessoa 1 pediu no servidor
                    msg = Message (MessageType.REGISTER.value, user, {
                        "username": user,
                        "password": base64.b64encode(pwd_kdf).decode('utf-8'),
                        "public_key": pub_key_b64,
                        "salt": base64.b64encode(salt).decode('utf-8'),
                        }
                    )
                    self._send_packet(self.server_socket, msg)
                    print("[*] Pedido de registo enviado...")

                # --- LOGIN ---
                elif cmd == "/login" and len(parts) == 3:
                    if self.username:
                        print("[!] Já tens sessão iniciada!")
                    else:
                        user, pwd = parts[1], parts[2]
                        pwd_kdf, salt = derive_key_PBKDF2HMAC(pwd)
                        self.session_manager.load_or_generate_identity_keys(password_kdf=pwd_kdf, user=user)
                        self.login(user, pwd)
                        print("[*] A tentar iniciar sessão...")

                # --- CHAT P2P ---
                elif cmd == "/chat" and len(parts) > 2:
                    if not self.username:
                        print("[!] Precisas de fazer /login primeiro.")
                        continue
                    
                    target, text = parts[1], parts[2]
                    
                    if target in self.peer_sessions:
                        payload = self.session_manager.encrypt_for_peer(target, text)
                        if payload:
                            msg = Message(MessageType.P2P_MSG.value, self.username, payload)
                            self._send_packet(self.peer_sessions[target]["socket"], msg)
                    else:
                        # 👇 guardar sempre para possível envio offline
                        self.pending_chats[target] = text 
                        
                        print(f"[*] A procurar {target}...")
                        req = Message(MessageType.GET_IP.value, self.username, {"target_user": target})
                        self._send_packet(self.server_socket, req)

                # --- LISTAR ONLINE ---
                elif cmd == "/list":
                    if not self.username:
                        print("[!] Precisas de fazer /login primeiro.")
                    else:
                        req = Message(MessageType.GET_USERS.value, self.username, {})
                        self._send_packet(self.server_socket, req)
                
                # --- SAIR ---
                elif cmd == "/exit":
                    # Avisa o servidor que vais sair
                    if self.username:
                        msg = Message(MessageType.DISCONNECT.value, self.username, {})
                        self._send_packet(self.server_socket, msg)
                    self.stop()
                
                else:
                    print("[!] Comando inválido ou formato incorreto.")

if __name__ == "__main__":
    print("\n=== CONFIGURAÇÃO DO SERVIDOR ===")
    server_host = input("Endereço IP do servidor [localhost]: ").strip() or "localhost"
    server_port = 5555

    print(f"[*] A conectar a {server_host}:{server_port}...")
    client = ChatClient(server_host=server_host, server_port=server_port)
    if client.connect():

        client.run_cli()
        