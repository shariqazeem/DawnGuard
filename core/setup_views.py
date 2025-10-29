# core/setup_views.py - One-Time Setup Flow

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import FamilyMember, UserProfile
import json
import secrets
import string
import hashlib

def check_setup_required(request):
    """Check if setup is required (no users exist)"""
    if User.objects.count() == 0:
        return True
    return False

def setup_wizard(request):
    """
    One-time setup wizard view
    Only accessible if no users exist yet
    """
    # Check if setup already done
    if not check_setup_required(request):
        # Setup already complete, redirect to login
        return redirect('login')

    return render(request, 'setup_wizard.html')


@csrf_exempt
def complete_setup(request):
    """
    Complete the initial setup
    Creates admin user and family members with auto-generated credentials
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    # Check if setup already done
    if not check_setup_required(request):
        return JsonResponse({'success': False, 'error': 'Setup already completed'}, status=400)

    try:
        data = json.loads(request.body)
        admin_data = data.get('admin', {})
        family_members_data = data.get('family_members', [])

        # Validate admin data
        if not admin_data.get('display_name'):
            return JsonResponse({'success': False, 'error': 'Display name required'}, status=400)

        auth_type = admin_data.get('auth_type', 'password')

        # Create admin user based on auth type
        if auth_type == 'wallet':
            # Wallet authentication
            wallet_address = admin_data.get('wallet_address')
            if not wallet_address:
                return JsonResponse({'success': False, 'error': 'Wallet address required'}, status=400)

            # Create user with wallet as username
            username = f"wallet_{wallet_address[:8]}"
            password = generate_secure_password()

            admin_user = User.objects.create_user(
                username=username,
                password=password
            )

            # Create profile with wallet
            UserProfile.objects.create(
                user=admin_user,
                solana_wallet=wallet_address,
                zkp_enabled=False
            )

        elif auth_type == 'zkp':
            # Zero-Knowledge Proof authentication
            zkp_secret = admin_data.get('zkp_secret')
            if not zkp_secret:
                return JsonResponse({'success': False, 'error': 'ZKP secret required'}, status=400)

            # Generate username
            username = admin_data.get('display_name').lower().replace(' ', '_')
            # Add random suffix if username exists
            if User.objects.filter(username=username).exists():
                username = f"{username}_{secrets.token_hex(3)}"

            # Generate secure password (won't be used for login, just for account)
            password = generate_secure_password()

            admin_user = User.objects.create_user(
                username=username,
                password=password
            )

            # Hash the ZKP secret
            secret_hash = hashlib.sha256(zkp_secret.encode()).hexdigest()

            # Create profile with ZKP enabled
            UserProfile.objects.create(
                user=admin_user,
                zkp_enabled=True,
                zkp_secret_hash=secret_hash
            )

        else:
            # Traditional password authentication
            username = admin_data.get('username')
            password = admin_data.get('password')

            if not username or not password:
                return JsonResponse({'success': False, 'error': 'Username and password required'}, status=400)

            admin_user = User.objects.create_user(
                username=username,
                password=password
            )

            # Create basic profile
            UserProfile.objects.create(
                user=admin_user,
                zkp_enabled=False
            )

        # Create FamilyMember for admin
        admin_member = FamilyMember.objects.create(
            user=admin_user,
            display_name=admin_data.get('display_name'),
            role='admin',
            avatar_color=admin_data.get('color', '#FF6B35')
        )

        # Create family members with auto-generated credentials
        created_members = []
        for member_data in family_members_data:
            member_username = member_data.get('username')
            member_password = member_data.get('password')
            member_name = member_data.get('name')
            member_role = member_data.get('role', 'member')
            member_color = member_data.get('color', '#6B35FF')

            # Create user for family member
            member_user = User.objects.create_user(
                username=member_username,
                password=member_password
            )

            # Create profile
            UserProfile.objects.create(
                user=member_user,
                zkp_enabled=False
            )

            # Create FamilyMember
            family_member = FamilyMember.objects.create(
                user=member_user,
                display_name=member_name,
                role=member_role,
                avatar_color=member_color
            )

            created_members.append({
                'username': member_username,
                'password': member_password,
                'name': member_name
            })

        # Log in the admin user
        login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')

        return JsonResponse({
            'success': True,
            'message': 'Setup completed successfully!',
            'admin_username': admin_user.username,
            'family_members': created_members
        })

    except Exception as e:
        print(f"Setup error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Setup failed: {str(e)}'
        }, status=500)


def generate_secure_password(length=16):
    """Generate a cryptographically secure random password"""
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def get_setup_status(request):
    """
    API endpoint to check if setup is required
    """
    return JsonResponse({
        'setup_required': check_setup_required(request),
        'user_count': User.objects.count()
    })
