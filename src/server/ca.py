"""
Certificate Authority (CA)
==========================
Internal PKI - manages user certificates for the chat system.
"""

import os
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from src.crypto.asymmetric import generate_keypair as rsa_generate
from src.crypto.certificates import (
    generate_ca_certificate,
    generate_user_certificate,
    load_certificate,
    get_subject,
    get_public_key,
    verify_signature,
    is_expired,
    get_validity_period
)

logger = logging.getLogger(__name__)


class CertificateAuthority:
    """
    Internal PKI Certificate Authority.
    """
    
    def __init__(self, storage):
        self.storage = storage
        self.ca_private_key = None
        self.ca_public_key = None
        self.ca_cert = None
        
        self.ca_key_path = os.path.join("data", "ca_key.pem")
        self.ca_cert_path = os.path.join("data", "ca_cert.pem")
        self.validity_days = 3650
    
    def initialize(self):
        """
        Initialize CA - load existing or generate new.
        """
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(self.ca_key_path) and os.path.exists(self.ca_cert_path):
            self.load_ca_keys()
            logger.info("CA keys loaded from storage")
        else:
            self.generate_ca_keys()
            logger.info("New CA keys generated")
        
        ca_cert = load_certificate(self.ca_cert)
        if is_expired(ca_cert):
            logger.warning("CA certificate has expired! Regenerating...")
            self.generate_ca_keys()
    
    def generate_ca_keys(self) -> Tuple[bytes, bytes]:
        """
        Generate new CA keypair.
        
        Returns:
            (private_key_pem, certificate_pem)
        """
        self.ca_private_key, self.ca_public_key = rsa_generate(key_size=4096)
        
        self.ca_cert = generate_ca_certificate(
            ca_private_key=self.ca_private_key,
            ca_public_key=self.ca_public_key,
            common_name="ChatServer CA",
            validity_days=self.validity_days
        )
        
        self.save_ca_keys(self.ca_private_key, self.ca_cert)
        logger.info("CA keypair generated and saved")
        return self.ca_private_key, self.ca_cert
    
    def load_ca_keys(self) -> bool:
        """Load existing CA keys from storage."""
        try:
            with open(self.ca_key_path, 'rb') as f:
                self.ca_private_key = f.read()
            
            with open(self.ca_cert_path, 'rb') as f:
                self.ca_cert = f.read()
            
            from src.crypto.asymmetric import load_public_key
            self.ca_public_key = get_public_key(load_certificate(self.ca_cert))
            
            return True
        except Exception as e:
            logger.error(f"Failed to load CA keys: {e}")
            return False
    
    def save_ca_keys(self, private_key_pem: bytes, cert_pem: bytes):
        """Save CA keys to storage."""
        with open(self.ca_key_path, 'wb') as f:
            f.write(private_key_pem)
        
        with open(self.ca_cert_path, 'wb') as f:
            f.write(cert_pem)
        
        os.chmod(self.ca_key_path, 0o600)
        logger.info("CA keys saved to storage")
    
    def sign_user_certificate(
        self,
        username: str,
        public_key: bytes,
        csr: bytes = None
    ) -> bytes:
        """
        Sign a user's certificate request.
        
        Args:
            username: User's identity
            public_key: User's public key to include in certificate
            csr: Optional Certificate Signing Request
            
        Returns:
            Signed certificate in PEM format
        """
        cert = generate_user_certificate(
            ca_private_key=self.ca_private_key,
            user_public_key=public_key,
            username=username,
            ca_cert=self.ca_cert,
            validity_days=365
        )
        
        self.storage.save_certificate(username, cert)
        self.storage.save_public_key(username, public_key)
        
        logger.info(f"Certificate issued for user: {username}")
        return cert
    
    def verify_certificate(self, cert_pem: bytes) -> bool:
        """
        Verify a certificate is signed by this CA.
        
        Args:
            cert_pem: Certificate to verify
            
        Returns:
            True if valid and signed by this CA
        """
        if not verify_signature(cert_pem, self.ca_cert):
            return False
        
        cert = load_certificate(cert_pem)
        
        if is_expired(cert):
            logger.warning("Certificate has expired")
            return False
        
        return True
    
    def revoke_certificate(self, username: str):
        """Revoke a user's certificate."""
        self.storage.save_public_key(username, None)
        self.storage.save_certificate(username, None)
        logger.info(f"Certificate revoked for user: {username}")
    
    def is_revoked(self, username: str) -> bool:
        """Check if certificate is revoked."""
        cert = self.storage.get_certificate(username)
        return cert is None
    
    def get_ca_certificate(self) -> Optional[bytes]:
        """Get CA certificate for distribution to clients."""
        return self.ca_cert
    
    def get_user_certificate(self, username: str) -> Optional[bytes]:
        """Get a user's certificate."""
        return self.storage.get_certificate(username)
    
    def get_user_public_key(self, username: str) -> Optional[bytes]:
        """Get a user's public key."""
        return self.storage.get_public_key(username)
