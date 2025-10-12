from django import template
import re

register = template.Library()

@register.filter(name='format_message')
def format_message(text):
    """Format message with markdown-like syntax"""
    if not text:
        return text
    
    # Convert **bold** to HTML
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert * bullet points
    text = re.sub(r'^(\s*)\* (.+)$', r'\1<span style="display: block; margin-left: 20px;">• \2</span>', text, flags=re.MULTILINE)
    
    # Convert numbered lists
    text = re.sub(r'^(\s*)(\d+)\. (.+)$', r'\1<span style="display: block; margin-left: 20px;"><strong>\2.</strong> \3</span>', text, flags=re.MULTILINE)
    
    return text

@register.filter
def decrypt_content(message):
    """Decrypt message content for display"""
    try:
        return message.get_decrypted_content()
    except:
        return message.content  # Fallback to raw content if decryption fails