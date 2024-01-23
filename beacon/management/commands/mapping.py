import os
import tempfile
import shutil
import requests
from functools import partial
from contextlib import contextmanager
from django.core.management.base import BaseCommand
from django.contrib.gis.gdal.datasource import DataSource
from django.contrib.gis.utils import LayerMapping
from django_countries import countries
from beacon.models import Area, AreaType


class MappingCommand(BaseCommand):
    model = None
    area_type = None
    mapping = None
    unique = None

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **options):
        if 'path' not in options:
            self.stderr.write('Please specify the path to the .shp file')
            return 'error'

        raw_path = options['path']
        if raw_path.startswith('https://'):
            pather = partial(download_file_to_tmpdir, self.stdout)
        else:
            pather = passthrough_file

        with pather(raw_path) as path:
            if not os.path.exists(path):
                self.stderr.write('File does not exist: {}'.format(path))
                return 'error'

            ds = DataSource(path)
            lm = LayerMapping(
                model=self.model,
                data=ds,
                mapping=self.mapping,
                unique=self.unique,
            )
            self.stdout.write('Loading shape data...')

            lm.save(progress=True)

        ensure_countries()

        self.stdout.write('Linking areas...')

        parent = Area.objects.get(place_id=self.parent_place_id())

        for feature in self.model.objects.filter(area=None):
            place_id = self.feature_place_id(feature)
            area, _ = Area.objects.update_or_create(defaults={
                'name': self.feature_name(feature),
                'area_type': self.area_type,
                'place_id': place_id,
                'belongs_to': parent,
                'geom': feature.geom,
            }, place_id=place_id)
            feature.area = area
            feature.save()

        self.stdout.write('Done!')

    def parent_place_id(self):
        raise NotImplementedError

    def feature_place_id(self, feature):
        raise NotImplementedError

    def feature_name(self, feature):
        raise NotImplementedError


def ensure_countries():
    for code, name in countries:
        Area.objects.get_or_create(
            area_type=AreaType.COUNTRY,
            place_id=f'country-{code.lower()}',
            defaults={
                'name': name,
            }
        )


@contextmanager
def download_file_to_tmpdir(writer, base_url):
    exts_needed = ['shp', 'shx', 'dbf', 'prj']
    with tempfile.TemporaryDirectory() as tmpdir:
        shp_path = None
        for ext in exts_needed:
            url = f'{base_url}.{ext}'
            writer.write(f'Downloading {url}...')
            res = requests.get(url, stream=True)
            res.raise_for_status()
            path = os.path.join(tmpdir, f'{os.path.basename(base_url)}.{ext}')
            if ext == 'shp':
                shp_path = path
            with open(path, 'wb') as f:
                shutil.copyfileobj(res.raw, f)

        yield shp_path


@contextmanager
def passthrough_file(path):
    yield path
