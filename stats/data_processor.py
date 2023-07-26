import discord

import datetime 
import emoji
import pytz
import re
import typing

from . import models

with open('stats/words/words.txt') as f:
    WORDS = {w.lower() for w in f.read().split('\n')}
    
with open('stats/words/curse_words.txt') as f:
    CURSE_WORDS = set(f.read().split('\n'))

### utility functions
def convert_to_pacific_time(dt: datetime.datetime) -> datetime.datetime:
    '''
    discord messages are in UTC by default. 
    this function converts them to PST/PDT
    '''
    PST_PDT = pytz.timezone('America/Los_Angeles')
    return dt.astimezone(PST_PDT)

def get_custom_emoji_URLs(string):
    '''returns a list of the URLs of all the custom emojis in a discord message'''
    EMOJI_URL = 'https://cdn.discordapp.com/emojis/'
    custom_emoji_id_list = re.findall(r'<:\w*:(\d*)>', string)
    return [EMOJI_URL + emoji_id for emoji_id in custom_emoji_id_list]

def get_URLs(string):
    '''extracts all the URLs from a string'''
    URL_REGEX = 'https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)'

    return re.findall(URL_REGEX, string)


class Data_Processor:
    '''self.cached_database structure:
    {
    'users':
        {user_id: models.User},

    'channel_counts':
        {hash((user_id, obj)): models.Channel_Count},
    'mention_counts':
        {hash((user_id, obj)): models.Mention_Count},
    etc. 
    '''

    DATABASE_KEY_TO_COUNT_MODEL = {
        'channel_counts': models.Channel_Count,
        'mention_counts': models.Mention_Count,
        'hour_counts': models.Hour_Count,
        'date_counts': models.Date_Count,
        'URL_counts': models.URL_Count,
        'default_emoji_counts': models.Default_Emoji_Count,
        'custom_emoji_counts': models.Custom_Emoji_Count,
        'unique_word_counts': models.Unique_Word_Count
    }

    def __init__(self):
        self.cached_database = {
            'users': dict(),
        }
        for key in self.DATABASE_KEY_TO_COUNT_MODEL:
            self.cached_database[key] = dict()
        
        self.cached_channel_objects = list()
    
    def _add_user(self, user: discord.User) -> models.User:
        assert user.id not in self.cached_database['users']
        user_model_obj = models.User(
            id = user.id,
            tag = user.name,
            nick = user.display_name,
            avatar = str(user.display_avatar),
        )
        self.cached_database['users'][user.id] = user_model_obj
        return user_model_obj
    
    def _create_or_increment(self, user: models.User, object: typing.Any, database_key: str, 
                             field_name: str) -> None:
        Model_Class = self.DATABASE_KEY_TO_COUNT_MODEL[database_key]
        hash_value = hash((user.id, object))
        if hash_value in self.cached_database[database_key]:
            count_model_obj = self.cached_database[database_key][hash_value]
        else:
            # what the fuck is this call
            count_model_obj = Model_Class(user=user, **{field_name: object})
            self.cached_database[database_key][hash_value] = count_model_obj
        count_model_obj.count += 1

    @staticmethod
    def _message_mentions(message: discord.message, reply_message: discord.message = None) -> typing.List[int]:
        '''
        a message's mentions consist of: the author of the message that's being replied to (if
        applicable), as well as all users pinged in the message 
        returns a list of user IDs
        '''
        mentions_list = list()
        if reply_message:
            mentions_list.append(message.author.id)
        mentions_list += [user.id for user in message.mentions]
        return mentions_list
    
    def process_message(self, message: discord.Message, reply_message: discord.Message = None):
        ### USER
        if message.author.id in self.cached_database['users']:
            user_model_obj = self.cached_database['users'][message.author.id]
        else:
            user_model_obj = self._add_user(message.author)
        user_model_obj.messages += 1

        ### CHANNEL
        channel_id = message.channel.id
        self._create_or_increment(user_model_obj, channel_id, 'channel_counts', 'channel_id')

        # convert to PST/PDT
        message_creation_dt = convert_to_pacific_time(message.created_at)

        ### HOUR 
        self._create_or_increment(
            user_model_obj, message_creation_dt.hour, 'hour_counts', 'hour'
        )

        ### DATE 
        self._create_or_increment(
            user_model_obj, message_creation_dt.date(), 'date_counts', 'date'
        )

        ### DEFAULT EMOJI
        for e in emoji.distinct_emoji_list(message.content):
            self._create_or_increment(
                user_model_obj, e, 'default_emoji_counts', 'default_emoji'
            )

        ### CUSTOM EMOJI
        for e in get_custom_emoji_URLs(message.content):
            self._create_or_increment(
                user_model_obj, e, 'custom_emoji_counts', 'custom_emoji'
            )

        ### URL
        for URL in get_URLs(message.content):
            self._create_or_increment(
                user_model_obj, URL, 'URL_counts', 'URL'
            )

        ### UNIQUE WORDS AND CURSE WORDS
        for word in message.content.split():
            # valid 'words' need to be alphabetic and between 3 and 18 characters
            if word.isalpha() and len(word) in range(3,19):
                word = word.lower()
                if word not in WORDS:
                    self._create_or_increment(
                        user_model_obj, word, 'unique_word_counts', 'word'
                    )
                if word in CURSE_WORDS:
                    user_model_obj.curse_word_count += 1
    
        ### MENTIONS
        mentions_list = self._message_mentions(message, reply_message)
        for user_id in mentions_list:
            self._create_or_increment(
                user_model_obj, user_id, 'mention_counts', 'mentioned_user_id'
            )

    async def _asave_count_model(self, database_key: str):
        Model_Class = self.DATABASE_KEY_TO_COUNT_MODEL[database_key]

        # this is a REALLY hacky way to get the name of the unique database attribute
        # I should probably rewrite this part 
        unique_field_name = Model_Class._meta.get_fields()[3].name

        bulk_count_model_objects = list(self.cached_database[database_key].values())
        for cached_count_model_object in bulk_count_model_objects:
            kwargs = {
                'user': cached_count_model_object.user,
                unique_field_name: getattr(cached_count_model_object, unique_field_name)
            }
            if await Model_Class.objects.filter(**kwargs).aexists():
                real_count_model_object = await Model_Class.objects.aget(**kwargs)
                real_count_model_object.count += cached_count_model_object.count
                await real_count_model_object.asave()
            else:
                await cached_count_model_object.asave()
        
    async def asave_to_database(self):
        bulk_user_model_objects = list(self.cached_database['users'].values())
        for cached_user_model_object in bulk_user_model_objects:
            user_id = cached_user_model_object.id
            if await models.User.objects.filter(id=user_id).aexists():
                real_user_model_object = await models.User.objects.aget(id=user_id)
                real_user_model_object.messages += cached_user_model_object.messages
                real_user_model_object.curse_word_count += cached_user_model_object.curse_word_count
                await real_user_model_object.asave()
            else:
                await cached_user_model_object.asave()

        for database_key in self.DATABASE_KEY_TO_COUNT_MODEL:
            print("working on", database_key)
            await self._asave_count_model(database_key)