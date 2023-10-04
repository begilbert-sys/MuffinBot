from django.core.management.base import BaseCommand
from django.conf import settings

from .bot import run

class Command(BaseCommand):
    help = "Run MuffinBot"

    def handle(self, *args, **options):
        run()