from django import template

register = template.Library()

@register.filter
def mul(value, multiplier):
    """Multiplie une valeur par un nombre"""
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0