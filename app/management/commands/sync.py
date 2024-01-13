from django.core.management.base import BaseCommand
from app.syncer import sync


class Command(BaseCommand):
    help = "Syncs the database with the NREL server"

    def handle(self, *args, **options):
        sync()
