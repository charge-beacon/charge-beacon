from django.apps import apps
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.sites.models import Site
from celery import shared_task
from celery.utils.log import get_task_logger


logging = get_task_logger(__name__)


def schedule_create_email_notification(search_id, time_range, timestamp):
    return create_email_notification.delay(search_id, time_range, timestamp)


def schedule_html_email(notification_id):
    return send_html_email.delay(notification_id)


@shared_task
def create_daily_rollup_emails():
    Search = apps.get_model("beacon", "Search")
    Search.objects.send_daily_rollup_emails()


@shared_task
def create_weekly_rollup_emails():
    Search = apps.get_model("beacon", "Search")
    Search.objects.send_weekly_rollup_emails()


@shared_task
def create_email_notification(search_id, time_range, timestamp):
    from beacon.emailer import create_email_notification
    notif_id = create_email_notification(search_id, time_range, timestamp)
    if notif_id == -1:
        raise Exception("No results found")
    schedule_html_email(notif_id)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=3,
    retry_kwargs={"max_retries": 3}
)
def send_html_email(task, notification_id):
    Notification = apps.get_model("beacon", "Notification")
    notification = Notification.objects.get(id=notification_id)

    if notification.sent_at:
        logging.info("[Task Retry] notification %s already sent", notification_id)
        return

    if task.request.retries > 0:
        logging.info(
            "[Task Retry] attempt %d/%d",
            task.request.retries,
            task.retry_kwargs["max_retries"],
        )

    logging.info("[Started] sending email to %s", notification.user)

    site = Site.objects.get_current()

    message = EmailMultiAlternatives(
        subject=notification.message['subject'],
        body=notification.message['body'],
        from_email=f'{site.name} <{settings.DEFAULT_FROM_EMAIL}>',
        to=[notification.message['recipient']]
    )
    message.attach_alternative(notification.message['body_html'], "text/html")
    message.send()

    notification.sent_at = timezone.now()
    notification.save()

    logging.info("[Completed] sent email to %s", notification.user)
    return notification.id
