import asyncio
import logging
import signal

from .storage import Storage
from .user_manager import OnlineUserManager
from .tcp_handler import ClientHandler

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
        handler = ClientHandler(reader, writer, self)
        await handler.handle()

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