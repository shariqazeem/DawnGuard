# core/family_views.py - Family-Focused Views

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import FamilyMember, VaultFile, Conversation
from .vault_views import vault_home
from .utils.llm_handler import LLMHandler

llm_handler = LLMHandler()


def family_home(request):
    """
    New family-focused homepage
    Clear, simple, focused on 2 features: Family Vault + Kids AI
    """
    # Note: Middleware handles first-time redirect to welcome animation
    return render(request, 'family_home.html', {
        'llm_available': llm_handler.available,
    })


@login_required
def family_dashboard(request):
    """
    Unified family dashboard
    Shows both Family Vault stats and Kids AI access
    """
    try:
        # Get or create family member
        family_member, created = FamilyMember.objects.get_or_create(
            user=request.user,
            defaults={
                'display_name': request.user.username.title(),
                'role': 'admin',
                'avatar_color': '#FF6B35'
            }
        )

        # Get vault stats
        vault_files = VaultFile.objects.filter(owner=family_member)
        total_files = vault_files.count()
        storage_used_gb = family_member.get_storage_used_gb()

        # Get all family members
        all_family_members = FamilyMember.objects.all()

        # Get kids AI stats (if enabled)
        kids_conversations = 0
        if family_member.role in ['admin', 'member']:
            kids_conversations = Conversation.objects.filter(
                user=request.user
            ).count()

        context = {
            'family_member': family_member,
            'all_family_members': all_family_members,
            'total_files': total_files,
            'storage_used_gb': round(storage_used_gb, 2),
            'storage_quota_gb': family_member.storage_quota_gb,
            'storage_percentage': round(family_member.get_storage_percentage(), 1),
            'kids_conversations': kids_conversations,
            'llm_available': llm_handler.available,
        }

        return render(request, 'family_dashboard.html', context)

    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('home')


@login_required
def kids_ai_home(request):
    """
    Kids-Safe AI Tutor homepage with chat history
    """
    try:
        family_member = FamilyMember.objects.get(user=request.user)

        # Check if AI chat is enabled for this user
        if not family_member.ai_chat_enabled:
            messages.warning(request, 'AI Chat is disabled for your account. Please ask a parent to enable it.')
            return redirect('family_dashboard')

        # Get past conversations for this user
        from .models import Conversation, Message
        from django.db.models import Count

        recent_conversations = Conversation.objects.filter(
            user=request.user
        ).annotate(message_count=Count('messages')).order_by('-created_at')[:5]  # Last 5 conversations

        # Get all family conversations (for parents)
        all_conversations = []
        if family_member.role == 'admin':
            all_conversations = Conversation.objects.all().annotate(
                message_count=Count('messages')
            ).order_by('-created_at')[:20]

        context = {
            'family_member': family_member,
            'llm_available': llm_handler.available,
            'recent_conversations': recent_conversations,
            'all_conversations': all_conversations,
        }

        return render(request, 'kids_ai/kids_ai_home.html', context)

    except FamilyMember.DoesNotExist:
        messages.error(request, 'Please complete family setup first')
        return redirect('family_dashboard')


