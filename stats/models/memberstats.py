from django.db import models

from . import Channel, Emoji, Guild, Member

from .debug import timed

from collections import Counter
import datetime
import heapq

class MemberStat_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        update_fields = ['count']
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = update_fields,
            unique_fields = ['id']
        )
    
    @timed
    def guild_top_n(self, guild: Guild, n: int = None) -> list[tuple['models.MemberStat', int]]:
        objs = Counter()
        for model_obj in self.filter(member__guild=guild).only('obj', 'count'):
            objs[model_obj.obj] += model_obj.count
        if n is None:
            return objs.most_common()
        else:
            return objs.most_common(n)
    @timed
    def member_top_n(self, member: Member, n: int) -> list['models.MemberStat']:
        return list(self.filter(member=member).order_by('-count')[:n])

class MemberStat(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    objects = MemberStat_Manager()

    def __str__(self):
        return f"{self.member.user.tag} / count: {self.count}"
    
    def merge(self, other):
        '''
        Update the count of one model with the counts of another, with the equivalent 
        Args:
            other (MemberStat) - a model of the same type 
        '''
        self.count += other.count

    class Meta:
        abstract = True
        ordering = ['-count']
    

# every model here has an additional 'member' and 'count' field, thanks to the UserStat abc

class Channel_Count_Manager(MemberStat_Manager):
    @timed
    def sorted_channels(self, guild: Guild):
        return
        channels = self.top_n_objs(guild)
        #for chann

        #return tuple(
            #(Channel.objects.get(id=key), 
             #sorted_channels[key], 
             #[channel_count.user for channel_count in self.filter(obj=key, user__blacklist=False).order_by('-count')[:5]]) for key in sortedver)

class Channel_Count(MemberStat):
    obj = models.ForeignKey(Channel, on_delete=models.CASCADE)

    objects = Channel_Count_Manager()

class Mention_Count_Manager(MemberStat_Manager):
    @timed
    def top_n_mention_pairs(self, guild: Guild, n):
        '''
        Return a list of four-element tuples containing info about the top n pairs of users who mention each other:
        (user1, user2, user1count, user2count)
        where the fourth and fifth ints represent the number of times that one user has mentioned the other 
        The algorithm uses a heap to find the top n elements in optimized time 
        '''
        # optimized
        top_n_tuples = list()
        pairdict = dict()
        for mention_count in self.filter(member__guild=guild, member__hidden=False):
            memberpair = frozenset({mention_count.member_id, mention_count.obj_id})
            if memberpair not in pairdict:
                pairdict[memberpair] = mention_count
            else:
                other_mention_count = pairdict[memberpair]
                logged_count = other_mention_count.count
                total = mention_count.count + logged_count
                n_tuple = (
                    total,
                    hash((mention_count.member_id, mention_count.obj_id)),
                    mention_count,
                    pairdict[memberpair]
                )
                if len(top_n_tuples) < n:
                    heapq.heappush(top_n_tuples, n_tuple)
                elif total > top_n_tuples[0][0]:
                    heapq.heappushpop(top_n_tuples, n_tuple)
        top_n_tuples_result = list()
        for n_tuple in sorted(top_n_tuples, key=lambda t: t[0], reverse=True):
            total, _, mention_count_1, mention_count_2 = n_tuple
            top_n_tuples_result.append((
                mention_count_1.member,
                mention_count_2.member,
                mention_count_1.count,
                mention_count_2.count,
            ))
        return top_n_tuples_result
    
    def top_n_member_mentions(self, member, n):
        return [(mention_count.obj, mention_count.count) for mention_count in self.filter(member=member, obj__hidden=False).order_by('-count')[:n]]

class Mention_Count(MemberStat):
    obj = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='mentioned_member')

    objects = Mention_Count_Manager()


class Hour_Count(MemberStat):
    Hours = models.IntegerChoices(
        'Hours', 
        '12PM 1AM 2AM 3AM 4AM 5AM 6AM 7AM 8AM 9AM 10AM 11AM\
         12AM 1PM 2PM 3PM 4PM 5PM 6PM 7PM 8PM 9PM 10PM 11PM',
         start=0
    )
    
    obj = models.PositiveSmallIntegerField(choices=Hours.choices)



class Date_Count_Manager(MemberStat_Manager):
    @timed
    def total_days(self, guild: Guild):
        return (self.last_message_date(guild) - self.first_message_date(guild)).days + 1
    @timed
    def first_message_date(self, guild: Guild):
        return self.filter(member__guild=guild).earliest().obj
    @timed
    def last_message_date(self, guild: Guild):
        return self.filter(member__guild=guild).latest().obj
    
    def first_member_message_date(self, member: Member):
        return self.filter(member=member).earliest().obj
    
    def last_member_message_date(self, member: Member):
        return self.filter(member=member).latest().obj
    
    def total_member_days(self, member: Member):
        return (self.last_member_message_date(member) - self.first_member_message_date(member)).days + 1
    
    def total_member_active_days(self, member: Member):
        return self.filter(member=member).count()
    @timed
    def date_counts_as_str(self, obj) -> dict:
        # optimized-ish
        '''returns a dictionary of how many messages were sent on every date
        past_n_days: allows the dict to be limited to the past n days. If None, returns all.'''
        date_strs = list()
        if type(obj) is Member:
            date_sums = list(self.filter(member=obj).values_list('obj').order_by('-obj').annotate(models.Sum('count')))
        elif type(obj) is Guild:
            date_sums = list(self.filter(member__guild=obj).values_list('obj').order_by('-obj').annotate(models.Sum('count')))
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
            total = self.filter(member__guild=guild, obj__week_day=weekday).aggregate(models.Sum('count'))['count__sum']
            if total is None:
                weekday_counts.append(0)
            else:
                weekday_counts.append(total)
        return weekday_counts
    
    def weekday_distribution_member(self, member):
        weekdays = [0] * 7
        for date_obj in self.filter(member=member).iterator():
            weekdays[date_obj.obj.weekday()] += date_obj.count
        return weekdays
    
class Date_Count(MemberStat):
    obj = models.DateField()

    objects = Date_Count_Manager()

    class Meta:
        ordering = ['-obj']
        get_latest_by = ['obj']
    
class URL_Count_Manager(MemberStat_Manager):
    pass


class URL_Count(MemberStat):
    obj = models.URLField()

    objects = URL_Count_Manager()


class Emoji_Count_Manager(MemberStat_Manager):
    @timed
    def top_n_emojis(self, guild: Guild, n):
        emojis = Counter()
        for emoji_count in self.filter(member__guild=guild):
            emojis[emoji_count.obj] += emoji_count.count
        return emojis.most_common(n)
    def sorted_member_emojis(self, member: Member):
        return [obj.emoji for obj in self.filter(member=member).order_by('-count')]
    
class Emoji_Count(MemberStat):
    obj = models.ForeignKey(Emoji, on_delete=models.CASCADE)

    objects = Emoji_Count_Manager()


class Unique_Word_Count_Manager(MemberStat_Manager):
    def top_n_member_words(self, member: Member, n):
        return list(self.filter(member=member)[:n].values_list('obj', 'count'))
    

class Unique_Word_Count(MemberStat):
    obj = models.CharField(max_length=15) 

    objects = Unique_Word_Count_Manager()


class Reaction_Count_Manager(MemberStat_Manager):
    pass


class Reaction_Count(MemberStat):
    obj = models.ForeignKey(Emoji, on_delete=models.CASCADE)

    objects = Reaction_Count_Manager()