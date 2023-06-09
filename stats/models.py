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


class UserStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.user.tag} / count: {self.count}"
    
    class Meta:
        abstract = True
    

# every model here has an additional 'user' and 'count' field, thanks to the UserStat abc

class Channel_Count(UserStat):
    channel_id = models.PositiveBigIntegerField()


class Mention_Count(UserStat):
    mentioned_user_id = models.PositiveBigIntegerField()


class Hour_Count(UserStat):
    Hours = models.IntegerChoices(
        'Hours', 
        '12PM 1AM 2AM 3AM 4AM 5AM 6AM 7AM 8AM 9AM 10AM 11AM\
         12AM 1PM 2PM 3PM 4PM 5PM 6PM 7PM 8PM 9PM 10PM 11PM',
         start=0
         )
    
    hour = models.IntegerField(choices=Hours.choices)


class Date_Count_Manager(models.Manager):
    def first_message_date(self):
        return self.all().order_by('date')[0].date
    
    def last_message_date(self):
        return self.all().order_by('-date')[0].date
    
    def total_days(self):
        return (self.last_message_date() - self.first_message_date()).days + 1
    
    def first_user_message_date(self, user: User):
        return self.filter(user=user).order_by('date')[0].date
    
    def last_user_message_date(self, user: User):
        return self.filter(user=user).order_by('date')[0].date
    
    def total_user_days(self, user: User):
        return (self.last_user_message_date(user) - self.first_user_message_date(user)).days + 1
    
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