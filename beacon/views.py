from django.http import JsonResponse
from django.db.models.query import Q
from beacon.models import Area, AreaType


def area_autocomplete(request):
    if user_query := request.GET.get('query', ''):
        query = Q(
            name__istartswith=user_query,
            area_type__in=[AreaType.STATE, AreaType.ZIP],
        )
    else:
        query = Q(area_type=AreaType.STATE)
    if selected := set(filter(bool, request.GET.get('selected', '').split(','))):
        query |= Q(id__in=selected)
    # print('query', query)
    areas = Area.objects.filter(query).order_by('name')[:100]
    results = [{
        'value': str(area.id),
        'label': area.name,
        'selected': str(area.id) in selected
    } for area in areas]
    # print('results', results)

    return JsonResponse(results, safe=False)
