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


# ============================================================
# FAMILY VAULT - Private Cloud Storage (Dropbox Replacement)
# ============================================================

class FamilyMember(models.Model):
    """
    Family members who can access the vault
    Each member has their own encrypted space
    """
    ROLE_CHOICES = [
        ('admin', 'Parent/Admin'),
        ('member', 'Family Member'),
        ('child', 'Child (Restricted)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='family_member')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    display_name = models.CharField(max_length=100)  # "Mom", "Dad", "Sarah"
    avatar_color = models.CharField(max_length=7, default='#FF6B35')  # Hex color

    # Storage quota
    storage_quota_gb = models.IntegerField(default=50)  # GB per member

    # Parental controls (for child accounts)
    ai_chat_enabled = models.BooleanField(default=True)
    file_upload_enabled = models.BooleanField(default=True)
    can_share_files = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.display_name} ({self.user.username})"

    def get_storage_used_mb(self):
        """Calculate total storage used by this member"""
        total_bytes = VaultFile.objects.filter(owner=self).aggregate(
            total=models.Sum('file_size')
        )['total'] or 0
        return total_bytes / (1024 * 1024)  # Convert to MB

    def get_storage_used_gb(self):
        return self.get_storage_used_mb() / 1024

    def get_storage_percentage(self):
        used_gb = self.get_storage_used_gb()
        return min((used_gb / self.storage_quota_gb) * 100, 100)


class VaultFolder(models.Model):
    """
    Folders in the vault (like Dropbox folders)
    """
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(FamilyMember, on_delete=models.CASCADE, related_name='folders')
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')

    # Sharing
    shared_with = models.ManyToManyField(FamilyMember, blank=True, related_name='shared_folders')
    is_public_to_family = models.BooleanField(default=False)  # All family can see

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'owner', 'parent_folder']

    def __str__(self):
        if self.parent_folder:
            return f"{self.parent_folder}/{self.name}"
        return self.name

    def get_path(self):
        """Get full folder path"""
        if self.parent_folder:
            return f"{self.parent_folder.get_path()}/{self.name}"
        return self.name


