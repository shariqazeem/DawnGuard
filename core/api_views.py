# core/api_views.py - API endpoints for dApp features

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .utils.llm_handler import LLMHandler

# Initialize LLM handler (lazy initialization pattern)
llm_handler = None


def get_llm_handler():
    """Get or create LLM handler instance"""
    global llm_handler
    if llm_handler is None:
        llm_handler = LLMHandler()
    return llm_handler


@csrf_exempt
@require_http_methods(["POST"])
def api_chat(request):
    """
    API endpoint for AI chat (Kids AI dApp)
    Calls local Ollama for responses
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        mode = data.get('mode', 'general')

        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'No message provided'
            }, status=400)

        # Get LLM handler instance
        handler = get_llm_handler()

        # Check if Ollama is available (re-check each time)
        handler.available = handler.check_ollama()

        if not handler.available:
            return JsonResponse({
                'success': False,
                'error': 'Ollama AI is not available. Please start Ollama: docker-compose up -d ollama'
            }, status=503)

        # Get AI response from local Ollama
        try:
            # Add system prompt for kids-safe mode
            if mode == 'kids_safe':
                system_prompt = """You are a helpful, friendly tutor for children.
                Keep your responses age-appropriate, educational, and encouraging.
                Never provide harmful, inappropriate, or adult content.
                If asked something inappropriate, politely redirect to educational topics."""

                full_prompt = f"{system_prompt}\n\nChild: {user_message}\nTutor:"
            else:
                full_prompt = user_message

            ai_response = handler.generate_response(full_prompt)

            if not ai_response or ai_response.strip() == '':
                ai_response = "I'm having trouble generating a response right now. Could you try rephrasing your question?"

            return JsonResponse({
                'success': True,
                'response': ai_response,
                'conversation_id': conversation_id,
                'mode': mode
            })

        except Exception as llm_error:
            return JsonResponse({
                'success': False,
                'error': f'AI generation error: {str(llm_error)}'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def api_chat_status(request):
    """
    Check if Ollama AI is available
    """
    handler = get_llm_handler()
    # Re-check availability
    handler.available = handler.check_ollama()

    return JsonResponse({
        'available': handler.available,
        'model': handler.default_model if handler.available else None,
        'endpoint': handler.ollama_host if handler.available else None
    })
