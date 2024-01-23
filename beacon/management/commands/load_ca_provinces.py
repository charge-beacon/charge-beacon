from beacon.models import CanadianProvince, AreaType
from beacon.management.commands.mapping import MappingCommand


class Command(MappingCommand):
    help = 'Load Canadian Province Areas data from a census-provided shp file'
    area_type = AreaType.STATE
    model = CanadianProvince
    mapping = {
        'name': 'PRENAME',
        'name_fr': 'PRFNAME',
        'abbreviation': 'PREABBR',
        'abbreviation_fr': 'PRFABBR',
        'geom': 'MULTIPOLYGON',
    }
    unique = ['name']

    def parent_place_id(self):
        return 'country-ca'

    def feature_place_id(self, feature):
        return f'ca-state-{feature.abbreviation.lower().replace(".", "").replace("-", "")}'

    def feature_name(self, feature):
        return feature.name
