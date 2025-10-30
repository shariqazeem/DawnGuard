# core/middleware.py - Custom Middleware

from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.urls import reverse

class SetupRequiredMiddleware:
    """
    Middleware to redirect to welcome animation then setup wizard if no users exist
    This ensures the epic first-run experience
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if no users exist (first time setup)
        no_users = User.objects.count() == 0

        if no_users:
            # Paths that are allowed during first-time setup
            exempt_paths = [
                reverse('welcome_animation'),
                reverse('setup_wizard'),
                reverse('complete_setup'),
                reverse('setup_status'),
                '/static/',
                '/media/',
            ]

            # Check if current path is exempt
            is_exempt = any(request.path.startswith(path) for path in exempt_paths)

            if not is_exempt:
                # First visit - always show welcome animation
                return redirect('welcome_animation')

        response = self.get_response(request)
        return response
