from django.db import models

class Guild(models.Model):

    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    icon = models.URLField()

class Channel(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    last_processed_message_datetime = models.DateTimeField(null=True)


class User_Manager(models.Manager):
    def number_of_users(self):
        return len(self.all())
    
    def total_messages(self):
        return self.all().aggregate(models.Sum('messages'))['messages__sum']
    
    def top_user_message_count(self) -> int:
        return self.all().order_by('-messages').first().messages
    
    def top_n_user_curse_proportion(self, n):
        top_100_users = self.all().order_by('-messages')[:100]
        return sorted(top_100_users, key = lambda user: user.curse_word_count / user.messages, reverse=True)[:n]

class User(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)

    tag = models.CharField(max_length=32)
    nick = models.CharField(max_length=32)
    avatar = models.URLField()
    messages = models.PositiveIntegerField(default=0)
    curse_word_count = models.PositiveIntegerField(default=0)

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
        
        # check that the objects share the same user attribute, as well as the attribute unique to their class
        unneeded_attrs = ['_state', 'id', 'messages', 'curse_word_count']

        self_attrs = vars(self)
        for attr in self_attrs:
            if attr not in unneeded_attrs:
                assert getattr(self, attr) == getattr(other, attr)

        self.messages += other.messages
        self.curse_word_count += other.curse_word_count

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

class Channel_Count(UserStat):
    channel_id = models.PositiveBigIntegerField()


class Mention_Count(UserStat):
    mentioned_user_id = models.PositiveBigIntegerField()


class Hour_Count_Manager(models.Manager):
    def total_hour_counts(self) -> dict:
        hour_count_dict = dict()
        for hour in range(24):
            hour_objs =  self.filter(hour=hour)
            hour_count_dict[hour] = hour_objs.aggregate(models.Sum('count'))['count__sum']
        return hour_count_dict
    
    def total_hour_count_max(self) -> int:
        return max(self.total_hour_counts().values())
    
    def user_hour_count_range(self, user: User, start: int, end: int):
        total = 0
        for hour in range(start, end+1):
            if self.filter(user=user, hour=hour).exists():
                total += self.get(user=user, hour=hour).count
        return total
    
    def top_n_users_in_range(self, n: int, start: int, end: int):
        user_dict = dict()
        for hour in range(start, end+1):
            for hour_count_obj in self.filter(hour=hour):
                user = hour_count_obj.user
                if user in user_dict:
                    user_dict[user] += hour_count_obj.count
                else:
                    user_dict[user] = hour_count_obj.count
        return sorted(user_dict.items(), key=lambda k: user_dict[k[0]], reverse=True)[:10]
    
    def top_user_in_range_message_count(self, start, end):
        user, count = self.top_n_users_in_range(1, start, end)[0]
        return count
        

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
    
    def date_counts(self, past_n_days: int = None) -> dict:
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
    

class URL_Count(UserStat):
    URL = models.URLField()


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
    def sorted_unique_user_words(self, user: User):
        return [obj.word for obj in self.filter(user=user).order_by('-count')]
    
class Unique_Word_Count(UserStat):
    word = models.CharField(max_length=18) 

    objects = Unique_Word_Count_Manager()