# core/api_views.py - API endpoints for dApp features

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .utils.llm_handler import LLMHandler

# Initialize LLM handler
llm_handler = LLMHandler()


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

        # Check if Ollama is available
        if not llm_handler.available:
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

            ai_response = llm_handler.generate_response(full_prompt)

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
    return JsonResponse({
        'available': llm_handler.available,
        'model': llm_handler.model if llm_handler.available else None,
        'endpoint': llm_handler.ollama_url if llm_handler.available else None
    })
