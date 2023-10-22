from django.db import models
from django.db.models import Sum
import heapq
from collections import Counter
import timeit
import datetime


class Guild(models.Model):

    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    icon = models.URLField()

class Channel_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        update_fields = ['name', 'last_processed_message_datetime']
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = update_fields,
            unique_fields = ['id']
        )

class Channel(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    last_processed_message_datetime = models.DateTimeField(null=True)
    objects = Channel_Manager()

class Emoji_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = ['name', 'count'],
            unique_fields = ['URL']
        )
class Emoji(models.Model):
    URL = models.URLField(primary_key=True)
    name = models.CharField(max_length=76) # length of the longest emoji name I could find
    count = models.PositiveIntegerField(default=0)

    objects = Emoji_Manager()
    
    def merge(self, other):
        '''
        Update the count of one model with the counts of another, with the equivalent 
        Args:
            other (UserStat) - a model of the same type 
        '''
        self.name = other.name
        self.count += other.count
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-count']

class User_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        fields = self.model._meta.get_fields()
        non_update_fields = ['id', 'blacklist']
        update_fields = [field.name for field in fields if (not field.is_relation and field.name not in non_update_fields)]
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = update_fields,
            unique_fields = ['id']
        )

    def total_messages(self):
        '''Return the total number of messages ever sent for a server'''
        return self.all().aggregate(models.Sum('messages'))['messages__sum']
    
    def top_user_message_count(self) -> int:
        return self.all().first().messages
    
    def top_n_curse_users(self, n):
        top_100_users = self.all()[:100]
        return heapq.nlargest(n, top_100_users, key = lambda user: user.curse_word_count / user.messages)
    
    def top_n_ALL_CAPS_users(self, n):
        top_100_users = self.all()[:100]
        return heapq.nlargest(n, top_100_users, key = lambda user: user.ALL_CAPS_count / user.messages)
    
    def top_n_verbose_users(self, n):
        top_100_users = self.all()[:100]
        return heapq.nlargest(n, top_100_users, key = lambda user: user.total_chars / user.messages)
    
    def get_rank(self, user):
        return self.filter(messages__gt=user.messages).count() + 1

class User_Whitelist_Manager(User_Manager):
    def get_queryset(self):
        return super().get_queryset().filter(blacklist=False)


class User(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)

    tag = models.CharField(max_length=32, unique=True)
    nick = models.CharField(max_length=32)
    avatar = models.URLField()
    messages = models.PositiveIntegerField(default=0)

    curse_word_count = models.PositiveIntegerField(default=0)
    ALL_CAPS_count = models.PositiveIntegerField(default=0)
    total_chars = models.PositiveBigIntegerField(default=0)

    blacklist = models.BooleanField(default=False)

    objects = User_Manager()
    whitelist = User_Whitelist_Manager()

    def __str__(self):
        return self.tag
    
    def merge(self, other):
        '''
        Update the counts of one User with the counts of another, with the equivalent 
        Args:
            other (UserStat) - a model of the same type 
        '''

        # check that the objects share the same user attribute, as well as the attribute unique to their class
        self.tag = other.tag
        self.nick = other.nick
        self.avatar = other.avatar 

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

    def top_n_objs(self, n: int):
        objs = Counter()
        for obj, count in self.values_list('obj', 'count'):
            objs[obj] += count
        return objs.most_common(n)
    
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
    def sorted_channels(self):

        #optimized
        sorted_channels = dict()
        for channel_count in self.all():
            if channel_count.obj_id in sorted_channels:
                sorted_channels[channel_count.obj_id] += channel_count.count
            else:
                sorted_channels[channel_count.obj_id] = channel_count.count
        
        sortedver = sorted(sorted_channels, key=lambda c: sorted_channels[c], reverse=True)
        return tuple((Channel.objects.get(id=key), sorted_channels[key], [channel_count.user for channel_count in self.filter(obj=key, user__blacklist=False).order_by('-count')[:5]]) for key in sortedver)

class Channel_Count(UserStat):
    obj = models.ForeignKey(Channel, on_delete=models.CASCADE)

    objects = Channel_Count_Manager()

