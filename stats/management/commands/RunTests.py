from django.core.management.base import BaseCommand
import unittest

from django.db.models import F

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
        guild = Guild(
            id=1,
            name='test',
            icon='https://www.google.com/',
        )
        guild.save()
        user = User(
            guild=guild,
            user_id=1,
            avatar_id='1',
            tag='blah'
        )
        User(
            guild=guild,
            user_id=2,
            avatar_id='1',
            tag='blah'
        ).save()
        #user.save()
        word = Unique_Word_Count(
            user=user,
            obj='blah'
        )
        print(word.user.user_id)