"""
Client Entry Point
==================
Run as: python -m client
"""

from .client import ChatClient

def main():
    client = ChatClient()
    client.start()

if __name__ == '__main__':
    main()
