"""
Digital Signatures
=================
Message signing and verification for authenticity.

TODO:
- Sign messages
- Verify signatures
- Sign certificates
"""

from typing import Tuple


def sign(private_key_pem: bytes, message: bytes) -> bytes:
    """
    TODO: Sign a message with RSA/ECC private key.
    
    Args:
        private_key_pem: Private key in PEM format
        message: Message to sign
        
    Returns:
        Signature bytes
    
    Implementation:
    - Use RSASSA-PSS or ECDSA
    - SHA-256 as hash function
    """
    pass


def verify(public_key_pem: bytes, message: bytes, signature: bytes) -> bool:
    """
    TODO: Verify a signature.
    
    Args:
        public_key_pem: Public key in PEM format
        message: Original message
        signature: Signature to verify
        
    Returns:
        True if signature is valid
    """
    pass


def sign_certificate(
    private_key_pem: bytes,
    certificate_data: bytes
) -> bytes:
    """
    TODO: Sign a certificate.
    
    Args:
        private_key_pem: CA private key
        certificate_data: Certificate to sign (TBSCertificate)
        
    Returns:
        Signed certificate
    """
    pass


def create_signature_payload(
    sender: str,
    recipient: str,
    message_id: str,
    encrypted_content: bytes,
    timestamp: int
) -> bytes:
    """
    TODO: Create signature payload for chat message.
    
    Args:
        sender: Sender's username
        recipient: Recipient's username
        message_id: Unique message ID
        encrypted_content: The encrypted message
        timestamp: Unix timestamp
        
    Returns:
        Serialized payload to sign
    """
    pass


# ============================================================================
# SIGNATURE USE CASES
# ============================================================================
#
# 1. Certificate Signing:
#    - CA signs user certificates
#    - Clients verify certificate chain
#
# 2. Message Authentication:
#    - Sender signs message
#    - Recipient verifies sender identity
#    - Combined with encryption for E2EE
#
# 3. Key Exchange Authentication:
#    - Sign ephemeral public keys
#    - Prevents MitM attacks
#
# Algorithm Choices:
# -----------------
# - RSA-PSS: Recommended for RSA keys
# - ECDSA: Recommended for ECC keys
# - Ed25519: Modern, fast (if supported)
#
# ============================================================================
