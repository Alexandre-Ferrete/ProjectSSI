"""
X.509 Certificates
==================
X.509 certificate creation and validation.

TODO:
- Create self-signed CA certificate
- Create user certificate signed by CA
- Parse certificate
- Validate certificate signature
"""

from datetime import datetime
from typing import Tuple, Optional


def generate_ca_certificate(
    ca_private_key: bytes,
    ca_public_key: bytes,
    common_name: str = "ChatServer CA",
    validity_days: int = 3650
) -> bytes:
    """
    TODO: Generate self-signed CA certificate.
    
    Args:
        ca_private_key: CA private key
        ca_public_key: CA public key
        common_name: Certificate subject name
        validity_days: Validity period in days
        
    Returns:
        Certificate in PEM format
    
    Implementation:
    - Use cryptography.x509
    - Set subject: CN=common_name
    - Set issuer: CN=common_name (self-signed)
    - Add extensions: Basic Constraints, Key Usage
    - Sign with CA private key
    """
    pass


def generate_user_certificate(
    ca_private_key: bytes,
    user_public_key: bytes,
    username: str,
    ca_cert: bytes,
    validity_days: int = 365
) -> bytes:
    """
    TODO: Generate user certificate signed by CA.
    
    Args:
        ca_private_key: CA private key for signing
        user_public_key: User's public key to embed
        username: User's identity (CN)
        ca_cert: CA certificate
        validity_days: Validity period
        
    Returns:
        Certificate in PEM format
    
    Implementation:
    - Set subject: CN=username
    - Set issuer: CN=ChatServer CA (from CA cert)
    - Add user public key
    - Add extensions
    - Sign with CA private key
    """
    pass


def load_certificate(cert_pem: bytes):
    """
    TODO: Load certificate from PEM.
    
    Args:
        cert_pem: Certificate in PEM format
        
    Returns:
        Certificate object
    """
    pass


def get_subject(cert) -> str:
    """
    TODO: Get subject common name from certificate.
    
    Args:
        cert: Certificate object
        
    Returns:
        Common name (username)
    """
    pass


def get_public_key(cert) -> bytes:
    """
    TODO: Extract public key from certificate.
    
    Args:
        cert: Certificate object
        
    Returns:
        Public key in PEM format
    """
    pass


def verify_signature(
    cert: bytes,
    signing_cert: bytes
) -> bool:
    """
    TODO: Verify certificate was signed by CA.
    
    Args:
        cert: Certificate to verify
        signing_cert: CA certificate
        
    Returns:
        True if valid signature
    """
    pass


def is_expired(cert) -> bool:
    """TODO: Check if certificate is expired."""
    pass


def get_validity_period(cert) -> Tuple[datetime, datetime]:
    """TODO: Get certificate validity period."""
    pass


# ============================================================================
# CERTIFICATE STRUCTURE
# ============================================================================
#
# X.509 Certificate Fields:
# --------------------------
# - Version: v3
# - Serial Number: Unique identifier
# - Signature Algorithm: SHA256 with RSA/ECDSA
# - Issuer: CN=ChatServer CA, O=SecureChat
# - Validity: NotBefore, NotAfter
# - Subject: CN=<username>
# - Subject Public Key: User's encryption key
# - Extensions:
#     * Basic Constraints: CA:FALSE
#     * Key Usage: Digital Signature, Key Encipherment
#     * Subject Alternative Name: <username>
#
# Trust Chain:
# ------------
# Client trusts the CA certificate (distributed with client)
# Server signs user certificates with CA key
# Client verifies user certificate against CA certificate
#
# ============================================================================
