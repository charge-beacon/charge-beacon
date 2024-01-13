from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from app.models import Station


@admin.register(Station)
class StationAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'street_address', 'updated_at', 'open_date'
    )
    search_fields = ['street_address', 'city', 'state', 'zip']
    list_filter = ['ev_network', 'state']
