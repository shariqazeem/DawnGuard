from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import ReputationScore, AchievementBadge

class Command(BaseCommand):
    help = 'Award early adopter badges to all existing users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        
        for user in users:
            # Create reputation if not exists
            reputation, created = ReputationScore.objects.get_or_create(
                user=user,
                defaults={
                    'total_score': 0,
                    'rank': 'Newcomer'
                }
            )
            
            # Award early adopter badge
            badge, badge_created = AchievementBadge.objects.get_or_create(
                user=user,
                badge_type='early_adopter',
                defaults={
                    'title': 'Early Adopter',
                    'description': 'Joined CypherVault in the early days',
                    'icon': '🚀',
                    'nft_metadata': {
                        'name': 'Early Adopter Badge',
                        'description': 'Early member of the CypherVault network',
                        'image': 'ipfs://badge-early-adopter',
                        'attributes': [
                            {'trait_type': 'Type', 'value': 'Achievement'},
                            {'trait_type': 'Rarity', 'value': 'Limited'}
                        ]
                    }
                }
            )
            
            if badge_created:
                self.stdout.write(self.style.SUCCESS(f'✅ Awarded Early Adopter badge to {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ {user.username} already has Early Adopter badge'))
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Processed {users.count()} users!'))