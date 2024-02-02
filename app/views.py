from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import Feed
from django.contrib import messages
from beacon.models import Search, Area
from beacon.forms import SearchForm
from app.models import Station, Update
from app.renderer import get_changes
from app.constants import LOOKUPS
from app.events import CREATE_SEARCH


def index(request):
    ctx = get_updates_context(request, search_id=request.GET.get('search_id', None))
    return render(request, 'app/index.html', ctx)


def updates_partial(request):
    ctx = get_updates_context(request, search_id=request.GET.get('search_id', None))
    return render(request, 'app/updates_body.html', ctx)


def station(request, beacon_name):
    item = get_object_or_404(Station, beacon_name=beacon_name)
    return render(request, 'app/station.html', {
        'base_uri': f'{request.scheme}://{request.get_host()}',
        'station': item,
        'updates': item.updates.all(),
    })


@login_required
def searches(request):
    saved = (
        Search.objects.filter(user=request.user)
        .order_by('name')
        .with_unread_count()
    )
    return render(request, 'app/search/list.html', {
        'searches': saved
    })


@login_required
def new_search(request):
    ctx = get_search_context(request)
    ctx['action'] = reverse('search-new')
    if request.method == 'POST':
        data = get_search_form_data(request, ctx)

        form = SearchForm(data, user=request.user)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, _('Search successfully created'))
            CREATE_SEARCH.send('New search created', {
                'name': form.instance.name,
                'username': request.user.get_username(),
            })
            return redirect('search-edit', search_id=form.instance.id)
        else:
            ctx['errors'] = form.errors

    return render(request, 'app/search/edit.html', ctx)


@login_required
def edit_search(request, search_id):
    ctx = get_search_context(request, search_id=search_id)

    if request.method == 'POST':
        if request.POST.get('delete', None) == 'true':
            ctx['search'].delete()
            messages.add_message(request, messages.INFO, _('Search successfully deleted'))
            return redirect('searches-list')

        data = get_search_form_data(request, ctx)

        form = SearchForm(data, instance=ctx['search'], user=request.user)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, _('Search saved successfully'))
            return redirect('search-edit', search_id=form.instance.id)
        else:
            ctx['errors'] = form.errors

    ctx['action'] = reverse('search-edit', kwargs={'search_id': search_id})

    return render(request, 'app/search/edit.html', ctx)


def get_search_form_data(request, ctx) -> dict:
    return {
        'name': request.POST.get('name', ''),
        'ev_networks': ctx['selected_networks'],
        'plug_types': ctx['selected_plug_types'],
        'dc_fast': ctx['dc_fast'],
        'only_new': ctx['only_new'],
        'within': ctx['selected_areas'],
        'daily_email': request.POST.get('daily_email', None),
        'weekly_email': request.POST.get('weekly_email', None),
        'is_public': request.POST.get('is_public', None)
    }


def get_search_context(request, search_id=None):
    ctx = {
        'networks': Station.objects.all_networks(),
        'plug_types': LOOKUPS['ev_connector_types'],
    }
    if search_id is not None:
        search = get_object_or_404(Search, id=search_id)
        if search.is_public or search.user == request.user:
            ctx['search'] = search
            ctx['selected_networks'] = search.ev_networks
            ctx['selected_area_ids'] = search.within.all().values_list('id', flat=True)
            ctx['selected_areas'] = search.within.all()
            ctx['selected_plug_types'] = search.plug_types
            ctx['dc_fast'] = search.dc_fast
            ctx['only_new'] = search.only_new
            ctx['daily_email'] = search.daily_email
            ctx['weekly_email'] = search.weekly_email
        else:
            raise Http404('invalid search')
    else:
        selected_networks = get_param(request, 'ev_network')
        selected_plug_types = get_param(request, 'plug_types')
        selected_areas = get_param(request, 'ev_area')
        selected_area_objects = {str(a.id): a for a in Area.objects.filter(id__in=selected_areas)}

        req_data = request.GET if request.method == 'GET' else request.POST

        ctx['selected_networks'] = selected_networks
        ctx['selected_area_ids'] = selected_areas
        ctx['selected_areas'] = [selected_area_objects[a] for a in selected_areas]

        ctx['selected_plug_types'] = selected_plug_types
        ctx['dc_fast'] = req_data.get('dc_fast', None) == 'true'
        ctx['only_new'] = req_data.get('only_new', None) == 'true'

    return ctx


def get_updates_context(request, search_id=None):
    ctx = get_search_context(request, search_id=search_id)

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
