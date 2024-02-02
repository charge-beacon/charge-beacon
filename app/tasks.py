import requests
from django.conf import settings
from django.apps import apps
from celery import shared_task
from celery.utils.log import get_task_logger
from discord_webhook import DiscordWebhook, DiscordEmbed


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
    logging.info('[Progress] got %d stations from NREL', len(data.get('fuel_stations', [])))
    stats = Station.objects.import_from_nrel(data)
    Station.objects.link_stations()
    logging.info("[Completed] scrape %d created %d updated %d skipped", stats.created, stats.updated, stats.skipped)
    return {
        'created': stats.created,
        'updated': stats.updated,
        'skipped': stats.skipped,
    }


@shared_task
def publish_update(update_id):
    Update = apps.get_model("app", "Update")
    Search = apps.get_model("beacon", "Search")
    update = Update.objects.get(id=update_id)
    n_published, errors = Search.objects.publish(update, f'update-{update_id}-{update.created_at}')
    logging.info("[Published] %d searches %d errors for update %s", n_published, len(errors), update_id)
    for error in errors:
        logging.error("[Publish Error] search publish error %s", error.id)
    return {
        'published': n_published,
        'errors': len(errors),
    }


@shared_task
def event(name, message, data):
    logging.info("[Event] %s %s %s", name, message, data)

    if name in settings.DISCORD_WEBHOOK_EVENTS:
        webhook = DiscordWebhook(url=settings.DISCORD_WEBHOOK_URL)
        embed = DiscordEmbed(
            title=name.replace("_", " ").title(),
            description=message,
            color='0x0087D8',
        )
        for k, v in data.items():
            embed.add_embed_field(name=k, value=v)
        webhook.add_embed(embed)
        webhook.execute()

    return {
        'name': name,
        'message': message,
        'data': data,
    }
