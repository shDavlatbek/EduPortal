from django import template

register = template.Library()

@register.filter
def message_tags(message):
    if message.strip() == 'error':
        return 'danger'
    elif message.strip() == 'success':
        return 'success'
    elif message.strip() == 'warning':
        return 'warning'
    else:
        return 'info'