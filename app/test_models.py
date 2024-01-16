import os
import json
from django.test import TestCase
from django.utils import dateparse
from app.models import Station, Update


class SyncingTest(TestCase):
    def test_sync_initial_change(self):
        Station.objects.import_from_nrel(_get_sync_data())
        self.assertEqual(Station.objects.count(), 1)
        self.assertEqual(Update.objects.count(), 2)
        for u in Update.objects.all():
            self.assertTrue(u.is_creation)

    def test_sync_with_no_updates(self):
        Station.objects.import_from_nrel(_get_sync_data())
        Station.objects.import_from_nrel(_get_sync_data())
        self.assertEqual(Station.objects.count(), 1)
        self.assertEqual(Update.objects.count(), 2)

    def test_sync_with_datetime_update(self):
        Station.objects.import_from_nrel(_get_sync_data())
        new_date_str = '2024-01-16T01:56:49Z'
        new_date = dateparse.parse_datetime(new_date_str)
        data = _get_sync_data(updated_at=new_date_str)
        Station.objects.import_from_nrel(data)
        self.assertEqual(Station.objects.count(), 1)
        self.assertEqual(Update.objects.count(), 2)
        # verify field updated
        station = Station.objects.first()
        self.assertEqual(station.updated_at, new_date)

    def test_sync_with_status_code_update(self):
        Station.objects.import_from_nrel(_get_sync_data())
        data = _get_sync_data(
            updated_at='2024-01-16T01:56:49Z',
            status_code='T',
            groups_with_access_code='TEMPORARILY UNAVAILABLE (Public)',
        )
        Station.objects.import_from_nrel(data)
        self.assertEqual(Station.objects.count(), 1)
        self.assertEqual(Update.objects.count(), 4)
        self.assertEqual(Update.objects.filter(is_creation=False).count(), 2)
        # verify field updated
        station = Station.objects.first()
        self.assertEqual(station.status_code, 'T')
        self.assertEqual(station.groups_with_access_code, 'TEMPORARILY UNAVAILABLE (Public)')

    def test_link_stations(self):
        Station.objects.import_from_nrel(load_test_stations())
        Station.objects.link_stations()
        self.assertEqual(Station.objects.count(), 48)
        unlinked = Station.objects.filter(linked_to__isnull=True)
        self.assertEqual(unlinked.count(), 8)


def _get_sync_data(**updates):
    station = load_test_stations()['fuel_stations'][-1]
    station.update(updates)
    return {'fuel_stations': [station]}


def load_test_stations():
    f = os.path.join(os.path.dirname(__file__), 'testdata', 'stations.json')
    with open(f) as f:
        return json.load(f)
