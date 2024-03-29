from django import template
from app.renderer import get_changes, render_field


register = template.Library()


@register.inclusion_tag('app/station_card.html')
def station_card(update):
    return {
        'update': update,
        'station': update.station,
        'new': update.is_creation,
        'timestamp': update.created_at,
        'changes': get_changes(update)
    }


@register.filter
def station_field(value, name):
    return render_field(name, value)
