from django.db import models
from django.db.models import Sum
import heapq
from collections import Counter
from timeit import default_timer
import datetime

import json
# for the emoji class
with open('stats/data/emoji_ids.json') as f:
    EMOJI_IDS = json.load(f)
    EMOJI_DICT = {v: k for k, v in EMOJI_IDS.items()} # {id: emoji}

def get_twemoji_URL(emoji_str: str) -> str:
    '''
    Given an emoji, return the corresponding twemoji URL
    Ref: https://github.com/twitter/twemoji/blob/master/scripts/build.js#L344
    '''
    # from Twemoji source code:
    # remove all variants (0xfe0f)
    # UNLESS there is a zero width joiner (0x200d)
    VS16 = 0xfe0f
    ZWJ = 0x200d
    hex_ints = [ord(unichar) for unichar in emoji_str]
    if ZWJ not in hex_ints:
        hex_ints = [hex_int for hex_int in hex_ints if hex_int != VS16]
    codepoint = '-'.join([format(hex_int, 'x') for hex_int in hex_ints])
    return f'https://raw.githubusercontent.com/twitter/twemoji/d94f4cf793e6d5ca592aa00f58a88f6a4229ad43/assets/svg/{codepoint}.svg'

# wrapper that times function execution. for debugging purposes
def timed(func):
    def wrap(*args, **kwargs):
        start = default_timer()
        
        result = func(*args, **kwargs)
        
        end = default_timer()
        print(f'"{func.__qualname__}" call speed: {end - start}')
        return result
    return wrap



class Guild(models.Model):

    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    icon = models.URLField()
    first_message_dt = models.DateTimeField(null=True)
    last_message_dt = models.DateTimeField(null=True)
    #timezone = models.CharField(max_length=32, default='utc')

class Channel(models.Model):
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    last_message_dt = models.DateTimeField(null=True)


class Emoji_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = ['name'],
            unique_fields = ['id']
        )


class Emoji(models.Model):
    id = models.BigIntegerField(primary_key=True)
    custom = models.BooleanField()
    name = models.CharField(max_length=76) # length of the longest emoji name I could find

    objects = Emoji_Manager()
    
    @property
    def URL(self):
        if self.custom:
            return f'https://cdn.discordapp.com/emojis/{self.id}'
        else:
            emoji_str = EMOJI_DICT[self.id]
            return get_twemoji_URL(emoji_str)
        
    def merge(self, other):
        '''
        Update name if it changes
        Args:
            other (UserStat) - a model of the same type 
        '''
        self.name = other.name
    def __str__(self):
        return self.name

class User_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        fields = self.model._meta.get_fields()
        non_update_fields = ['guild', 'id', 'user_id', 'blacklist']
        update_fields = [field.name for field in fields if (not field.is_relation and field.name not in non_update_fields)]
        await self.abulk_create(
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
    nick = models.CharField(max_length=32)
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
        self.nick = other.nick
        self.avatar_id = other.avatar_id

        self.messages += other.messages

        self.curse_word_count += other.curse_word_count
        self.ALL_CAPS_count += other.ALL_CAPS_count
        self.total_chars += other.total_chars

    class Meta:
        ordering = ['-messages']

class UserStat_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        update_fields = ['count']
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = update_fields,
            unique_fields = ['id']
        )

    def cull(self):
        '''deletes all objects with a count equal to 1'''
        self.filter(count=1).delete()
    
    @timed
    def top_n_objs(self, guild: Guild, n: int = None):
        objs = Counter()
        for obj, count in self.filter(user__guild=guild).values_list('obj', 'count'):
            objs[obj] += count
        if n is None:
            return objs.most_common()
        else:
            return objs.most_common(n)
    @timed
    def top_n_user_objs(self, user: User, n: int):
        return self.filter(user=user)[:n]



class UserStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    objects = UserStat_Manager()

    def __str__(self):
        return f"{self.user.tag} / count: {self.count}"
    
    def merge(self, other):
        '''
        Update the count of one model with the counts of another, with the equivalent 
        Args:
            other (UserStat) - a model of the same type 
        '''
        self.count += other.count

    class Meta:
        abstract = True
        ordering = ['-count']
    

