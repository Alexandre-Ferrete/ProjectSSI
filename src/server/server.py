import asyncio
import json
import logging
import signal
from typing import Dict, Any

# Assumindo que estes ficheiros estão na mesma pasta
from .storage import Storage
from .user_manager import OnlineUserManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 5555):
        self.host = host
        self.port = port
        self.storage = Storage()
        self.online_users = OnlineUserManager()
        self.server = None

    async def start(self):
        """Inicializa storage e arranca o servidor."""
        self.storage.initialize()
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        
        addr = self.server.sockets[0].getsockname()
        logger.info(f"[*] Servidor à escuta em {addr}")

        async with self.server:
            await self.server.serve_forever()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Gere a ligação de cada cliente."""
        addr = writer.get_extra_info('peername')
        logger.info(f"[+] Nova conexão: {addr}")
        current_user = None

        try:
            while True:
                try: 
                    header = await asyncio.wait_for(reader.readexactly(4), timeout = 300.0)
                    msg_len = int.from_bytes(header, byteorder='big')
                    data = await asyncio.wait_for(reader.readexactly(msg_len), timeout=10.0)
                except (asyncio.IncompleteReadError, asyncio.TimeoutError):
                    break

                if not data: break
                    

                message = data.decode().strip()
                request = json.loads(message)
                if not message: continue

                response, auth_user = await self.process_command(request, addr, writer, current_user)
                        
                if auth_user:
                    current_user = auth_user

                resp_encoded = json.dumps(response).encode()
                writer.write(len(resp_encoded).to_bytes(4, byteorder='big') + resp_encoded)
                await writer.drain()

        except Exception as e:
            logger.error(f"[!] Erro com {addr}: {e}")
        finally:
            if current_user:
                await self.online_users.remove_online_user(current_user)
                logger.info(f"[-] Utilizador '{current_user}' saiu.")
            writer.close()
            await writer.wait_closed()

    async def process_command(self, request: Dict[str, Any], addr: tuple, writer: asyncio.StreamWriter, current_user: str = None):
        cmd = request.get("type")
        data = request.get("data", {})

        # Exemplo de proteção: só permite GET_USERS se estiver logado
        if cmd == "GET_USERS" and not current_user:
            return {"status": "error", "message": "Não autenticado"}, None

        if cmd == "LOGIN":
            user = data.get("username")
            # ... lógica de verificação na DB ...
            if login_sucesso:
                await self.online_users.add_online_user(user, addr[0], data.get("p2p_port", 0), writer)
                return {"status": "success", "message": "Login OK"}, user # Retorna o user para o handle_client

        return {"status": "error", "message": "Comando desconhecido"}, None

    async def shutdown(self):
        """Encerramento limpo com proteção contra race conditions."""
        logger.info("[*] A encerrar servidor...")
        if self.server:
            self.server.close()
            # Aguarda que todas as conexões existentes terminem ou fechem
            await self.server.wait_closed()
        
        # Só fecha a storage depois de garantir que nenhum handler a está a usar
        self.storage.close()
        logger.info("[*] Recursos libertados.")

async def main():
    """Lógica principal de execução do servidor."""
    server = ChatServer()
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    # Configura sinais de paragem
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass # Para compatibilidade com Windows

    server_task = asyncio.create_task(server.start())
    
    await stop_event.wait() # Fica aqui até alguém fazer Ctrl+C
    
    await server.shutdown()
    server_task.cancel()