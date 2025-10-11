# core/models.py - REPLACE the entire file with this:
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cryptography.fernet import Fernet
import base64
import json
from django.conf import settings

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