class VaultFile(models.Model):
    """
    Files stored in the vault
    Encrypted at rest, AI-searchable
    """
    FILE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('archive', 'Archive'),
        ('other', 'Other'),
    ]

    # Basic info
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='vault_files/%Y/%m/%d/')

    # Organization
    folder = models.ForeignKey(VaultFolder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    owner = models.ForeignKey(FamilyMember, on_delete=models.CASCADE, related_name='files')

    # File metadata
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.BigIntegerField(default=0)  # Bytes
    mime_type = models.CharField(max_length=100, blank=True)

    # Encryption
    is_encrypted = models.BooleanField(default=True)
    encryption_key_hash = models.CharField(max_length=64, blank=True)

    # AI features
    ai_description = models.TextField(blank=True)  # AI-generated description
    ai_tags = models.JSONField(default=list, blank=True)  # ["vacation", "beach", "2024"]
    ai_processed = models.BooleanField(default=False)

    # Image-specific (for photos)
    thumbnail = models.ImageField(upload_to='vault_thumbnails/', null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)

    # Sharing
    shared_with = models.ManyToManyField(FamilyMember, blank=True, related_name='shared_files')
    is_public_to_family = models.BooleanField(default=False)

    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    download_count = models.IntegerField(default=0)

    # Blockchain proof (optional)
    blockchain_hash = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['owner', 'file_type']),
            models.Index(fields=['owner', 'uploaded_at']),
        ]

    def __str__(self):
        return self.name

    def get_file_size_display(self):
        """Human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_icon(self):
        """Get Bootstrap icon based on file type"""
        icons = {
            'document': 'bi-file-earmark-text',
            'image': 'bi-file-earmark-image',
            'video': 'bi-file-earmark-play',
            'audio': 'bi-file-earmark-music',
            'archive': 'bi-file-earmark-zip',
            'other': 'bi-file-earmark',
        }
        return icons.get(self.file_type, 'bi-file-earmark')

    def detect_file_type(self):
        """Auto-detect file type from mime type"""
        if not self.mime_type:
            return 'other'

        if self.mime_type.startswith('image/'):
            return 'image'
        elif self.mime_type.startswith('video/'):
            return 'video'
        elif self.mime_type.startswith('audio/'):
            return 'audio'
        elif self.mime_type in ['application/pdf', 'application/msword',
                                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                 'text/plain']:
            return 'document'
        elif self.mime_type in ['application/zip', 'application/x-rar',
                                 'application/x-7z-compressed']:
            return 'archive'
        return 'other'


class FileShareLink(models.Model):
    """
    Shareable links for files (like Dropbox share links)
    Can be sent to anyone, even outside the family
    """
    file = models.ForeignKey(VaultFile, on_delete=models.CASCADE, related_name='share_links')
    created_by = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)

    # Link details
    share_token = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=128, blank=True)  # Optional password

    # Permissions
    allow_download = models.BooleanField(default=True)
    allow_preview = models.BooleanField(default=True)
    max_downloads = models.IntegerField(null=True, blank=True)  # Limit downloads

    # Expiry
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Stats
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Share link for {self.file.name}"

    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def can_download(self):
        if not self.is_active or self.is_expired():
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return self.allow_download


class VaultActivity(models.Model):
    """
    Activity log for the vault (who uploaded/downloaded what)
    Helps parents monitor kids' activity
    """
    ACTION_CHOICES = [
        ('upload', 'Uploaded'),
        ('download', 'Downloaded'),
        ('delete', 'Deleted'),
        ('share', 'Shared'),
        ('view', 'Viewed'),
    ]

    member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    file = models.ForeignKey(VaultFile, on_delete=models.SET_NULL, null=True, blank=True)
    folder = models.ForeignKey(VaultFolder, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Vault activities'

    def __str__(self):
        return f"{self.member.display_name} {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# ============================================================
# AI GUARDIAN - Content Moderation & Safety
# ============================================================

class AIGuardianScan(models.Model):
    """
    AI Guardian scan results for uploaded files
    Detects personal data, inappropriate content, privacy risks
    """
    SEVERITY_CHOICES = [
        ('safe', 'Safe'),
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scanning', 'Scanning'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]

    # File being scanned
    file = models.OneToOneField(VaultFile, on_delete=models.CASCADE, related_name='guardian_scan')

    # Scan info
    scanned_by = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Results
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='safe')
    risk_score = models.IntegerField(default=0)  # 0-100

    # Detected issues (JSON)
    detected_patterns = models.JSONField(default=list)  # ["SSN", "Credit Card"]
    detected_keywords = models.JSONField(default=list)  # ["password", "confidential"]
    risk_categories = models.JSONField(default=list)  # ["personal_data", "privacy"]

    # AI analysis
    ai_summary = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Parent notification
    parent_notified = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Scan: {self.file.name} - {self.severity}"

    def is_alert(self):
        """Check if this scan requires an alert"""
        return self.severity in ['medium', 'high', 'critical']

    def get_severity_color(self):
        """Get color for severity level"""
        colors = {
            'safe': 'success',
            'low': 'info',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'danger',
        }
        return colors.get(self.severity, 'secondary')

    def get_severity_icon(self):
        """Get icon for severity level"""
        icons = {
            'safe': '✅',
            'low': 'ℹ️',
            'medium': '⚠️',
            'high': '🚨',
            'critical': '🔴',
        }
        return icons.get(self.severity, '❓')


class AIGuardianAlert(models.Model):
    """
    Active alerts from AI Guardian that require parent attention
    """
    ALERT_TYPE_CHOICES = [
        ('personal_data', 'Personal Data Detected'),
        ('inappropriate', 'Inappropriate Content'),
        ('privacy', 'Privacy Concern'),
        ('security', 'Security Risk'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    # Related scan
    scan = models.ForeignKey(AIGuardianScan, on_delete=models.CASCADE, related_name='alerts')

    # Alert details
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Who needs to see it
    family_member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE, related_name='guardian_alerts')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Actions taken
    action_taken = models.TextField(blank=True)
    resolved_by = models.ForeignKey(FamilyMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.alert_type} - {self.title}"

    def get_alert_icon(self):
        """Get icon for alert type"""
        icons = {
            'personal_data': '🔐',
            'inappropriate': '⚠️',
            'privacy': '🔒',
            'security': '🛡️',
            'other': 'ℹ️',
        }
        return icons.get(self.alert_type, 'ℹ️')


# ============================================================
# ENCRYPTED FAMILY MEMORY - Digital Journal System
# ============================================================

class FamilyJournalEntry(models.Model):
    """
    Daily journal entries written by family members
    Encrypted locally, used for weekly AI summaries
    """
    MOOD_CHOICES = [
        ('amazing', '😄 Amazing'),
        ('happy', '😊 Happy'),
        ('okay', '😐 Okay'),
        ('sad', '😢 Sad'),
        ('stressed', '😰 Stressed'),
    ]

    # Who wrote it
    author = models.ForeignKey(FamilyMember, on_delete=models.CASCADE, related_name='journal_entries')

    # Entry content (encrypted)
    title = models.CharField(max_length=200)
    content = models.TextField()  # Will be encrypted
    encrypted_content = models.TextField(blank=True)

    # Metadata
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='okay')
    tags = models.JSONField(default=list, blank=True)  # ["school", "sports", "family"]

    # Privacy
    is_private = models.BooleanField(default=False)  # Only author can see
    shared_with = models.ManyToManyField(FamilyMember, blank=True, related_name='shared_journal_entries')

    # Timestamps
    entry_date = models.DateField()  # Date this entry is about
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # AI processing
    ai_processed = models.BooleanField(default=False)
    sentiment_score = models.FloatField(null=True, blank=True)  # -1.0 to 1.0

    class Meta:
        ordering = ['-entry_date', '-created_at']
        verbose_name_plural = 'Family journal entries'
        indexes = [
            models.Index(fields=['author', 'entry_date']),
        ]

    def __str__(self):
        return f"{self.author.display_name} - {self.entry_date}: {self.title}"

    def get_mood_emoji(self):
        """Get emoji for mood"""
        mood_map = {
            'amazing': '😄',
            'happy': '😊',
            'okay': '😐',
            'sad': '😢',
            'stressed': '😰',
        }
        return mood_map.get(self.mood, '😐')


class FamilyWeeklySummary(models.Model):
    """
    AI-generated weekly summaries of family journal entries
    "Your week in review" - emotional, beautiful, searchable
    """
    # Time period
    week_start = models.DateField()  # Monday of the week
    week_end = models.DateField()    # Sunday of the week
    year = models.IntegerField()
    week_number = models.IntegerField()  # Week 1-52

    # AI-generated content
    ai_summary = models.TextField()  # Beautiful prose summary
    highlights = models.JSONField(default=list)  # ["Emma got an A", "Family pizza night"]
    overall_mood = models.CharField(max_length=20, default='happy')

    # Stats
    total_entries = models.IntegerField(default=0)
    participating_members = models.JSONField(default=list)  # ["Mom", "Emma", "Dad"]

    # Related entries
    entries = models.ManyToManyField(FamilyJournalEntry, blank=True, related_name='weekly_summaries')

    # Encryption (summary is encrypted too)
    encrypted_summary = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(FamilyMember, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-week_start']
        unique_together = ['year', 'week_number']
        verbose_name_plural = 'Family weekly summaries'

    def __str__(self):
        return f"Week {self.week_number}, {self.year} ({self.week_start} to {self.week_end})"

    def get_week_label(self):
        """Get human-readable week label"""
        return f"Week of {self.week_start.strftime('%B %d, %Y')}"

    def get_mood_emoji(self):
        """Get emoji for overall week mood"""
        mood_map = {
            'amazing': '😄',
            'happy': '😊',
            'okay': '😐',
            'sad': '😢',
            'stressed': '😰',
        }
        return mood_map.get(self.overall_mood, '😊')


class FamilyMemoryMilestone(models.Model):
    """
    Important family milestones/memories
    Auto-detected from journals or manually added
    """
    MILESTONE_TYPES = [
        ('achievement', '🏆 Achievement'),
        ('birthday', '🎂 Birthday'),
        ('trip', '✈️ Trip/Vacation'),
        ('special', '⭐ Special Moment'),
        ('first', '🎉 First Time'),
        ('other', '💫 Other'),
    ]

    # Who it's about
    family_members = models.ManyToManyField(FamilyMember, related_name='milestones')

    # Milestone details
    title = models.CharField(max_length=200)
    description = models.TextField()
    milestone_type = models.CharField(max_length=20, choices=MILESTONE_TYPES, default='special')

    # When
    milestone_date = models.DateField()

    # Related content
    journal_entries = models.ManyToManyField(FamilyJournalEntry, blank=True, related_name='milestones')
    photos = models.JSONField(default=list, blank=True)  # File paths/URLs

    # Auto-detection
    auto_detected = models.BooleanField(default=False)
    ai_confidence = models.FloatField(default=0.0)  # 0.0-1.0

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-milestone_date']

    def __str__(self):
        return f"{self.get_milestone_type_display()}: {self.title}"

    def get_type_emoji(self):
        """Get emoji for milestone type"""
        type_map = {
            'achievement': '🏆',
            'birthday': '🎂',
            'trip': '✈️',
            'special': '⭐',
            'first': '🎉',
            'other': '💫',
        }
        return type_map.get(self.milestone_type, '💫')