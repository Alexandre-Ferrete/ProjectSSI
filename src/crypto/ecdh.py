"""
ECDH Key Exchange
================
Elliptic Curve Diffie-Hellman for Perfect Forward Secrecy (PFS).

TODO:
- Generate ECDH keypair (ephemeral)
- Perform key exchange
- Derive shared secret
"""

from typing import Tuple


# Curve selection
# TODO: Choose curve (secp256r1/P-256 recommended)
# ECDH_CURVE = "secp256r1"


def generate_keypair(curve: str = "secp256r1") -> Tuple[bytes, bytes]:
    """
    TODO: Generate ECDH keypair.
    
    Args:
        curve: Elliptic curve name (secp256r1, secp384r1, X25519)
        
    Returns:
        (private_key_pem, public_key_pem)
    
    Implementation:
    - Use cryptography.hazmat.primitives.asymmetric.ec
    - Generate private key on selected curve
    - Serialize public key to PEM/compressed format
    """
    pass


def perform_exchange(
    private_key_pem: bytes,
    peer_public_key_pem: bytes,
    curve: str = "secp256r1"
) -> bytes:
    """
    TODO: Perform ECDH key exchange.
    
    Args:
        private_key_pem: Our private key
        peer_public_key_pem: Peer's public key
        curve: Elliptic curve
        
    Returns:
        Shared secret (raw)
    
    Implementation:
    - Load both keys
    - Perform ECDH agreement
    - Return raw shared secret
    """
    pass


def derive_key(
    shared_secret: bytes,
    length: int = 32,
    salt: bytes = None,
    info: bytes = None
) -> bytes:
    """
    TODO: Derive encryption key from shared secret using HKDF.
    
    Args:
        shared_secret: Raw ECDH shared secret
        length: Desired key length (32 for AES-256)
        salt: Optional salt (recommended)
        info: Optional context/application info
        
    Returns:
        Derived key
    
    Implementation:
    - Use HKDF from cryptography.hazmat.primitives.kdf.hkdf
    - SHA256 as hash function
    """
    pass


def load_public_key(public_key_pem: bytes, curve: str = "secp256r1"):
    """TODO: Load public key from PEM."""
    pass


def load_private_key(private_key_pem: bytes, curve: str = "secp256r1"):
    """TODO: Load private key from PEM."""
    pass


# ============================================================================
# PERFECT FORWARD SECRECY (PFS)
# ============================================================================
#
# ECDH provides Perfect Forward Secrecy when:
# - Each session uses ephemeral (one-time) keypairs
# - Private keys are discarded after use
# - Long-term keys only sign/verify, not encrypt
#
# Key Exchange Flow:
# -----------------
# 1. Alice generates ephemeral keypair (A_priv, A_pub)
# 2. Bob generates ephemeral keypair (B_priv, B_pub)
# 3. Alice sends A_pub to Bob
# 4. Bob sends B_pub to Alice
# 5. Alice computes: ECDH(A_priv, B_pub) = shared_secret
# 6. Bob computes: ECDH(B_priv, A_pub) = shared_secret
# 7. Both derive session key: HKDF(shared_secret)
# 8. Encrypt messages with session key
# 9. Discard ephemeral keys after conversation
#
# Advantages:
# - Compromised long-term keys don't expose past messages
# - Each conversation has unique session key
# - Even if current session key is compromised, past messages safe
#
# ============================================================================
