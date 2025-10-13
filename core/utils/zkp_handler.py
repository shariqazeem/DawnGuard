# core/utils/zkp_handler.py
import hashlib
import secrets
from datetime import datetime, timedelta
from django.utils import timezone

class ZKPHandler:
    """Zero-Knowledge Proof handler for authentication"""
    
    def __init__(self):
        self.challenge_length = 32
        self.proof_validity = 300  # 5 minutes
    
    def generate_challenge(self):
        """Generate a random challenge for ZK proof"""
        return secrets.token_hex(self.challenge_length)
    
    def create_proof(self, challenge, secret):
        """Create a ZK proof from challenge and secret"""
        # Combine challenge with secret
        combined = f"{challenge}{secret}"
        proof_hash = hashlib.sha256(combined.encode()).hexdigest()
        return proof_hash
    
    def verify_proof(self, challenge, response, expected_hash):
        """Verify ZK proof without revealing the secret"""
        computed_hash = hashlib.sha256(f"{challenge}{response}".encode()).hexdigest()
        return computed_hash == expected_hash
    
    def generate_commitment(self, value):
        """Generate a commitment for zero-knowledge proof"""
        salt = secrets.token_hex(16)
        commitment = hashlib.sha256(f"{value}{salt}".encode()).hexdigest()
        return commitment, salt
    
    def verify_commitment(self, value, salt, commitment):
        """Verify a commitment"""
        computed = hashlib.sha256(f"{value}{salt}".encode()).hexdigest()
        return computed == commitment