"""
ECDH Key Exchange
================
Elliptic Curve Diffie-Hellman for Perfect Forward Secrecy (PFS).

TODO:
- Generate ECDH keypair (ephemeral)
- Perform key exchange
- Derive shared secret
"""
import cryptography
from typing import Tuple
from cryptography.hazmat.primitives.asymmetric import ec,x25519
from cryptography.hazmat.primitives import serialization
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
    curve = curve.lower()

    if curve == "secp256r1":
        private_key = ec.generate_private_key(ec.SECP256R1())
    elif curve == "secp384r1":
        private_key = ec.generate_private_key(ec.SECP384R1())
    elif curve == "x25519":
        private_key = x25519.X25519PrivateKey.generate()
    else:
        raise ValueError(f"Unsupported curve: {curve}")
    
    public_key = private_key.public_key()

    private_bytes= private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    if curve == "x25519":
        # X25519 usa formato raw (mais comum)
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    else:
        # EC padrão → PEM (SubjectPublicKeyInfo)
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    return private_bytes, public_bytes


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
    curve = curve.lower()

    # Carregar chave privada
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None
    )

    # Carregar chave pública do peer
    if curve == "x25519":
        # Espera formato RAW (32 bytes)
        if b"BEGIN" in peer_public_key_pem:
            # fallback caso venha PEM (menos comum)
            peer_public = serialization.load_pem_public_key(peer_public_key_pem)
        else:
            peer_public = x25519.X25519PublicKey.from_public_bytes(peer_public_key_pem)

        # ECDH (X25519)
        shared_secret = private_key.exchange(peer_public)

    elif curve in ("secp256r1", "secp384r1"):
        peer_public = serialization.load_pem_public_key(peer_public_key_pem)

        # ECDH clássico
        shared_secret = private_key.exchange(ec.ECDH(), peer_public)

    else:
        raise ValueError(f"Unsupported curve: {curve}")

    return shared_secret


from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

def derive_key(
    shared_secret: bytes,
    length: int = 32,
    salt: bytes = None,
    info: bytes = None
) -> bytes:
    """
    Derive encryption key from shared secret using HKDF-SHA256.
    Args:
        shared_secret: Raw ECDH shared secret
        length: Desired key length (default 32 for AES-256)
        salt: Optional salt (recommended)
        info: Optional application context (may be None)
    Returns:
        Derived key of given length (bytes)
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    )
    return hkdf.derive(shared_secret)


def load_public_key(public_key_pem: bytes, curve: str = "secp256r1"):
    """
    Load public key from PEM or raw bytes for given curve.
    Args:
        public_key_pem: PEM-encoded or raw bytes public key
        curve: Curve name (secp256r1, secp384r1, x25519)
    Returns:
        Public key object
    """
    curve = curve.lower()
    if curve == "x25519":
        # If detected PEM encoding
        if public_key_pem.startswith(b"-----BEGIN"):
            return serialization.load_pem_public_key(public_key_pem)
        else:
            return x25519.X25519PublicKey.from_public_bytes(public_key_pem)
    elif curve in ("secp256r1", "secp384r1"):
        return serialization.load_pem_public_key(public_key_pem)
    else:
        raise ValueError(f"Unsupported curve: {curve}")


def load_private_key(private_key_pem: bytes, curve: str = "secp256r1"):
    """
    Load private key from PEM bytes for given curve.
    Args:
        private_key_pem: PEM-encoded bytes
        curve: Curve name (secp256r1, secp384r1, x25519)
    Returns:
        Private key object
    """
    curve = curve.lower()
    return serialization.load_pem_private_key(private_key_pem, password=None)


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
