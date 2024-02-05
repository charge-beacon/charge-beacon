from django.http import JsonResponse, HttpResponse
from django.contrib.gis.geos import Polygon
from django.core.serializers import serialize
from app.models import Station


def stations_in_bounds(request):
    # Extract "bounds" parameter from the request
    bounds = request.GET.get('bounds')
    if not bounds:
        return JsonResponse({'error': 'No bounds provided'}, status=400)

    try:
        sw_lng, sw_lat, ne_lng, ne_lat = map(float, bounds.split(','))
    except ValueError:
        return JsonResponse({'error': 'Invalid bounds format'}, status=400)

    # Create a polygon from the bounding box
    bbox_polygon = Polygon.from_bbox((sw_lng, sw_lat, ne_lng, ne_lat))

    # Filter stations within the bounding box
    stations = Station.objects.filter(point__within=bbox_polygon)

    # Serialize queryset to GeoJSON
    geojson = serialize('geojson', stations, geometry_field='point', fields=('beacon_name', 'ev_dc_fast_num'))

    return HttpResponse(geojson, content_type='application/json')

