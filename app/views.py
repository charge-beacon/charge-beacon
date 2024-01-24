from django.core.paginator import Paginator
from django.contrib.syndication.views import Feed
from django.shortcuts import render
from django.urls import reverse
from beacon.models import Area, AreaType
from app.models import Station, Update
from app.renderer import get_changes
from app.constants import LOOKUPS


def index(request):
    return render(request, 'app/index.html', get_updates_context(request))


def updates_partial(request):
    return render(request, 'app/updates_body.html', get_updates_context(request))


def station(request, beacon_name):
    item = Station.objects.get(beacon_name=beacon_name)
    return render(request, 'app/station.html', {
        'base_uri': f'{request.scheme}://{request.get_host()}',
        'station': item,
        'updates': item.updates.all(),
    })


def get_updates_context(request):
    feed_kwargs = {
        'station': None,
    }
    if selected_networks := get_param(request, 'ev_network'):
        feed_kwargs['ev_networks'] = selected_networks
    if selected_states := get_param(request, 'ev_state'):
        feed_kwargs['areas'] = selected_states
    if selected_plug_types := get_param(request, 'plug_types'):
        feed_kwargs['ev_connector_types'] = selected_plug_types

    queryset = Update.objects.feed(**feed_kwargs)

    if request.GET.get('dc_fast', None) == 'true':
        queryset = queryset.filter(station__ev_dc_fast_num__gt=0)

    if request.GET.get('only_new', None) == 'true':
        queryset = queryset.filter(is_creation=True)

    paginator = Paginator(queryset, 25)
    base_uri = f'{request.scheme}://{request.get_host()}'
    ctx = {
        'base_uri': base_uri,
        'queryset': queryset,
        'updates': paginator.get_page(request.GET.get('page', '1')),
        'networks': Station.objects.all_networks(),
        'selected_networks': selected_networks,
        'states': Area.objects.filter(area_type=AreaType.STATE).order_by('name'),
        'selected_states': selected_states,
        'plug_types': LOOKUPS['ev_connector_types'],
        'selected_plug_types': selected_plug_types,
        'feed_url': f'{base_uri}{reverse("updates-feed")}?{request.GET.urlencode()}',
    }

    return ctx


def get_param(request, name) -> list[str]:
    return list(filter(bool, request.GET.getlist(name)))


class CustomFeed(Feed):
    title = "EV Charging Stations"
    link = "/updates/"
    description_template = 'app/station_card_feed.html'

    def get_object(self, request, *args, **kwargs):
        ctx = get_updates_context(request)
        return ctx

    def items(self, obj):
        return obj['queryset'][:100]

    def link(self, obj):
        return obj['feed_url']

    def item_title(self, item):
        return f"{item.station.station_name} ({item.station.ev_network})"

    def get_context_data(self, item, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['station'] = item.station
        ctx['new'] = item.is_creation
        ctx['timestamp'] = item.created_at
        ctx['changes'] = get_changes(item)
        return ctx

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.created_at
