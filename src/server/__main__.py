import asyncio
import sys
from .server import main

if __name__ == '__main__':
    try:
        # Executa a função main do chat_server.py
        asyncio.run(main())
    except KeyboardInterrupt:
        # Garante que o terminal fica limpo ao sair
        sys.exit(0)