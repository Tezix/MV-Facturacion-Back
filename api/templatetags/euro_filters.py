from django import template

register = template.Library()

def euro_format(value):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

euro_format.is_safe = True
register.filter('euro', euro_format)

# Multiply filter for use in templates
@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

# Add filter for use in templates
@register.filter
def add(value, arg):
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return ''
