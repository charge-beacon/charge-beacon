import requests
from django.conf import settings
from django.apps import apps
from celery import shared_task
from celery.utils.log import get_task_logger


logging = get_task_logger(__name__)
URL = 'https://developer.nrel.gov/api/alt-fuel-stations/v1.json'
params = {
    'fuel_type': 'ELEC',
    'api_key': settings.NREL_API_KEY,
    'country': 'all',
}


@shared_task(
    bind=True,
    autoretry_for=(requests.HTTPError,),
    retry_backoff=3,
    retry_kwargs={
        "max_retries": 3,
    },
)
def sync_fuel_stations(task):
    if task.request.retries > 0:
        logging.info(
            "[Task Retry] attempt %d/%d",
            task.request.retries,
            task.retry_kwargs["max_retries"],
        )
    logging.info("[Started] scraping data from %s ....", URL)
    Station = apps.get_model("app", "Station")
    data = requests.get(URL, params=params).json()
    logging.Info('[Progress] got %d stations from NREL', len(data.get('fuel_stations', [])))
    stats = Station.objects.import_from_nrel(data)
    Station.objects.link_stations()
    logging.info("[Completed] scrape %d imported %d updated %d skipped", stats.imported, stats.updated, stats.skipped)


@shared_task
def publish_update(update_id):
    Update = apps.get_model("app", "Update")
    Search = apps.get_model("app", "Search")
    update = Update.objects.get(id=update_id)
    n_published, errors = Search.objects.publish(update, f'update-{update_id}-{update.created}')
    logging.info("[Published] %d searches %d errors for update %s", n_published, len(errors), update_id)
    for error in errors:
        logging.error("[Publish Error] search publish error %s", error.id)

