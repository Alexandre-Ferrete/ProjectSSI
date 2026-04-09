"""
Session Manager
==============
Manages user keys, certificates, and session state.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Tuple

from src.crypto.ecdh import generate_keypair as ecdh_generate, perform_exchange, derive_key
from src.crypto.symmetric import generate_key, encrypt, decrypt
from src.crypto.hybrid import encrypt_ecdh, decrypt_ecdh
from src.crypto.certificates import verify_signature, load_certificate, is_expired
from src.crypto.asymmetric import generate_keypair as rsa_generate
from src.utils.helpers import encode_base64, decode_base64, ensure_directory

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages cryptographic session for the client.
    """
    
    def __init__(self, username: str = None, data_dir: str = "client_data"):
        self.username = username
        self.data_dir = data_dir
        self.user_dir = os.path.join(data_dir, username) if username else data_dir
        
        self.private_key = None
        self.public_key = None
        self.certificate = None
        self.ca_certificate = None
        
        self.session_keys = {}
        
        self.recipient_keys = {}
        
        self._key_dir = os.path.join(self.user_dir, "keys")
        self._cert_file = os.path.join(self.user_dir, "certificate.pem")
        self._ca_cert_file = os.path.join(self.user_dir, "ca_certificate.pem")
    
    def set_username(self, username: str):
        """Set username and update directories."""
        self.username = username
        self.user_dir = os.path.join(self.data_dir, username)
        self._key_dir = os.path.join(self.user_dir, "keys")
        self._cert_file = os.path.join(self.user_dir, "certificate.pem")
        self._ca_cert_file = os.path.join(self.user_dir, "ca_certificate.pem")
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate RSA keypair for the user.
        
        Returns:
            (private_key_pem, public_key_pem)
        """
        self.private_key, self.public_key = rsa_generate(key_size=2048)
        
        ensure_directory(self._key_dir)
        self._save_key("private_key.pem", self.private_key)
        self._save_key("public_key.pem", self.public_key)
        
        logger.info("Keypair generated")
        return self.private_key, self.public_key
    
    def load_keys(self) -> bool:
        """
        Load existing keys from storage.
        
        Returns:
            True if keys loaded successfully
        """
        try:
            if self.username is None:
                return False
            
            private_key_path = os.path.join(self._key_dir, "private_key.pem")
            public_key_path = os.path.join(self._key_dir, "public_key.pem")
            
            if os.path.exists(private_key_path):
                with open(private_key_path, 'rb') as f:
                    self.private_key = f.read()
            
            if os.path.exists(public_key_path):
                with open(public_key_path, 'rb') as f:
                    self.public_key = f.read()
            
            if os.path.exists(self._cert_file):
                with open(self._cert_file, 'rb') as f:
                    self.certificate = f.read()
            
            if os.path.exists(self._ca_cert_file):
                with open(self._ca_cert_file, 'rb') as f:
                    self.ca_certificate = f.read()
            
            logger.info("Keys loaded from storage")
            return self.private_key is not None
            
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            return False
    
    def save_keys(self, private_key_pem: bytes, public_key_pem: bytes):
        """Save keys to storage."""
        ensure_directory(self._key_dir)
        self._save_key("private_key.pem", private_key_pem)
        self._save_key("public_key.pem", public_key_pem)
        self.private_key = private_key_pem
        self.public_key = public_key_pem
    
    def _save_key(self, filename: str, data: bytes):
        """Save key data to file."""
        path = os.path.join(self._key_dir, filename)
        with open(path, 'wb') as f:
            f.write(data)
        os.chmod(path, 0o600)
    
    def set_certificate(self, certificate: bytes):
        """Set user's certificate."""
        self.certificate = certificate
        ensure_directory(self.user_dir)
        with open(self._cert_file, 'wb') as f:
            f.write(certificate)
        logger.info("Certificate saved")
    
    def get_certificate(self) -> Optional[bytes]:
        """Get user's certificate."""
        return self.certificate
    
    def set_ca_certificate(self, ca_cert: bytes):
        """Set CA certificate for verification."""
        self.ca_certificate = ca_cert
        ensure_directory(self.user_dir)
        with open(self._ca_cert_file, 'wb') as f:
            f.write(ca_cert)
        logger.info("CA certificate saved")
    
    def get_ca_certificate(self) -> Optional[bytes]:
        """Get CA certificate."""
        return self.ca_certificate
    
    def verify_certificate(self, cert: bytes) -> bool:
        """
        Verify a certificate against CA certificate.
        
        Args:
            cert: Certificate to verify
            
        Returns:
            True if valid
        """
        if self.ca_certificate is None:
            logger.warning("CA certificate not set")
            return False
        
        try:
            if not verify_signature(cert, self.ca_certificate):
                logger.warning("Certificate signature verification failed")
                return False
            
            cert_obj = load_certificate(cert)
            if is_expired(cert_obj):
                logger.warning("Certificate has expired")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Certificate verification error: {e}")
            return False
    
    def generate_ephemeral_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate ephemeral ECDH keypair for session.
        
        Returns:
            (ephemeral_private_key, ephemeral_public_key)
        """
        return ecdh_generate(curve="secp256r1")
    
    def perform_key_exchange(self, recipient: str, their_public_key: bytes) -> bytes:
        """
        Perform ECDH key exchange with recipient.
        
        Args:
            recipient: Recipient's username
            their_public_key: Recipient's public key
            
        Returns:
            Shared secret (to be used for symmetric encryption)
        """
        ephemeral_priv, ephemeral_pub = self.generate_ephemeral_keypair()
        
        shared_secret = perform_exchange(ephemeral_priv, their_public_key)
        
        session_key = derive_key(shared_secret)
        
        self.session_keys[recipient] = {
            "session_key": session_key,
            "ephemeral_private": ephemeral_priv,
            "ephemeral_public": ephemeral_pub
        }
        
        logger.info(f"Key exchange completed with {recipient}")
        return session_key
    
    def get_session_key(self, recipient: str) -> Optional[bytes]:
        """
        Get existing session key for recipient.
        
        Args:
            recipient: Recipient's username
            
        Returns:
            Session key if exists, None otherwise
        """
        session = self.session_keys.get(recipient)
        if session:
            return session["session_key"]
        return None
    
    def has_session_key(self, recipient: str) -> bool:
        """Check if session key exists for recipient."""
        return recipient in self.session_keys
    
    def clear_session_key(self, recipient: str):
        """Clear session key."""
        if recipient in self.session_keys:
            del self.session_keys[recipient]
            logger.info(f"Session key cleared for {recipient}")
    
    def add_recipient_key(self, username: str, public_key: bytes):
        """
        Store recipient's public key.
        
        Args:
            username: Recipient's username
            public_key: Recipient's public key
        """
        self.recipient_keys[username] = public_key
        logger.info(f"Public key stored for {username}")
    
    def get_recipient_key(self, username: str) -> Optional[bytes]:
        """Get recipient's public key."""
        return self.recipient_keys.get(username)
    
    def remove_recipient_key(self, username: str):
        """Remove recipient's public key."""
        if username in self.recipient_keys:
            del self.recipient_keys[username]
    
    def get_public_key_bytes(self) -> Optional[bytes]:
        """Get public key as bytes for transmission."""
        return self.public_key
    
    def get_public_key_b64(self) -> Optional[str]:
        """Get public key as base64 for transmission."""
        if self.public_key:
            return encode_base64(self.public_key)
        return None
    
    def clear_all_session_keys(self):
        """Clear all session keys (on logout)."""
        self.session_keys.clear()
        logger.info("All session keys cleared")
    
    def encrypt_message(self, recipient: str, plaintext: bytes) -> Dict[str, Any]:
        """
        Encrypt a message for recipient using ECDH.
        
        Args:
            recipient: Recipient's username
            plaintext: Message to encrypt
            
        Returns:
            Dictionary with encrypted data
        """
        recipient_key = self.get_recipient_key(recipient)
        
        if not recipient_key:
            raise ValueError(f"No public key for recipient: {recipient}")
        
        ephemeral_pub, nonce, tag, ciphertext = encrypt_ecdh(recipient_key, plaintext)
        
        return {
            "encrypted_content": encode_base64(ciphertext),
            "ephemeral_public_key": encode_base64(ephemeral_pub),
            "nonce": encode_base64(nonce),
            "tag": encode_base64(tag)
        }
    
    def decrypt_message(
        self,
        sender: str,
        encrypted_content_b64: str,
        ephemeral_pub_b64: str,
        nonce_b64: str,
        tag_b64: str
    ) -> bytes:
        """
        Decrypt a message from sender.
        
        Args:
            sender: Sender's username
            encrypted_content_b64: Encrypted content
            ephemeral_pub_b64: Ephemeral public key
            nonce_b64: Nonce
            tag_b64: Authentication tag
            
        Returns:
            Decrypted plaintext
        """
        encrypted_content = decode_base64(encrypted_content_b64)
        ephemeral_pub = decode_base64(ephemeral_pub_b64)
        nonce = decode_base64(nonce_b64)
        tag = decode_base64(tag_b64)
        
        if self.private_key is None:
            raise ValueError("Private key not available")
        
        return decrypt_ecdh(
            self.private_key,
            ephemeral_pub,
            nonce,
            tag,
            encrypted_content
        )
    
    def has_keys(self) -> bool:
        """Check if user has keys generated."""
        return self.private_key is not None and self.public_key is not None