# every model here has an additional 'user' and 'count' field, thanks to the UserStat abc

class Channel_Count_Manager(UserStat_Manager):
    @timed
    def sorted_channels(self, guild: Guild):
        return
        channels = self.top_n_objs(guild)
        #for chann

        #return tuple(
            #(Channel.objects.get(id=key), 
             #sorted_channels[key], 
             #[channel_count.user for channel_count in self.filter(obj=key, user__blacklist=False).order_by('-count')[:5]]) for key in sortedver)

class Channel_Count(UserStat):
    obj = models.ForeignKey(Channel, on_delete=models.CASCADE)

    objects = Channel_Count_Manager()

class Mention_Count_Manager(UserStat_Manager):
    @timed
    def top_n_mention_pairs(self, guild: Guild, n):
        '''
        Returns a list of four-element tuples containing info about the top n pairs of users who mention each other:
        (user1, user2, user1count, user2count)
        where the fourth and fifth ints represent the number of times that one user has mentioned the other 
        The algorithm uses a heap to find the top n elements in optimized time 
        '''
        # optimized
        top_n_tuples = list()
        pairdict = dict()
        for mention_count in self.filter(user__guild=guild, user__blacklist=False):
            userpair = frozenset({mention_count.user_id, mention_count.obj_id})
            if userpair not in pairdict:
                pairdict[userpair] = mention_count
            else:
                other_mention_count = pairdict[userpair]
                logged_count = other_mention_count.count
                total = mention_count.count + logged_count
                n_tuple = (
                    total,
                    hash((mention_count.user_id, mention_count.obj_id)),
                    mention_count,
                    pairdict[userpair]
                )
                if len(top_n_tuples) < n:
                    heapq.heappush(top_n_tuples, n_tuple)
                elif total > top_n_tuples[0][0]:
                    heapq.heappushpop(top_n_tuples, n_tuple)
        top_n_tuples_result = list()
        for n_tuple in sorted(top_n_tuples, key=lambda t: t[0], reverse=True):
            total, _, mention_count_1, mention_count_2 = n_tuple
            top_n_tuples_result.append((
                mention_count_1.user,
                mention_count_2.user,
                mention_count_1.count,
                mention_count_2.count,
            ))
        return top_n_tuples_result
    
    def top_n_user_mentions(self, user, n):
        return [(mention_count.obj, mention_count.count) for mention_count in self.filter(user=user, obj__blacklist=False).order_by('-count')[:n]]

class Mention_Count(UserStat):
    obj = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentioned_user')

    objects = Mention_Count_Manager()

class Hour_Count_Manager(UserStat_Manager):
    @timed
    def total_hour_counts(self, guild: Guild) -> dict:
        hour_count_dict = dict()
        for hour in range(24):
            hour_objs = self.filter(user__guild=guild, obj=hour)
            hour_sum = hour_objs.aggregate(models.Sum('count'))['count__sum']
            hour_count_dict[hour] = hour_sum if hour_sum is not None else 0
        return hour_count_dict
    
    def user_hour_count_range(self, user: User, start: int, end: int):
        # optimized
        return Hour_Count.objects.filter(user=user, obj__range=(start,end)).aggregate(Sum('count'))['count__sum']
    @timed
    def top_n_users_in_range(self, guild: Guild, n: int, start: int, end: int):
        '''
        Return a list of tuples of length 2, with each tuple containing the user obj,
        and the total count for the range
        '''
        # optimized
        user_dict = Counter()
        for hour_count in self.filter(user__guild=guild, obj__range=(start, end), user__blacklist=False).select_related("user"):
            user_dict[hour_count.user] += hour_count.count
        n_largest_users = heapq.nlargest(n, user_dict.items(), key=lambda item: item[1])
        return n_largest_users
    
    def top_user_in_range_message_count(self, start, end):
        user, count = self.top_n_users_in_range(1, start, end)[0]
        return count
    
    def user_hour_counts(self, user):
        hour_counts = [0 for _ in range(24)]
        for hour_count in self.filter(user=user):
            hour_counts[hour_count.obj] = hour_count.count
        return hour_counts
    
        

