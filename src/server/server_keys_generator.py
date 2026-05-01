from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def generate_server_keys(password: str):
    # Gera o par (Privada + Pública derivada)
    ca_priv_key = ed25519.Ed25519PrivateKey.generate()
    ca_pub_key = ca_priv_key.public_key()

    # 1. Guardar a Privada (Encriptada com a password)
    # O salt é gerado automaticamente pelo BestAvailableEncryption e guardado no PEM
    with open("ca_identity.key", "wb") as f:
        f.write(ca_priv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode())
        ))

    # 2. Guardar a Pública (Para o 'Pinning' no Cliente e verificação de certificados)
    with open("ca_public.key", "wb") as f:
        f.write(ca_pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo # Correção aqui
        ))
    
    print("[*] Chaves do servidor geradas e guardadas.")

def load_server_pubkey():
    with open("ca_public.key", "rb") as f:
        pub_key_data = f.read()
        return serialization.load_pem_public_key(pub_key_data)
    
def load_server_privkey(password: str):
    with open("ca_identity.key", "rb") as f:
        priv_key_data = f.read()
        # O load_pem_private_key lê o salt do cabeçalho do ficheiro e reconstrói a chave
        return serialization.load_pem_private_key(priv_key_data, password=password.encode())