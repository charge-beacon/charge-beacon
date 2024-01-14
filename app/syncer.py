import requests
from django.conf import settings
from app.models import Station


URL = 'https://developer.nrel.gov/api/alt-fuel-stations/v1.json'
params = {
    'fuel_type': 'ELEC',
    'api_key': settings.NREL_API_KEY,
}


def sync():
    data = requests.get(URL, params=params).json()
    Station.objects.import_from_nrel(data)
    Station.objects.link_stations()
