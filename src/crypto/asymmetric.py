"""
Asymmetric Encryption (RSA)
===========================
RSA encryption and decryption for key encapsulation.

TODO:
- Generate RSA keypair
- Encrypt data (typically for key encapsulation)
- Decrypt data
"""

from typing import Tuple


def generate_keypair(key_size: int = 2048) -> Tuple[bytes, bytes]:
    """
    TODO: Generate RSA keypair.
    
    Args:
        key_size: Size of key in bits (2048, 4096)
        
    Returns:
        (private_key_pem, public_key_pem)
    
    Implementation:
    - Use cryptography.hazmat.primitives.asymmetric.rsa
    - Generate private key with public exponent 65537
    - Serialize to PEM format
    """
    pass


def encrypt(public_key_pem: bytes, data: bytes) -> bytes:
    """
    TODO: Encrypt data with RSA public key.
    
    Args:
        public_key_pem: RSA public key in PEM format
        data: Data to encrypt (typically a symmetric key)
        
    Returns:
        Encrypted data
    
    Implementation:
    - Use OAEP padding with SHA256
    - Maximum data size depends on key size
    """
    pass


def decrypt(private_key_pem: bytes, encrypted_data: bytes) -> bytes:
    """
    TODO: Decrypt data with RSA private key.
    
    Args:
        private_key_pem: RSA private key in PEM format
        encrypted_data: Data encrypted with public key
        
    Returns:
        Decrypted data
    """
    pass


def load_public_key(public_key_pem: bytes):
    """TODO: Load public key from PEM."""
    pass


def load_private_key(private_key_pem: bytes):
    """TODO: Load private key from PEM."""
    pass


# ============================================================================
# USAGE NOTES
# ============================================================================
#
# RSA is typically used for:
# - Key encapsulation (encrypting symmetric keys)
# - Digital signatures
#
# For large data, use hybrid encryption:
# 1. Generate random AES key
# 2. Encrypt data with AES
# 3. Encrypt AES key with RSA
# 4. Send both encrypted key + encrypted data
#
# Key Sizes:
# - 2048 bits: Minimum secure (recommended)
# - 4096 bits: Higher security
#
# ============================================================================
