import discord

import asyncio
import datetime 
import emoji
import json
import logging
import re

from itertools import chain 

from stats import models
from django.db import connection

DELETED_USER_ID = 456226577798135808

logger = logging.getLogger('collection')

with open('stats/data/words.txt') as f:
    WORDS = set(f.read().split('\n'))
    
with open('stats/data/curse_words.txt') as f:
    CURSE_WORDS = set(f.read().split('\n'))

with open('stats/data/emoji_ids.json') as f:
    EMOJI_IDS = json.load(f)

def get_URLs(string: str) -> list[str]:
    '''Extract all the URLs from a string'''
    url_regex = r'(http|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])'
    raw_urls = [url.group(0) for url in re.finditer(url_regex, string) if len(url.group(0)) <= 200]
    return raw_urls


def get_icon_id(icon_url: str) -> str:
    # storiung this instead of the entire URL cuts storage space big time
    '''Given the URL of a discord avatar, return the avatar's hex ID'''
    av_id_regex = r'https://cdn\.discordapp\.com/(?:avatars|icons)/\d+/((?:a_)?[0-9a-f]+)'
    regex_match = re.match(av_id_regex, icon_url)
    if regex_match:
        return regex_match.group(1)
    else:
        return None # indicates default avatar

def get_half_hour_increment(dt: datetime.datetime) -> int:
    '''Given a datetime, return an int from 0 to 47 denoting the time of day'''
    return (dt.hour * 2) + (1 if dt.minute >= 30 else 0)


# list all of the count model classes
COUNT_MODELS = models.MemberStat.__subclasses__()

