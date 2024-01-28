from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Station, Update
from beacon.models import Search, SearchResult


class TestSearch(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username='test', password='testtest', email='test@test.net'
        )
        self.station = Station.objects.create(
            id=1337,
            ev_network='ChargePoint',
            ev_connector_types=['J1772'],
            ev_dc_fast_num=0,
            point='POINT(-122.123 47.123)'
        )
        self.update = Update.objects.create(
            station=self.station,
            is_creation=True
        )

    def tearDown(self) -> None:
        self.user.delete()

    def test_search_publish_simple(self):
        Search.objects.create(name='test', user=self.user, ev_networks=[], plug_types=[])
        n_published, errors = Search.objects.publish(self.update, 'idempotency-key')
        self.assertEqual(n_published, 1)
        self.assertEqual(len(errors), 0)

    def test_search_publish_plug_types(self):
        res1 = Search.objects.create(name='test', user=self.user, ev_networks=[], plug_types=['J1772'])
        also_res1 = Search.objects.create(name='test2', user=self.user, ev_networks=[], plug_types=['J1772', 'CHAdeMO'])
        no_res = Search.objects.create(name='test3', user=self.user, ev_networks=[], plug_types=['CHAdeMO'])
        n_published, errors = Search.objects.publish(self.update, 'idempotency-key')
        self.assertEqual(n_published, 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(SearchResult.objects.filter(search=res1).count(), 1)
        self.assertEqual(SearchResult.objects.filter(search=also_res1).count(), 1)
        self.assertEqual(SearchResult.objects.filter(search=no_res).count(), 0)

    def test_search_publish_dc_fast(self):
        res1 = Search.objects.create(name='test', user=self.user, ev_networks=[], plug_types=[], dc_fast=False)
        no_res = Search.objects.create(name='test2', user=self.user, ev_networks=[], plug_types=[], dc_fast=True)
        n_published, errors = Search.objects.publish(self.update, 'idempotency-key')
        self.assertEqual(n_published, 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(SearchResult.objects.filter(search=res1).count(), 1)
        self.assertEqual(SearchResult.objects.filter(search=no_res).count(), 0)

    def test_search_publish_new(self):
        res1 = Search.objects.create(name='test', user=self.user, ev_networks=[], plug_types=[], only_new=False)
        also_res = Search.objects.create(name='test2', user=self.user, ev_networks=[], plug_types=[], only_new=True)
        n_published, errors = Search.objects.publish(self.update, 'idempotency-key')
        self.assertEqual(n_published, 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(SearchResult.objects.filter(search=res1).count(), 1)
        self.assertEqual(SearchResult.objects.filter(search=also_res).count(), 1)

    def test_search_publish_not_new(self):
        self.update.is_creation = False
        self.update.save()

        res1 = Search.objects.create(name='test', user=self.user, ev_networks=[], plug_types=[], only_new=False)
        no_res = Search.objects.create(name='test2', user=self.user, ev_networks=[], plug_types=[], only_new=True)
        n_published, errors = Search.objects.publish(self.update, 'idempotency-key')
        self.assertEqual(n_published, 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(SearchResult.objects.filter(search=res1).count(), 1)
        self.assertEqual(SearchResult.objects.filter(search=no_res).count(), 0)
