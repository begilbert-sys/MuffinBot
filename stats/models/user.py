from django.db import models
import json

def get_timezones() -> dict:
    '''
    Return a dictionary of the form {timezone:readable name} for every timezone
    These are used as choices for User's timezone field
    '''
    with open("stats/data/timezones.json") as f:
        timezone_dict = json.load(f)
    tz_values = dict()
    for continent in timezone_dict:
        tz_values[continent] = {val:name for name,val in timezone_dict[continent].items()}
    return tz_values


class User_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = ['tag', 'discriminator', 'avatar_id'],
            unique_fields = ['id']
        )

class User(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    tag = models.CharField(max_length=32)
    discriminator = models.CharField(max_length=4, null=True)
    avatar_id = models.CharField(max_length=34, null=True) # the 'a_' prefix for animated avatars adds two characters

    last_login = models.DateTimeField(null=True)
    timezone = models.CharField(max_length=32, default='US/Pacific', choices=get_timezones)

    objects = User_Manager()

    def __str__(self):
        return self.tag
    
    def merge(self, other):
        self.tag = other.tag
        self.discriminator = other.discriminator
        self.avatar_id = other.avatar_id
    
    @property
    def avatar(self):
        if self.avatar_id:
            return f'https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_id}.png'
        else:
            return 'https://cdn.discordapp.com/embed/avatars/0.png'

    
    def is_authenticated(self):
        return True

class UserBlacklist(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True) # user ID of blacklisted user