@csrf_exempt
def kids_ai_chat(request):
    """
    Kids AI chat endpoint - sends messages to Ollama with safety filtering
    Works with or without authentication (dApp mode)
    """
    import json

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        # Check if user is authenticated (Django mode) or anonymous (dApp mode)
        if request.user.is_authenticated:
            try:
                family_member = FamilyMember.objects.get(user=request.user)
                # Check permissions
                if not family_member.ai_chat_enabled:
                    return JsonResponse({
                        'success': False,
                        'error': 'AI Chat is disabled for your account'
                    }, status=403)
            except FamilyMember.DoesNotExist:
                # User exists but no family member profile - allow anyway
                pass
        # If not authenticated, allow anonymous usage (dApp mode)

        # Get message
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', None)

        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        # Conversation tracking (only for authenticated users)
        conversation = None
        if request.user.is_authenticated:
            # If conversation_id provided, continue that conversation
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=request.user)
                    # Mark it as active and update timestamp
                    conversation.is_active = True
                    conversation.save()
                except Conversation.DoesNotExist:
                    return JsonResponse({'error': 'Conversation not found'}, status=404)
            else:
                # Close any other active conversations for this user
                Conversation.objects.filter(user=request.user, is_active=True).update(is_active=False)

                # Create new conversation
                conversation = Conversation.objects.create(
                    user=request.user,
                    title=user_message[:50],  # Use first message as title
                    is_active=True
                )
        # For anonymous users (dApp mode), skip conversation tracking

        # Check if Ollama is available
        if not llm_handler.available:
            # Return mock response
            response_text = get_mock_kids_response(user_message)

            # Save messages to database (only if authenticated)
            if conversation:
                from .models import Message
                Message.objects.create(
                    conversation=conversation,
                    role='user',
                    content=user_message
                )
                Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=response_text
                )

            return JsonResponse({
                'success': True,
                'response': response_text,
                'mock_mode': True,
                'conversation_id': conversation.id if conversation else None
            })

        # Create kid-safe system prompt
        system_prompt = """You are a friendly, patient AI tutor helping kids with homework.
Rules:
1. Keep responses appropriate for children (ages 8-16)
2. Be encouraging and positive
3. Explain concepts simply, step-by-step
4. Ask guiding questions instead of giving direct answers
5. Use analogies and examples kids can understand
6. NEVER provide inappropriate content
7. If asked something inappropriate, politely redirect to learning

Remember: You're helping them learn, not doing their homework for them!"""

        # Generate response with Ollama
        try:
            response_text = llm_handler.generate_response(
                prompt=user_message,
                context=[{
                    'role': 'system',
                    'content': system_prompt
                }]
            )

            # Save conversation to database for parental monitoring (only if authenticated)
            if conversation:
                from .models import Message
                Message.objects.create(
                    conversation=conversation,
                    role='user',
                    content=user_message
                )
                Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=response_text
                )

            return JsonResponse({
                'success': True,
                'response': response_text,
                'mock_mode': False,
                'conversation_id': conversation.id if conversation else None
            })

        except Exception as e:
            # Fallback to mock
            response_text = get_mock_kids_response(user_message)

            # Still save to database (only if authenticated)
            if conversation:
                from .models import Message
                Message.objects.create(
                    conversation=conversation,
                    role='user',
                    content=user_message
                )
                Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=response_text
                )

            return JsonResponse({
                'success': True,
                'response': response_text,
                'mock_mode': True,
                'note': f'Ollama error: {str(e)}',
                'conversation_id': conversation.id if conversation else None
            })

    except FamilyMember.DoesNotExist:
        # This exception won't be raised anymore since we made it optional
        return JsonResponse({'error': 'Family member not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_conversation_detail(request, conversation_id):
    """
    Get detailed messages for a specific conversation
    """
    from django.http import JsonResponse
    import json

    try:
        # Get conversation and verify access
        conversation = Conversation.objects.get(id=conversation_id)

        # Check permissions: owner or admin parent
        family_member = FamilyMember.objects.get(user=request.user)
        if conversation.user != request.user and family_member.role != 'admin':
            return JsonResponse({'error': 'Access denied'}, status=403)

        # Get all messages
        from .models import Message
        messages = Message.objects.filter(conversation=conversation).order_by('timestamp')

        messages_data = [{
            'role': msg.role,
            'content': msg.get_decrypted_content() if msg.is_encrypted else msg.content,
            'timestamp': msg.timestamp.strftime('%b %d, %Y %I:%M %p')
        } for msg in messages]

        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'conversation_title': conversation.title,
            'user': conversation.user.username
        })

    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_mock_kids_response(message):
    """
    Mock responses for when Ollama isn't available
    """
    lower = message.lower()

    if 'math' in lower or 'homework' in lower or 'solve' in lower or 'calculate' in lower:
        return """I'd be happy to help with your math! 📐

Can you show me the specific problem you're working on?

Here's how we can work through it together:
1. First, let's understand what the problem is asking
2. Then, we'll figure out what steps we need
3. Finally, we'll solve it step-by-step!

Remember: It's okay if it's hard - that means you're learning! 💪"""

    elif 'science' in lower or 'photosynthesis' in lower or 'experiment' in lower:
        return """Great science question! 🔬

Let me explain this in a simple way:

Think of photosynthesis like a plant's kitchen. Plants need food to grow, right? Here's how they make it:

**Ingredients they use:**
- Sunlight (their energy source)
- Water (from the soil through roots)
- Carbon dioxide (from the air)

**What they make:**
- Glucose (sugar - their food!)
- Oxygen (which we breathe!)

Pretty cool, right? Plants are basically making food from sunlight! ☀️🌱

Do you have any questions about this?"""

    elif 'essay' in lower or 'writing' in lower or 'write' in lower:
        return """I can help you organize your essay! ✍️

Let's build it together. Answer these questions:

1. **What's your topic?** (What are you writing about?)
2. **Main idea?** (What's the ONE big thing you want to say?)
3. **Three points?** (What are 3 things that support your main idea?)

Once we have these, we can create an awesome outline!

Remember: Good writing is like building with blocks - we need a strong foundation first! 📚"""

    elif 'hello' in lower or 'hi' in lower:
        return """Hi there! 👋 I'm your friendly AI tutor!

I'm here to help you with:
📐 Math problems
🔬 Science questions
✍️ Writing essays
📚 Understanding concepts

What would you like to work on today?"""

    else:
        return f"""That's an interesting question! 🤔

I want to make sure I help you learn this properly. Can you tell me more about:
- What subject is this for?
- What specifically are you trying to understand?
- Have you learned anything about this in class yet?

The more you tell me, the better I can help you! Remember, asking questions is how we learn! 💡"""
