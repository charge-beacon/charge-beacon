from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.aggregates import Union
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Q
from django.urls import reverse
from django.utils import dateparse, timezone
from django.core.serializers.json import json, DjangoJSONEncoder
from simple_history.models import HistoricalRecords
import randomname
from django.forms import model_to_dict
from beacon.models import Area
from app.caching import cached
from app.constants import LOOKUPS
from app.tasks import publish_update


class ImportStats:
    created: int
    updated: int
    skipped: int

    def __init__(self):
        self.created = 0
        self.updated = 0
        self.skipped = 0


class StationQuerySet(models.QuerySet):
    def import_from_nrel(self, data) -> ImportStats:
        stats = ImportStats()
        interesting_fields = [
            'id', 'access_code', 'access_days_time', 'access_detail_code', 'cards_accepted', 'date_last_confirmed',
            'expected_date', 'fuel_type_code', 'groups_with_access_code', 'maximum_vehicle_class', 'open_date',
            'owner_type_code', 'restricted_access', 'status_code', 'facility_type', 'station_name', 'station_phone',
            'updated_at', 'geocode_status', 'latitude', 'longitude', 'city', 'country', 'intersection_directions',
            'plus4', 'state', 'street_address', 'zip', 'ev_connector_types', 'ev_dc_fast_num', 'ev_level1_evse_num',
            'ev_level2_evse_num', 'ev_network', 'ev_network_web', 'ev_other_evse', 'ev_pricing', 'ev_renewable_source',
            'ev_workplace_charging', 'nps_unit_name', 'ev_network_ids'
        ]
        no_history_fields = {'updated_at', 'date_last_confirmed'}
        for station in data['fuel_stations']:
            clean_station_json(station)

            qs = self.filter(id=station['id'])
            create = Station(**{k: v for k, v in station.items() if k in interesting_fields})
            updated_fields = []
            update = None

            if qs.exists():
                existing = qs.first()
                for field in interesting_fields:
                    f1 = getattr(existing, field)
                    f2 = getattr(create, field)
                    if f1 != f2:
                        updated_fields.append(field)
                        setattr(existing, field, f2)
                point_updated = update_point(station, existing)
                if updated_fields or point_updated:
                    if not updated_fields:
                        existing.skip_history_when_saving = True
                    existing.save()
                if not all(f in no_history_fields for f in updated_fields):
                    stats.updated += 1
                    update = Update.objects.station_updated(existing)
                else:
                    stats.skipped += 1
            else:
                update_point(station, create)
                create.save()
                stats.created += 1
                update = Update.objects.station_updated(create, is_creation=True)

            if update:
                publish_update.delay(update.id)

        return stats

    def link_stations(self):
        all_stations = self.all()
        matches = {}
        for station in all_stations:
            key = station.key()
            if key not in matches:
                matches[key] = []
            matches[key].append(station)
        for key, stations in matches.items():
            if len(stations) > 1:
                stations = sorted(stations, key=lambda x: x.id)
                for station in stations[1:]:
                    if station.linked_to != stations[0]:
                        station.skip_history_when_saving = True
                        station.linked_to = stations[0]
                        station.save()

    def primaries(self):
        return self.filter(linked_to__isnull=True)

    @cached(60 * 60 * 24, key='all_station_networks', version=1)
    def all_networks(self):
        count = models.Count('ev_network', filter=models.Q(linked_to__isnull=True))
        result = self.values('ev_network').annotate(count=count).order_by('ev_network')
        networks = []
        for r in result:
            name = r['ev_network'] or 'None'
            name = LOOKUPS['ev_network'].get(name, name)
            networks.append({
                'name': name,
                'id': r['ev_network'] or 'None',
                'handle': network_name_as_handle(r['ev_network']),
                'count': r['count'],
            })
        return sorted(networks, key=lambda x: x['name'].lower())


NAME_ARGS = (
    list({
        'verbs/driving', 'verbs/movement', 'verbs/thought', 'verbs/graphics', 'verbs/creation',
        'verbs/art', 'verbs/sports', 'verbs/music_production', 'verbs/cooking', 'verbs/music',
        'verbs/communication'
    }),
    list({
        'nouns/driving', 'nouns/water', 'nouns/storage', 'nouns/fortifications', 'nouns/sports',
        'nouns/geography', 'nouns/physics', 'nouns/minerals', 'nouns/infrastructure', 'nouns/filmmaking',
        'nouns/typography', 'nouns/architecture', 'nouns/astronomy', 'nouns/geometry', 'nouns/music_instruments',
        'nouns/dogs', 'nouns/metals', 'nouns/construction',
    }),
)


def get_beacon_name():
    name = randomname.generate(*NAME_ARGS)
    while Station.objects.filter(beacon_name=name).exists():
        name = randomname.get_name()
    return name


