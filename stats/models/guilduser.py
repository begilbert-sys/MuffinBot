from django.db import models
from django.contrib.postgres.fields import ArrayField

from . import Guild, User

from .debug import timed

import heapq

class GuildUser_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        return await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = ['messages', 'curse_word_count', 'ALL_CAPS_count', 'total_chars'],
            unique_fields = ['id']
        )
    @timed
    def total_messages(self, guild: Guild):
        '''Return the total number of messages ever sent for a server'''
        return self.filter(guild=guild).aggregate(models.Sum('messages'))['messages__sum']
    @timed
    def total_users(self, guild: Guild):
        return self.filter(guild=guild).count()
    @timed
    def top_user_message_count(self, guild: Guild) -> int:
        return self.filter(guild=guild).first().messages
    @timed
    def top_n_curse_users(self, guild: Guild, n):
        top_100_users = self.filter(guild=guild)[:100]
        return heapq.nlargest(n, top_100_users, key = lambda user: user.curse_ratio)
    @timed
    def top_n_ALL_CAPS_users(self, guild: Guild, n):
        top_100_users = self.filter(guild=guild)[:100]
        return heapq.nlargest(n, top_100_users, key = lambda user: user.CAPS_ratio)
    @timed
    def top_n_verbose_users(self, guild: Guild, n):
        top_100_users = self.filter(guild=guild)[:100]
        return heapq.nlargest(n, top_100_users, key = lambda user: user.average_chars)
    @timed
    def get_rank(self, guild: Guild, user):
        return self.filter(guild=guild, messages__gt=user.messages).count() + 1

class GuildUser_Whitelist_Manager(GuildUser_Manager):
    def get_queryset(self):
        return super().get_queryset().filter(hidden=False)

def _hourfield():
    return [0 for _ in range(48)]

class GuildUser(models.Model):
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    messages = models.PositiveIntegerField(default=0)

    hour_counts = ArrayField(models.PositiveIntegerField(), size=48, default=_hourfield)
    curse_word_count = models.PositiveIntegerField(default=0)
    ALL_CAPS_count = models.PositiveIntegerField(default=0)
    total_chars = models.PositiveBigIntegerField(default=0)

    hidden = models.BooleanField(default=False)
    manage_guild_perm = models.BooleanField(default=False)
    in_guild = models.BooleanField(default=True)
    
    objects = GuildUser_Manager()
    whitelist = GuildUser_Whitelist_Manager()

    def __str__(self):
        return self.user.tag

    @property
    def curse_ratio(self):
        return (self.curse_word_count / self.messages) * 100
    
    @property
    def CAPS_ratio(self):
        return (self.ALL_CAPS_count / self.messages) * 100

    @property
    def average_chars(self):
        return self.total_chars / self.messages
    
    def merge(self, other):
        '''
        Update the counts of one User with the counts of another, with the equivalent 
        Args:
            other (UserStat) - a model of the same type 
        '''

        self.messages += other.messages

        self.curse_word_count += other.curse_word_count
        self.ALL_CAPS_count += other.ALL_CAPS_count
        self.total_chars += other.total_chars

    class Meta:
        ordering = ['-messages']