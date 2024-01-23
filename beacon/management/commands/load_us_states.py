from beacon.management.commands.mapping import MappingCommand
from beacon.models import USState, AreaType


class Command(MappingCommand):
    help = 'Load US State Areas data from a census-provided shp file'
    model = USState
    area_type = AreaType.STATE
    mapping = {
        'name': 'NAME',
        'abbreviation': 'STUSPS',
        'geom': 'MULTIPOLYGON',
    }
    unique = ['name']

    def parent_place_id(self):
        return 'country-us'

    def feature_place_id(self, feature):
        return f'us-state-{feature.abbreviation.lower()}'

    def feature_name(self, feature):
        return feature.name