class Processor:
    def __init__(self, *, history: bool):
        # denotes if the processor is processing message history or current messages
        self.history = history

        # explanation for this variable in save() function 
        self._saving_semaphore = asyncio.Semaphore(1)
        
        if history:
            self.current_channel_model_obj = None

        self.reset()

    def reset(self):
        '''
        Reset the cache
        '''
        self.cache_count = 0
        self.cached_model_objects = {
            Model_Class: dict() for Model_Class in COUNT_MODELS
        }
        self.cached_model_objects[models.User] = dict()
        self.cached_model_objects[models.Member] = dict()
        self.cached_model_objects[models.Emoji] = dict()
        self.cached_model_objects[models.Channel] = dict()

    def _get_member(self, user: discord.User) -> models.Member:
        '''
        Return a Member model object from the cache dict or, if one does not exist, then add one and return it
        '''
        if user.id in self.cached_model_objects[models.Member]:
            return self.cached_model_objects[models.Member][user.id]
        new_user_model_obj = models.User(
            id=user.id,
            tag=user.name,
            discriminator=user.discriminator if user.discriminator != '0' else None,
            avatar_id = get_icon_id(str(user.display_avatar))
        )
        if user.id == DELETED_USER_ID:
            new_user_model_obj.hidden = True
        self.cached_model_objects[models.User][user.id] = new_user_model_obj
        new_member_model_obj = models.Member(
            guild=self.guild_model_obj,
            user=new_user_model_obj
        )
        self.cached_model_objects[models.Member][user.id] = new_member_model_obj
        return new_member_model_obj
    
    def _get_channel(self, channel: discord.TextChannel):
        if channel.id in self.cached_model_objects[models.Channel]:
            channel_model_obj = self.cached_model_objects[models.Channel][channel.id]
        else:
            channel_model_obj = models.Channel(
                id=channel.id,
                guild=self.guild_model_obj,
                name=channel.name
            )
            self.cached_model_objects[models.Channel][channel.id] = channel_model_obj
        return channel_model_obj
    
    def _get_message_mentions(self, message: discord.message, reply_message: discord.message = None) -> list[models.Member]:
        '''
        Return a generator of the Member model objects representing a message's mentions
        A message's mentions consist of: the author of the message that's being replied to (if
        applicable), as well as all members pinged in the message 
        '''
        if reply_message:
            yield self._get_member(reply_message.author)
        for user in message.mentions:
            yield self._get_member(user)

    def _get_emoji(self, emoji_id: int, emoji_name: str, *, custom: bool):
        '''
        Return an emoji model object from the cache, or add one if it isn't there
        '''
        assert type(emoji_id) is int
        if emoji_id in self.cached_model_objects[models.Emoji]:
            return self.cached_model_objects[models.Emoji][emoji_id]
        
        emoji_model_obj = models.Emoji(
            id = emoji_id,
            name = emoji_name,
            custom = custom
        )
        self.cached_model_objects[models.Emoji][emoji_id] = emoji_model_obj
        return emoji_model_obj
        
    def _get_default_emojis(self, message: discord.Message):
        '''
        Yield the default emoji objects from a discord message
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

    def _increment_count(self, Count_Class: type, member: models.Member, object, increment_by: int):
        '''
        Increment (or decrement) a count object from the cache or, if one does not exist, create one and add it to the cache
        The cache dict key is a hashed tuple consisting of the user's ID and a unique object associated with the model object
        '''
        if Count_Class is models.Mention_Count:
            key = (member.user_id, object.user_id)
        else:
            # user models can't be hashed due to the id being unassigned till saved
            key = (member.user_id, object)
        if key in self.cached_model_objects[Count_Class]:
            count_model_obj = self.cached_model_objects[Count_Class][key]
        else:
            count_model_obj = Count_Class(**{'obj': object, 'member': member})
            self.cached_model_objects[Count_Class][key] = count_model_obj
        count_model_obj.count += increment_by
    
    def process_reaction(self, message, reaction, count):
        emoji_object = reaction.emoji
        member_model_obj = self._get_member(message.author)
        if type(emoji_object) is str:
            if emoji_object not in EMOJI_IDS:
                return
            emoji_id = EMOJI_IDS[emoji_object]
            emoji_name = emoji.demojize(emoji_object, delimiters=('', ''))
            emoji_model_obj = self._get_emoji(emoji_id, emoji_name, custom=False)
            self._increment_count(models.Reaction_Count, member_model_obj, emoji_model_obj, count)
        elif type(emoji_object) in [discord.Emoji, discord.PartialEmoji]:
            emoji_model_obj = self._get_emoji(emoji_object.id, emoji_object.name, custom=True)
            self._increment_count(models.Reaction_Count, member_model_obj, emoji_model_obj, count)
            
    def process_message(self, message: discord.Message, reply_message: discord.Message = None, *, unprocess = False):
        '''
        Given a message, increment or decrement all of the cached models accordingly 
        '''
        if unprocess:
            crement = -1
        else:
            crement = 1

        ### MEMBER
        member_model_obj = self._get_member(message.author)
        member_model_obj.messages += crement

        ### TOTAL CHARS
        member_model_obj.total_chars += (len(message.content) * crement)

        ### ALL CAPS
        if message.content.isupper():
            member_model_obj.ALL_CAPS_count += crement
    
        ### CHANNEL
        if self.history:
            channel_model_obj = self.current_channel_model_obj
        else:
            channel_model_obj = self._get_channel(message.channel)
        self._increment_count(models.Channel_Count, member_model_obj, channel_model_obj, crement)

        ### HOUR
        msg_hour = message.created_at.hour

        member_model_obj.half_hour_counts[get_half_hour_increment(message.created_at)] += crement

        self._increment_count(models.Hour_Count, member_model_obj, msg_hour, crement)

        ### DATE
        msg_date = message.created_at.date()
        self._increment_count(models.Date_Count, member_model_obj, msg_date, crement)

        ### EMOJIS
        all_emojis = chain(self._get_default_emojis(message), self._get_custom_emojis(message))
        for emoji_model_obj in all_emojis:
            self._increment_count(models.Emoji_Count, member_model_obj, emoji_model_obj, crement)

        ### REACTIONS
        for reaction in message.reactions:
            emoji_object = reaction.emoji
            if type(emoji_object) is str:
                if emoji_object not in EMOJI_IDS:
                    continue
                emoji_id = EMOJI_IDS[emoji_object]
                emoji_name = emoji.demojize(emoji_object, delimiters=('', ''))
                emoji_model_obj = self._get_emoji(emoji_id, emoji_name, custom=False)
                self._increment_count(models.Reaction_Count, member_model_obj, emoji_model_obj, (reaction.count * crement))
            elif type(emoji_object) in [discord.Emoji, discord.PartialEmoji]:
                emoji_model_obj = self._get_emoji(emoji_object.id, emoji_object.name, custom=True)
            self._increment_count(models.Reaction_Count, member_model_obj, emoji_model_obj, (reaction.count * crement))
        
        ### URL
        for URL in get_URLs(message.content):
            self._increment_count(models.URL_Count, member_model_obj, URL, crement)
        
        ### UNIQUE WORDS AND CURSE WORDS
        for word in message.content.lower().split():
            # valid 'words' need to be alphabetic and between 3 and 18 characters
            if word.isalpha() and len(word) in range(3,19):
                if word not in WORDS:
                    self._increment_count(models.Unique_Word_Count, member_model_obj, word, crement)
                if word in CURSE_WORDS:
                    member_model_obj.curse_word_count += crement

        ### MENTIONS
        all_mentions = self._get_message_mentions(message, reply_message)
        for member in all_mentions:
            self._increment_count(models.Mention_Count, member_model_obj, member, crement)
        
        self.cache_count += 1

    async def process_guild(self, guild: discord.guild):
        '''
        Save a guild's info to the DB if it has not already been added
        '''
        self.guild_name = guild.name
        self.guild_model_obj, newly_created = await models.Guild.objects.aget_or_create(
            id=guild.id, 
            defaults={
                "name": guild.name, 
                "icon_id": get_icon_id(str(guild.icon)),
                "join_dt": datetime.datetime.now(datetime.UTC)
            }
        )
        if newly_created: 
            for channel in guild.channels:
                perms = channel.permissions_for(guild.me)
                if type(channel) is discord.channel.TextChannel and perms.read_message_history:
                    await models.Channel.objects.acreate(
                        guild = self.guild_model_obj,
                        id=channel.id,
                        name=channel.name,
                    )
        else: # update these values, just in case they've changed
            self.guild_model_obj.name = guild.name
            self.guild_model_obj.icon_id = get_icon_id(str(guild.icon))
            await self.guild_model_obj.asave()
        
    async def process_channel(self, channel: discord.channel):
        '''
        Sets up the channel history object to be 
        '''
        if self.history:
            if not self.current_channel_model_obj is None:
                await self.current_channel_model_obj.asave()
            try:
                self.current_channel_model_obj = await models.Channel.objects.aget(id=channel.id)
            except models.Channel.DoesNotExist:
                self.current_channel_model_obj = models.Channel(
                    id=channel.id,
                    guild=self.guild_model_obj,
                    name=channel.name
                )
        
        # I don't actually know when this would be used 
        # but this is just in case. . .
        else:
            self._get_channel(channel)


    async def _update_and_save_count_model_objects(self, Model_Class):
        '''
        Update all model objects for a specific model, and save them to the DB
        '''
        logger.debug(f'{self.guild_name}::{Model_Class.__name__} saving. . .')
        items = tuple(self.cache_copy[Model_Class].items())
        for hash_val, dummy_model_obj in items:
            assert issubclass(Model_Class, models.MemberStat)
            valid_member = self.cache_copy[models.Member][dummy_model_obj.member.user_id]
            if Model_Class is models.Mention_Count:
                obj_attr = self.cache_copy[models.Member][dummy_model_obj.obj.user_id]
            else:
                obj_attr = dummy_model_obj.obj
            kwargs = {'member': valid_member, 'obj': obj_attr}
            try:
                real_model_obj = await Model_Class.objects.aget(**kwargs)
                real_model_obj.merge(dummy_model_obj)
            except Model_Class.DoesNotExist:
                real_model_obj = Model_Class(
                    member = valid_member,
                    obj=obj_attr,
                    count=dummy_model_obj.count
                )
            self.cache_copy[Model_Class][hash_val] = real_model_obj

        await Model_Class.objects.abulk_create_or_update(
            self.cache_copy[Model_Class].values()
        )
        logger.debug(f'{self.guild_name}::{Model_Class.__name__} saved to DB')
    
    async def _update_and_save_member_objects(self):
        '''
        Update and save Member objects to the DB
        Update the Member object IDs to those assigned to them by the database
        '''
        logger.debug(self.guild_name + '::Member saving. . . ')
        for hash_val, dummy_model_obj in self.cache_copy[models.Member].items():
            user_id = dummy_model_obj.user_id
            guild = dummy_model_obj.guild
            try:
                real_model_obj = await models.Member.objects.aget(user_id=user_id, guild=guild)
                real_model_obj.merge(dummy_model_obj)
                self.cache_copy[models.Member][hash_val] = real_model_obj
            except models.Member.DoesNotExist:
                pass
        
        await models.Member.objects.abulk_create_or_update(
            self.cache_copy[models.Member].values()
        )
        updated_models_list = list()
        for member in self.cache_copy[models.Member].values():
            real_model_obj = await models.Member.objects.aget(user_id=member.user_id, guild=self.guild_model_obj) 
            updated_models_list.append(real_model_obj)
            

        # after postgres assigns auto IDs to all of the user models,
        # the cached (temporary) user models must be updated with those IDs
        # this is so that the count objects can backreference the correct user object
        # this is ABSOLUTELY NECESSARY
        self.cache_copy[models.Member] = {member_model_obj.user_id:member_model_obj for member_model_obj in updated_models_list}

        logger.debug(self.guild_name + '::Member saved to DB')


    async def _update_and_save_objects(self, Model_Class):
        '''
        Update and save objects from the cache to the DB
        '''
        logger.debug(f'{self.guild_name}::{Model_Class.__name__} saving. . .')
        for obj_id, dummy_model_obj in self.cache_copy[Model_Class].items():
            try:
                real_model_obj = await Model_Class.objects.aget(id=dummy_model_obj.id)
                real_model_obj.merge(dummy_model_obj)
                self.cache_copy[Model_Class][obj_id] = real_model_obj  
            except Model_Class.DoesNotExist:
                pass
        await Model_Class.objects.abulk_create_or_update(
            self.cache_copy[Model_Class].values()
        )   
        logger.debug(f'{self.guild_name}::{Model_Class.__name__} saved to DB')
    
    def _compare_hour_and_user_counts(self):
        for member_model_obj in self.cached_model_objects[models.Member].values():
            for hour in range(24):
                value = member_model_obj.hour_counts_tz('utc')[hour]
                if value != 0:
                    assert self.cached_model_objects[models.Hour_Count][(member_model_obj.user_id, hour)].count == value
                

    async def _save(self):
        '''
        Asynchronously saves all info to the DB
        '''
        # sometimes, the program will save() before the previous save() is done saving
        # using a semaphore here ensures that only one call to save() will be running at any given time
        async with self._saving_semaphore:
            self._compare_hour_and_user_counts()

            self.guild_model_obj.last_msg_dt = datetime.datetime.now(datetime.UTC)
            await self.guild_model_obj.asave()

            # freeze the entire cache in-place for it to be saved
            self.cache_copy = self.cached_model_objects
            self.reset()


            # save these objects first, to avoid foreign key conflicts (you dummy)
            await self._update_and_save_objects(models.User)
            await self._update_and_save_objects(models.Emoji)

            await self._update_and_save_member_objects()

            if self.history:
                await self.current_channel_model_obj.asave()
            else:
                await self._update_and_save_objects(models.Channel)

            # save the rest asynchronously
            gather_list = []
            for Model_Class in COUNT_MODELS:
                gather_list.append(self._update_and_save_count_model_objects(Model_Class))

            await asyncio.gather(*gather_list)

    async def save(self):
        try:
            await self._save()
        except Exception as e:
            logger.error(e, exc_info=True)
