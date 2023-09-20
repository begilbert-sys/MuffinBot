import discord

import asyncio
import datetime 
import emoji
import logging
import pytz
import re

from stats import models

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

def downsize_avatar_link(URL: str):
    '''sets the size of a user's avatar link to be 128px. this speeds up website loading times'''
    if '?size=' not in URL:
        return URL + '?size=128'
    else:
        return re.sub('\?size=[\d]+', '?size=128', URL)

def get_custom_emoji_URLs(string: str) -> list[str]:
    '''Returns a list of the URLs of all the custom emojis in a discord message'''
    EMOJI_URL = 'https://cdn.discordapp.com/emojis/'
    custom_emoji_id_list = re.findall(r'<:\w*:(\d*)>', string)
    return [EMOJI_URL + emoji_id for emoji_id in custom_emoji_id_list]

def get_URLs(string: str) -> list[str]:
    '''Extracts all the URLs from a string'''
    URL_REGEX = 'https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)'

    return re.findall(URL_REGEX, string)

def _get_special_field(Count_Class: type) -> str:
    '''
    Given a count class, returns the field unique to that count class
    for example, Hour_Counts would return 'hour'
    '''
    INHERITED_FIELDS = ['id', 'user', 'count']
    [special_field] = [field.name for field in Count_Class._meta.fields if field.name not in INHERITED_FIELDS]
    return special_field

# list of all the count model classes
COUNT_MODELS = models.UserStat.__subclasses__()

class Data_Processor:
    def __init__(self):
        self.cached_model_objects = {
            Model_Class: dict() for Model_Class in COUNT_MODELS
        }
        self.cached_model_objects[models.User] = dict()

        self.cached_channels = dict()
    def _get_or_add_user(self, user: discord.User) -> models.User:
        '''
        Return a user model object from the cache dict or, if one does not exist, then add one and return it
        The cache dict key is the user's ID
        '''
        if user.id in self.cached_model_objects[models.User]:
            user_model_obj = self.cached_model_objects[models.User][user.id]
        else:
            user_model_obj = models.User(
                id=user.id,
                tag=user.name,
                nick = user.display_name,
                avatar = downsize_avatar_link(str(user.display_avatar))
            )
            self.cached_model_objects[models.User][user.id] = user_model_obj
        return user_model_obj
    
    def _create_or_increment(self, Count_Class: type, user: models.User, object):
        '''
        Increment a count object from the cache dict or, if one does not exist, create one and add it to the cache
        The cache dict key is a hashed tuple consisting of the user's ID and a unique object associated with the model object
        '''
        special_field = _get_special_field(Count_Class)

        key = hash((user.id, object))
        if key in self.cached_model_objects[Count_Class]:
            count_model_obj = self.cached_model_objects[Count_Class][key]
        else:
            count_model_obj = Count_Class(**{special_field: object, 'user': user})
            self.cached_model_objects[Count_Class][key] = count_model_obj
        count_model_obj.count += 1

    def _message_mentions(self, message: discord.message, reply_message: discord.message = None) -> list[models.User]:
        '''
        A message's mentions consist of: the author of the message that's being replied to (if
        applicable), as well as all users pinged in the message 
        returns a list of the User model objects
        '''
        mentions_list = list()
        if reply_message:
            mentions_list.append(self._get_or_add_user(reply_message.author))
        mentions_list += [self._get_or_add_user(user) for user in message.mentions]
        return mentions_list

    def process_message(self, message: discord.Message, reply_message: discord.Message = None):
        '''
        Given a message, increment all of the cached models accordingly 
        '''
        user_id = message.author.id

        ### USER 
        user_model_obj = self._get_or_add_user(message.author)
        user_model_obj.messages += 1

        ### TOTAL CHARS
        user_model_obj.total_chars += len(message.content)

        ### ALL CAPS
        if message.content.isupper():
             user_model_obj.ALL_CAPS_count += 1
    
        ### CHANNEL
        channel_id = message.channel.id
        self._create_or_increment(models.Channel_Count, user_model_obj, self.current_channel_model_obj)

        # convert to PST/PDT
        message_creation_dt = convert_to_pacific_time(message.created_at)

        ### HOUR
        msg_hour = message_creation_dt.hour
        self._create_or_increment(models.Hour_Count, user_model_obj, msg_hour)

        ### DATE 
        msg_date = message_creation_dt.date()
        self._create_or_increment(models.Date_Count, user_model_obj, msg_date)

        ### DEFAULT EMOJI
        for e in emoji.distinct_emoji_list(message.content):
            self._create_or_increment(models.Default_Emoji_Count, user_model_obj, e)
        
        ### CUSTOM EMOJI
        for e in get_custom_emoji_URLs(message.content):
            self._create_or_increment(models.Custom_Emoji_Count, user_model_obj, e)
        
        ### URL
        for URL in get_URLs(message.content):
            self._create_or_increment(models.URL_Count, user_model_obj, URL)
        
        ### UNIQUE WORDS AND CURSE WORDS
        for word in message.content.split():
            # valid 'words' need to be alphabetic and between 3 and 18 characters
            if word.isalpha() and len(word) in range(3,19):
                word = word.lower()
                if word not in WORDS:
                    self._create_or_increment(models.Unique_Word_Count, user_model_obj, word)
                if word in CURSE_WORDS:
                    user_model_obj.curse_word_count += 1

        ### MENTIONS
        mentions_list = self._message_mentions(message, reply_message)
        for user in mentions_list:
            self._create_or_increment(models.Mention_Count, user_model_obj, user)

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
        await models.Channel.objects.abulk_create(
            self.cached_channels.values(),
            update_conflicts = True,
            update_fields = ['last_processed_message_datetime'],
            unique_fields = ['id']
        )

    async def _update_model_objects(self, Model_Class):
        '''
        For a specific model: update all of the DB models with data from the cached models
        '''
        for hash_val, dummy_model_obj in self.cached_model_objects[Model_Class].items():
            if Model_Class is models.User:
                kwargs = {'id': dummy_model_obj.id}
            elif Model_Class is models.Mention_Count: # mention counts are special because the field is a user
                kwargs = {'user': dummy_model_obj.user, 'mentioned_user': await models.User.objects.aget(id=dummy_model_obj.mentioned_user.id)}
            else:
                assert issubclass(Model_Class, models.UserStat)
                special_field = _get_special_field(Model_Class)
                kwargs = {'user': dummy_model_obj.user, special_field: getattr(dummy_model_obj, special_field)}

            if await Model_Class.objects.filter(**kwargs).aexists():
                real_model_obj = await Model_Class.objects.aget(**kwargs)
                real_model_obj.update(dummy_model_obj)
                self.cached_model_objects[Model_Class][hash_val] = real_model_obj

    async def _update_and_save_model_objects(self, Model_Class):
        '''
        Updates all model objects for a specific model, and saves them to the DB
        '''
        logging.debug(Model_Class.__name__ + ' saving. . .')
        await self._update_model_objects(Model_Class)
        if Model_Class is models.User:
            update_fields = ['messages', 'curse_word_count', 'avatar']
        else:
            update_fields = ['count']
        await Model_Class.objects.abulk_create(
            self.cached_model_objects[Model_Class].values(),
            update_conflicts = True,
            update_fields = update_fields,
            unique_fields = ['id']
        )
        logging.debug(Model_Class.__name__ + ' saved to DB')

    async def save(self):
        '''
        Asynchronously saves all info to the DB
        '''
        # save User objects first, to avoid foreign key conflicts (you dummy)
        await self._update_and_save_model_objects(models.User)
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
            user_model_obj = self._get_or_add_user(user)
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