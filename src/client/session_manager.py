import os
import json
import base64
from typing import Optional, Dict, Any, Tuple

# NOTA: Importar as funções da Pessoa 3 aqui
# from crypto.rsa import generate_rsa_keypair
# from crypto.dh import generate_dh_keypair, compute_shared_secret
# from crypto.aes import encrypt_aes_gcm, decrypt_aes_gcm

class SessionManager:
    
    """
    Gere as chaves de identidade (longo prazo) e as chaves de sessão (efémeras) para o P2P.
    """
    
    def __init__(self, username: str = None, data_dir: str = "client_data"):
        self.username = username
        self.data_dir = data_dir
        
        # Chaves de Identidade (Longo prazo - RSA/Ed25519)
        self.identity_priv_key: Optional[bytes] = None
        self.identity_pub_key: Optional[bytes] = None
        
        # Estado P2P
        # Guarda a nossa chave privada efémera temporária antes de calcular o segredo
        self.pending_ephemeral_priv_keys: Dict[str, bytes] = {}
        
        # A "Caixa Forte": Guarda a chave simétrica final partilhada com cada amigo
        # Ex: {"bob": b"chave_secreta_aes_256"}
        self.active_sessions: Dict[str, bytes] = {}
        
        if username:
            self._ensure_dir()

    def set_username(self, username: str):
        """Define o username e garante que a pasta de dados existe."""
        self.username = username
        self._ensure_dir()
        print(f"[*] SessionManager configurado para: {username}")

    def _ensure_dir(self):
        """Garante que a pasta para guardar as chaves existe."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    # ==========================================
    # 1. CHAVES DE IDENTIDADE (Para o Servidor)
    # ==========================================

    def load_or_generate_identity_keys(self) -> str:
        """
        Carrega as chaves do disco. Se não existirem, pede à Pessoa 3 para gerar.
        Retorna a chave pública em Base64 para enviar no REGISTER/AUTH.
        """
        priv_path = os.path.join(self.data_dir, f"{self.username}_priv.pem")
        pub_path = os.path.join(self.data_dir, f"{self.username}_pub.pem")
        
        if os.path.exists(priv_path) and os.path.exists(pub_path):
            with open(priv_path, "rb") as f: self.identity_priv_key = f.read()
            with open(pub_path, "rb") as f: self.identity_pub_key = f.read()
        else:
            # CHAMAR PESSOA 3: Gerar par de chaves RSA
            # self.identity_priv_key, self.identity_pub_key = generate_rsa_keypair()
            
            # (Simulação temporária)
            self.identity_priv_key, self.identity_pub_key = b"priv", b"pub_key_base64"
            
            with open(priv_path, "wb") as f: f.write(self.identity_priv_key)
            with open(pub_path, "wb") as f: f.write(self.identity_pub_key)
            
        return base64.b64encode(self.identity_pub_key).decode('utf-8')

    # ==========================================
    # 2. HANDSHAKE P2P (Diffie-Hellman)
    # ==========================================

    def get_handshake_data(self, peer_username: str) -> str:
        """
        Gera uma chave efémera para iniciar conversa com um peer.
        Retorna a chave pública efémera (em Base64) para colocar no P2P_HELLO.
        """
        # CHAMAR PESSOA 3: Gerar chaves Diffie-Hellman para esta sessão
        # eph_priv, eph_pub = generate_dh_keypair()
        
        # (Simulação temporária)
        eph_priv, eph_pub = b"eph_priv", b"minha_chave_publica_efemera"
        
        # Guardamos a privada para podermos calcular o segredo quando o peer responder
        self.pending_ephemeral_priv_keys[peer_username] = eph_priv
        
        return base64.b64encode(eph_pub).decode('utf-8')

    def process_peer_handshake(self, peer_username: str, peer_pub_key_b64: str):
        """
        Recebe a chave pública efémera do peer e calcula a chave simétrica final.
        """
        peer_pub_key = base64.b64decode(peer_pub_key_b64)
        my_eph_priv = self.pending_ephemeral_priv_keys.pop(peer_username, None)
        
        if not my_eph_priv:
            print(f"[Erro] Handshake com {peer_username} falhou: Chave privada efémera não encontrada.")
            return

        # CHAMAR PESSOA 3: Calcular Segredo Partilhado (Diffie-Hellman)
        # shared_secret = compute_shared_secret(my_eph_priv, peer_pub_key)
        
        # (Simulação temporária)
        shared_secret = b"CHAVE_SIMETRICA_SUPER_SECRETA"
        
        # Guardar a chave final na sessão ativa!
        self.active_sessions[peer_username] = shared_secret
        print(f"[*] Sessão criptográfica estabelecida com {peer_username}!")

    # ==========================================
    # 3. ENCRIPTAÇÃO DE MENSAGENS (AES)
    # ==========================================

    def encrypt_for_peer(self, peer_username: str, plaintext: str) -> Optional[Dict[str, str]]:
        """
        Usa a chave partilhada para encriptar a mensagem. 
        Retorna dicionário perfeito para a tua dataclass `Message`.
        """
        if peer_username not in self.active_sessions:
            print(f"[Erro] Não há sessão segura com {peer_username}")
            return None
            
        shared_key = self.active_sessions[peer_username]
        
        # CHAMAR PESSOA 3: Encriptar (ex: AES-GCM)
        # ciphertext, nonce, tag = encrypt_aes_gcm(shared_key, plaintext.encode('utf-8'))
        
        # (Simulação temporária)
        ciphertext = f"ENC({plaintext})".encode('utf-8')
        nonce, tag = b"nonce", b"tag"
        
        return {
            "content": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }

    def decrypt_from_peer(self, peer_username: str, payload: dict) -> Optional[str]:
        """
        Usa a chave partilhada para desencriptar a mensagem recebida.
        """
        if peer_username not in self.active_sessions:
            return None
            
        shared_key = self.active_sessions[peer_username]
        
        ciphertext = base64.b64decode(payload["content"])
        nonce = base64.b64decode(payload["nonce"])
        tag = base64.b64decode(payload["tag"])
        
        # CHAMAR PESSOA 3: Desencriptar
        # try:
        #     plaintext = decrypt_aes_gcm(shared_key, ciphertext, nonce, tag)
        #     return plaintext.decode('utf-8')
        # except Exception as e:
        #     print("Erro na verificação da mensagem (Alguém alterou os dados!)")
        #     return None
        
        # (Simulação temporária - remove a string "ENC(" e ")")
        return ciphertext.decode('utf-8').replace("ENC(", "").replace(")", "")