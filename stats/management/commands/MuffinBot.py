from django.core.management.base import BaseCommand
from django.conf import settings

# I hate that I have to use triple dots here

from ...bot import client

from ...presets import TOKEN


class Command(BaseCommand):
    help = "Run MuffinBot"

    def handle(self, *args, **options):
        client.run(TOKEN)