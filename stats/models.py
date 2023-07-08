from django.db import models

class Guild(models.Model):

    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    icon = models.URLField()

class Channel(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    last_processed_message_id = models.PositiveBigIntegerField(null=True)

class User(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)

    tag = models.CharField(max_length=32)
    nick = models.CharField(max_length=32)
    avatar = models.URLField()

    curse_word_count = models.PositiveIntegerField()


class UserStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.PositiveIntegerField()

    class Meta:
        abstract = True

# every model here has an additional 'user' and 'count' field, thanks to the UserStat abc

class Channel_Count(UserStat):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)

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

class Date_Count(UserStat):
    date = models.DateField()

class URL_Count(UserStat):
    URL = models.URLField()

class Default_Emoji_Count(UserStat):
    default_emoji = models.CharField(max_length=1)

class Custom_Emoji_Count(UserStat):
    custom_emoji = models.URLField()

class Unique_Word_Count(UserStat):
    word = models.CharField(max_length=18) 