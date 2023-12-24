from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from typing import Self

import datetime 
import pytz 
import heapq


from . import Guild, User

from .debug import timed

CACHE_TIMEOUT = 60 * 60 * 24


def half_hours_to_hours(half_hour_counts: tuple[int], timezone: str) -> tuple[int]:
    '''Given a list of half hour counts and a timezone, return a tuple of 24 hour counts translated into that timezone'''
    hour_counts = [0] * 24
    dummy_dt = datetime.datetime.now(datetime.UTC)
    for half_hour in range(48):
        hour_24 = half_hour // 2
        minute = 30 if half_hour % 2 == 1 else 0
        dummy_dt = dummy_dt.replace(hour=hour_24, minute=minute)
        local_tz = dummy_dt.astimezone(pytz.timezone(timezone))
        hour_counts[local_tz.hour] += half_hour_counts[half_hour]
    return tuple(hour_counts)

class Member_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        return await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = ['messages', 'curse_word_count', 'ALL_CAPS_count', 'total_chars', 'half_hour_counts'],
            unique_fields = ['id']
        )
    def top_100(self, guild: Guild):
        top_100_members = cache.get_or_set('top100', self.filter(guild=guild)[:100], CACHE_TIMEOUT, version=guild.id)
        return top_100_members
    @timed
    def total_messages(self, guild: Guild):
        '''Return the total number of messages ever sent for a server'''
        return self.filter(guild=guild).aggregate(models.Sum('messages'))['messages__sum']
    
    @timed
    def total_members(self, guild: Guild):
        return self.filter(guild=guild).count()
    
    @timed
    def top_member_message_count(self, guild: Guild) -> int:
        return self.filter(guild=guild).first().messages
    
    @timed
    def top_n_curse_members(self, guild: Guild, n):
        top_100_members = self.top_100(guild)
        return heapq.nlargest(n, top_100_members, key = lambda member: member.curse_ratio)
    
    @timed
    def top_n_ALL_CAPS_members(self, guild: Guild, n):
        top_100_members = self.top_100(guild)
        return heapq.nlargest(n, top_100_members, key = lambda member: member.CAPS_ratio)
    
    @timed
    def top_n_verbose_members(self, guild: Guild, n):
        top_100_members = self.top_100(guild)
        return heapq.nlargest(n, top_100_members, key = lambda member: member.average_chars)
    
    def total_hour_counts(self, guild: Guild, timezone) -> tuple[int]:
        '''
        Return a tuple of length 24 representing every hour count in the guild
        '''
        half_hour_counts_lists = self.filter(guild=guild).values_list('half_hour_counts', flat=True)
        total_half_hour_counts = tuple(sum(count) for count in zip(*half_hour_counts_lists))
        return half_hours_to_hours(total_half_hour_counts, timezone)
    def top_n_in_hour_range(self, guild: Guild, timezone: str, n: int, lower_bound: int, upper_bound: int) -> list[tuple['Member', int]]:
        '''Return a list of tuples representing the top n members with the most messages sent in the hour range of `lower_bound` to `upper_bound`
        Each tuple contains the member object as well as the hour range message count for that user'''
        top_100_members = self.top_100(guild)
        with_counts = [(member, sum(member.hour_counts_tz(timezone)[lower_bound:upper_bound]))
                         for member in top_100_members]
        return sorted(
            with_counts,
            key=lambda tup: tup[1],
            reverse=True
        )[:n]

    @timed
    def get_rank(self, guild: Guild, member):
        return self.filter(guild=guild, messages__gt=member.messages).count() + 1
    

class Member_Whitelist_Manager(Member_Manager):
    def get_queryset(self):
        return super().get_queryset().filter(hidden=False)


def _hourfield():
    return [0] * 48

class Member(models.Model):
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    messages = models.PositiveIntegerField(default=0)

    half_hour_counts = ArrayField(models.PositiveIntegerField(), size=48, default=_hourfield)
    curse_word_count = models.PositiveIntegerField(default=0)
    ALL_CAPS_count = models.PositiveIntegerField(default=0)
    total_chars = models.PositiveBigIntegerField(default=0)

    hidden = models.BooleanField(default=False)
    manage_guild_perm = models.BooleanField(default=False)
    in_guild = models.BooleanField(default=True)
    
    objects = Member_Manager()
    whitelist = Member_Whitelist_Manager()

    def __str__(self):
        return self.user.tag

    @property
    def curse_ratio(self):
        return (self.curse_word_count / self.messages) * 100 if self.messages != 0 else 0 
    
    @property
    def CAPS_ratio(self):

        return (self.ALL_CAPS_count / self.messages) * 100 if self.messages != 0 else 0 

    @property
    def average_chars(self):
        return (self.total_chars / self.messages) if self.messages != 0 else 0 
    
    def hour_counts_tz(self, timezone: str) -> tuple[int]:
        '''
        Return the user's hour count for each hour of the day in a given timezone
        '''
        return half_hours_to_hours(self.half_hour_counts, timezone)

    
    def merge(self, other: Self):
        '''
        Update the counts of one Member with the counts of another
        Args:
            other (MemberStat) - a model of the same type 
        '''

        self.messages += other.messages

        self.curse_word_count += other.curse_word_count
        self.ALL_CAPS_count += other.ALL_CAPS_count
        self.total_chars += other.total_chars

        self.half_hour_counts = [self.half_hour_counts[i] + other.half_hour_counts[i] for i in range(48)]

    class Meta:
        ordering = ['-messages']