class Station(models.Model):
    id = models.IntegerField(primary_key=True)
    beacon_name = models.SlugField(max_length=255, default=get_beacon_name, unique=True)
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
    restricted_access = models.BooleanField(blank=True, null=True)
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
    ev_dc_fast_num = models.IntegerField(blank=True, null=True, db_index=True)
    ev_level1_evse_num = models.IntegerField(blank=True, null=True)
    ev_level2_evse_num = models.IntegerField(blank=True, null=True)
    ev_network = models.TextField(blank=True, null=True, db_index=True)
    ev_network_web = models.URLField(blank=True, null=True)
    ev_other_evse = models.TextField(blank=True, null=True)
    ev_pricing = models.TextField(blank=True, null=True)
    ev_renewable_source = models.TextField(blank=True, null=True)
    ev_workplace_charging = models.BooleanField(default=False, blank=True, null=True)
    ev_network_ids = models.JSONField(blank=True, null=True)
    nps_unit_name = models.TextField(blank=True, null=True)
    linked_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, blank=True, null=True, related_name='linked', editable=False
    )
    history = HistoricalRecords()
    point = models.PointField(blank=True, null=True)

    objects = StationQuerySet.as_manager()

    class Meta:
        indexes = [
            GinIndex(fields=['ev_connector_types']),
        ]

    @property
    def network_name_as_handle(self):
        return network_name_as_handle(self.ev_network)

    @property
    def state_as_handle(self):
        return state_as_handle(self.state)

    def get_absolute_url(self):
        return reverse('station', kwargs={'beacon_name': self.beacon_name})

    def key(self):
        return f'{self.ev_network}: {self.street_address}, {self.city}, {self.state}'.lower()

    def full_address_one_line(self):
        return f'{self.street_address}, {self.city}, {self.state} {self.zip}'

    def to_dict(self):
        return dict_from_model(self)


def network_name_as_handle(network):
    return network.lower().replace(' ', '-') if network else 'none'


def state_as_handle(state):
    return state.lower() if state else 'na'


class PersonaQuerySet(models.QuerySet):
    def from_network_name(self, network):
        return self.get(handle=network_name_as_handle(network))

    def from_state(self, state):
        return self.get(handle=state_as_handle(state))


class PersonaType(models.TextChoices):
    NETWORK = 'n', 'Network'
    STATE = 's', 'State'


class Persona(models.Model):
    handle = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    persona_type = models.CharField(max_length=1, choices=PersonaType.choices)

    objects = PersonaQuerySet.as_manager()

    def __str__(self):
        return self.name


class UpdateQuerySet(models.QuerySet):
    def station_updated(self, station, is_creation=False):
        history = station.history.filter()[:2]
        args = {
            'station': station,
            'created_at': timezone.now(),
            'is_creation': is_creation,
            'current': dict_from_model(history[0]),
            'previous': dict_from_model(history[1]) if len(history) > 1 else None,
        }
        return self.create(**args)

    def feed(self, ev_networks: list[str] = None, areas: list[str] = None, ev_connector_types: list[str] = None,
             station: Station = None):
        qs = self.all().select_related('station')
        if station:
            qs = qs.filter(station=station)
        else:
            qs = qs.filter(station__linked_to__isnull=True)
        if ev_networks:
            qs = qs.filter(station__ev_network__in=ev_networks)
        if areas:
            areas = Area.objects.filter(id__in=areas)
            combined_geom = areas.aggregate(area=Union('geom'))['area']
            qs = qs.filter(station__point__within=combined_geom)
        if ev_connector_types:
            q = Q()
            for t in ev_connector_types:
                q |= Q(station__ev_connector_types__contains=t)
            qs = qs.filter(q)
        return qs


class Update(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='updates')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_creation = models.BooleanField(default=False, db_index=True)
    current = models.JSONField(blank=True, null=True)
    previous = models.JSONField(blank=True, null=True)

    objects = UpdateQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['station', 'created_at']),
        ]

    def get_absolute_url(self):
        return f'{self.station.get_absolute_url()}#update-{self.id}'


def dict_from_model(model):
    obj = model_to_dict(model)
    keys_to_del = ['point', 'linked_to']
    keys_to_del.extend([f for f in obj if f.startswith('history')])
    for f in keys_to_del:
        if f in obj:
            del obj[f]
    data = json.dumps(obj, cls=DjangoJSONEncoder)
    return json.loads(data)


def clean_station_json(station_json):
    if station_json.get('restricted_access', None) is not None:
        if str(station_json.get('restricted_access', 'false')).lower() == 'false':
            station_json['restricted_access'] = False
        else:
            station_json['restricted_access'] = True
    if station_json.get('open_date', None):
        station_json['open_date'] = dateparse.parse_date(station_json['open_date'])
    if station_json.get('expected_date', None):
        station_json['expected_date'] = dateparse.parse_date(station_json['expected_date'])
    if station_json.get('date_last_confirmed', None):
        station_json['date_last_confirmed'] = dateparse.parse_date(station_json['date_last_confirmed'])
    if station_json.get('updated_at', None):
        station_json['updated_at'] = dateparse.parse_datetime(station_json['updated_at'])
    if station_json.get('latitude', None):
        station_json['latitude'] = float(station_json['latitude'])
    if station_json.get('longitude', None):
        station_json['longitude'] = float(station_json['longitude'])


def update_point(cleaned_station_json, station) -> bool:
    latitude = cleaned_station_json.get('latitude', None)
    longitude = cleaned_station_json.get('longitude', None)
    if latitude is not None and longitude is not None:
        point = Point(longitude, latitude)
        if not station.point or (station.point and (station.point.x, station.point.y) != (point.x, point.y)):
            station.point = point
            return True
    return False
