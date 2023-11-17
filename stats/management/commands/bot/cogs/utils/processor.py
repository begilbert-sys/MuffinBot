import discord

import asyncio
import datetime 
import emoji
import json
import logging
import pytz
import re

from itertools import chain 

from stats import models
from django.db import connection

logger = logging.getLogger('collection')

with open('stats/data/words.txt') as f:
    WORDS = set(f.read().split('\n'))
    
with open('stats/data/curse_words.txt') as f:
    CURSE_WORDS = set(f.read().split('\n'))

with open('stats/data/emoji_ids.json') as f:
    EMOJI_IDS = json.load(f)

### utility functions
def convert_to_pacific_time(dt: datetime.datetime) -> datetime.datetime:
    '''
    discord messages are in UTC by default
    this function converts them to PST/PDT
    '''
    PST_PDT = pytz.timezone('America/Los_Angeles')
    return dt.astimezone(PST_PDT)

def downsize_img_link(URL: str):
    '''sets the size of an image URL to be 64px. this speeds up website loading times'''
    if '?size=' not in URL:
        return URL + '?size=64'
    else:
        return re.sub('\?size=[\d]+', '?size=64', URL)

def get_URLs(string: str) -> list[str]:
    '''Extract all the URLs from a string'''
    url_regex = r'(http|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])'
    raw_urls = [url.group(0) for url in re.finditer(url_regex, string) if len(url.group(0)) <= 200]
    return raw_urls


def get_avatar_id(icon_url: str) -> str:
    # this cuts storage space
    '''given the URL of a discord avatar, returns the avatar's hex ID'''
    av_id_regex = r'https://cdn\.discordapp\.com/avatars/\d+/((?:a_)?[0-9a-f]+)'
    regex_match = re.match(av_id_regex, icon_url)
    if regex_match:
        return regex_match.group(1)
    else:
        return None
    



# list all of the count model classes
COUNT_MODELS = models.UserStat.__subclasses__()

