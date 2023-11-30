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
        queryset = Date_Count.objects.all()
        days_of_week = Date_Count.objects.filter(obj__week_day=0).aggregate(Sum('count'))
        print(days_of_week['count__sum'])