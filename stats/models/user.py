from django.db import models

from . import Guild

from .debug import timed

import heapq

class User_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        fields = self.model._meta.get_fields()
        non_update_fields = ['guild', 'id', 'user_id', 'blacklist']
        update_fields = [field.name for field in fields if (not field.is_relation and field.name not in non_update_fields)]
        return await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = update_fields,
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

class User_Whitelist_Manager(User_Manager):
    def get_queryset(self):
        return super().get_queryset().filter(blacklist=False)


class User(models.Model):
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)


    # this is not the primary key b/c the same user can exist
    # as two different user objs across multiple guilds
    user_id = models.PositiveBigIntegerField() 

    tag = models.CharField(max_length=32)
    avatar_id = models.CharField(max_length=34, null=True) # the 'a_' prefix for animated avatars adds two characters
    messages = models.PositiveIntegerField(default=0)

    curse_word_count = models.PositiveIntegerField(default=0)
    ALL_CAPS_count = models.PositiveIntegerField(default=0)
    total_chars = models.PositiveBigIntegerField(default=0)


    blacklist = models.BooleanField(default=False)

    objects = User_Manager()
    whitelist = User_Whitelist_Manager()

    def __str__(self):
        return self.tag
    
    @property
    def avatar(self):
        if self.avatar_id:
            return f'https://cdn.discordapp.com/avatars/{self.user_id}/{self.avatar_id}.png'
        else:
            return 'https://cdn.discordapp.com/embed/avatars/0.png'
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

        # these variables need to be updated in case the user changes anything
        self.tag = other.tag
        self.avatar_id = other.avatar_id

        self.messages += other.messages

        self.curse_word_count += other.curse_word_count
        self.ALL_CAPS_count += other.ALL_CAPS_count
        self.total_chars += other.total_chars

    class Meta:
        ordering = ['-messages']