class Processor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.cached_model_objects = {
            Model_Class: dict() for Model_Class in COUNT_MODELS
        }
        self.cached_model_objects[models.User] = dict()
        self.cached_model_objects[models.Emoji] = dict()

    def cull_database(self):
        models.Emoji_Count.cull()
        models.Unique_Word_Count.cull()
        models.URL_Count.cull()
        connection

    def _get_user(self, user: discord.User) -> models.User:
        '''
        Return a user model object from the cache dict or, if one does not exist, then add one and return it
        The cache dict key is the user's ID
        '''
        if user.id in self.cached_model_objects[models.User]:
            user_model_obj = self.cached_model_objects[models.User][user.id]
        else:
            if user.discriminator == '0':
                tag = user.name
            else:
                tag = user.name + '＃' + user.discriminator
            user_model_obj = models.User(
                guild=self.guild_model_obj,
                user_id = user.id,
                tag = tag,
                nick = user.display_name,
                avatar_id = get_avatar_id(str(user.display_avatar))
            )
            self.cached_model_objects[models.User][user.id] = user_model_obj
        return user_model_obj

    def _get_message_mentions(self, message: discord.message, reply_message: discord.message = None) -> list[models.User]:
        '''
        A message's mentions consist of: the author of the message that's being replied to (if
        applicable), as well as all users pinged in the message 
        returns a generator of the User model objects
        '''
        if reply_message:
            yield self._get_user(reply_message.author)
        for user in message.mentions:
            yield self._get_user(user)

    def _get_emoji(self, emoji_id: int, emoji_name: str, *, custom: bool):
        assert type(emoji_id) is int
        if emoji_id in self.cached_model_objects[models.Emoji]:
            return self.cached_model_objects[models.Emoji][emoji_id]
        else:
            emoji_model_obj = models.Emoji(
                id = emoji_id,
                name = emoji_name,
                custom = custom
            )
            self.cached_model_objects[models.Emoji][emoji_id] = emoji_model_obj
            return emoji_model_obj
        
    def _get_default_emojis(self, message: discord.Message):
        '''
        Yield the default emojis objects from a discord message
        '''
        for emoji_str in emoji.distinct_emoji_list(message.content):
            if emoji_str not in EMOJI_IDS:
                continue
            key = EMOJI_IDS[emoji_str]
            name = emoji.demojize(emoji_str, delimiters=('', ''))
            yield self._get_emoji(key, name, custom=False)

    def _get_custom_emojis(self, message: discord.Message):
        '''
        Yield the custom emojis objects from a discord message
        '''
        EMOJI_CODE_REGEX = r'<a?:(\w+):(\d+)>'
        for name, key in re.findall(EMOJI_CODE_REGEX, message.content):
            yield self._get_emoji(int(key), name, custom=True)

    def _increment_count(self, Count_Class: type, user: models.User, object, increment_by=1):
        '''
        Increment a count object from the cache dict or, if one does not exist, create one and add it to the cache
        The cache dict key is a hashed tuple consisting of the user's ID and a unique object associated with the model object
        '''
        if Count_Class is models.Mention_Count:
            key = (user.user_id, object.user_id)
        else:
            # user models can't be hashed due to the id being unassigned till saved
            key = (user.user_id, object)
        if key in self.cached_model_objects[Count_Class]:
            count_model_obj = self.cached_model_objects[Count_Class][key]
        else:
            count_model_obj = Count_Class(**{'obj': object, 'user': user})
            self.cached_model_objects[Count_Class][key] = count_model_obj
        count_model_obj.count += increment_by

    def process_message(self, message: discord.Message, reply_message: discord.Message = None):
        '''
        Given a message, increment all of the cached models accordingly 
        '''
        user_id = message.author.id

        ### USER
        user_model_obj = self._get_user(message.author)
        user_model_obj.messages += 1

        ### TOTAL CHARS
        user_model_obj.total_chars += len(message.content)

        ### ALL CAPS
        if message.content.isupper():
            user_model_obj.ALL_CAPS_count += 1
    
        ### CHANNEL
        self._increment_count(models.Channel_Count, user_model_obj, self.current_channel_model_obj)
        # convert to PST/PDT
        message_creation_dt = message.created_at

        ### HOUR
        msg_hour = message_creation_dt.hour
        self._increment_count(models.Hour_Count, user_model_obj, msg_hour)

        ### DATE
        msg_date = message_creation_dt.date()
        self._increment_count(models.Date_Count, user_model_obj, msg_date)

        ### EMOJIS
        all_emojis = chain(self._get_default_emojis(message), self._get_custom_emojis(message))
        for emoji_model_obj in all_emojis:
            self._increment_count(models.Emoji_Count, user_model_obj, emoji_model_obj)

        ### REACTIONS
        for reaction in message.reactions:
            emoji_object = reaction.emoji
            if type(emoji_object) is str:
                if emoji_object not in EMOJI_IDS:
                    continue
                emoji_id = EMOJI_IDS[emoji_object]
                emoji_name = emoji.demojize(emoji_object, delimiters=('', ''))
                emoji_model_obj = self._get_emoji(emoji_id, emoji_name, custom=False)
                self._increment_count(models.Reaction_Count, user_model_obj, emoji_model_obj, reaction.count)
            elif type(emoji_object) in [discord.Emoji, discord.PartialEmoji]:
                emoji_model_obj = self._get_emoji(emoji_object.id, emoji_object.name, custom=True)
            self._increment_count(models.Reaction_Count, user_model_obj, emoji_model_obj, reaction.count)
        
        ### URL
        for URL in get_URLs(message.content):
            self._increment_count(models.URL_Count, user_model_obj, URL)
        
        ### UNIQUE WORDS AND CURSE WORDS
        for word in message.content.split():
            # valid 'words' need to be alphabetic and between 3 and 18 characters
            if word.isalpha() and len(word) in range(3,19):
                word = word.lower()
                if word not in WORDS:
                    self._increment_count(models.Unique_Word_Count, user_model_obj, word)
                if word in CURSE_WORDS:
                    user_model_obj.curse_word_count += 1

        ### MENTIONS
        all_mentions = self._get_message_mentions(message, reply_message)
        for user in all_mentions:
            self._increment_count(models.Mention_Count, user_model_obj, user)
        

    async def process_guild(self, guild: discord.guild):
        '''
        Save a guild's info to the DB if it has not already been added
        '''
        self.guild_model_obj, created = await models.Guild.objects.aget_or_create(
            id=guild.id, 
            defaults={"name": guild.name, "icon": guild.icon}
        )

        if not created: # update these values, just in case they change 
            self.guild_model_obj.name = guild.name
            self.guild_model_obj.icon = guild.icon
            await self.guild_model_obj.asave()
        

    async def process_channel(self, channel: discord.channel) -> datetime.datetime:
        '''
        If a channel is already in the database, add it to the chanel cache and return the datetime of the last processed message
        If it is not in the database, create a new channel model object and add it to the cache - the return value in this case will be None
        '''
        channel_model_object, channel_created = await models.Channel.objects.aget_or_create(
            id=channel.id,
            guild=self.guild_model_obj,
            defaults={'name': channel.name}
        )
        if channel_created:
            await channel_model_object.asave()
        self.current_channel_model_obj = channel_model_object

    async def _merge_model_objects(self, Model_Class):
        '''
        For a specific model: update all of the DB models with data from the cached models
        '''
        for hash_val, dummy_model_obj in self.cached_model_objects[Model_Class].items():
            if Model_Class is models.User:
                kwargs = {'guild': self.guild_model_obj, 'user_id': dummy_model_obj.user_id}
            elif Model_Class is models.Emoji:
                kwargs = {'id': dummy_model_obj.id}
            else:
                assert issubclass(Model_Class, models.UserStat)
                kwargs = {'user': dummy_model_obj.user, 'obj': dummy_model_obj.obj}

            if await Model_Class.objects.filter(**kwargs).aexists():
                real_model_obj = await Model_Class.objects.aget(**kwargs)
                real_model_obj.merge(dummy_model_obj)
                self.cached_model_objects[Model_Class][hash_val] = real_model_obj

    async def _update_and_save_model_objects(self, Model_Class):
        '''
        Updates all model objects for a specific model, and saves them to the DB
        '''
        logger.debug(Model_Class.__name__ + ' saving. . .')
        await self._merge_model_objects(Model_Class)
        await Model_Class.objects.abulk_create_or_update(
            self.cached_model_objects[Model_Class].values(),
        )

        logger.debug(Model_Class.__name__ + ' saved to DB')

    async def save(self):
        '''
        Asynchronously saves all info to the DB
        '''
        # save User & Emoji objects first, to avoid foreign key conflicts (you dummy)
        await self._update_and_save_model_objects(models.User)
        await self._update_and_save_model_objects(models.Emoji)
        # save the rest asynchronously
        gather_list = []
        for Model_Class in COUNT_MODELS:
            gather_list.append(self._update_and_save_model_objects(Model_Class))

        await asyncio.gather(*gather_list)
        self.reset()
        
    '''
    @staticmethod
    async def blacklist(guild: discord.Guild, user: discord.User):
        if await models.User.objects.filter(guild=guild, user_id=user.id).aexists():
            user_model_obj = await models.User.objects.aget(id=user.id)
            if user_model_obj.blacklist:
                return 'You are already blacklisted.'
        else:
            user_model_obj = self._get_user(user)
        user_model_obj.blacklist = True
        await user_model_obj.asave()
        return 'You have been blacklisted.'
    
    @staticmethod
    async def whitelist(self, user: discord.User):
        if await models.User.objects.filter(id=user.id).aexists():
            user_model_obj = await models.User.objects.aget(id=user.id)
            if user_model_obj.blacklist:
                user_model_obj.blacklist = False
                await user_model_obj.asave()
                return 'You have been whitelisted.'
        return 'You are already whitelisted.'
    '''