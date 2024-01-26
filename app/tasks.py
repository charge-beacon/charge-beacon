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
    data = requests.get(URL, params=params).json()

    if task.request.retries > 0:
        logging.info(
            "[Task Retry] attempt %d/%d",
            task.request.retries,
            task.retry_kwargs["max_retries"],
        )
    logging.info("[Started] scraping data from %s ....", URL)
    Station = apps.get_model("app", "Station")
    Station.objects.import_from_nrel(data)
    Station.objects.link_stations()
    logging.info("[Completed] scrape")
