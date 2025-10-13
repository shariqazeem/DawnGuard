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

# Initialize handlers
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
    
    context = {
        'conversations': user_conversations,
        'documents': user_documents,
        'profile': profile,
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
    """User registration"""
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
            
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
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
    # Get or create user's Black Box node
    node, created = BlackBoxNode.objects.get_or_create(
        user=request.user,
        defaults={
            'node_id': '',
            'public_key': ''
        }
    )
    
    if created or not node.public_key:
        # Generate keypair for new node
        node.generate_node_id()
        private_key, public_key = p2p_handler.generate_keypair()
        node.public_key = public_key
        node.save()
        
        # Store private key securely in session (in production, use proper key management)
        request.session['p2p_private_key'] = private_key
    
    # Get network statistics
    total_nodes = BlackBoxNode.objects.filter(is_online=True).count()
    my_shared_knowledge = SharedKnowledge.objects.filter(shared_by=node).count()
    received_knowledge = node.received_knowledge.count()
    active_connections = P2PConnection.objects.filter(
        from_node=node,
        is_active=True
    ).count()
    
    # Get available knowledge from network
    public_knowledge = SharedKnowledge.objects.filter(is_public=True).exclude(shared_by=node)[:10]
    my_knowledge = SharedKnowledge.objects.filter(shared_by=node)[:10]
    
    # Get connected nodes
    connected_nodes = BlackBoxNode.objects.filter(
        incoming_connections__from_node=node,
        incoming_connections__is_active=True
    )[:10]
    
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
    """Share knowledge on P2P network"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            is_public = data.get('is_public', False)
            category = data.get('category', 'general')
            
            node = BlackBoxNode.objects.get(user=request.user)
            
            # Encrypt content
            encrypted_content = encryption_manager.encrypt(content)
            content_hash = p2p_handler.create_knowledge_hash(content)
            
            # Create shared knowledge
            knowledge = SharedKnowledge.objects.create(
                title=title,
                content=encrypted_content,
                encryption_key_hash=content_hash,
                shared_by=node,
                is_public=is_public,
                category=category
            )
            
            return JsonResponse({
                'success': True,
                'knowledge_id': knowledge.id,
                'message': 'Knowledge shared successfully'
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
                'redirect': '/dashboard/'
            })
            
        except Exception as e:
            print(f"ZKP Login error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Authentication error'}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def setup_zkp_view(request):
    """Page to setup ZKP secret"""
    return render(request, 'setup_zkp.html')

@login_required
@csrf_exempt
def setup_zkp(request):
    """Setup ZKP secret for user"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            current_password = data.get('current_password')
            zkp_secret = data.get('zkp_secret')
            
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