import markdown as md
import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p','pre','code','table','thead','tbody','tr','th','td',
    'h1','h2','h3','h4','h5','h6','ul','ol','li','strong','em','blockquote'
]
ALLOWED_ATTRS = {
    '*': ['class', 'id'],
    'a': ['href', 'title', 'rel'],
    'code': ['class']
}

@register.filter(name='markdown_to_html')
def markdown_to_html(text):
    """Convertit le texte Markdown en HTML sécurisé"""
    if not text:
        return ''
    html = md.markdown(
        text,
        extensions=['tables', 'fenced_code']
    )
    clean_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return mark_safe(clean_html)