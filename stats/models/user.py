from django.db import models
from hashlib import sha256
import json

def get_timezones() -> dict:
    '''
    Return a dictionary of the form {timezone:readable name} for every timezone
    These are used as choices for User's timezone field
    '''
    with open("stats/data/timezones.json") as f:
        return json.load(f)


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
    timezone = models.CharField(max_length=32, default='US/Pacific', choices=get_timezones)
    timezone_set = models.BooleanField(default=False)

    hidden = models.BooleanField(default=False)

    last_login = models.DateTimeField(null=True)
    is_superuser = models.BooleanField(default=False)

    objects = User_Manager()

    def __str__(self):
        return self.tag
    
    def merge(self, other):
        self.tag = other.tag
        self.discriminator = other.discriminator
        self.avatar_id = other.avatar_id

    @property
    def avatar(self):
        if len(self.avatar_id) == 1:
            return f'https://cdn.discordapp.com/embed/avatars/{self.avatar_id}.png'
        else:
            return f'https://cdn.discordapp.com/avatars/{self.id}/{self.avatar_id}.png'
        
    def full_tag(self) -> str:
        '''Return the user's tag with the discriminator attatched, if they have one '''
        if self.discriminator is None:
            return self.tag
        else:
            return self.tag + '＃' + self.discriminator

    def is_authenticated(self):
        return True

class UserBlacklist(models.Model):
    hash_value = models.CharField(max_length=64, primary_key=True)

class UserDeletionQueue(models.Model):
    id = models.BigIntegerField(primary_key=True)