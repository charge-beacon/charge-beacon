from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import Feed
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from beacon.models import Search, Area
from app.models import Station, Update
from app.renderer import get_changes
from app.constants import LOOKUPS


def index(request):
    return render(request, 'app/index.html', get_updates_context(request))


def updates_partial(request):
    return render(request, 'app/updates_body.html', get_updates_context(request))


def station(request, beacon_name):
    item = get_object_or_404(Station, beacon_name=beacon_name)
    return render(request, 'app/station.html', {
        'base_uri': f'{request.scheme}://{request.get_host()}',
        'station': item,
        'updates': item.updates.all(),
    })


@login_required
def searches(request):
    saved = Search.objects.filter(user=request.user)
    return render(request, 'app/search/list.html', {
        'saved': saved
    })


@login_required
def new_search(request):
    ctx = get_search_context(request)
    ctx['action'] = reverse('search-new')
    return render(request, 'app/search/edit.html', ctx)


@login_required
def edit_search(request, search_id):
    search = get_object_or_404(Search, id=search_id)
    ctx = get_search_context(request)
    ctx.update({
        'model': search,
        'action': reverse('search-edit', kwargs={'search_id': search_id})
    })
    return render(request, 'app/search/edit.html', ctx)


def get_search_context(request):
    selected_networks = get_param(request, 'ev_network')
    selected_plug_types = get_param(request, 'plug_types')
    selected_areas = get_param(request, 'ev_area')
    selected_area_objects = {str(a.id): a for a in Area.objects.filter(id__in=selected_areas)}

    ctx = {
        'networks': Station.objects.all_networks(),
        'selected_networks': selected_networks,
        'selected_area_ids': selected_areas,
        'selected_areas': [selected_area_objects[a] for a in selected_areas],
        'plug_types': LOOKUPS['ev_connector_types'],
        'selected_plug_types': selected_plug_types,
        'dc_fast': request.GET.get('dc_fast', None) == 'true',
        'only_new': request.GET.get('only_new', None) == 'true'
    }

    return ctx


def get_updates_context(request):
    ctx = get_search_context(request)

    queryset = Update.objects.feed(
        ev_networks=ctx['selected_networks'],
        areas=ctx['selected_area_ids'],
        ev_connector_types=ctx['selected_plug_types']
    )

    if ctx['dc_fast']:
        queryset = queryset.filter(station__ev_dc_fast_num__gt=0)

    if ctx['only_new']:
        queryset = queryset.filter(is_creation=True)

    max_results = 25
    if user_max_results := request.GET.get('max_results', None):
        max_results = int(user_max_results)

    paginator = Paginator(queryset, max_results)
    base_uri = f'{request.scheme}://{request.get_host()}'

    ctx.update({
        'base_uri': base_uri,
        'queryset': queryset,
        'updates': paginator.get_page(request.GET.get('page', '1')),
        'feed_url': f'{base_uri}{reverse("updates-feed")}?{request.GET.urlencode()}',
        'pagination': request.GET.get('pagination', 'true') == 'true'
    })

    return ctx


def get_param(request, name) -> list[str]:
    source = request.GET if request.method == 'GET' else request.POST
    return list(filter(bool, source.getlist(name)))


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
