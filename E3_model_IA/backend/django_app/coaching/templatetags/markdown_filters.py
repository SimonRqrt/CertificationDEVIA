import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def markdown_to_html(value):
    """Convertit le texte Markdown en HTML sécurisé"""
    if not value:
        return ""
    
    # Configuration markdown avec extensions utiles
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists'
        ],
        tab_length=2
    )
    
    html = md.convert(str(value))
    return mark_safe(html)