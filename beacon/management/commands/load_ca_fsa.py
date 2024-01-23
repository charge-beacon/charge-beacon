from beacon.management.commands.mapping import MappingCommand
from beacon.models import ForwardStatisticalArea, AreaType


class Command(MappingCommand):
    help = 'Load CA Forward Statistical Areas data from a census-provided shp file'
    area_type = AreaType.ZIP
    model = ForwardStatisticalArea
    mapping = {
        'code': 'CFSAUID',
        'geom': 'MULTIPOLYGON',
    }
    unique = ['code']

    def parent_place_id(self):
        return 'country-ca'

    def feature_place_id(self, feature):
        return f'ca-zip-{feature.code}'

    def feature_name(self, feature):
        return feature.code
