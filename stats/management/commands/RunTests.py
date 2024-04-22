from django.core.management.base import BaseCommand
import unittest

from django.db.models import Count, Sum
from django.db.models.functions import ExtractWeekDay

from stats import models
from timeit import default_timer
from collections import Counter

import random 
import asyncio

class Command(BaseCommand):
    help = """
    If you need Arguments, please check other modules in 
    django/core/management/commands.
    """

    def handle(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestChronology)
        unittest.TextTestRunner().run(suite)


class TestChronology(unittest.TestCase):
    def test_suite(self):
        guilds = models.Guild.objects.all()
        print(guilds)