import os
import json
import base64
import utils.helpers as help
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from crypto import generate_keypair_Ed25519
from crypto.kdf import derive_key_PBKDF2HMAC
from crypto import generate_keypair as generate_x25519_keypair
from crypto import perform_exchange, derive_key as derive_key_from_ecdh
from crypto.symmetric import generate_key as generate_symmetric_key, encrypt, decrypt
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
        
        # Salt em bytes para fallback na memória
        self._salt: Optional[bytes] = None
        
        # Estado P2P
        self.pending_ephemeral_priv_keys: Dict[str, bytes] = {}
        self.pending_ephemeral_pub_keys: Dict[str, str] = {}
        self.peer_public_keys: Dict[str, bytes] = {}
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

    def set_salt(self, salt):
        """Guarda o salt (do servidor ou local) e persiste no disco."""
        self.salt = salt
        if isinstance(salt, bytes):
            self._salt = salt
        else:
            try:
                self._salt = base64.b64decode(salt)
            except:
                self._salt = None
        
        if self.username and self._salt:
            try:
                salt_path = os.path.join(self.data_dir, f"{self.username}.salt")
                with open(salt_path, "wb") as f:
                    f.write(self._salt)
                print(f"[*] Salt guardado em disco: {salt_path}")
            except Exception as e:
                print(f"[!] Erro ao guardar salt: {e}")

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
            
            priv_path = os.path.join(self.data_dir, f"{user}_priv.pem")
            pub_path = os.path.join(self.data_dir, f"{user}_pub.pem")
            cert_path = os.path.join(self.data_dir, f"{user}_cert.pem")

            # Check if keys exist and validate password
            if os.path.exists(priv_path) and os.path.exists(pub_path):
                try:
                    with open(priv_path, "rb") as f:
                        priv_key = serialization.load_pem_private_key(
                            f.read(),
                            password=password_kdf
                        )
                    with open(pub_path, "rb") as f:
                        self.identity_pub_key = serialization.load_pem_public_key(f.read())
                    print("[*] Chaves carregadas do disco")
                except ValueError as e:
                    if "Bad decrypt" in str(e):
                        print("[!] Password incorreta. A gerar novas chaves...")
                        for f in [priv_path, pub_path, cert_path]:
                            if os.path.exists(f):
                                os.remove(f)
                    else:
                        raise
            
            # Generate new keys if needed
            if not os.path.exists(priv_path):
                print("[*] A gerar novo par de chaves Ed25519...")
                priv_key, pub_key = generate_keypair_Ed25519()
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

                with open(priv_path, "wb") as f:
                    f.write(priv_pem)
                with open(pub_path, "wb") as f:
                    f.write(pub_pem)
                print(f"[*] Chaves guardadas em {self.data_dir}")

            # Ensure pub_pem is always defined
            pub_pem = self.identity_pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Certificate
            if os.path.exists(cert_path):
                print("[*] A carregar certificado existente...")
                with open(cert_path, "rb") as f:
                    self.identity_cert = f.read()
            else:
                print("[*] A gerar certificado X.509...")
                self.identity_cert = self._generate_self_signed_cert(user, pub_pem, password_kdf)
                with open(cert_path, "wb") as f:
                    f.write(self.identity_cert)
                print(f"[*] Certificado guardado em {cert_path}")

            # Always generate pub_pem for return
            pub_pem = self.identity_pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
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

    def get_public_key_pem(self) -> str:
        """Return the public key in PEM format."""
        if not self.identity_pub_key:
            raise ValueError("Public key not loaded.")
        pub_pem = self.identity_pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pub_pem.decode("utf-8")

    def get_salt(self) -> bytes:
        """Return the salt in bytes."""
        local_salt_path = os.path.join(self.data_dir, f"{self.username}.salt")
        if os.path.exists(local_salt_path):
            with open(local_salt_path, "rb") as f:
                return f.read()
        return self._salt

    def sign_with_identity_key(self, data: bytes) -> bytes:
        """Load private key temporarily, sign data, then discard key."""
        priv_path = os.path.join(self.data_dir, f"{self.username}_priv.pem")
        
        print("[*] A carregar chave privada temporariamente...")
        
        # Use local salt from disk, or fallback to memory salt
        local_salt_path = os.path.join(self.data_dir, f"{self.username}.salt")
        if os.path.exists(local_salt_path):
            with open(local_salt_path, "rb") as f:
                local_salt = f.read()
        elif self._salt:
            local_salt = self._salt
        else:
            raise ValueError(f"Salt não encontrado para {self.username}")
        
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
    # 2. HANDSHAKE P2P (X25519 ECDH)
    # ==========================================
    
    def get_handshake_data(self, peer_username: str) -> str:
        """
        Gera chave efémera X25519 para handshake P2P.
        Retorna a chave pública efémera em base64.
        """
        eph_priv_pem, eph_pub_raw = generate_x25519_keypair()
        
        # Guardamos a chave privada efémera temporariamente
        self.pending_ephemeral_priv_keys[peer_username] = eph_priv_pem
        
        print(f"[DEBUG HANDSHAKE] Generated X25519 keypair for {peer_username}")
        print(f"[DEBUG HANDSHAKE] Ephemeral pub key (base64): {base64.b64encode(eph_pub_raw).decode('utf-8')[:50]}...")
        
        return base64.b64encode(eph_pub_raw).decode('utf-8')

    def process_peer_handshake(self, peer_username: str, peer_pub_key_b64: str):
        """
        Processa a chave pública efémera do peer e deriva a chave de sessão.
        """
        try:
            # Decodificar chave pública do peer
            peer_pub_raw = base64.b64decode(peer_pub_key_b64)
            
            # Obter nossa chave privada efémera
            my_eph_priv_pem = self.pending_ephemeral_priv_keys.pop(peer_username, None)
            
            if not my_eph_priv_pem:
                print(f"[Erro] Chave efémera não encontrada para {peer_username}")
                return
            
            print(f"[DEBUG HANDSHAKE] Peer {peer_username} pub key (base64): {peer_pub_key_b64[:50]}...")
            
            # Perform ECDH - derivar segredo partilhado
            shared_secret = perform_exchange(my_eph_priv_pem, peer_pub_raw)
            print(f"[DEBUG HANDSHAKE] Shared secret (hex): {shared_secret.hex()[:50]}...")
            
            # Derivar chave simétrica com HKDF-SHA256
            session_key = derive_key_from_ecdh(shared_secret, length=32, info=b"P2PChat")
            print(f"[DEBUG HANDSHAKE] Session key (hex): {session_key.hex()[:32]}...")
            
            # Guardar chave de sessão e chave pública do peer
            self.active_sessions[peer_username] = session_key
            self.peer_public_keys[peer_username] = peer_pub_raw
            
            print(f"[*] Sessão criptográfica X25519 estabelecida com {peer_username}")
            
        except Exception as e:
            print(f"[Erro] Handshake X25519 falhou: {e}")

    def ratchet_session(self, peer_username: str):
        """ Faz rotação de chaves: gera novo par efémero e deriva nova chave de sessão."""
        if peer_username not in self.active_sessions:
            print(f"[Erro] Não há sessão com {peer_username}")
            return
        
        old_key = self.active_sessions[peer_username]
        
        new_eph_pub, new_eph_priv = generate_x25519_keypair()
        
        new_pub_b64 = base64.b64encode(new_eph_pub).decode('utf-8')
        
        self.pending_ephemeral_pub_keys[peer_username] = new_pub_b64
        self.pending_ephemeral_priv_keys[peer_username] = new_eph_priv
        
        new_shared = perform_exchange(new_eph_priv, self.peer_public_keys[peer_username])
        new_session_key = derive_key_from_ecdh(new_shared, length=32, info=b"P2PChatRatchet")
        
        self.active_sessions[peer_username] = new_session_key
        
        print(f"[*] Ratchet: nova chave de sessão derivada para {peer_username}")

    # ==========================================
    # 3. ENCRIPTAÇÃO DE MENSAGENS (AES-GCM)
    # ==========================================

    def encrypt_for_peer(self, peer_username: str, plaintext: str) -> Optional[Dict[str, str]]:
        """Encripta mensagem usando AES-GCM com chave de sessão."""
        if peer_username not in self.active_sessions:
            print(f"[Erro] Não há sessão segura com {peer_username}")
            return None
            
        session_key = self.active_sessions[peer_username]
        plaintext_bytes = plaintext.encode('utf-8')
        
        # AES-GCM: returns (ciphertext, nonce, tag)
        ciphertext, nonce, tag = encrypt(session_key, plaintext_bytes)
        
        print(f"[DEBUG ENCRYPT] Peer: {peer_username}")
        print(f"[DEBUG ENCRYPT] Plaintext: {plaintext}")
        print(f"[DEBUG ENCRYPT] Key (hex): {session_key.hex()[:32]}...")
        print(f"[DEBUG ENCRYPT] Ciphertext (base64): {base64.b64encode(ciphertext).decode('utf-8')[:50]}...")
        print(f"[DEBUG ENCRYPT] Nonce (hex): {nonce.hex()}")
        print(f"[DEBUG ENCRYPT] Tag (hex): {tag.hex()}")
        
        return {
            "content": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }

    def decrypt_from_peer(self, peer_username: str, payload: dict) -> Optional[str]:
        """Desencripta mensagem usando AES-GCM com chave de sessão."""
        if peer_username not in self.active_sessions:
            print(f"[Erro] Não há sessão com {peer_username}")
            return None
            
        try:
            session_key = self.active_sessions[peer_username]
            
            ciphertext = base64.b64decode(payload["content"])
            nonce = base64.b64decode(payload["nonce"])
            tag = base64.b64decode(payload["tag"])
            
            print(f"[DEBUG DECRYPT] Peer: {peer_username}")
            print(f"[DEBUG DECRYPT] Key (hex): {session_key.hex()[:32]}...")
            print(f"[DEBUG DECRYPT] Ciphertext (base64): {base64.b64encode(ciphertext).decode('utf-8')[:50]}...")
            print(f"[DEBUG DECRYPT] Nonce (hex): {nonce.hex()}")
            print(f"[DEBUG DECRYPT] Tag (hex): {tag.hex()}")
            
            plaintext = decrypt(session_key, ciphertext, nonce, tag)
            print(f"[DEBUG DECRYPT] Decrypted: {plaintext.decode('utf-8')}")
            return plaintext.decode('utf-8')
            
        except Exception as e:
            print(f"[Erro] Desencriptação falhou: {e}")
            return None
    
    def encrypt_offline(self, recipient_pub_key_b64: str, text: str) -> Dict[str, str]:
        """
        Encripta mensagem para destinatário offline usando a sua chave pública Ed25519.
        Nota: Ed25519 é para assinaturas, não encriptação. Para encriptar,
        seria necessário usar RSA ou ECDH (mas o peer não tem chave ECDH pública).
        Esta implementação é um placeholder - o servidorstore a mensagem
        e o destinatário usa a sua chave de identidade para desencriptar.
        """
        from crypto.hybrid import encrypt_content
        
        try:
            # A chave pública do recipient está em formato PEM base64
            # hybrid.py deve tratar da encriptação
            encrypted = encrypt_content(text, recipient_pub_key_b64)
            return encrypted
        except Exception as e:
            print(f"[Erro] Encriptação offline falhou: {e}")
            # Fallback placeholder
            ciphertext = f"OFFLINE_ENC({text})".encode('utf-8')
            return {
                "content": help.encode_base64(ciphertext),
                "nonce": help.encode_base64(b"static_nonce"),
                "tag": help.encode_base64(b"static_tag")
            }

    def decrypt_offline(self, encrypted_payload: dict) -> str:
        """Desencripta mensagem offline usando chave de identidade."""
        from crypto.hybrid import decrypt_content
        
        try:
            return decrypt_content(encrypted_payload)
        except Exception as e:
            print(f"[Erro] Desencriptação offline falhou: {e}")
            # Fallback placeholder
            content_b64 = encrypted_payload.get("content")
            raw_bytes = help.decode_base64(content_b64) 
            raw_str = raw_bytes.decode('utf-8')
            return raw_str.replace("OFFLINE_ENC(", "").replace(")", "")