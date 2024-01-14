from django import template
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def url_params(context, **kwargs):
    if 'request' not in context:
        raise ValueError('url_params requires request in context')
    safe_args = context['request'].GET.copy()
    safe_args.update({k: v for k, v in kwargs.items() if v is not None})
    if safe_args:
        return '?{}'.format(urlencode(safe_args))
    return ''
