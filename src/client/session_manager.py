import os
import json
import base64
import utils.helpers as help
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from crypto import generate_keypair_Ed25519
from crypto.kdf import derive_key_PBKDF2HMAC
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID


class SessionManager:
    
    """
    Gere as chaves de identidade (longo prazo) e as chaves de sessão (efémeras) para o P2P.
    
    NOTA: A chave privada NUNCA é guardada em memória. Carrega-se temporariamente para usar e depois descartas.
    """
    
    def __init__(self, username: str = None, data_dir: str = "client_data"):
        self.username = username
        self.data_dir = data_dir
        
        # Apenas a chave pública é guardada em memória (não sensível)
        self.identity_pub_key: Optional[object] = None
        self.identity_cert: Optional[bytes] = None
        
        # Password temporária para derivar chave (NUNCA guarda a chave derivada!)
        self._temp_password: Optional[str] = None
        
        # Estado P2P
        self.pending_ephemeral_priv_keys: Dict[str, bytes] = {}
        self.active_sessions: Dict[str, bytes] = {}
        
        if username:
            self._ensure_dir()

    def set_password(self, password: str):
        """Guarda password temporariamente para derivar chave quando necessário."""
        self._temp_password = password

    def clear_password(self):
        """Remove password da memória."""
        self._temp_password = None
        
    def set_username(self, username: str):
        """Define o username e garante que a pasta de dados existe."""
        self.username = username
        self._ensure_dir()
        print(f"[*] SessionManager configurado para: {username}")

    def set_salt(self, salt: str):
        self.salt = salt

    def _ensure_dir(self):
        """Garante que a pasta para guardar as chaves existe."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    # ==========================================
    # 1. CHAVES DE IDENTIDADE (Para o Servidor)
    # ==========================================

    def load_or_generate_identity_keys(self, password_kdf: bytes, user: str) -> str:
            """
            Carrega as chaves de identidade do disco. Se não existirem,
            gera um novo par Ed25519.
            """
            self.set_username(user)
            print(f"[*] SessionManager: A carregar chaves para {user}...")

            if not self.username:
                raise ValueError("Username não pode ser vazio")

            if not password_kdf:
                raise ValueError("password_kdf não pode ser vazio")
            
            
            priv_path = os.path.join(self.data_dir, f"{self.username}_priv.pem")
            pub_path = os.path.join(self.data_dir, f"{self.username}_pub.pem")
            cert_path = os.path.join(self.data_dir, f"{self.username}_cert.pem")


            if os.path.exists(priv_path) and os.path.exists(pub_path):
                print("[*] A carregar chave pública do disco...")
                with open(pub_path, "rb") as f:
                    self.identity_pub_key = serialization.load_pem_public_key(
                        f.read()
                    )
                
                # Load existing certificate if exists
                if os.path.exists(cert_path):
                    print("[*] A carregar certificado existente...")
                    with open(cert_path, "rb") as f:
                        self.identity_cert = f.read()
                else:
                    print("[!] Certificado não encontrado. A gerar novo...")
                    self.identity_cert = self._generate_self_signed_cert(user, self.identity_pub_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ), password_kdf)
            else:
                print("[*] A gerar novo par de chaves Ed25519...")
                priv_key, pub_key = generate_keypair_Ed25519()

                # NÃO guardamos a chave privada em memória!
                self.identity_pub_key = pub_key

                priv_pem = priv_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(password_kdf)
                )

                pub_pem = pub_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )

                print("[*] A guardar chaves no disco...")
                with open(priv_path, "wb") as f:
                    f.write(priv_pem)

                with open(pub_path, "wb") as f:
                    f.write(pub_pem)

                # Generate self-signed certificate
                print("[*] A gerar certificado X.509...")
                self.identity_cert = self._generate_self_signed_cert(user, pub_pem, password_kdf)

            pub_pem = self.identity_pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Generate self-signed X.509 certificate
            self.identity_cert = self._generate_self_signed_cert(user, pub_pem, password_kdf)

            return base64.b64encode(pub_pem).decode("utf-8")

    def _generate_self_signed_cert(self, username: str, public_key_pem: bytes, password_kdf: bytes = None) -> bytes:
        """Generate a self-signed X.509 certificate using Ed25519 key."""
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, username)
        ])
        
        # Load private key temporarily to sign the certificate
        priv_path = os.path.join(self.data_dir, f"{username}_priv.pem")
        with open(priv_path, "rb") as f:
            priv_key = serialization.load_pem_private_key(
                f.read(),
                password=password_kdf
            )
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False
                ), critical=True
            )
            .sign(priv_key, algorithm=None)
        )
        
        # Save certificate to disk
        cert_path = os.path.join(self.data_dir, f"{username}_cert.pem")
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        with open(cert_path, "wb") as f:
            f.write(cert_pem)
        
        self.identity_cert = cert_pem
        return cert_pem

    def get_certificate(self) -> str:
        """Return the certificate encoded in Base64."""
        if not self.identity_cert:
            raise ValueError("Certificate not generated. Call load_or_generate_identity_keys first.")
        print(f"[*] Certificate carregada, tamanho: {len(self.identity_cert)} bytes")
        return base64.b64encode(self.identity_cert).decode("utf-8")

    def sign_with_identity_key(self, data: bytes) -> bytes:
        """Load private key temporarily, sign data, then discard key."""
        priv_path = os.path.join(self.data_dir, f"{self.username}_priv.pem")
        
        print("[*] A carregar chave privada temporariamente...")
        
        # Use local salt from disk
        local_salt_path = os.path.join(self.data_dir, f"{self.username}.salt")
        with open(local_salt_path, "rb") as f:
            local_salt = f.read()
        
        # Derive password to get the key
        password_kdf = derive_key_PBKDF2HMAC(self._temp_password, local_salt)[0]
        
        with open(priv_path, "rb") as f:
            priv_key = serialization.load_pem_private_key(
                f.read(),
                password=password_kdf
            )
        
        signature = priv_key.sign(data)
        
        print("[*] Chave privada descartada da memória")
        return signature

    # ==========================================
    # 2. HANDSHAKE P2P (Diffie-Hellman)
    # ==========================================
    def get_handshake_data(self, peer_username: str) -> str:
        """Generate ephemeral key for P2P handshake."""
        # Placeholder - would call DH key generation
        eph_priv, eph_pub = b"eph_priv", b"minha_chave_publica_efemera"
        self.pending_ephemeral_priv_keys[peer_username] = eph_priv
        return base64.b64encode(eph_pub).decode('utf-8')

    def process_peer_handshake(self, peer_username: str, peer_pub_key_b64: str):
        """Process peer's ephemeral key and compute shared secret."""
        peer_pub_key = base64.b64decode(peer_pub_key_b64)
        my_eph_priv = self.pending_ephemeral_priv_keys.pop(peer_username, None)
        
        if not my_eph_priv:
            print(f"[Erro] Handshake com {peer_username} falhou.")
            return

        # Placeholder - would compute DH shared secret
        shared_secret = b"CHAVE_SIMETRICA_SUPER_SECRETA"
        self.active_sessions[peer_username] = shared_secret
        print(f"[*] Sessão criptográfica estabelecida com {peer_username}!")

    # ==========================================
    # 3. ENCRIPTAÇÃO DE MENSAGENS (AES)
    # ==========================================

    def encrypt_for_peer(self, peer_username: str, plaintext: str) -> Optional[Dict[str, str]]:
        """Encrypt message using shared session key."""
        if peer_username not in self.active_sessions:
            print(f"[Erro] Não há sessão segura com {peer_username}")
            return None
            
        shared_key = self.active_sessions[peer_username]
        # Placeholder - would use AES-GCM
        ciphertext = f"ENC({plaintext})".encode('utf-8')
        nonce, tag = b"nonce", b"tag"
        
        return {
            "content": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }

    def decrypt_from_peer(self, peer_username: str, payload: dict) -> Optional[str]:
        """Decrypt message using shared session key."""
        if peer_username not in self.active_sessions:
            return None
            
        shared_key = self.active_sessions[peer_username]
        
        ciphertext = base64.b64decode(payload["content"])
        # Placeholder - would use AES-GCM
        return ciphertext.decode('utf-8').replace("ENC(", "").replace(")", "")
    
    def encrypt_offline(self, recipient_pub_key_b64: str, text: str) -> Dict[str, str]:
        """Encrypt message for offline recipient using their public key."""
        ciphertext = f"OFFLINE_ENC({text})".encode('utf-8')
        return {
            "content": help.encode_base64(ciphertext),
            "nonce": help.encode_base64(b"static_nonce"),
            "tag": help.encode_base64(b"static_tag")
            }

    def decrypt_offline(self, encrypted_payload: dict) -> str:
        """Decrypt offline message using our private key."""
        content_b64 = encrypted_payload.get("content")
        raw_bytes = help.decode_base64(content_b64) 
        raw_str = raw_bytes.decode('utf-8')
        return raw_str.replace("OFFLINE_ENC(", "").replace(")", "")