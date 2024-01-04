from django.core.management.base import BaseCommand
import unittest

from django.db.models import Count, Sum
from django.db.models.functions import ExtractWeekDay

from stats.models import *
from timeit import default_timer
from collections import Counter

import asyncio

from asgiref.sync import sync_to_async

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
        guild_model_obj = Guild.objects.all().first()
        asyncio.run(self.main())

    async def main(self):
        guild_model_obj = await Guild.objects.all().afirst()
        guild_ids_query = MemberBlacklist.objects.filter(guild=guild_model_obj).values_list('id')
        print({tup[0] async for tup in guild_ids_query})