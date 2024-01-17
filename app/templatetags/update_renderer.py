from django import template
from app.renderer import render_update


register = template.Library()


@register.filter(name='render_update')
def render_update_filter(update):
    return render_update(update)
