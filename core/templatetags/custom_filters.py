# core/templatetags/custom_filters.py
from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='format_message')
def format_message(text):
    """Format message with markdown-like syntax"""
    if not text:
        return ""
    
    # Ensure text is a string
    text = str(text)
    
    # Escape HTML first to prevent XSS
    from django.utils.html import escape
    text = escape(text)
    
    # Convert **bold** to HTML
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert bullet points
    text = re.sub(r'^(\s*)\* (.+)$', r'\1<div style="margin-left: 20px;">• \2</div>', text, flags=re.MULTILINE)
    
    # Convert numbered lists
    text = re.sub(r'^(\s*)(\d+)\. (.+)$', r'\1<div style="margin-left: 20px;"><strong>\2.</strong> \3</div>', text, flags=re.MULTILINE)
    
    # Preserve line breaks
    text = text.replace('\n', '<br>')
    
    return mark_safe(text)