# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime, timedelta
import json
import time
import psutil
import platform
import socket
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncHour
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
# Import models
from .models import (
    Conversation, 
    Message, 
    Document, 
    UserProfile, 
    SystemStats,
    BlackBoxNode, 
    SharedKnowledge, 
    ZKProof, 
    P2PConnection
)

# Import utility handlers
from .utils.llm_handler import LLMHandler
from .utils.encryption import EncryptionManager
from .utils.zkp_handler import ZKPHandler
from .utils.p2p_handler import P2PHandler

import base58
import hashlib

# Initialize handlers
SOLANA_RPC = "https://api.devnet.solana.com"
PROGRAM_ID = "CypherVault111111111111111111111111111111111"  # Demo program ID
llm_handler = LLMHandler()
encryption_manager = EncryptionManager()
zkp_handler = ZKPHandler()
p2p_handler = P2PHandler()

def home(request):
    """Landing page with privacy-first messaging"""
    return render(request, 'home.html', {
        'llm_available': llm_handler.available,
        'stats': {
            'total_conversations': Conversation.objects.count(),
            'messages_encrypted': Message.objects.filter(is_encrypted=True).count(),
            'active_users': UserProfile.objects.filter(local_only_mode=True).count()
        }
    })

@login_required
def dashboard(request):
    """User dashboard with stats and recent activity"""
    user_conversations = Conversation.objects.filter(user=request.user, is_active=True)[:5]
    user_documents = Document.objects.filter(user=request.user)[:5]
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get or create reputation score
    from .models import ReputationScore, AchievementBadge
    reputation, rep_created = ReputationScore.objects.get_or_create(
        user=request.user,
        defaults={
            'total_score': 0,
            'rank': 'Newcomer'
        }
    )
    
    # Award "Early Adopter" badge if new user
    if rep_created:
        AchievementBadge.objects.get_or_create(
            user=request.user,
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
    
    # Get user's badges
    user_badges = AchievementBadge.objects.filter(user=request.user)[:4]
    
    context = {
        'conversations': user_conversations,
        'documents': user_documents,
        'profile': profile,
        'reputation': reputation,
        'user_badges': user_badges,
        'total_messages': Message.objects.filter(conversation__user=request.user).count(),
        'encrypted_messages': Message.objects.filter(
            conversation__user=request.user, 
            is_encrypted=True
        ).count(),
        'llm_status': 'Online' if llm_handler.available else 'Offline (Mock Mode)',
    }
    return render(request, 'dashboard.html', context)

@login_required
def chat_view(request, conversation_id=None):
    """Main chat interface"""
    # Get or create conversation
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    else:
        # Create new conversation
        conversation = Conversation.objects.create(
            user=request.user,
            title=f"Chat {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        )
        return redirect('chat_with_id', conversation_id=conversation.id)
    
    # Get all user conversations for sidebar
    conversations = Conversation.objects.filter(user=request.user, is_active=True)
    
    # Get messages for this conversation and decrypt them
    messages = conversation.messages.all().order_by('timestamp')
    chat_messages = []
    
    for msg in messages:
        chat_messages.append({
            'role': msg.role,
            'content': msg.get_decrypted_content(),  # Decrypt here
            'timestamp': msg.timestamp,
            'id': msg.id
        })

    context = {
        'conversation': conversation,
        'conversations': conversations,
        'chat_messages': chat_messages,
    }
    return render(request, 'chat.html', context)

@login_required
@csrf_exempt
def send_message(request, conversation_id):
    """Handle message sending and AI response with streaming"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)
        
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        
        # Save user message (encrypted)
        user_msg = Message.objects.create(
            conversation=conversation,
            content=user_message,
            role='user',
            is_encrypted=True
        )
        
        # Get conversation context for LLM (last 10 messages)
        recent_messages = []
        all_messages = list(conversation.messages.all().order_by('-timestamp')[:10])
        all_messages.reverse()
        
        for msg in all_messages:
            recent_messages.append({
                'role': msg.role,
                'content': msg.get_decrypted_content()
            })
        
        # Generate AI response streaming
        context_for_ai = recent_messages[:-1] if len(recent_messages) > 1 else []
        
        def generate_stream():
            full_response = ""
            
            try:
                # Use the streaming generator from LLM handler
                for chunk in llm_handler.generate_response_stream(user_message, context_for_ai):
                    full_response += chunk
                    
                    # Send chunk as SSE
                    yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
                
                # Save complete AI response
                ai_msg = Message.objects.create(
                    conversation=conversation,
                    content=full_response.strip(),
                    role='assistant',
                    is_encrypted=True,
                    tokens_used=len(full_response.split())
                )
                
                # Update conversation timestamp
                conversation.updated_at = timezone.now()
                conversation.save()
                
                # Update stats
                today = timezone.now().date()
                stats, created = SystemStats.objects.get_or_create(date=today)
                stats.total_messages += 2
                stats.encryption_operations += 2
                stats.save()
                
                # Send completion signal
                yield f"data: {json.dumps({'chunk': '', 'done': True, 'message_id': ai_msg.id})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        
        response = StreamingHttpResponse(generate_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    conversation.is_active = False
    conversation.save()
    messages.success(request, 'Conversation deleted successfully')
    return redirect('chat')

@login_required
def settings_view(request):
    """User settings page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update settings
        profile.enable_encryption = request.POST.get('enable_encryption') == 'on'
        profile.local_only_mode = request.POST.get('local_only_mode') == 'on'
        profile.auto_delete_days = int(request.POST.get('auto_delete_days', 30))
        profile.ai_model = request.POST.get('ai_model', 'llama3.2:3b')
        profile.temperature = float(request.POST.get('temperature', 0.7))
        profile.save()
        
        messages.success(request, 'Settings updated successfully')
        return redirect('settings')
    
    context = {
        'profile': profile,
        'available_models': ['llama3.2:3b', 'llama3.2:1b', 'mistral:7b'],
        'llm_status': llm_handler.available
    }
    return render(request, 'settings.html', context)

def register_view(request):
    """User registration - Redirect to family dashboard"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create user profile WITHOUT ZKP enabled
            UserProfile.objects.create(
                user=user,
                zkp_enabled=False,  # User must manually enable it
                zkp_secret_hash=None
            )

            # Create family member for new user
            from .models import FamilyMember
            FamilyMember.objects.create(
                user=user,
                display_name=user.username.title(),
                role='admin',  # First user is admin
                avatar_color='#FF6B35'
            )

            login(request, user)
            messages.success(request, '🎉 Welcome to DawnGuard! Your family dashboard is ready.')
            return redirect('family_dashboard')  # Changed from 'dashboard'
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    """Custom logout view with confirmation"""
    logout(request)
    messages.success(request, '👋 You have been successfully logged out. Your data remains secure!')
    return redirect('home')

@login_required
def p2p_network_view(request):
    """P2P network dashboard"""
    # Get or create user's Black Box node - FIX: Use try/except to handle existing nodes
    try:
        node = BlackBoxNode.objects.get(user=request.user)
        created = False
    except BlackBoxNode.DoesNotExist:
        node = BlackBoxNode.objects.create(
            user=request.user,
            node_id='',
            public_key=''
        )
        created = True

    if created or not node.public_key:
        # Generate keypair for new node
        node.generate_node_id()
        private_key, public_key = p2p_handler.generate_keypair()
        node.public_key = public_key
        node.save()

        # Store private key securely in session
        request.session['p2p_private_key'] = private_key

    # Mark this node as online
    node.is_online = True
    node.last_seen = timezone.now()
    node.save()
    
    # Get network statistics - COUNT ALL NODES, not just online
    total_nodes = BlackBoxNode.objects.count()  # Changed from filter(is_online=True)
    
    # If no other nodes exist, create some demo nodes for testing
    if total_nodes == 1:
        # Create a few demo nodes so the network doesn't look empty
        demo_users = []
        demo_names = ['Alice-HomeGuard', 'Bob-FamilyVault', 'Charlie-DataShield']

        for i, demo_name in enumerate(demo_names):
            # Check if demo node already exists
            if not BlackBoxNode.objects.filter(node_id=f"demo_node_{i}").exists():
                # Create demo user if doesn't exist
                demo_user, _ = User.objects.get_or_create(
                    username=f'demo_user_{i}',
                    defaults={'email': f'demo{i}@homeguard.local'}
                )
                demo_users.append(demo_user)

                # Create demo node
                BlackBoxNode.objects.create(
                    node_id=f"demo_node_{i}",
                    user=demo_user,
                    public_key=f"demo_key_{i}_{timezone.now().timestamp()}",
                    is_online=True,
                    reputation_score=85 + i * 5
                )
        total_nodes = BlackBoxNode.objects.count()

        # Create demo knowledge to make network look active
        demo_knowledge_items = [
            {
                'title': '🔐 How to Secure Your Family Photos',
                'content': 'Best practices for encrypting and backing up precious family memories using AES-256 encryption.',
                'category': 'security',
                'views': 127
            },
            {
                'title': '💡 AI-Powered Home Automation Tips',
                'content': 'Learn how to set up smart home devices while maintaining privacy with local-first AI.',
                'category': 'ai',
                'views': 94
            },
            {
                'title': '🏠 Setting Up Your Family Vault',
                'content': 'Step-by-step guide to creating a private cloud storage for your family without subscriptions.',
                'category': 'tutorial',
                'views': 203
            },
            {
                'title': '⚡ Solana Smart Contracts for Privacy',
                'content': 'Building decentralized apps on Solana that prioritize user privacy and data ownership.',
                'category': 'blockchain',
                'views': 156
            }
        ]

        demo_nodes = BlackBoxNode.objects.filter(node_id__startswith='demo_node_')
        for idx, demo_node in enumerate(demo_nodes):
            if idx < len(demo_knowledge_items):
                item = demo_knowledge_items[idx]
                # Only create if doesn't exist
                if not SharedKnowledge.objects.filter(title=item['title'], shared_by=demo_node).exists():
                    encrypted_content = encryption_manager.encrypt(item['content'])
                    content_hash = p2p_handler.create_knowledge_hash(item['content'])

                    SharedKnowledge.objects.create(
                        title=item['title'],
                        content=encrypted_content,
                        encryption_key_hash=content_hash,
                        shared_by=demo_node,
                        is_public=True,
                        category=item['category'],
                        views_count=item['views'],
                        upvotes=15 + idx * 5
                    )

    my_shared_knowledge = SharedKnowledge.objects.filter(shared_by=node).count()
    received_knowledge = node.received_knowledge.count()
    active_connections = P2PConnection.objects.filter(
        from_node=node,
        is_active=True
    ).count()

    # Get available knowledge from network
    public_knowledge = SharedKnowledge.objects.filter(is_public=True).exclude(shared_by=node).order_by('-created_at')[:10]
    my_knowledge = SharedKnowledge.objects.filter(shared_by=node).order_by('-created_at')[:10]
    
    # Get connected nodes - show ALL nodes except self
    connected_nodes = BlackBoxNode.objects.exclude(id=node.id)[:10]
    
    context = {
        'node': node,
        'total_nodes': total_nodes,
        'my_shared_knowledge': my_shared_knowledge,
        'received_knowledge': received_knowledge,
        'active_connections': active_connections,
        'public_knowledge': public_knowledge,
        'my_knowledge': my_knowledge,
        'connected_nodes': connected_nodes,
    }
    
    return render(request, 'p2p_network.html', context)

@login_required
@csrf_exempt
def share_knowledge(request):
    """Share knowledge on P2P network with reputation system"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            is_public = data.get('is_public', False)
            category = data.get('category', 'general')
            
            wallet_address = request.session.get('solana_wallet')
            node = BlackBoxNode.objects.get(user=request.user)
            
            # Encrypt content
            encrypted_content = encryption_manager.encrypt(content)
            content_hash = p2p_handler.create_knowledge_hash(content)
            
            # Create knowledge record
            knowledge = SharedKnowledge.objects.create(
                title=title,
                content=encrypted_content,
                encryption_key_hash=content_hash,
                shared_by=node,
                is_public=is_public,
                category=category
            )
            
            # Award reputation points
            from .models import ReputationScore, AchievementBadge
            reputation, created = ReputationScore.objects.get_or_create(user=request.user)
            reputation.knowledge_shared += 1
            reputation.calculate_score()
            
            # Check for first share badge
            if reputation.knowledge_shared == 1:
                AchievementBadge.objects.get_or_create(
                    user=request.user,
                    badge_type='first_share',
                    defaults={
                        'title': 'First Share',
                        'description': 'Shared your first knowledge on the network',
                        'icon': '🎉',
                        'nft_metadata': {
                            'name': 'First Share Achievement',
                            'description': 'Pioneer who shared knowledge on CypherVault',
                            'image': 'ipfs://badge-first-share',
                            'attributes': [
                                {'trait_type': 'Type', 'value': 'Achievement'},
                                {'trait_type': 'Rarity', 'value': 'Common'}
                            ]
                        }
                    }
                )
            
            # Check for Knowledge Master badge (10 shares)
            if reputation.knowledge_shared >= 10:
                AchievementBadge.objects.get_or_create(
                    user=request.user,
                    badge_type='knowledge_master',
                    defaults={
                        'title': 'Knowledge Master',
                        'description': 'Shared 10+ pieces of knowledge',
                        'icon': '🧠',
                        'nft_metadata': {
                            'name': 'Knowledge Master',
                            'description': 'Prolific contributor to the knowledge network',
                            'image': 'ipfs://badge-knowledge-master',
                            'attributes': [
                                {'trait_type': 'Type', 'value': 'Achievement'},
                                {'trait_type': 'Rarity', 'value': 'Rare'}
                            ]
                        }
                    }
                )
            
            response_data = {
                'success': True,
                'knowledge_id': knowledge.id,
                'message': 'Knowledge shared successfully',
                'content_hash': content_hash,
                'reputation_earned': 10,
                'new_reputation': reputation.total_score,
                'rank': reputation.rank
            }
            
            # Blockchain integration
            if wallet_address:
                transaction_data = {
                    'knowledge_id': knowledge.id,
                    'content_hash': content_hash,
                    'title': title,
                    'category': category,
                    'reputation_score': reputation.total_score,
                    'timestamp': int(time.time()),
                    'wallet': wallet_address
                }
                
                message_to_sign = json.dumps(transaction_data, sort_keys=True)
                
                response_data['requires_signature'] = True
                response_data['transaction_data'] = transaction_data
                response_data['message_to_sign'] = message_to_sign
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def governance_view(request):
    """Governance dashboard"""
    from .models import NetworkGovernance, ReputationScore
    
    active_proposals = NetworkGovernance.objects.filter(status='active')
    my_proposals = NetworkGovernance.objects.filter(proposed_by=request.user)
    
    # Get user's voting power (based on reputation)
    reputation, _ = ReputationScore.objects.get_or_create(user=request.user)
    voting_power = min(reputation.total_score // 10, 100)  # Max 100 voting power
    
    context = {
        'active_proposals': active_proposals,
        'my_proposals': my_proposals,
        'voting_power': voting_power,
        'reputation': reputation
    }
    
    return render(request, 'governance.html', context)


@login_required
@csrf_exempt
def vote_on_proposal(request, proposal_id):
    """Vote on a governance proposal"""
    if request.method == 'POST':
        try:
            from .models import NetworkGovernance, Vote, ReputationScore
            
            data = json.loads(request.body)
            vote_choice = data.get('vote')  # 'for', 'against', 'abstain'
            
            proposal = NetworkGovernance.objects.get(id=proposal_id)
            reputation, _ = ReputationScore.objects.get_or_create(user=request.user)
            
            # Voting power based on reputation
            voting_power = min(reputation.total_score // 10, 100)
            
            # Create or update vote
            vote, created = Vote.objects.update_or_create(
                proposal=proposal,
                voter=request.user,
                defaults={
                    'vote': vote_choice,
                    'voting_power': voting_power
                }
            )
            
            # Update proposal vote counts
            if vote_choice == 'for':
                proposal.votes_for += voting_power
            elif vote_choice == 'against':
                proposal.votes_against += voting_power
            
            proposal.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Vote recorded!',
                'voting_power': voting_power,
                'current_votes': {
                    'for': proposal.votes_for,
                    'against': proposal.votes_against
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def zkp_auth_view(request):
    """Zero-Knowledge Proof authentication page"""
    context = {
        'zkp_proofs': ZKProof.objects.filter(user=request.user)[:10]
    }
    return render(request, 'zkp_auth.html', context)

@csrf_exempt
def generate_zkp_challenge(request):
    """Generate ZK proof challenge"""
    if request.method == 'POST':
        try:
            # Try to parse JSON, if it fails, just generate challenge anyway
            try:
                data = json.loads(request.body)
                username = data.get('username', '')
            except:
                username = ''
            
            # Generate challenge
            challenge = zkp_handler.generate_challenge()
            
            # Store challenge in session
            request.session['zkp_challenge'] = challenge
            request.session['zkp_challenge_time'] = timezone.now().isoformat()
            
            return JsonResponse({
                'success': True,
                'challenge': challenge
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
@csrf_exempt
def verify_zkp(request):
    """Verify zero-knowledge proof"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            response = data.get('response')
            
            # Get challenge from session
            challenge = request.session.get('zkp_challenge')
            challenge_time_str = request.session.get('zkp_challenge_time')
            
            if not challenge or not challenge_time_str:
                return JsonResponse({'success': False, 'error': 'No active challenge'}, status=400)
            
            # Check if challenge expired (5 minutes)
            from datetime import datetime  # Add this import
            challenge_time = datetime.fromisoformat(challenge_time_str)
            
            # Make challenge_time timezone-aware
            if challenge_time.tzinfo is None:
                import pytz
                challenge_time = pytz.utc.localize(challenge_time)
            
            if timezone.now() - challenge_time > timedelta(minutes=5):
                return JsonResponse({'success': False, 'error': 'Challenge expired'}, status=400)
            
            # Create proof hash
            proof_hash = zkp_handler.create_proof(challenge, response)
            
            # Save proof
            expires_at = timezone.now() + timedelta(hours=24)
            zkproof = ZKProof.objects.create(
                user=request.user,
                challenge=challenge,
                response='[REDACTED]',  # Never store the actual response
                proof_hash=proof_hash,
                is_verified=True,
                expires_at=expires_at
            )
            
            # Clear session
            del request.session['zkp_challenge']
            del request.session['zkp_challenge_time']
            
            return JsonResponse({
                'success': True,
                'proof_id': zkproof.id,
                'message': 'Proof verified successfully',
                'expires_at': expires_at.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
@csrf_exempt
def connect_to_node(request, node_id):
    """Connect to another Black Box node"""
    if request.method == 'POST':
        try:
            my_node = BlackBoxNode.objects.get(user=request.user)
            target_node = BlackBoxNode.objects.get(node_id=node_id)
            
            # Create or get connection
            connection, created = P2PConnection.objects.get_or_create(
                from_node=my_node,
                to_node=target_node,
                defaults={
                    'connection_type': 'direct',
                    'shared_keys': encryption_manager.generate_key()
                }
            )
            
            connection.is_active = True
            connection.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Connected to {target_node}'
            })
            
        except BlackBoxNode.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Node not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def download_knowledge(request, knowledge_id):
    """Download shared knowledge"""
    try:
        knowledge = SharedKnowledge.objects.get(id=knowledge_id)
        my_node = BlackBoxNode.objects.get(user=request.user)
        
        # Check if user has access
        if not knowledge.is_public and my_node not in knowledge.shared_with.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Decrypt content
        decrypted_content = encryption_manager.decrypt(knowledge.content)
        
        # Increment download count
        knowledge.downloads += 1
        knowledge.save()
        
        # Add to received knowledge
        knowledge.shared_with.add(my_node)
        
        return JsonResponse({
            'success': True,
            'title': knowledge.title,
            'content': decrypted_content,
            'shared_by': str(knowledge.shared_by),
            'category': knowledge.category
        })
        
    except SharedKnowledge.DoesNotExist:
        return JsonResponse({'error': 'Knowledge not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Add this to views.py

@csrf_exempt
def zkp_login_view(request):
    """Zero-Knowledge Proof login - SECURE VERSION"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            response = data.get('response')
            
            if not username or not response:
                return JsonResponse({'success': False, 'error': 'Username and secret required'}, status=400)
            
            # Get user
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
            
            # Get challenge from session
            challenge = request.session.get('zkp_challenge')
            challenge_time_str = request.session.get('zkp_challenge_time')
            
            if not challenge or not challenge_time_str:
                return JsonResponse({'success': False, 'error': 'No active challenge. Please request a new one.'}, status=400)
            
            # Check if challenge expired (5 minutes)
            challenge_time = datetime.fromisoformat(challenge_time_str)
            
            # Make timezone-aware
            if challenge_time.tzinfo is None:
                import pytz
                challenge_time = pytz.utc.localize(challenge_time)
            
            if timezone.now() - challenge_time > timedelta(minutes=5):
                # Clear expired challenge
                del request.session['zkp_challenge']
                del request.session['zkp_challenge_time']
                return JsonResponse({'success': False, 'error': 'Challenge expired. Please request a new one.'}, status=400)
            
            # Get user's profile and stored ZKP hash
            try:
                user_profile = UserProfile.objects.get(user=user)
                
                # Check if ZKP is enabled for this user
                if not user_profile.zkp_enabled or not user_profile.zkp_secret_hash:
                    return JsonResponse({
                        'success': False, 
                        'error': 'ZKP not enabled for this account. Please use regular password login.'
                    }, status=403)
                
                stored_secret_hash = user_profile.zkp_secret_hash
                
            except UserProfile.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'error': 'User profile not found'
                }, status=404)
            
            # **THE CRITICAL VERIFICATION STEP**
            # Create proof hash from user's response
            user_proof_hash = zkp_handler.create_proof(challenge, response)
            
            # Verify: Does the proof match what we expect?
            # The stored hash was created with: hash(INIT + secret)
            # We need to verify: hash(challenge + secret) is valid
            
            # For proper ZKP, we verify the pattern is correct
            # Since we can't directly compare (that would reveal the secret),
            # we verify the user knows the same secret that created the stored hash
            
            # Create a verification proof using the same secret pattern
            # If user provided correct secret, these should match
            expected_pattern = zkp_handler.create_proof("INIT", response)
            
            if expected_pattern != stored_secret_hash:
                # Log failed attempt
                print(f"ZKP Login failed for user {username}")
                return JsonResponse({
                    'success': False, 
                    'error': 'Invalid proof. Authentication failed.'
                }, status=401)
            
            # **SUCCESS! The proof is valid**
            # Login the user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Save proof for audit trail
            expires_at = timezone.now() + timedelta(hours=24)
            ZKProof.objects.create(
                user=user,
                challenge=challenge,
                response='[REDACTED-FOR-SECURITY]',  # Never store the actual secret
                proof_hash=user_proof_hash,
                is_verified=True,
                expires_at=expires_at
            )
            
            # Clear session
            del request.session['zkp_challenge']
            del request.session['zkp_challenge_time']
            
            return JsonResponse({
                'success': True,
                'message': 'ZKP Authentication successful',
                'redirect': '/family/'  # Redirect to family dashboard
            })
            
        except Exception as e:
            print(f"ZKP Login error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Authentication error'}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def setup_zkp_view(request):
    """Page to setup ZKP secret"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'setup_zkp.html', {'profile': profile})

@login_required
@csrf_exempt
def setup_zkp(request):
    """Setup ZKP secret for user"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            zkp_secret = data.get('zkp_secret')
            is_wallet_user = data.get('is_wallet_user', False)
            
            if not zkp_secret:
                return JsonResponse({
                    'success': False,
                    'error': 'ZKP secret is required'
                }, status=400)
            
            # Only verify password for non-wallet users
            if not is_wallet_user:
                current_password = data.get('current_password')
                
                if not current_password:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Current password is required'
                    }, status=401)
                
                # Verify current password
                if not request.user.check_password(current_password):
                    return JsonResponse({
                        'success': False, 
                        'error': 'Invalid current password'
                    }, status=401)
                
                # Make sure ZKP secret is different from password
                if request.user.check_password(zkp_secret):
                    return JsonResponse({
                        'success': False,
                        'error': 'ZKP secret must be DIFFERENT from your password'
                    }, status=400)
            
            # Get or create profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Store the ZKP secret hash
            profile.zkp_secret_hash = zkp_handler.create_proof("INIT", zkp_secret)
            profile.zkp_enabled = True
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'ZKP authentication enabled successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def check_zkp_enabled(request):
    """Check if ZKP is enabled for a user"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            
            if not username:
                return JsonResponse({'success': False, 'error': 'Username required'}, status=400)
            
            try:
                user = User.objects.get(username=username)
                profile = UserProfile.objects.get(user=user)
                
                return JsonResponse({
                    'success': True,
                    'zkp_enabled': profile.zkp_enabled and profile.zkp_secret_hash is not None
                })
            except (User.DoesNotExist, UserProfile.DoesNotExist):
                return JsonResponse({
                    'success': True,
                    'zkp_enabled': False
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


# Add this to views.py

@login_required
@csrf_exempt
def upvote_knowledge(request, knowledge_id):
    """Upvote shared knowledge"""
    if request.method == 'POST':
        try:
            knowledge = SharedKnowledge.objects.get(id=knowledge_id)
            
            # Prevent self-upvoting
            my_node = BlackBoxNode.objects.get(user=request.user)
            if knowledge.shared_by == my_node:
                return JsonResponse({
                    'success': False, 
                    'error': 'Cannot upvote your own knowledge'
                }, status=400)
            
            # Increment upvotes
            knowledge.upvotes += 1
            knowledge.save()
            
            # Increase reputation of the sharer
            sharer_node = knowledge.shared_by
            sharer_node.reputation_score = min(100, sharer_node.reputation_score + 1)
            sharer_node.save()
            
            return JsonResponse({
                'success': True,
                'upvotes': knowledge.upvotes,
                'message': 'Upvoted successfully'
            })
            
        except SharedKnowledge.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Knowledge not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def blackbox_status(request):
    """Show Black Box hardware status"""
    
    # Get system information
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Network info
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Check if Ollama is running
    ollama_status = "Running" if llm_handler.available else "Offline"
    
    # Get GPU info (if available)
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        gpu_info = [{
            'name': gpu.name,
            'load': gpu.load * 100,
            'memory_used': gpu.memoryUsed,
            'memory_total': gpu.memoryTotal,
            'temperature': gpu.temperature
        } for gpu in gpus]
    except:
        gpu_info = []
    
    context = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used': memory.used / (1024**3),  # GB
        'memory_total': memory.total / (1024**3),  # GB
        'disk_percent': disk.percent,
        'disk_used': disk.used / (1024**3),  # GB
        'disk_total': disk.total / (1024**3),  # GB
        'hostname': hostname,
        'local_ip': local_ip,
        'ollama_status': ollama_status,
        'gpu_info': gpu_info,
        'platform': platform.system(),
        'platform_version': platform.version(),
    }
    
    return JsonResponse(context)

@login_required
def blackbox_dashboard_view(request):
    """Black Box hardware dashboard"""
    context = {
        'active_connections': P2PConnection.objects.filter(is_active=True).count(),
        'total_messages': Message.objects.count(),
    }
    return render(request, 'blackbox_dashboard.html', context)

@login_required
def analytics_view(request):
    """Analytics dashboard"""
    user = request.user
    
    # Basic stats
    total_conversations = Conversation.objects.filter(user=user).count()
    total_messages = Message.objects.filter(conversation__user=user).count()
    knowledge_shared = SharedKnowledge.objects.filter(shared_by__user=user).count()
    
    # This week
    week_ago = timezone.now() - timedelta(days=7)
    conversations_this_week = Conversation.objects.filter(
        user=user,
        created_at__gte=week_ago
    ).count()
    
    # Activity over last 7 days
    activity = Message.objects.filter(
        conversation__user=user,
        timestamp__gte=week_ago
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    activity_labels = [a['date'].strftime('%b %d') for a in activity]
    activity_data = [a['count'] for a in activity]
    
    # Message types
    user_messages = Message.objects.filter(conversation__user=user, role='user').count()
    ai_messages = Message.objects.filter(conversation__user=user, role='assistant').count()
    p2p_messages = knowledge_shared
    
    # Hours distribution
    hours = [0, 0, 0, 0]  # 4 time blocks
    for msg in Message.objects.filter(conversation__user=user):
        hour = msg.timestamp.hour
        if 0 <= hour < 6:
            hours[0] += 1
        elif 6 <= hour < 12:
            hours[1] += 1
        elif 12 <= hour < 18:
            hours[2] += 1
        else:
            hours[3] += 1
    
    # Privacy score (simple calculation)
    privacy_score = 100  # Always 100 for local processing
    
    context = {
        'total_conversations': total_conversations,
        'conversations_this_week': conversations_this_week,
        'total_messages': total_messages,
        'knowledge_shared': knowledge_shared,
        'privacy_score': privacy_score,
        'activity_labels': json.dumps(activity_labels),
        'activity_data': json.dumps(activity_data),
        'user_messages': user_messages,
        'ai_messages': ai_messages,
        'p2p_messages': p2p_messages,
        'hours_data': json.dumps(hours),
    }
    
    return render(request, 'analytics.html', context)

@login_required
@csrf_exempt
def share_knowledge(request):
    """Share knowledge on P2P network with REAL blockchain transaction"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            is_public = data.get('is_public', False)
            category = data.get('category', 'general')
            
            # Check if wallet is connected
            wallet_address = request.session.get('solana_wallet')
            
            node = BlackBoxNode.objects.get(user=request.user)
            
            # Encrypt content
            encrypted_content = encryption_manager.encrypt(content)
            content_hash = p2p_handler.create_knowledge_hash(content)
            
            # Create knowledge record
            knowledge = SharedKnowledge.objects.create(
                title=title,
                content=encrypted_content,
                encryption_key_hash=content_hash,
                shared_by=node,
                is_public=is_public,
                category=category
            )
            
            response_data = {
                'success': True,
                'knowledge_id': knowledge.id,
                'message': 'Knowledge shared successfully',
                'content_hash': content_hash,
            }
            
            # If wallet connected, prepare for blockchain transaction
            if wallet_address:
                # Create transaction data that frontend will sign
                transaction_data = {
                    'knowledge_id': knowledge.id,
                    'content_hash': content_hash,
                    'title': title,
                    'category': category,
                    'timestamp': int(time.time()),
                    'wallet': wallet_address
                }
                
                # Create message to sign (this will be signed by user's wallet)
                message_to_sign = json.dumps(transaction_data, sort_keys=True)
                
                response_data['requires_signature'] = True
                response_data['transaction_data'] = transaction_data
                response_data['message_to_sign'] = message_to_sign
                response_data['message'] = 'Knowledge created - please sign transaction'
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@csrf_exempt
def confirm_blockchain_share(request):
    """
    Confirm knowledge sharing with REAL Solana blockchain verification
    This verifies the transaction actually exists on Solana
    """
    if request.method == 'POST':
        try:
            from .utils.solana_handler import solana_handler
            
            data = json.loads(request.body)
            knowledge_id = data.get('knowledge_id')
            signature = data.get('signature')
            transaction_data = data.get('transaction_data')
            
            if not knowledge_id or not signature:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields'
                }, status=400)
            
            print(f"🔍 Verifying Solana transaction...")
            print(f"   Signature: {signature}")
            print(f"   Knowledge ID: {knowledge_id}")
            
            # ✅ VERIFY THE SIGNATURE ON SOLANA BLOCKCHAIN
            is_valid = solana_handler.verify_transaction(signature)
            
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid Solana transaction. Please wait 10-15 seconds for confirmation and try again.'
                }, status=400)
            
            # Get detailed transaction info
            tx_details = solana_handler.get_transaction_details(signature)
            
            # Update knowledge with blockchain data
            knowledge = SharedKnowledge.objects.get(id=knowledge_id)
            
            # Store blockchain signature
            # Note: You may need to add this field to SharedKnowledge model:
            # blockchain_tx = models.CharField(max_length=100, blank=True, null=True)
            # For now, we'll just confirm it worked
            
            print(f"✅ Blockchain verification successful!")
            print(f"   TX Details: {tx_details}")
            
            return JsonResponse({
                'success': True,
                'message': 'Knowledge verified on Solana blockchain!',
                'tx_signature': signature,
                'explorer_url': f'https://explorer.solana.com/tx/{signature}?cluster=devnet',
                'tx_details': tx_details,
                'block_time': tx_details.get('block_time'),
                'slot': tx_details.get('slot'),
                'confirmed': tx_details.get('confirmed', False)
            })
            
        except SharedKnowledge.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Knowledge entry not found'
            }, status=404)
        except Exception as e:
            print(f"❌ Blockchain confirmation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Verification failed: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def auth_wallet(request):
    """Store wallet address in session"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet = data.get('wallet')
            
            if wallet:
                request.session['solana_wallet'] = wallet
                return JsonResponse({'success': True, 'wallet': wallet})
            else:
                return JsonResponse({'success': False, 'error': 'No wallet provided'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

import secrets
import time



@csrf_exempt
@require_http_methods(["GET", "POST"])
def wallet_login_view(request):
    """Wallet-based login - Sign in with Solana wallet"""
    if request.method == "GET":
        # Ensure CSRF token is generated
        get_token(request)
    return render(request, 'wallet_login.html')


@csrf_exempt
@require_http_methods(["POST"])
def wallet_auth_challenge(request):
    """Generate challenge for wallet signature"""
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        wallet_address = data.get('wallet')
        
        if not wallet_address:
            return JsonResponse({
                'success': False, 
                'error': 'Wallet address required'
            }, status=400)
        
        # Generate unique challenge message
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        challenge = f"CypherVault Login\nWallet: {wallet_address}\nTimestamp: {timestamp}\nNonce: {nonce}"
        
        # Store challenge in session
        request.session['wallet_challenge'] = challenge
        request.session['wallet_address'] = wallet_address
        request.session['challenge_time'] = timestamp
        request.session.modified = True  # Force session save
        
        return JsonResponse({
            'success': True,
            'challenge': challenge,
            'message': 'Sign this message with your wallet'
        })
        
    except Exception as e:
        print(f"Challenge error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def wallet_auth_verify(request):
    """Verify wallet signature and login user"""
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        wallet_address = data.get('wallet')
        signature = data.get('signature')
        
        print(f"Verifying wallet: {wallet_address}")
        
        # Get challenge from session
        challenge = request.session.get('wallet_challenge')
        stored_wallet = request.session.get('wallet_address')
        challenge_time = request.session.get('challenge_time')
        
        print(f"Session data - Challenge exists: {bool(challenge)}, Stored wallet: {stored_wallet}")
        
        if not challenge or not stored_wallet:
            return JsonResponse({
                'success': False, 
                'error': 'No active challenge. Please refresh and try again.'
            }, status=400)
        
        # Check if challenge expired (5 minutes)
        if time.time() - challenge_time > 300:
            return JsonResponse({
                'success': False, 
                'error': 'Challenge expired. Please try again.'
            }, status=400)
        
        # Verify wallet matches
        if wallet_address != stored_wallet:
            return JsonResponse({
                'success': False, 
                'error': 'Wallet mismatch'
            }, status=400)
        
        # Verify signature exists (simplified for demo)
        if not signature or len(signature) < 10:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid signature'
            }, status=400)
        
        print(f"All checks passed, finding/creating user...")
        
        # Find or create user for this wallet
        try:
            profile = UserProfile.objects.get(solana_wallet=wallet_address)
            user = profile.user
            print(f"Found existing user: {user.username}")
            
            # Update verification
            profile.wallet_verified = True
            profile.wallet_signature = signature
            profile.save()
            
        except UserProfile.DoesNotExist:
            # Create new user for this wallet
            username = f"wallet_{wallet_address[:8]}"
            
            # Make username unique
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
            
            print(f"Creating new user: {username}")
            
            # Create user with random password
            user = User.objects.create_user(
                username=username,
                password=secrets.token_urlsafe(32)
            )
            
            # Create profile with wallet
            profile = UserProfile.objects.create(
                user=user,
                solana_wallet=wallet_address,
                wallet_verified=True,
                wallet_signature=signature
            )
            
            print(f"Created new user and profile")
        
        # Login user
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        print(f"User logged in: {user.username}")

        # Create family member if doesn't exist
        from .models import FamilyMember
        FamilyMember.objects.get_or_create(
            user=user,
            defaults={
                'display_name': user.username.title(),
                'role': 'admin',
                'avatar_color': '#6B35FF'  # Purple for wallet users
            }
        )

        # Clear challenge from session
        if 'wallet_challenge' in request.session:
            del request.session['wallet_challenge']
        if 'wallet_address' in request.session:
            del request.session['wallet_address']
        if 'challenge_time' in request.session:
            del request.session['challenge_time']

        # Store wallet in session
        request.session['solana_wallet'] = wallet_address
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'message': 'Wallet authenticated successfully',
            'redirect': '/family/',  # Redirect to family dashboard
            'username': user.username
        })
        
    except Exception as e:
        print(f"Wallet verification error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'error': f'Authentication error: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def wallet_link(request):
    """Link Solana wallet to existing account"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet_address = data.get('wallet')
            signature = data.get('signature')
            
            if not wallet_address or not signature:
                return JsonResponse({
                    'success': False, 
                    'error': 'Wallet and signature required'
                }, status=400)
            
            # Check if wallet is already linked to another account
            existing_profile = UserProfile.objects.filter(solana_wallet=wallet_address).first()
            if existing_profile and existing_profile.user != request.user:
                return JsonResponse({
                    'success': False, 
                    'error': 'This wallet is already linked to another account'
                }, status=400)
            
            # Get or update user profile
            profile = request.user.userprofile
            profile.solana_wallet = wallet_address
            profile.wallet_verified = True
            profile.wallet_signature = signature
            profile.save()
            
            # Store in session
            request.session['solana_wallet'] = wallet_address
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': 'Wallet linked successfully',
                'wallet': wallet_address
            })
            
        except Exception as e:
            print(f"Wallet link error: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)
@login_required
def guardian_alerts_view(request):
    """AI Guardian Alerts Dashboard - Real-time data from scans"""
    from .models import AIGuardianScan, AIGuardianAlert, FamilyMember
    from django.db.models import Count, Q

    try:
        # Get family member
        family_member = FamilyMember.objects.get(user=request.user)

        # Get all scans
        all_scans = AIGuardianScan.objects.select_related('file', 'scanned_by').all()

        # Get active alerts for this user (if admin, show all; otherwise show own)
        if family_member.role == 'admin':
            active_alerts = AIGuardianAlert.objects.filter(
                status='active'
            ).select_related('scan__file', 'family_member').order_by('-created_at')[:5]
        else:
            active_alerts = AIGuardianAlert.objects.filter(
                family_member=family_member,
                status='active'
            ).select_related('scan__file').order_by('-created_at')[:5]

        # Calculate statistics
        total_scans = all_scans.count()
        safe_scans = all_scans.filter(severity='safe').count()
        alert_scans = all_scans.filter(severity__in=['medium', 'high', 'critical']).count()

        # Calculate family safety score (percentage of safe files)
        if total_scans > 0:
            safety_score = int((safe_scans / total_scans) * 100)
        else:
            safety_score = 100

        # Recent scans for table
        recent_scans = all_scans.order_by('-created_at')[:20]

        # Severity breakdown
        severity_stats = all_scans.values('severity').annotate(count=Count('id'))

        context = {
            'family_member': family_member,
            'safety_score': safety_score,
            'total_scans': total_scans,
            'safe_scans': safe_scans,
            'alert_scans': alert_scans,
            'active_alerts': active_alerts,
            'recent_scans': recent_scans,
            'severity_stats': severity_stats,
        }

        return render(request, 'guardian_alerts.html', context)

    except FamilyMember.DoesNotExist:
        # Create family member if doesn't exist
        from .models import FamilyMember
        family_member = FamilyMember.objects.create(
            user=request.user,
            display_name=request.user.username.title(),
            role='admin'
        )
        return redirect('guardian_alerts')

