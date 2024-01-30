from unittest import mock
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from app.models import Station, Update
from beacon.models import Search, SearchResult, Notification, NotificationType
from beacon.tasks import create_email_notification


class BeaconTestCase(TestCase):
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


class TestSearch(BeaconTestCase):
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


class TestNotificationScheduling(BeaconTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.daily_search = Search.objects.create(
            name='test', user=self.user, ev_networks=[], plug_types=[], daily_email=True
        )

    @mock.patch('beacon.models.schedule_create_email_notification')
    def test_daily_notif_created(self, schedule_create):
        Search.objects.publish(self.update, 'idem-key')
        Search.objects.send_daily_rollup_emails()
        schedule_create.assert_called_once_with(self.daily_search.id, 'daily', mock.ANY)

    @mock.patch('beacon.models.schedule_create_email_notification')
    def test_daily_notif_not_created(self, schedule_create):
        Search.objects.send_daily_rollup_emails()
        schedule_create.assert_not_called()

    @mock.patch('beacon.models.schedule_create_email_notification')
    def test_daily_notif_not_created_no_unread(self, schedule_create):
        Search.objects.publish(self.update, 'idem-key')
        self.daily_search.last_notified_timestamp = timezone.now()  # mark as read
        self.daily_search.save()
        Search.objects.send_daily_rollup_emails()
        schedule_create.assert_not_called()


class TestNotificationCreation(BeaconTestCase):
    @mock.patch('beacon.models.schedule_create_email_notification')
    def setUp(self, schedule_create) -> None:
        super().setUp()
        self.daily_search = Search.objects.create(
            name='test', user=self.user, ev_networks=[], plug_types=[], daily_email=True
        )
        Search.objects.publish(self.update, 'idem-key')
        Search.objects.send_daily_rollup_emails()

    @mock.patch('beacon.tasks.schedule_html_email')
    def test_create_email_notifications(self, schedule_email):
        create_email_notification(self.daily_search.id, 'daily', timezone.now() - timedelta(seconds=1))
        schedule_email.assert_called_once_with(mock.ANY)


class NotificationBeaconTestCase(BeaconTestCase):
    @mock.patch('beacon.models.schedule_create_email_notification')
    @mock.patch('beacon.tasks.schedule_html_email')
    def setUp(self, schedule_create, schedule_email) -> None:
        super().setUp()
        self.daily_search = Search.objects.create(
            name='test', user=self.user, ev_networks=[], plug_types=[], daily_email=True
        )
        Search.objects.publish(self.update, 'idem-key')
        Search.objects.send_daily_rollup_emails()
        create_email_notification(self.daily_search.id, 'daily', timezone.now() - timedelta(seconds=1))
        self.notif = Notification.objects.get(id=schedule_email.call_args.args[0])

    def test_notification_type(self):
        self.assertEqual(self.notif.type, NotificationType.EMAIL)

    def test_notification_content(self):
        self.assertIn('1 new search result on example.com', self.notif.message['body_html'])
