# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
import json
from .models import Conversation, Message, Document, UserProfile, SystemStats
from .utils.llm_handler import LLMHandler
from .utils.encryption import EncryptionManager
from django.contrib.auth import logout
from django.http import StreamingHttpResponse
import time

# Initialize handlers
llm_handler = LLMHandler()
encryption_manager = EncryptionManager()

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
            # Create user profile
            UserProfile.objects.create(user=user)
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