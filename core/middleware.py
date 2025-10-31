# core/middleware.py - Custom Middleware

from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.urls import reverse

class SetupRequiredMiddleware:
    """
    Middleware to show welcome animation for new visitors
    Tracks via session, not database - ensures every NEW user/visitor sees welcome
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that don't require welcome check
        exempt_paths = [
            reverse('welcome_animation'),
            reverse('setup_wizard'),
            reverse('complete_setup'),
            reverse('setup_status'),
            reverse('login'),
            reverse('logout'),
            '/static/',
            '/media/',
            '/api/',
        ]

        # Check if current path is exempt
        is_exempt = any(request.path.startswith(path) for path in exempt_paths)

        if not is_exempt:
            # Check if user is authenticated
            if request.user.is_authenticated:
                # Logged in users don't need welcome screen
                pass
            else:
                # Not logged in - check if they've seen welcome screen
                if not request.session.get('seen_welcome', False):
                    # First time visitor - show welcome animation
                    request.session['seen_welcome'] = True
                    return redirect('welcome_animation')

        response = self.get_response(request)
        return response
