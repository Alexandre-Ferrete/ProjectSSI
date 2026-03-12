"""
Symmetric Encryption (AES-GCM)
=============================
AES-GCM for encrypting message data.

TODO:
- Generate symmetric key
- Encrypt data (with authentication)
- Decrypt and verify
"""

from typing import Tuple


# Key sizes
KEY_SIZE_256 = 32  # AES-256
KEY_SIZE_128 = 16  # AES-128


def generate_key(key_size: int = KEY_SIZE_256) -> bytes:
    """
    TODO: Generate random symmetric key.
    
    Args:
        key_size: Key size in bytes (16 or 32)
        
    Returns:
        Random key bytes
    """
    pass


def encrypt(key: bytes, plaintext: bytes, aad: bytes = None) -> Tuple[bytes, bytes, bytes]:
    """
    TODO: Encrypt data with AES-GCM.
    
    Args:
        key: Symmetric key (16 or 32 bytes)
        plaintext: Data to encrypt
        aad: Additional Authenticated Data (optional, for context)
        
    Returns:
        (ciphertext, nonce, tag)
    
    Implementation:
    - Use AES-GCM from cryptography
    - Generate random 12-byte nonce
    - Tag is appended to ciphertext or returned separately
    """
    pass


def decrypt(key: bytes, ciphertext: bytes, nonce: bytes, tag: bytes, aad: bytes = None) -> bytes:
    """
    TODO: Decrypt and verify data with AES-GCM.
    
    Args:
        key: Symmetric key
        ciphertext: Encrypted data
        nonce: Nonce used during encryption
        tag: Authentication tag
        aad: Additional Authenticated Data (if used during encryption)
        
    Returns:
        Decrypted plaintext
        
    Raises:
        Exception if authentication fails
    """
    pass


def encrypt_with_iv(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    TODO: Encrypt with AES-CBC (alternative, less recommended).
    
    Returns:
        (ciphertext, iv, encrypted_key) - for hybrid encryption
    """
    pass


def decrypt_with_iv(key: bytes, ciphertext: bytes, iv: bytes) -> bytes:
    """TODO: Decrypt AES-CBC."""
    pass


# ============================================================================
# SECURITY NOTES
# ============================================================================
#
# AES-GCM (Galois/Counter Mode):
# - Provides both confidentiality AND authentication
# - Authenticated encryption (AEAD)
# - No separate MAC needed
# - 12-byte nonce (never reuse with same key!)
# - 16-byte authentication tag
#
# AES-CBC (legacy, avoid):
# - Provides only confidentiality
# - Requires separate HMAC for authentication
# - Must use random IV
#
# Recommended: AES-GCM
#
# ============================================================================
