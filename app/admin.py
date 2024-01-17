from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from app.models import Station, Persona, Update


@admin.register(Station)
class StationAdmin(SimpleHistoryAdmin):
    list_display = (
        'id', 'status_code', 'full_address', 'open_date', 'updated_at'
    )
    search_fields = ['street_address', 'city', 'state', 'zip']
    list_filter = ['ev_network', 'state']

    def full_address(self, obj):
        return f'{obj.street_address}, {obj.city}, {obj.state}'


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('name', 'handle', 'persona_type')


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ('station_full_address', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('station')

    def station_full_address(self, obj):
        return f'{obj.station.street_address}, {obj.station.city}, {obj.station.state}'
