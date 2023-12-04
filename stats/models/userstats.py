from django.db import models

from . import Channel, Emoji, Guild, GuildUser

from .debug import timed

from collections import Counter
import datetime
import heapq

class UserStat_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        update_fields = ['count']
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = update_fields,
            unique_fields = ['id']
        )
    
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
    def top_n_user_objs(self, user: GuildUser, n: int):
        return self.filter(user=user)[:n]

class UserStat(models.Model):
    user = models.ForeignKey(GuildUser, on_delete=models.CASCADE)
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
        for mention_count in self.filter(user__guild=guild, user__hidden=False):
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
        return [(mention_count.obj, mention_count.count) for mention_count in self.filter(user=user, obj__hidden=False).order_by('-count')[:n]]

class Mention_Count(UserStat):
    obj = models.ForeignKey(GuildUser, on_delete=models.CASCADE, related_name='mentioned_user')

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
    
    def user_hour_count_range(self, user: GuildUser, start: int, end: int):
        # optimized
        return Hour_Count.objects.filter(user=user, obj__range=(start,end)).aggregate(models.Sum('count'))['count__sum']
    @timed
    def top_n_users_in_range(self, guild: Guild, n: int, start: int, end: int):
        '''
        Return a list of tuples of length 2, with each tuple containing the user obj,
        and the total count for the range
        '''
        # optimized
        user_dict = Counter()
        for hour_count in self.filter(user__guild=guild, obj__range=(start, end), user__hidden=False).select_related("user"):
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
    
    def first_user_message_date(self, user: GuildUser):
        return self.filter(user=user).earliest().obj
    
    def last_user_message_date(self, user: GuildUser):
        return self.filter(user=user).latest().obj
    
    def total_user_days(self, user: GuildUser):
        return (self.last_user_message_date(user) - self.first_user_message_date(user)).days + 1
    
    def total_user_active_days(self, user: GuildUser):
        return self.filter(user=user).count()
    @timed
    def date_counts_as_str(self, obj) -> dict:
        # optimized-ish
        '''returns a dictionary of how many messages were sent on every date
        past_n_days: allows the dict to be limited to the past n days. If None, returns all.'''
        date_strs = list()
        if type(obj) is GuildUser:
            date_sums = list(self.filter(user=obj).values_list('obj').order_by('-obj').annotate(models.Sum('count')))
        elif type(obj) is Guild:
            date_sums = list(self.filter(user__guild=obj).values_list('obj').order_by('-obj').annotate(models.Sum('count')))
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
        weekday_counts = list()
        for weekday in range(1, 8):
            total = self.filter(user__guild=guild, obj__week_day=weekday).aggregate(models.Sum('count'))['count__sum']
            if total is None:
                weekday_counts.append(0)
            else:
                weekday_counts.append(total)
        return weekday_counts
    
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
    def sorted_user_emojis(self, user: GuildUser):
        return [obj.emoji for obj in self.filter(user=user).order_by('-count')]
    
class Emoji_Count(UserStat):
    obj = models.ForeignKey(Emoji, on_delete=models.CASCADE)

    objects = Emoji_Count_Manager()


class Unique_Word_Count_Manager(UserStat_Manager):
    def top_n_user_words(self, user: GuildUser, n):
        return list(self.filter(user=user)[:n].values_list('obj', 'count'))
    

class Unique_Word_Count(UserStat):
    obj = models.CharField(max_length=18) 

    objects = Unique_Word_Count_Manager()


class Reaction_Count_Manager(UserStat_Manager):
    pass


class Reaction_Count(UserStat):
    obj = models.ForeignKey(Emoji, on_delete=models.CASCADE)

    objects = Reaction_Count_Manager()