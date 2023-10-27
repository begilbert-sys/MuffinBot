from django.core.management.base import BaseCommand
import unittest

from stats.models import *

class Command(BaseCommand):
    help = """
    If you need Arguments, please check other modules in 
    django/core/management/commands.
    """

    def handle(self, **options):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestChronology)
        unittest.TextTestRunner().run(suite)


class TestChronology(unittest.TestCase):
    def setUp(self):
        pass

    def test_emoji_obj_count(self):
        guild = Guild.objects.get(id=424942639906029568)

        print(list(Emoji_Count.objects.top_n_emojis(guild, 10)))
    
    def test_hour_counts(self):
        user = User.objects.all().first()
        print(len(Hour_Count.objects.filter(user=user)))
        print(user.messages)
        '''
        print({
            'night': Hour_Count.objects.user_hour_count_range(user, 0, 5),
            'morning':  Hour_Count.objects.user_hour_count_range(user, 6, 11),
            'afternoon': Hour_Count.objects.user_hour_count_range(user, 12, 17),
            'evening': Hour_Count.objects.user_hour_count_range(user, 18, 23)
        })
        '''