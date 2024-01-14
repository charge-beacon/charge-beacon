from django.shortcuts import render
from django.core.paginator import Paginator
from app.models import Station, Persona, Update


def index(request):
    feed_kwargs = {
        'persona': None,
        'station': None,
    }
    if selected_network := request.GET.get('ev_network', None):
        feed_kwargs['persona'] = Persona.objects.from_network_name(selected_network)
    elif selected_state := request.GET.get('state', None):
        feed_kwargs['persona'] = Persona.objects.from_state(selected_state)
    queryset = Update.objects.feed(**feed_kwargs)
    paginator = Paginator(queryset, 25)

    return render(request, 'app/index.html', {
        'updates': paginator.get_page(request.GET.get('page', '1')),
        'networks': Station.objects.all_networks(),
        'states': Station.objects.all_states(),
    })
