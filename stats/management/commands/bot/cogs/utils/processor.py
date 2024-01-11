import discord
import asyncio
import datetime 
import emoji
import json
import logging
import re
from itertools import chain 

from stats import models
from stats.utils import hashed_id

logger = logging.getLogger('collection')

DELETED_USER_ID = 456226577798135808

with open('stats/data/words.txt') as f:
    WORDS = set(f.read().split('\n'))
    
with open('stats/data/curse_words.txt') as f:
    CURSE_WORDS = set(f.read().split('\n'))

with open('stats/data/emoji_ids.json') as f:
    EMOJI_IDS = json.load(f)

# list all of the count model classes
COUNT_MODELS = models.MemberStat.__subclasses__()

def get_URLs(string: str) -> list[str]:
    '''Extract all the URLs from a string'''
    url_regex = r'(http|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])'
    raw_urls = [url.group(0) for url in re.finditer(url_regex, string) if len(url.group(0)) <= 200]
    return raw_urls

def get_half_hour_increment(dt: datetime.datetime) -> int:
    '''Given a datetime, return an int from 0 to 47 denoting the time of day'''
    return (dt.hour * 2) + (1 if dt.minute >= 30 else 0)

class Processor:
    def __init__(self):
        self.active = False

        # denotes if the processor is also processing message history
        self.history = False
        self.current_channel_model_obj = None

        self.guild_model_obj = None

        # explanation for this variable in save() function 
        self._saving_semaphore = asyncio.Semaphore(1)

        # ensures that the save() function finishes every time. for debugging
        self._save_checker = 0

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
    
    async def activate(self):
        self.active = True
        self.guild_model_obj.setup = True
        self.guild_model_obj.start_dt = datetime.datetime.now(datetime.UTC)
        await self.guild_model_obj.asave()

    def _get_member(self, user: discord.User | discord.Member) -> models.Member:
        '''
        
        '''
        if user.id in self.cached_model_objects[models.Member]:
            return self.cached_model_objects[models.Member][user.id]
        new_user_model_obj = models.User(
            id=user.id,
            tag=user.name,
            discriminator=user.discriminator if user.discriminator != '0' else None,
            avatar_id = user.display_avatar.key
        )
        self.cached_model_objects[models.User][user.id] = new_user_model_obj
        new_member_model_obj = models.Member(
            guild=self.guild_model_obj,
            user=new_user_model_obj,
            nick=user.global_name if user.global_name else user.name
        )
        if type(user) is discord.Member and user.nick:
            new_member_model_obj.nick = user.nick
        if user.id == DELETED_USER_ID:
            new_member_model_obj.hidden = True
        self.cached_model_objects[models.Member][user.id] = new_member_model_obj
        return new_member_model_obj
    
    def _get_channel(self, channel: discord.TextChannel) -> models.Channel:
        '''
        Get, update, or create a channel model obj in the cache. Return the obj
        '''
        if channel.id in self.cached_model_objects[models.Channel]:
            channel_model_obj = self.cached_model_objects[models.Channel][channel.id]
            channel_model_obj.name = channel.name
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
        
    async def is_blacklisted(self, user: discord.User) -> bool:
        '''Return whether or not a user is blacklisted'''
        hashed = hashed_id(user.id)
        return await models.UserBlacklist.objects.filter(hash_value=hashed).aexists() or await models.MemberBlacklist.objects.filter(user_id=user.id, guild=self.guild_model_obj).aexists()
    
    def process_reaction(self, reaction: discord.Reaction, count):
        emoji_object = reaction.emoji
        print(emoji_object)
        member_model_obj = self._get_member(reaction.message.author)
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
            
    def process_message(self, message: discord.Message, *, unprocess = False, history = False):
        '''
        Given a message, increment or decrement all of the cached models accordingly 
        '''
        if message.author.bot: # ignore if user is bot
            if self.history:
                self.current_channel_model_obj.last_message_dt = message.created_at
            return

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
            self.process_reaction(reaction, crement)
        
        ### URL
        for URL in get_URLs(message.content):
            self._increment_count(models.URL_Count, member_model_obj, URL, crement)
        
        ### UNIQUE WORDS AND CURSE WORDS
        for word in message.content.lower().split():
            # valid 'words' need to be alphabetic and between 3 and 18 characters
            if word.isalpha() and len(word) in range(3,15):
                if word not in WORDS:
                    self._increment_count(models.Unique_Word_Count, member_model_obj, word, crement)
                if word in CURSE_WORDS:
                    member_model_obj.curse_word_count += crement

        ### MENTIONS
        reply_message = None
        if message.type is discord.MessageType.reply and type(message.reference.resolved) is not discord.DeletedReferencedMessage:
            reply_message = message.reference.resolved
        all_mentions = self._get_message_mentions(message, reply_message)
        for member in all_mentions:
            self._increment_count(models.Mention_Count, member_model_obj, member, crement)

        if self.history:
            self.current_channel_model_obj.last_message_dt = message.created_at
        self.cache_count += 1

    async def process_guild(self, guild: discord.guild):
        '''
        Save a guild's info to the DB if it has not already been added
        '''
        if self.guild_model_obj: # the guild must always be the same
            assert self.guild_model_obj.id == guild.id

        self.guild_model_obj, newly_created = await models.Guild.objects.aupdate_or_create(
            id=guild.id, 
            defaults={
                "name": guild.name, 
                "icon_id": guild.icon.key if guild.icon else None
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
    
    async def set_channel(self, channel: discord.channel):
        '''
        Only for use when collecting server history
        Sets the channel model obj
        '''
        assert self.history
        # this save is to ensure the last_message_dt value gets saved
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

    async def process_channel(self, channel: discord.channel):
        '''
        Processes a channel
        '''
        self._get_channel(channel)
    
    async def _update_and_save_count_model_objects(self, Model_Class):
        '''
        Update all model objects for a specific model, and save them to the DB
        '''
        logger.debug(f'{self.guild_model_obj.name}::{Model_Class.__name__} saving. . .')
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
        logger.debug(f'{self.guild_model_obj.name}::{Model_Class.__name__} saved to DB')
    
    async def _update_and_save_member_objects(self):
        '''
        Update and save Member objects to the DB
        Update the Member object IDs to those assigned to them by the database
        '''
        logger.debug(self.guild_model_obj.name + '::Member saving. . . ')
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

        logger.debug(self.guild_model_obj.name + '::Member saved to DB')

    async def _update_and_save_objects(self, Model_Class):
        '''
        Update and save objects from the cache to the DB
        '''
        logger.debug(f'{self.guild_model_obj.name}::{Model_Class.__name__} saving. . .')
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
        logger.debug(f'{self.guild_model_obj.name}::{Model_Class.__name__} saved to DB')
    
    async def _clear_deletion_queue(self) -> [int, int]:
        '''
        Delete all member objects in the deletion queue, if any
        Return number of member and user objects deleted, respectively 
        '''
        count = [0, 0]
        async for obj in models.MemberDeletionQueue.objects.filter(guild=self.guild_model_obj):
            user_id = obj.user_id
            member_model_obj = await models.Member.objects.aget(user_id=user_id, guild=self.guild_model_obj)
            await member_model_obj.adelete()
            await obj.adelete()
            count[0] += 1
            # if all member objects have been deleted, and there's still an object in the user deletion queue, delete it

            if not await models.MemberDeletionQueue.objects.filter(user_id=user_id).aexists():
                try:
                    user_deletion_obj = await models.UserDeletionQueue.objects.aget(id=user_id)
                except models.UserDeletionQueue.DoesNotExist:
                    return count
                user_model_obj = await models.User.objects.aget(id=user_deletion_obj.id)
                await user_model_obj.adelete()
                await user_deletion_obj.adelete()
                count[1] += 1
        return count

    async def _save(self):
        '''
        Asynchronously saves all info to the DB
        '''
        # sometimes, the program will save() before the previous save() is done saving
        # using a semaphore here ensures that only one call to save() will be running at any given time
        async with self._saving_semaphore:
            assert self._save_checker == 0
            self._save_checker = 1
            logger.info(f"Saving {self.guild_model_obj.name}. . .")

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
            await self._update_and_save_objects(models.Channel)

            # save the rest asynchronously
            gather_list = []
            for Model_Class in COUNT_MODELS:
                gather_list.append(self._update_and_save_count_model_objects(Model_Class))

            await asyncio.gather(*gather_list)
            logger.info("Done saving")

            logger.info("Clearing Deletion Queue")
            member_count, user_count = await self._clear_deletion_queue()
            logger.info(f"{member_count} members deleted, {user_count} users deleted")

            self._save_checker = 0
            
    async def save(self):
        try:
            await self._save() # saving to DB should finish once it starts, hence the shield
        except Exception as e:
            logger.error(e, exc_info=True)
