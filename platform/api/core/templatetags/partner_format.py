from django import template

register = template.Library()


@register.filter
def comma(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError, OverflowError):
        return "0"
