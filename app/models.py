from django.db import models
from simple_history.models import HistoricalRecords


class StationQuerySet(models.QuerySet):
    def import_from_nrel(self, data):
        interesting_fields = [
            'id', 'access_code', 'access_days_time', 'access_detail_code', 'cards_accepted', 'date_last_confirmed',
            'expected_date', 'fuel_type_code', 'groups_with_access_code', 'maximum_vehicle_class', 'open_date',
            'owner_type_code', 'restricted_access', 'status_code', 'facility_type', 'station_name', 'station_phone',
            'updated_at', 'geocode_status', 'latitude', 'longitude', 'city', 'country', 'intersection_directions',
            'plus4', 'state', 'street_address', 'zip', 'ev_connector_types', 'ev_dc_fast_num', 'ev_level1_evse_num',
            'ev_level2_evse_num', 'ev_network', 'ev_network_web', 'ev_other_evse', 'ev_pricing', 'ev_renewable_source',
            'ev_workplace_charging', 'nps_unit_name',
        ]
        for station in data['fuel_stations']:
            self.update_or_create(id=station['id'], defaults={k: station[k] for k in interesting_fields})


class Station(models.Model):
    id = models.IntegerField(primary_key=True)
    access_code = models.TextField(blank=True, null=True)
    access_days_time = models.TextField(blank=True, null=True)
    access_detail_code = models.TextField(blank=True, null=True)
    cards_accepted = models.TextField(blank=True, null=True)
    date_last_confirmed = models.DateField(blank=True, null=True)
    expected_date = models.DateField(blank=True, null=True)
    fuel_type_code = models.TextField(blank=True, null=True)
    groups_with_access_code = models.TextField(blank=True, null=True)
    maximum_vehicle_class = models.TextField(blank=True, null=True)
    open_date = models.DateField(blank=True, null=True)
    owner_type_code = models.TextField(blank=True, null=True)
    restricted_access = models.TextField(blank=True, null=True)
    status_code = models.TextField(blank=True, null=True)
    facility_type = models.TextField(blank=True, null=True)
    station_name = models.TextField(blank=True, null=True)
    station_phone = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    geocode_status = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    intersection_directions = models.TextField(blank=True, null=True)
    plus4 = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    street_address = models.TextField(blank=True, null=True)
    zip = models.TextField(blank=True, null=True)
    ev_connector_types = models.JSONField(blank=True, null=True)
    ev_dc_fast_num = models.IntegerField(blank=True, null=True)
    ev_level1_evse_num = models.IntegerField(blank=True, null=True)
    ev_level2_evse_num = models.IntegerField(blank=True, null=True)
    ev_network = models.TextField(blank=True, null=True)
    ev_network_web = models.URLField(blank=True, null=True)
    ev_other_evse = models.TextField(blank=True, null=True)
    ev_pricing = models.TextField(blank=True, null=True)
    ev_renewable_source = models.TextField(blank=True, null=True)
    ev_workplace_charging = models.BooleanField(default=False, blank=True, null=True)
    nps_unit_name = models.TextField(blank=True, null=True)
    history = HistoricalRecords()
    objects = StationQuerySet.as_manager()
