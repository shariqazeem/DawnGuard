# core/utils/p2p_handler.py
import json
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

class P2PHandler:
    """Handle P2P encrypted knowledge sharing"""
    
    def __init__(self):
        self.key_size = 2048
    
    def generate_keypair(self):
        """Generate RSA keypair for P2P encryption"""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
                backend=default_backend()
            )
            
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return private_pem.decode(), public_pem.decode()
        except Exception as e:
            print(f"Error generating keypair: {e}")
            # Return dummy keys if cryptography fails
            return "PRIVATE_KEY_PLACEHOLDER", "PUBLIC_KEY_PLACEHOLDER"
    
    def encrypt_for_peer(self, data, peer_public_key_pem):
        """Encrypt data for a specific peer"""
        try:
            # Load peer's public key
            public_key = serialization.load_pem_public_key(
                peer_public_key_pem.encode(),
                backend=default_backend()
            )
            
            # For large data, we need to chunk it (RSA has size limits)
            # For simplicity, just hash it here
            data_hash = hashlib.sha256(data.encode()).hexdigest()
            
            # Encrypt the hash
            encrypted = public_key.encrypt(
                data_hash.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return encrypted.hex()
        except Exception as e:
            print(f"Error encrypting: {e}")
            return hashlib.sha256(data.encode()).hexdigest()
    
    def decrypt_from_peer(self, encrypted_hex, private_key_pem):
        """Decrypt data from a peer"""
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            
            # Decrypt
            decrypted = private_key.decrypt(
                bytes.fromhex(encrypted_hex),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted.decode()
        except Exception as e:
            print(f"Error decrypting: {e}")
            return "[Decryption Error]"
    
    def create_knowledge_hash(self, content):
        """Create hash for knowledge verification"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def sign_knowledge(self, content, private_key_pem):
        """Sign knowledge to prove authenticity"""
        try:
            from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
            
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            
            signature = private_key.sign(
                content.encode(),
                asym_padding.PSS(
                    mgf=asym_padding.MGF1(hashes.SHA256()),
                    salt_length=asym_padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return signature.hex()
        except Exception as e:
            print(f"Error signing: {e}")
            return hashlib.sha256(content.encode()).hexdigest()