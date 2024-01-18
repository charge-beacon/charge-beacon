from django.shortcuts import render
from django.core.paginator import Paginator
from app.models import Station, Persona, Update


def index(request):
    feed_kwargs = {
        'station': None,
    }
    if selected_networks := get_param(request, 'ev_network'):
        feed_kwargs['ev_networks'] = selected_networks
    if selected_states := get_param(request, 'state'):
        feed_kwargs['states'] = selected_states

    queryset = Update.objects.feed(**feed_kwargs)

    if request.GET.get('dc_fast', None) == 'true':
        queryset = queryset.filter(station__ev_dc_fast_num__gt=0)

    if request.GET.get('only_new', None) == 'true':
        queryset = queryset.filter(is_creation=True)

    paginator = Paginator(queryset, 25)

    return render(request, 'app/index.html', {
        'updates': paginator.get_page(request.GET.get('page', '1')),
        'networks': Station.objects.all_networks(),
        'states': Station.objects.all_states(),
    })


def get_param(request, name) -> list[str]:
    return list(filter(bool, request.GET.getlist(name)))
