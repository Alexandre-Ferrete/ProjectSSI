"""Tratamento de uma ligação TCP individual de cliente.

Esta classe contém a lógica que antes vivia em `server.py`: parsing,
routing de comandos e geração de respostas tipadas.
"""

import json
from typing import Optional, Dict, Any, Tuple

from protocol.messages import Message, MessageType


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
        """Normaliza o formato recebido para {type, sender, data}."""
        try:
            message = Message.from_json(message_text)
            return {"type": message.msg_type, "sender": message.sender, "data": message.payload}
        except Exception:
            raw = json.loads(message_text)
            if "type" in raw or "data" in raw:
                return raw
            return {"type": raw.get("msg_type"), "sender": raw.get("sender"), "data": raw.get("payload", {})}

    def _build_response(self, msg_type: MessageType, sender: str, payload: Dict[str, Any]) -> Message:
        return Message(msg_type=msg_type.value, sender=sender, payload=payload)

    async def process_command(self, request: Dict[str, Any]):
        """Executa a lógica de cada comando suportado pelo protocolo."""
        cmd = (request.get("type") or "").lower()
        data = request.get("data", {}) or {}
        sender = request.get("sender") or self.username or "server"

        if cmd == MessageType.REGISTER.value:
            username = data.get("username") or sender
            password = data.get("password")
            public_key = data.get("public_key")
            certificate = data.get("certificate")

            if not username or not password:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Username e password são obrigatórios"}), None, False

            if self.server.storage.get_user(username):
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Utilizador já existe"}), None, False

            created = self.server.storage.create_user(username, password, public_key, certificate)
            if not created:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Falha ao criar utilizador"}), None, False

            return self._build_response(MessageType.RESPONSE, "server", {"status": "success", "message": "Registo efetuado com sucesso"}), None, False

        if cmd == MessageType.AUTH.value:
            username = data.get("username")
            password = data.get("password")
            p2p_port = int(data.get("p2p_port", 0) or 0)

            if not username or not password:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Credenciais inválidas"}), None, False

            user = self.server.storage.get_user(username)
            if not user or user.get("password_hash") != password:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Login inválido"}), None, False

            await self.server.online_users.add_online_user(username, self.address[0], p2p_port, self.writer)
            return self._build_response(MessageType.RESPONSE, "server", {"status": "success", "message": "Login OK", "username": username}), username, False

        if cmd == MessageType.GET_IP.value:
            if not self.username:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Não autenticado"}), None, False

            target_user = data.get("target_user")
            address = await self.server.online_users.get_user_address(target_user)
            if address:
                ip, port = address
                return self._build_response(MessageType.IP_RESPONSE, "server", {"target_user": target_user, "ip": ip, "port": port, "status": "success"}), None, False

            return self._build_response(MessageType.IP_RESPONSE, "server", {"target_user": target_user, "ip": None, "port": None, "status": "offline"}), None, False

        if cmd == MessageType.GET_USERS.value:
            if not self.username:
                return self._build_response(MessageType.RESPONSE, "server", {"status": "error", "message": "Não autenticado"}), None, False

            users = await self.server.online_users.list_online_users()
            return self._build_response(MessageType.USERS_LIST, "server", {"users": users}), None, False

        if cmd == MessageType.DISCONNECT.value:
            return self._build_response(MessageType.RESPONSE, "server", {"status": "success", "message": "Desconectado"}), None, True

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
