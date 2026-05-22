"""
Hybrid Encryption
=================
Combines asymmetric and symmetric encryption for efficient data encryption.
"""

from typing import Tuple


def encrypt_ecdh(
    recipient_public_key: bytes,
    plaintext: bytes
) -> Tuple[bytes, bytes, bytes, bytes]:
    """
    Encrypt using ECDH key exchange (PFS).

    Process:
    1. Generate ephemeral ECDH keypair
    2. Perform ECDH with recipient's key
    3. Derive session key using HKDF
    4. Encrypt data with session key
    5. Send: ephemeral_public_key + nonce + tag + ciphertext
    
    Args:
        recipient_public_key: Recipient's long-term public key
        plaintext: Data to encrypt
        
    Returns:
        (ephemeral_public_key, nonce, tag, ciphertext)
    """
    from . import ecdh, symmetric
    ephemeral_priv, ephemeral_pub = ecdh.generate_keypair()
    shared_secret = ecdh.perform_exchange(ephemeral_priv, recipient_public_key)
    session_key = ecdh.derive_key(shared_secret)
    ciphertext, nonce, tag = symmetric.encrypt(session_key, plaintext)
    return ephemeral_pub, nonce, tag, ciphertext


def decrypt_ecdh(
    private_key: bytes,
    ephemeral_public_key: bytes,
    nonce: bytes,
    tag: bytes,
    ciphertext: bytes
) -> bytes:
    """
    Decrypt using ECDH key exchange.

    Process:
    1. Perform ECDH with our private key + ephemeral public key
    2. Derive same session key using HKDF
    3. Decrypt ciphertext and verify tag
    
    Args:
        private_key: Our long-term private key
        ephemeral_public_key: Sender's ephemeral public key
        nonce: Nonce from sender
        tag: Authentication tag
        ciphertext: Encrypted data
        
    Returns:
        Decrypted plaintext
    """
    from . import ecdh, symmetric
    shared_secret = ecdh.perform_exchange(private_key, ephemeral_public_key)
    session_key = ecdh.derive_key(shared_secret)
    plaintext = symmetric.decrypt(session_key, ciphertext, nonce, tag)
    return plaintext


# HIGH-LEVEL API 

import base64


def encrypt_content(plaintext: str, recipient_pub_key_b64: str) -> dict:
    """
    Encripta mensagem para destinatário offline.
    Args:
        plaintext: Mensagem em texto
        recipient_pub_key_b64: Chave pública do destinatário em base64
    Returns:
        dict com content, nonce, tag (todos em base64)
    """
    from cryptography.hazmat.primitives import serialization
    
    # Converter base64 para bytes
    pub_key_bytes = base64.b64decode(recipient_pub_key_b64)
    
    # Detectar formato (PEM ou raw)
    if b"BEGIN" in pub_key_bytes:
        # Nota: Se for RSA, falhará aqui se as funções RSA forem necessárias
        # Mas o projeto parece estar a transitar para Ed25519
        public_key = serialization.load_pem_public_key(pub_key_bytes)
        # Se chegarmos aqui com RSA, precisamos de asymmetric.py
        # Por agora, assumimos que as chaves Ed25519 são o padrão
        raise NotImplementedError("Cifragem RSA (PEM) não suportada sem asymmetric.py")
    else:
        # É uma chave Ed25519 raw
        from . import ecdh, symmetric
        import os
        
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
        
        kdf = ConcatKDFHash(
            algorithm=hashes.SHA256(),
            length=32,
            other_info=b"OfflineMessage"
        )
        session_key = kdf.derive(pub_key_bytes)
        
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext, nonce, tag = symmetric.encrypt(session_key, plaintext_bytes)
        
        return {
            "content": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }


def decrypt_content(encrypted_payload: dict) -> str:
    """
    Desencripta mensagem offline.
    Args:
        encrypted_payload: dict com content, nonce, tag (base64)
    Returns:
        Mensagem em texto
    """
    # Por agora, retornamos erro indicando que precisa de implementação
    raise NotImplementedError("Desencriptação offline requer revisão")


# ============================================================================
# HYBRID ENCRYPTION ARCHITECTURE
# ============================================================================
#
# Flow (ECDH-based - with PFS):
# -----------------------------
# 1. Alice has Bob's public key
# 2. Alice generates ephemeral keypair (eA_priv, eA_pub)
# 3. Alice: ECDH(eA_priv, Bob_pub) -> shared_secret
# 4. Alice: HKDF(shared_secret) -> session_key
# 5. Alice encrypts message with session_key
# 6. Alice sends (eA_pub, ciphertext) to Bob
# 7. Bob: ECDH(Bob_priv, eA_pub) -> shared_secret
# 8. Bob: HKDF(shared_secret) -> session_key
# 9. Bob decrypts message
#
# Advantages of ECDH:
# - Perfect Forward Secrecy
# - Ephemeral keys discarded after use
# - Compromised long-term keys don't expose messages
#
# ============================================================================
