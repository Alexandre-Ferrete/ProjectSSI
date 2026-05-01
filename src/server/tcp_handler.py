"""Tratamento de uma ligação TCP individual de cliente.

Esta classe contém a lógica que antes vivia em `server.py`: parsing,
routing de comandos e geração de respostas tipadas.
"""

import json
import logging
import base64
import os
from typing import Optional, Dict, Any, Tuple

from protocol.messages import Message, MessageType

logger = logging.getLogger(__name__)

class ClientHandler:
    """Gere a comunicação com um único cliente TCP."""

    def __init__(self, reader, writer, server):
        self.reader = reader
        self.writer = writer
        self.server = server
        self.address = writer.get_extra_info("peername")
        self.username: Optional[str] = None
        self.running = False

    async def handle(self):
        """Loop principal de receção e despacho de comandos."""
        self.running = True
        try:
            while self.running:
                message_text = await self._receive()
                if message_text is None:
                    break

                request = self._parse_request(message_text)
                response_message, auth_user, should_close = await self.process_command(request)

                if auth_user:
                    self.username = auth_user

                await self.send_message(response_message)

                if should_close:
                    break
        finally:
            await self._handle_disconnect()

    async def _receive(self) -> Optional[str]:
        """Lê uma mensagem com prefixo de tamanho."""
        try:
            header = await self.reader.readexactly(4)
            msg_len = int.from_bytes(header, byteorder="big")
            data = await self.reader.readexactly(msg_len)
            return data.decode().strip()
        except Exception:
            return None

    def _parse_request(self, message_text: str) -> Dict[str, Any]:
        try:
            raw = json.loads(message_text)
            # Tenta ler msg_type (teu) ou type (dele)
            t = raw.get("msg_type") or raw.get("type")
            s = raw.get("sender")
            # Tenta ler payload (teu) ou data (dele)
            d = raw.get("payload") or raw.get("data") or {}
            
            return {"type": t, "sender": s, "data": d}
        except Exception as e:
            logger.error(f"Erro no parsing: {e}")
            return {"type": None, "sender": None, "data": {}}

    def _build_response(self, msg_type: MessageType, sender: str, payload: Dict[str, Any]) -> Message:
        return Message(msg_type=msg_type.value, sender=sender, payload=payload)

    async def process_command(self, request: Dict[str, Any]):
        """Executa a lógica de cada comando suportado pelo protocolo."""
        # O _parse_request já normalizou os campos para "type" e "data"
        cmd = (request.get("type") or "").lower()
        data = request.get("data", {}) or {}
        sender = request.get("sender") or self.username or "server"
        # 1. REGISTO
        if cmd == MessageType.REGISTER.value:
            username = data.get("username") or sender
            password = data.get("password")
            public_key = data.get("public_key")
            certificate = data.get("certificate")

            if not username or not password:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Username e password são obrigatórios"}), None, False

            # Verifica se o utilizador já existe na DB
            if self.server.storage.get_user(username):
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Utilizador já existe"}), None, False

            created = self.server.storage.create_user(username, password, public_key, certificate)
            if not created:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Falha ao criar utilizador"}), None, False

            return self._build_response(MessageType.RESPONSE, "server", {"status": "success", "message": "Registo efetuado com sucesso"}), None, False

        # 2. LOGIN (AUTH) - CORRIGIDO
        if cmd == MessageType.AUTH.value:
            username = data.get("username")
            password = data.get("password")
            p2p_port = int(data.get("p2p_port", 0) or 0)

            # Validação de campos vazios
            if not username or not password:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Credenciais incompletas"}), None, False

            # Busca o utilizador na base de dados
            user = self.server.storage.get_user(username)
            
            # CORREÇÃO CRÍTICA: Se 'user' for None, o utilizador não existe.
            if user is None:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Utilizador não encontrado"}), None, False

            # Verifica a password
            if user.get("password_hash") != password:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Password incorreta"}), None, False

            # Se passou as verificações, adiciona aos online
            await self.server.online_users.add_online_user(username, self.address[0], p2p_port, self.writer)
            nonce = base64.b64encode(os.urandom(16)).decode('utf-8')
            self.nonce = nonce
            return self._build_response(MessageType.RESPONSE, "server", {"status": "success", "message": "Login OK", "username": username, "nonce": nonce}), username, False
            

        # 3. OBTER IP (Para P2P)
        if cmd == MessageType.GET_IP.value:
            target_user = data.get("target_user")
            address = await self.server.online_users.get_user_address(target_user)
            
            if address:
                ip, port = address
                return self._build_response(MessageType.IP_RESPONSE, "server", {"target_user": target_user, "ip": ip, "port": port, "status": "success"}), None, False

            # --- ALTERAÇÃO AQUI ---
            # Se o user está offline, vamos buscar a chave pública dele à DB para o remetente poder cifrar offline
            user_data = self.server.storage.get_user(target_user)
            pub_key = None
            if user_data:
                pub_key = user_data.get("public_key") # Já deve estar em Base64 ou bytes

            return self._build_response(MessageType.IP_RESPONSE, "server", {
                "target_user": target_user, 
                "ip": None, 
                "port": None, 
                "status": "offline",
                "public_key": pub_key # <--- Enviar isto!
            }), None, False

        # 4. LISTAR UTILIZADORES
        if cmd == MessageType.GET_USERS.value:
            if not self.username:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Não autenticado"}), None, False

            users = await self.server.online_users.list_online_users()
            return self._build_response(MessageType.USERS_LIST, "server", {"users": users}), None, False


        # 5. OFFLINE STORE (guardar ou pedir mensagens) e receber nonce
        if cmd == MessageType.OFFLINE_STORE.value:
            action = data.get("action")
            nonce_encrypted = data.get("nonce_encrypted")

            # 📥 PEDIR MENSAGENS OFFLINE (O cliente acabou de fazer login) e verificar nonce
            if action == "get":
                user = self.server.storage.get_offline_messages(sender)
                Iden_pub_key = user.get("public_key")
                nonce_decrypted = Iden_pub_key.verify(nonce_encrypted, self.nonce)

                mensagens_db = self.server.storage.get_offline_messages(sender)
                mensagens_para_enviar = []

                for m in mensagens_db:
                    # Função auxiliar interna para evitar o Double Base64
                    def ensure_str(data):
                        if data is None: 
                            return ""
                        if isinstance(data, bytes):
                            try:
                                # Tenta ver se já é uma string Base64 guardada como bytes
                                return data.decode('utf-8')
                            except UnicodeDecodeError:
                                # Se falhar, é porque são bytes binários reais, aí sim fazemos encode
                                return base64.b64encode(data).decode('utf-8')
                        return str(data)

                    payload_msg = {
                        "sender": m["sender"],
                        "content": ensure_str(m["content"]),
                        "nonce": ensure_str(m["nonce"]),
                        "tag": ensure_str(m["tag"])
                    }
                    mensagens_para_enviar.append(payload_msg)

                # Opcional: Limpar as mensagens da DB para não as receberes sempre que fazes login
                self.server.storage.clear_offline_messages(sender)

                return Message(
                    msg_type="offline_messages",
                    sender="server",
                    payload={"messages": mensagens_para_enviar}
                ), None, False              

            # 📤 GUARDAR MENSAGEM OFFLINE (O destinatário estava offline)
            elif action == "store":
                recipient = data.get("recipient")
                content = data.get("content") # String Base64 vinda do JSON
                nonce = data.get("nonce")
                tag = data.get("tag")

                # Validação básica de integridade
                if not recipient or not content:
                    return self._build_response(
                        MessageType.RESPONSE, 
                        "server", 
                        {"status": "error", "message": "Dados insuficientes para guardar offline"}
                    ), None, False

                # Guardamos como bytes na DB (o SQLite trata o BLOB automaticamente)
                # Fazemos o .encode() apenas se for string, para evitar erros caso já venha em bytes
                self.server.storage.store_offline_message(
                    recipient,
                    sender,
                    content.encode() if isinstance(content, str) else content,
                    nonce.encode() if nonce and isinstance(nonce, str) else nonce,
                    tag.encode() if tag and isinstance(tag, str) else tag
                )

                return self._build_response(
                    MessageType.RESPONSE,
                    "server",
                    {"status": "success", "message": "Mensagem guardada offline com sucesso"}
                ), None, False

            else:
                return self._build_response(
                    MessageType.RESPONSE, 
                    "server", 
                    {"status": "error", "message": "Ação offline desconhecida"}
                ), None, False


        # 6. DESCONECTAR
        if cmd == MessageType.DISCONNECT.value:
            return self._build_response(MessageType.RESPONSE, "server", {"status": "success", "message": "Desconectado"}), None, True

        # COMANDO DESCONHECIDO
        return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": f"Comando desconhecido: {cmd}"}), None, False

    async def _handle_disconnect(self):
        """Remove o utilizador dos online e fecha a ligação."""
        if self.username:
            await self.server.online_users.remove_online_user(self.username)
            self.username = None

        self.running = False
        await self.close()

    async def send_message(self, message: Message):
        """Envia uma Message com framing de 4 bytes + JSON."""
        data = message.to_json().encode("utf-8")
        self.writer.write(len(data).to_bytes(4, byteorder="big") + data)
        await self.writer.drain()

    async def send_error(self, error_message: str):
        await self.send_message(self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": error_message}))

    async def send_success(self, data: Dict[str, Any]):
        await self.send_message(self._build_response(MessageType.RESPONSE, "server", {"status": "success", **data}))

    async def close(self):
        if not self.writer.is_closing():
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:
                pass
