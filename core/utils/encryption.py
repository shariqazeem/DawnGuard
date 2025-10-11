# core/utils/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
import secrets
from django.conf import settings

class EncryptionManager:
    def __init__(self):
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self):
        """Derive encryption key from settings"""
        password = settings.ENCRYPTION_KEY.encode()
        salt = b'cyphervault-dawn-blackbox'  # Fixed salt for consistency
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return ""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return ""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return "[Decryption Error]"
    
    def generate_key(self):
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()
    
    def hash_password(self, password: str) -> str:
        """Hash password for additional security"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_secure_token(self, length=32):
        """Generate secure random token"""
        return secrets.token_urlsafe(length)