from django.db import models
from django.urls import reverse
from django.utils import dateparse, timezone
from django.core.serializers.json import json, DjangoJSONEncoder
from simple_history.models import HistoricalRecords
import randomname
from django.forms import model_to_dict


class StationQuerySet(models.QuerySet):
    def import_from_nrel(self, data):
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
            cobj = Station(**{k: v for k, v in station.items() if k in interesting_fields})
            updated_fields = []
            if qs.exists():
                obj = qs.first()
                for field in interesting_fields:
                    f1 = getattr(obj, field)
                    f2 = getattr(cobj, field)
                    if f1 != f2:
                        updated_fields.append(field)
                        setattr(obj, field, f2)
                if updated_fields:
                    obj.save()
                if not all(f in no_history_fields for f in updated_fields):
                    Update.objects.station_updated(obj)
            else:
                cobj.save()
                Update.objects.station_updated(cobj, is_creation=True)

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

    def all_networks(self):
        count = models.Count('ev_network', filter=models.Q(linked_to__isnull=True))
        result = self.values('ev_network').annotate(count=count).order_by('ev_network')
        networks = []
        for r in result:
            name = r['ev_network'] or 'None'
            networks.append({
                'name': name.replace('_', ' ').title(),
                'id': r['ev_network'] or 'None',
                'handle': network_name_as_handle(r['ev_network']),
                'count': r['count'],
            })
        return sorted(networks, key=lambda x: x['name'])

    def all_states(self):
        count = models.Count('state', filter=models.Q(linked_to__isnull=True))
        result = self.values('state').annotate(count=count).order_by('state')
        states = []
        for r in result:
            if not r['state']:
                continue
            states.append({
                'name': r['state'].upper(),
                'id': r['state'] or 'None',
                'handle': state_as_handle(r['state']),
                'count': r['count'],
            })
        return sorted(states, key=lambda x: x['name'])


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
    ev_dc_fast_num = models.IntegerField(blank=True, null=True)
    ev_level1_evse_num = models.IntegerField(blank=True, null=True)
    ev_level2_evse_num = models.IntegerField(blank=True, null=True)
    ev_network = models.TextField(blank=True, null=True)
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

    objects = StationQuerySet.as_manager()

    @property
    def network_name_as_handle(self):
        return network_name_as_handle(self.ev_network)

    @property
    def state_as_handle(self):
        return state_as_handle(self.state)

    def get_absolute_url(self):
        return reverse('station', args=[self.beacon_name])

    def key(self):
        return f'{self.ev_network}: {self.street_address}, {self.city}, {self.state}'.lower()


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
        self.create(**args)

    def feed(self, ev_networks: list[str] = None, states: list[str] = None, station: Station = None):
        qs = self.all().select_related('station')
        if station:
            qs = qs.filter(station=station)
        else:
            qs = qs.filter(station__linked_to__isnull=True)
        if ev_networks:
            qs = qs.filter(station__ev_network__in=ev_networks)
        if states:
            qs = qs.filter(station__state__in=states)
        return qs


class Update(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_creation = models.BooleanField(default=False)
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
    keys_to_del = [f for f in obj if f.startswith('history')]
    for f in keys_to_del:
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