class Mention_Count_Manager(UserStat_Manager):
    def top_n_mention_pairs(self, n):
        '''
        Returns a list of four-element tuples containing info about the top n pairs of users who mention each other:
        (user1, user2, user1count, user2count)
        where the fourth and fifth ints represent the number of times that one user has mentioned the other 
        The algorithm uses a heap to find the top n elements in optimized time 
        '''
        # optimized
        top_n_tuples = list()
        pairdict = dict()
        for mention_count in self.filter(user__blacklist=False):
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
    def total_hour_counts(self) -> dict:
        hour_count_dict = dict()
        for hour in range(24):
            hour_objs = self.filter(obj=hour)
            hour_count_dict[hour] = hour_objs.aggregate(models.Sum('count'))['count__sum']
        return hour_count_dict
    
    def user_hour_count_range(self, user: User, start: int, end: int):
        # optimized
        return Hour_Count.objects.filter(user=user, obj__range=(start,end)).aggregate(Sum('count'))['count__sum']
    
    def top_n_users_in_range(self, n: int, start: int, end: int):
        '''
        Return a list of tuples of length 2, with each tuple containing the user obj,
        and the total count for the range
        '''
        # optimized
        user_dict = Counter()
        for hour_count in self.filter(obj__range=(start, end), user__blacklist=False).select_related("user"):
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
    
    obj = models.IntegerField(choices=Hours.choices)

    objects = Hour_Count_Manager()



class Date_Count_Manager(UserStat_Manager):
    def total_days(self):
        return (self.latest().obj - self.earliest().obj).days + 1
    
    def first_user_message_date(self, user: User):
        return self.filter(user=user).earliest().obj
    
    def last_user_message_date(self, user: User):
        return self.filter(user=user).latest().obj
    
    def total_user_days(self, user: User):
        return (self.last_user_message_date(user) - self.first_user_message_date(user)).days + 1
    
    def total_user_active_days(self, user: User):
        return self.filter(user=user).count()
    
    def date_counts_as_str(self, user: User = None) -> dict:
        # optimized-ish
        '''returns a dictionary of how many messages were sent on every date
        past_n_days: allows the dict to be limited to the past n days. If None, returns all.'''
        date_strs = list()
        if user:
            date_sums = list(self.filter(user=user).values_list('obj').order_by('-obj').annotate(Sum('count')))
        else:
            date_sums = list(self.values_list('obj').order_by('-obj').annotate(Sum('count')))
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
    
    def weekday_distribution(self):
        start = timeit.default_timer()
        weekdays = [0] * 7
        for date_obj in self.all().iterator():
            weekdays[date_obj.obj.weekday()] += date_obj.count
        return weekdays
    def weekday_distribution_user(self, user):
        start = timeit.default_timer()
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
    def top_n_URLs(self, n):
        #optimized (i think)
        urls = dict()
        for url_count in self.all():
            if url_count.obj in urls:
                urls[url_count.obj] += 1
            else:
                urls[url_count.obj] = 1
        return heapq.nlargest(n, urls.items(), key=lambda x: x[1])


class URL_Count(UserStat):
    obj = models.URLField(max_length=255)

    objects = URL_Count_Manager()


class Emoji_Count_Manager(UserStat_Manager):
    def top_n_emojis(self, n):
        emojis = Counter()
        for emoji, count in self.values_list('obj', 'count'):
            emojis[emoji] += count
        return emojis.most_common(n)
    
    def sorted_user_emojis(self, user: User):
        return [obj.emoji for obj in self.filter(user=user).order_by('-count')]
    
class Emoji_Count(UserStat):
    obj = models.ForeignKey(Emoji, on_delete=models.CASCADE)

    objects = Emoji_Count_Manager()


class Unique_Word_Count_Manager(UserStat_Manager):
    def top_n_words(self, n):
        words = Counter()
        for word, count in self.values_list('obj', 'count'):
            words[word] += count
        return words.most_common(n)

    def top_n_user_words(self, user: User, n):
        return list(self.filter(user=user)[:n].values_list('obj', 'count'))
    def speedtest(self):
        start = timeit.default_timer()
        for obj in self.all().select_related("user").iterator():
            pass

class Unique_Word_Count(UserStat):
    obj = models.CharField(max_length=18) 

    objects = Unique_Word_Count_Manager()