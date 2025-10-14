# core/models.py - REPLACE the entire file with this:
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cryptography.fernet import Fernet
import base64
import json
from django.conf import settings
import hashlib
import secrets

def get_cipher():
    """Get or create Fernet cipher for encryption"""
    key = settings.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0')
    return Fernet(base64.urlsafe_b64encode(key))

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_encrypted = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def get_message_count(self):
        return self.messages.count()

class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    encrypted_content = models.TextField(blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(default=0)
    is_encrypted = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def save(self, *args, **kwargs):
        if self.is_encrypted and self.content:
            cipher = get_cipher()
            self.encrypted_content = cipher.encrypt(self.content.encode()).decode()
            self.content = ""  # Clear plaintext
        super().save(*args, **kwargs)
    
    def get_decrypted_content(self):
        if self.is_encrypted and self.encrypted_content:
            try:
                cipher = get_cipher()
                return cipher.decrypt(self.encrypted_content.encode()).decode()
            except:
                return "[Decryption Error]"
        return self.content

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/')
    encrypted_content = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    file_size = models.IntegerField(default=0)
    file_type = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    enable_encryption = models.BooleanField(default=True)
    local_only_mode = models.BooleanField(default=True)
    auto_delete_days = models.IntegerField(default=30)
    ai_model = models.CharField(max_length=50, default="llama3.2:3b")
    max_tokens = models.IntegerField(default=2048)
    temperature = models.FloatField(default=0.7)
    created_at = models.DateTimeField(auto_now_add=True)
    solana_wallet = models.CharField(max_length=100, blank=True, null=True, unique=True)
    wallet_verified = models.BooleanField(default=False)
    wallet_signature = models.TextField(blank=True, null=True)
        # Zero-Knowledge Proof
    zkp_secret_hash = models.CharField(max_length=64, blank=True, null=True)
    zkp_enabled = models.BooleanField(default=False)
    def __str__(self):
        return f"Profile: {self.user.username}"



class SystemStats(models.Model):
    date = models.DateField(unique=True)
    total_messages = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    encryption_operations = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats for {self.date}"

class BlackBoxNode(models.Model):
    """Represents a Black Box node in the P2P network"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='blackbox_node')
    node_id = models.CharField(max_length=64, unique=True)  # SHA256 hash
    public_key = models.TextField()  # For P2P encryption
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.IntegerField(default=8000)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    reputation_score = models.IntegerField(default=100)  # For trust
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"BlackBox-{self.node_id[:8]}"
    
    def generate_node_id(self):
        """Generate unique node ID"""
        data = f"{self.user.username}{secrets.token_hex(16)}"
        self.node_id = hashlib.sha256(data.encode()).hexdigest()
        return self.node_id

class SharedKnowledge(models.Model):
    """P2P shared knowledge between Black Boxes"""
    title = models.CharField(max_length=200)
    content = models.TextField()  # Encrypted content
    encryption_key_hash = models.CharField(max_length=64)  # Hash of the key
    
    shared_by = models.ForeignKey(BlackBoxNode, on_delete=models.CASCADE, related_name='shared_knowledge')
    shared_with = models.ManyToManyField(BlackBoxNode, related_name='received_knowledge', blank=True)
    
    is_public = models.BooleanField(default=False)  # Public in the P2P network
    category = models.CharField(max_length=50, default='general')
    
    downloads = models.IntegerField(default=0)
    upvotes = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class ZKProof(models.Model):
    """Zero-Knowledge Proof for authentication"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='zk_proofs')
    challenge = models.CharField(max_length=128)  # Random challenge
    response = models.CharField(max_length=256)  # User's response
    proof_hash = models.CharField(max_length=64)  # Hash of the proof
    
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
    
    def verify_proof(self, user_response):
        """Verify ZK proof without revealing the secret"""
        expected = hashlib.sha256(f"{self.challenge}{user_response}".encode()).hexdigest()
        return expected == self.proof_hash

class P2PConnection(models.Model):
    """Track P2P connections between Black Boxes"""
    from_node = models.ForeignKey(BlackBoxNode, on_delete=models.CASCADE, related_name='outgoing_connections')
    to_node = models.ForeignKey(BlackBoxNode, on_delete=models.CASCADE, related_name='incoming_connections')  # Fixed: models.CASCADE instead of CASCADE
    
    connection_type = models.CharField(max_length=20, choices=[
        ('direct', 'Direct'),
        ('relay', 'Relay'),
        ('mesh', 'Mesh')
    ], default='direct')
    
    is_active = models.BooleanField(default=True)
    shared_keys = models.TextField()  # Encrypted shared session keys
    
    established_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['from_node', 'to_node']
    
    def __str__(self):
        return f"{self.from_node} -> {self.to_node}"

class ReputationScore(models.Model):
    """On-chain verifiable reputation"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reputation')
    
    # Contribution metrics
    knowledge_shared = models.IntegerField(default=0)
    knowledge_downloaded = models.IntegerField(default=0)
    upvotes_received = models.IntegerField(default=0)
    helpful_votes = models.IntegerField(default=0)
    
    # Reputation score (0-1000)
    total_score = models.IntegerField(default=0)
    rank = models.CharField(max_length=50, default='Newcomer')
    
    # Blockchain verification
    last_blockchain_sync = models.DateTimeField(null=True, blank=True)
    blockchain_proof = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_score']
    
    def calculate_score(self):
        """Calculate reputation score from contributions"""
        score = (
            (self.knowledge_shared * 10) +
            (self.knowledge_downloaded * 2) +
            (self.upvotes_received * 5) +
            (self.helpful_votes * 3)
        )
        self.total_score = score
        
        # Determine rank
        if score >= 500:
            self.rank = 'Legend'
        elif score >= 300:
            self.rank = 'Expert'
        elif score >= 150:
            self.rank = 'Contributor'
        elif score >= 50:
            self.rank = 'Active'
        else:
            self.rank = 'Newcomer'
        
        self.save()
        return score
    
    def __str__(self):
        return f"{self.user.username} - {self.rank} ({self.total_score})"


class AchievementBadge(models.Model):
    """NFT-style achievement badges"""
    BADGE_TYPES = [
        ('first_share', 'First Share'),
        ('knowledge_master', 'Knowledge Master'),
        ('helpful_peer', 'Helpful Peer'),
        ('early_adopter', 'Early Adopter'),
        ('blockchain_verified', 'Blockchain Verified'),
        ('privacy_advocate', 'Privacy Advocate'),
        ('zkp_user', 'ZKP User'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🏆')  # Emoji icon
    
    # NFT metadata (ready for on-chain minting)
    nft_metadata = models.JSONField(default=dict)
    blockchain_tx = models.CharField(max_length=100, blank=True, null=True)
    minted_on_chain = models.BooleanField(default=False)
    
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'badge_type']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class NetworkGovernance(models.Model):
    """Decentralized governance proposals"""
    PROPOSAL_TYPES = [
        ('feature', 'Feature Request'),
        ('parameter', 'Network Parameter'),
        ('moderation', 'Content Moderation'),
        ('upgrade', 'Protocol Upgrade'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('passed', 'Passed'),
        ('rejected', 'Rejected'),
        ('executed', 'Executed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    proposal_type = models.CharField(max_length=50, choices=PROPOSAL_TYPES)
    
    proposed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposals')
    
    # Voting
    votes_for = models.IntegerField(default=0)
    votes_against = models.IntegerField(default=0)
    voters = models.ManyToManyField(User, through='Vote', related_name='voted_proposals')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Blockchain integration
    blockchain_proposal_id = models.CharField(max_length=100, blank=True, null=True)
    on_chain = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    voting_ends_at = models.DateTimeField()
    executed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.status}"


class Vote(models.Model):
    """Individual votes on governance proposals"""
    VOTE_CHOICES = [
        ('for', 'For'),
        ('against', 'Against'),
        ('abstain', 'Abstain'),
    ]
    
    proposal = models.ForeignKey(NetworkGovernance, on_delete=models.CASCADE, related_name='proposal_votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    
    # Weight based on reputation
    voting_power = models.IntegerField(default=1)
    
    # Blockchain verification
    blockchain_signature = models.TextField(blank=True, null=True)
    
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['proposal', 'voter']
    
    def __str__(self):
        return f"{self.voter.username} - {self.vote} on {self.proposal.title}"