class Hour_Count(UserStat):
    Hours = models.IntegerChoices(
        'Hours', 
        '12PM 1AM 2AM 3AM 4AM 5AM 6AM 7AM 8AM 9AM 10AM 11AM\
         12AM 1PM 2PM 3PM 4PM 5PM 6PM 7PM 8PM 9PM 10PM 11PM',
         start=0
    )
    
    obj = models.PositiveSmallIntegerField(choices=Hours.choices)

    objects = Hour_Count_Manager()



class Date_Count_Manager(UserStat_Manager):
    @timed
    def total_days(self, guild: Guild):
        return (self.last_message_date(guild) - self.first_message_date(guild)).days + 1
    @timed
    def first_message_date(self, guild: Guild):
        return self.filter(user__guild=guild).earliest().obj
    @timed
    def last_message_date(self, guild: Guild):
        return self.filter(user__guild=guild).latest().obj
    
    def first_user_message_date(self, user: User):
        return self.filter(user=user).earliest().obj
    
    def last_user_message_date(self, user: User):
        return self.filter(user=user).latest().obj
    
    def total_user_days(self, user: User):
        return (self.last_user_message_date(user) - self.first_user_message_date(user)).days + 1
    
    def total_user_active_days(self, user: User):
        return self.filter(user=user).count()
    @timed
    def date_counts_as_str(self, obj) -> dict:
        # optimized-ish
        '''returns a dictionary of how many messages were sent on every date
        past_n_days: allows the dict to be limited to the past n days. If None, returns all.'''
        date_strs = list()
        if type(obj) is User:
            date_sums = list(self.filter(user=obj).values_list('obj').order_by('-obj').annotate(Sum('count')))
        elif type(obj) is Guild:
            date_sums = list(self.filter(user__guild=obj).values_list('obj').order_by('-obj').annotate(Sum('count')))
        date = self.earliest().obj
        last = self.latest().obj
        while date <= last:
            if len(date_sums) != 0 and date == date_sums[-1][0]:
                date_pair = date_sums.pop()
                date_strs.append((date_pair[0].strftime("%m/%d/%Y"), date_pair[1]))
            else:
                date_strs.append((date.strftime("%m/%d/%Y"), 0))
            date += datetime.timedelta(days=1)
        return date_strs
    @timed
    def weekday_distribution(self, guild: Guild):
        weekdays = [0] * 7
        for date_obj in self.filter(user__guild=guild).iterator():
            weekdays[date_obj.obj.weekday()] += date_obj.count
        return weekdays
    
    def weekday_distribution_user(self, user):
        weekdays = [0] * 7
        for date_obj in self.filter(user=user).iterator():
            weekdays[date_obj.obj.weekday()] += date_obj.count
        return weekdays
    
class Date_Count(UserStat):
    obj = models.DateField()

    objects = Date_Count_Manager()

    class Meta:
        ordering = ['-obj']
        get_latest_by = ['obj']
    
class URL_Count_Manager(UserStat_Manager):
    pass


class URL_Count(UserStat):
    obj = models.URLField()

    objects = URL_Count_Manager()


class Emoji_Count_Manager(UserStat_Manager):
    @timed
    def top_n_emojis(self, guild: Guild, n):
        emojis = Counter()
        for emoji_count in self.filter(user__guild=guild):
            emojis[emoji_count.obj] += emoji_count.count
        return emojis.most_common(n)
    def sorted_user_emojis(self, user: User):
        return [obj.emoji for obj in self.filter(user=user).order_by('-count')]
    
class Emoji_Count(UserStat):
    obj = models.ForeignKey(Emoji, on_delete=models.CASCADE)

    objects = Emoji_Count_Manager()


class Unique_Word_Count_Manager(UserStat_Manager):
    def top_n_user_words(self, user: User, n):
        return list(self.filter(user=user)[:n].values_list('obj', 'count'))
    

class Unique_Word_Count(UserStat):
    obj = models.CharField(max_length=18) 

    objects = Unique_Word_Count_Manager()


class Reaction_Count_Manager(UserStat_Manager):
    pass


class Reaction_Count(UserStat):
    obj = models.ForeignKey(Emoji, on_delete=models.CASCADE)

    objects = Reaction_Count_Manager()