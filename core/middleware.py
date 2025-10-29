# core/middleware.py - Custom Middleware

from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.urls import reverse

class SetupRequiredMiddleware:
    """
    Middleware to redirect to setup wizard if no users exist
    This ensures the one-time setup runs on first launch
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that don't require setup check
        exempt_paths = [
            reverse('setup_wizard'),
            reverse('complete_setup'),
            reverse('setup_status'),
            '/static/',
            '/media/',
        ]

        # Check if current path is exempt
        is_exempt = any(request.path.startswith(path) for path in exempt_paths)

        # If no users exist and path is not exempt, redirect to setup
        if not is_exempt and User.objects.count() == 0:
            return redirect('setup_wizard')

        response = self.get_response(request)
        return response
