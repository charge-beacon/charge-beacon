from beacon.management.commands.mapping import MappingCommand
from beacon.models import ZipCodeTabulationArea, AreaType


class Command(MappingCommand):
    help = 'Load US Zip Code Tabulation Areas data from a census-provided shp file'
    area_type = AreaType.ZIP
    model = ZipCodeTabulationArea
    mapping = {
        'zip_code': 'ZCTA5CE20',
        'geom': 'MULTIPOLYGON',
    }
    unique = ['zip_code']

    def parent_place_id(self):
        return 'country-us'

    def feature_place_id(self, feature):
        return f'us-zip-{feature.zip_code}'

    def feature_name(self, feature):
        return feature.zip_code
