from django import template
from app.renderer import get_changes


register = template.Library()


@register.inclusion_tag('app/station_card.html')
def station_card(update):
    return {
        'station': update.station,
        'new': update.is_creation,
        'timestamp': update.created_at,
        'changes': get_changes(update)
    }
