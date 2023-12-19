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
        guild = Guild.objects.get(id=424942639906029568)
        emoji_counts = Counter()
        for emoji_count in Emoji_Count.objects.filter(member__guild=guild).select_related('obj'):
            emoji_counts[emoji_count.obj] += emoji_count.count
        emojis = emoji_counts.most_common(100)

        if len(emojis) <= 5:
            return emojis
        
        max_emoji_count = emojis[0][1]
        step = round(max_emoji_count * 0.2)
        lower_bound = max_emoji_count
        emoji_matrix = list()
        for slice in range(5):
            if len(emojis) == 0:
                break
            sublist = list()
            lower_bound = lower_bound - step
            while True:
                if len(emojis) == 0:
                    break
                if emojis[0][1] >= lower_bound:
                    sublist.append(emojis.pop(0))
                else:
                    break
            if len(sublist) > 0:
                emoji_matrix.append(sublist)
        for sublist in emoji_matrix:
            print(sublist)
            print('---')