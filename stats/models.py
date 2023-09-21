from django.db import models
import heapq
import timeit

class Guild(models.Model):

    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    icon = models.URLField()

class Channel(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    #guild = models.ForeignKey(Guild, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    last_processed_message_datetime = models.DateTimeField(null=True)


class User_Manager(models.Manager):
    def total_messages(self):
        return self.all().aggregate(models.Sum('messages'))['messages__sum']
    
    def top_user_message_count(self) -> int:
        return self.filter(blacklist=False).order_by('-messages').first().messages
    
    def top_n_user_curse_proportion(self, n):
        top_100_users = self.filter(blacklist=False).order_by('-messages')[:100]
        return heapq.nlargest(n, top_100_users, key = lambda user: user.curse_word_count / user.messages)
    def get_rank(self, user):
        return self.filter(blacklist=False, messages__gt=user.messages).count() + 1

class User(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    #guild = models.ForeignKey(Guild, on_delete=models.CASCADE)

    tag = models.CharField(max_length=32, unique=True)
    nick = models.CharField(max_length=32)
    avatar = models.URLField()
    messages = models.PositiveIntegerField(default=0)

    curse_word_count = models.PositiveIntegerField(default=0)
    ALL_CAPS_count = models.PositiveIntegerField(default=0)
    #laugh_count = models.PositiveIntegerField(default=0)
    total_chars = models.PositiveBigIntegerField(default=0)

    blacklist = models.BooleanField(default=False)

    objects = User_Manager()

    def __str__(self):
        return self.tag
    
    def update(self, other):
        '''
        Update the counts of one User with the counts of another, with the equivalent 
        Args:
            other (UserStat) - a model of the same type 
        '''

        # make absolutely sure that the correct models are being combined

        assert type(self) is type(other) # check that the objects are of the same class

        assert self.id == other.id # check that the users match 
        
        # check that the objects share the same user attribute, as well as the attribute unique to their class

        self.messages += other.messages
        self.curse_word_count += other.curse_word_count
        self.ALL_CAPS_count += other.ALL_CAPS_count
        self.total_chars += other.total_chars

class UserStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.user.tag} / count: {self.count}"
    
    
    def update(self, other):
        '''
        Update the count of one model with the counts of another, with the equivalent 
        Args:
            other (UserStat) - a model of the same type 
        '''

        # make absolutely sure that the correct models are being combined

        assert type(self) is type(other) # check that the objects are of the same class
        
        # check that the objects share the same user attribute, as well as the attribute unique to their class
        unneeded_attrs = ['_state', 'id', 'count']

        self_attrs = vars(self)
        for attr in self_attrs:
            if attr not in unneeded_attrs:
                assert getattr(self, attr) == getattr(other, attr)
        self.count += other.count

    class Meta:
        abstract = True
    

# every model here has an additional 'user' and 'count' field, thanks to the UserStat abc

class Channel_Count_Manager(models.Manager):
    def sorted_channels(self):
        #optimized
        sorted_channels = dict()
        for channel_count in self.all():
            if channel_count.channel_id in sorted_channels:
                sorted_channels[channel_count.channel_id] += channel_count.count
            else:
                sorted_channels[channel_count.channel_id] = channel_count.count
        
        sortedver = sorted(sorted_channels, key=lambda c: sorted_channels[c], reverse=True)
        return tuple((Channel.objects.get(id=key), sorted_channels[key], [channel_count.user for channel_count in self.filter(channel=key, user__blacklist=False).order_by('-count')[:5]]) for key in sortedver)

class Channel_Count(UserStat):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)

    objects = Channel_Count_Manager()

