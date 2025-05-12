from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key."""
    return dictionary.get(key) 