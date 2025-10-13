# core/management/commands/setup_zkp.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
from core.utils.zkp_handler import ZKPHandler
import hashlib

class Command(BaseCommand):
    help = 'Setup ZKP for existing users'

    def handle(self, *args, **kwargs):
        zkp_handler = ZKPHandler()
        
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            if not profile.zkp_secret_hash:
                # Use their current password hash as the base
                # In reality, they'd set up a separate secret
                secret_base = f"{user.username}_zkp_secret"
                profile.zkp_secret_hash = zkp_handler.create_proof("INIT", secret_base)
                profile.zkp_enabled = True
                profile.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'ZKP enabled for user: {user.username}')
                )