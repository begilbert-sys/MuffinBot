import discord

import asyncio
import datetime 
import emoji
import logging
import pytz
import re

from itertools import chain 

from stats import models


logger = logging.getLogger(__package__)

with open('stats/words/words.txt') as f:
    WORDS = set(f.read().split('\n'))
    
with open('stats/words/curse_words.txt') as f:
    CURSE_WORDS = set(f.read().split('\n'))

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
    URL_REGEX = 'https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)'
    return re.findall(URL_REGEX, string)

def get_twemoji_URL(emoji_str: str) -> str:
    '''
    Given an emoji, return the corresponding twemoji URL
    Ref: https://github.com/twitter/twemoji/blob/master/scripts/build.js#L344
    '''
    # from Twemoji source code:
    # remove all variants (0xfe0f)
    # UNLESS there is a zero width joiner (0x200d)
    VS16 = 0xfe0f
    ZWJ = 0x200d
    hex_ints = [ord(unichar) for unichar in emoji_str]
    if ZWJ not in hex_ints:
        hex_ints = [hex_int for hex_int in hex_ints if hex_int != VS16]
    codepoint = '-'.join([format(hex_int, 'x') for hex_int in hex_ints])
    return f'https://raw.githubusercontent.com/twitter/twemoji/d94f4cf793e6d5ca592aa00f58a88f6a4229ad43/assets/svg/{codepoint}.svg'

# list of all the count model classes
COUNT_MODELS = models.UserStat.__subclasses__()

class Data_Processor:
    def __init__(self):
        self.cached_model_objects = {
            Model_Class: dict() for Model_Class in COUNT_MODELS
        }
        self.cached_model_objects[models.User] = dict()
        self.cached_model_objects[models.Emoji] = dict()

        self.cached_channels = dict()

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
                id = user.id,
                tag = tag,
                nick = user.display_name,
                avatar = downsize_img_link(str(user.display_avatar))
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
    
    def _get_default_emojis(self, message: discord.Message):
        '''
        Yield the default emojis objects from a discord message
        '''
        for emoji_str in emoji.distinct_emoji_list(message.content):
            url = get_twemoji_URL(emoji_str)
            key = hash(url)
            if key in self.cached_model_objects[models.Emoji]:
                yield self.cached_model_objects[models.Emoji][key]
            else:
                name = emoji.demojize(emoji_str, delimiters=('', ''))
                emoji_model_obj = models.Emoji(
                    URL = url,
                    name = name
                )
                self.cached_model_objects[models.Emoji][key] = emoji_model_obj
                yield emoji_model_obj

    def _get_custom_emojis(self, message: discord.Message):
        EMOJI_CODE_REGEX = r'<a?:(\w+):(\d+)>'
        for name, id in re.findall(EMOJI_CODE_REGEX, message.content):
            url = downsize_img_link(f'https://cdn.discordapp.com/emojis/{id}')
            key = hash(url)
            if key in self.cached_model_objects[models.Emoji]:
                yield self.cached_model_objects[models.Emoji][key]
            else:
                emoji_model_obj = models.Emoji(
                    URL = url,
                    name = name
                )
                self.cached_model_objects[models.Emoji][key] = emoji_model_obj
                yield emoji_model_obj

    def _increment_count(self, Count_Class: type, user: models.User, object):
        '''
        Increment a count object from the cache dict or, if one does not exist, create one and add it to the cache
        The cache dict key is a hashed tuple consisting of the user's ID and a unique object associated with the model object
        '''

        key = hash((user.id, object))
        if key in self.cached_model_objects[Count_Class]:
            count_model_obj = self.cached_model_objects[Count_Class][key]
        else:
            count_model_obj = Count_Class(**{'obj': object, 'user': user})
            self.cached_model_objects[Count_Class][key] = count_model_obj
        count_model_obj.count += 1
    
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
        message_creation_dt = convert_to_pacific_time(message.created_at)

        ### HOUR
        msg_hour = message_creation_dt.hour
        self._increment_count(models.Hour_Count, user_model_obj, msg_hour)

        ### DATE 
        msg_date = message_creation_dt.date()
        self._increment_count(models.Date_Count, user_model_obj, msg_date)

        ### EMOJIS
        all_emojis = chain(self._get_default_emojis(message), self._get_custom_emojis(message))
        for emoji_model_obj in all_emojis:
            emoji_model_obj.count += 1
            self._increment_count(models.Emoji_Count, user_model_obj, emoji_model_obj)
        
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
        if not await models.Guild.objects.aexists():
            guild_model_object = await models.Guild.objects.acreate(id=guild.id, name=guild.name, icon=guild.icon.url)
            await guild_model_object.asave()

    async def handle_channel(self, channel: discord.channel) -> datetime.datetime:
        '''
        If a channel is already in the database, add it to the chanel cache and return the datetime of the last processed message
        If it is not in the database, create a new channel model object and add it to the cache - the return value in this case will be None
        '''
        channel_model_object, channel_created = await models.Channel.objects.aget_or_create(
            id=channel.id,
            defaults={'name': channel.name}
        )
        self.current_channel_model_obj = channel_model_object
        self.cached_channels[channel.id] = channel_model_object
        return channel_model_object.last_processed_message_datetime
    
    async def update_channel_last_message(self, channel, last_message: discord.Message):
        '''
        Update the last processed message of a channel model object
        '''
        channel_model_obj =  self.cached_channels[channel.id]
        channel_model_obj.last_processed_message_datetime = last_message.created_at
    
    async def _save_channels(self):
        '''
        Save all of the cached channel model objects to the DB
        '''
        await models.Channel.objects.abulk_create_or_update(
            self.cached_channels.values()
        )

    async def _merge_model_objects(self, Model_Class):
        '''
        For a specific model: update all of the DB models with data from the cached models
        '''
        for hash_val, dummy_model_obj in self.cached_model_objects[Model_Class].items():
            if Model_Class is models.User:
                kwargs = {'id': dummy_model_obj.id}
            elif Model_Class is models.Emoji:
                kwargs = {'URL': dummy_model_obj.URL}
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
        # save User objects first, to avoid foreign key conflicts (you dummy)
        await self._update_and_save_model_objects(models.User)
        await self._update_and_save_model_objects(models.Emoji)
        # save the rest asynchronously
        gather_list = []
        gather_list.append(self._save_channels())
        for Model_Class in COUNT_MODELS:
            gather_list.append(self._update_and_save_model_objects(Model_Class))

        await asyncio.gather(*gather_list)
    
    async def blacklist(self, user: discord.User):
        if await models.User.objects.filter(id=user.id).aexists():
            user_model_obj = await models.User.objects.aget(id=user.id)
            if user_model_obj.blacklist:
                return 'You are already blacklisted.'
        else:
            user_model_obj = self._get_user(user)
        user_model_obj.blacklist = True
        await user_model_obj.asave()
        return 'You have been blacklisted.'

    async def whitelist(self, user: discord.User):
        if await models.User.objects.filter(id=user.id).aexists():
            user_model_obj = await models.User.objects.aget(id=user.id)
            if user_model_obj.blacklist:
                user_model_obj.blacklist = False
                await user_model_obj.asave()
                return 'You have been whitelisted.'
        return 'You are already whitelisted.'