class Mention_Count_Manager(models.Manager):
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
            userpair = frozenset({mention_count.user_id, mention_count.mentioned_user_id})
            if userpair not in pairdict:
                pairdict[userpair] = mention_count
            else:
                other_mention_count = pairdict[userpair]
                logged_count = other_mention_count.count
                total = mention_count.count + logged_count
                n_tuple = (
                    total,
                    hash((mention_count.user_id, mention_count.mentioned_user_id)),
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
        return [(mention_count.mentioned_user, mention_count.count) for mention_count in self.filter(user=user, mentioned_user__blacklist=False).order_by('-count')[:n]]



class Mention_Count(UserStat):
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentioned_user')

    objects = Mention_Count_Manager()

class Hour_Count_Manager(models.Manager):
    def total_hour_counts(self) -> dict:
        hour_count_dict = dict()
        for hour in range(24):
            hour_objs = self.filter(hour=hour)
            hour_count_dict[hour] = hour_objs.aggregate(models.Sum('count'))['count__sum']
        return hour_count_dict
    
    def total_hour_count_max(self) -> int:
        return max(self.total_hour_counts().values())
    
    def user_hour_count_range(self, user: User, start: int, end: int):
        # optimized
        total = 0
        for hour_count in self.filter(user=user):
            if start <= hour_count.hour <= end:
                total += hour_count.count
        return total
    
    def top_n_users_in_range(self, n: int, start: int, end: int):
        # optimized
        user_dict = dict()
        for hour_count in self.filter(hour__range=(start, end), user__blacklist=False):
            user_id = hour_count.user_id
            if user_id in user_dict:
                user_dict[user_id][1] += hour_count.count
            else:
                user_dict[user_id] = [hour_count, hour_count.count]
        n_largest_users = heapq.nlargest(n, user_dict, key=lambda key: user_dict[key][1])
        return [(user_dict[key][0].user, user_dict[key][1]) for key in n_largest_users]
    
    def top_user_in_range_message_count(self, start, end):
        user, count = self.top_n_users_in_range(1, start, end)[0]
        return count
    
    def user_hour_counts(self, user):
        hour_counts = [0 for _ in range(24)]
        for hour_count in self.filter(user=user):
            hour_counts[hour_count.hour] = hour_count.count
        return hour_counts

        

class Hour_Count(UserStat):
    Hours = models.IntegerChoices(
        'Hours', 
        '12PM 1AM 2AM 3AM 4AM 5AM 6AM 7AM 8AM 9AM 10AM 11AM\
         12AM 1PM 2PM 3PM 4PM 5PM 6PM 7PM 8PM 9PM 10PM 11PM',
         start=0
         )
    
    hour = models.IntegerField(choices=Hours.choices)

    objects = Hour_Count_Manager()


class Date_Count_Manager(models.Manager):
    def first_message_date(self):
        return self.all().order_by('date').first().date
    
    def last_message_date(self):
        return self.all().order_by('date').last().date
    
    def total_days(self):
        return (self.last_message_date() - self.first_message_date()).days + 1
    
    def first_user_message_date(self, user: User):
        return self.filter(user=user).order_by('date').first().date
    
    def last_user_message_date(self, user: User):
        return self.filter(user=user).order_by('date').last().date
    
    def total_user_days(self, user: User):
        return (self.last_user_message_date(user) - self.first_user_message_date(user)).days + 1
    
    def total_user_active_days(self, user: User):
        return self.filter(user=user).count()
    def date_counts(self, past_n_days: int = None) -> dict:
        # needs optimizing
        '''returns a dictionary of how many messages were sent on every date
        past_n_days: allows the dict to be limited to the past n days. If None, returns all.'''
        dates_dict = dict()

        for obj in Date_Count.objects.all().order_by('-date')[:past_n_days]:
            filtered_objs = Date_Count.objects.filter(date=obj.date)
            dates_dict[obj.date] = filtered_objs.aggregate(models.Sum('count'))['count__sum']
        return dates_dict

    
class Date_Count(UserStat):
    date = models.DateField()

    objects = Date_Count_Manager()
    
class URL_Count_Manager(models.Manager):
    def top_n_URLs(self, n):
        #optimized (i think)
        urls = dict()
        for url_count in self.all():
            if url_count.URL in urls:
                urls[url_count.URL] += 1
            else:
                urls[url_count.URL] = 1
        return heapq.nlargest(n, urls.items(), key=lambda x: x[1])


class URL_Count(UserStat):
    URL = models.URLField()

    objects = URL_Count_Manager()


class Default_Emoji_Count_Manager(models.Manager):
    def sorted_user_default_emojis(self, user: User):
        return [obj.default_emoji for obj in self.filter(user=user).order_by('-count')]
    
class Default_Emoji_Count(UserStat):
    default_emoji = models.CharField(max_length=1)

    objects = Default_Emoji_Count_Manager()


class Custom_Emoji_Count_Manager(models.Manager):
    def sorted_user_custom_emojis(self, user: User):
        return [obj.custom_emoji for obj in self.filter(user=user).order_by('-count')]
    
class Custom_Emoji_Count(UserStat):
    custom_emoji = models.URLField()

    objects = Custom_Emoji_Count_Manager()


class Unique_Word_Count_Manager(models.Manager):
    def top_n_unqiue_words(self, n):
        words = dict()
        for word_count in self.all():
            if word_count.word in words:
                words[word_count.word] += 1
            else:
                words[word_count.word] = 1
        return heapq.nlargest(n, words.items(), key=lambda x: x[1])
    
    def sorted_unique_user_words(self, user: User):
        return [obj.word for obj in self.filter(user=user).order_by('-count')]
    
class Unique_Word_Count(UserStat):
    word = models.CharField(max_length=18) 

    objects = Unique_Word_Count_Manager()