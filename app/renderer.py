from dataclasses import dataclass

from dictdiffer import diff

from app.constants import LOOKUPS
from app.models import Update, clean_station_json


@dataclass
class Change:
    kind: str
    field: str
    field_name: str
    previous: str
    current: str


def get_changes(upd: Update) -> [Change]:
    result = []
    if not upd.previous:
        return result
    clean_station_json(upd.previous)
    clean_station_json(upd.current)
    changes = diff(upd.previous, upd.current)
    for desc, field, change in changes:
        if desc == 'change':
            if isinstance(field, list):
                field = field[0]
            if field in ignore_fields:
                continue
            fn = field.replace('_', ' ').title()
            fva = render_field(field, change[0])
            fvb = render_field(field, change[1])
            result.append(Change('change', field, fn, fva, fvb))

    return result


def render_field(field: str, value: str) -> str:
    if field == 'cards_accepted':
        field_value = ', '.join([LOOKUPS['cards_accepted'].get(v, v) for v in value.split()])
    elif field in LOOKUPS:
        field_value = LOOKUPS[field].get(value, value)
    else:
        field_value = str(value)
    return field_value


ignore_fields = {
    'updated_at',
    'date_last_confirmed',
    'ev_network_ids',
    'beacon_name'
}
