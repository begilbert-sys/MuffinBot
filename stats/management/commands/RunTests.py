from django.core.management.base import BaseCommand
import unittest

from django.db.models import Count, Sum
from django.db.models.functions import ExtractWeekDay

from stats.models import *
from timeit import default_timer
from collections import Counter

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
        for member in Member.objects.all():
            new_hour_counts = member.hour_counts_tz('utc')
            old_hour_counts = tuple(Hour_Count.objects.member_hour_counts(member))
            if new_hour_counts != old_hour_counts:
                print(member.user.tag)
                print(new_hour_counts)
                print(old_hour_counts)
                print('---')