from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.template.loader import get_template
from django.contrib.sites.models import Site
from beacon.models import Search, SearchResult, Notification


def create_email_notification(search_id: int, time_range: str, timestamp: datetime) -> int:
    with transaction.atomic():
        search = Search.objects.get(id=search_id)
        results = SearchResult.objects.filter(
            search_id=search_id,
            created_at__gt=search.last_notified_timestamp,
        ).order_by('-created_at')

        if not len(results):
            return -1

        search.last_notified_timestamp = results[0].created_at
        search.save()

        body_tmpl = get_template('beacon/emails/search_roll_up.html')
        body_text_tmpl = get_template('beacon/emails/search_roll_up.txt')
        subject_tmpl = get_template('beacon/emails/search_roll_up_subject.txt')
        url_scheme = 'https' if settings.DEBUG else 'http'
        site = Site.objects.get_current()
        ctx = {
            'search': search,
            'results': results,
            'result_count': results.count(),
            'time_range': time_range,
            'url_scheme': url_scheme,
            'site': site,
            'base_url': f'{url_scheme}://{site.domain}',
        }

        notification = Notification.objects.create(
            search=search,
            user=search.user,
            type='e',
            message={
                'subject': subject_tmpl.render(ctx).strip(),
                'body': body_text_tmpl.render(ctx),
                'body_html': body_tmpl.render(ctx),
                'recipient': search.user.email
            }
        )

    return notification.id
