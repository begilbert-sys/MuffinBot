import discord

import datetime
import logging
import os
import pytz

from timeit import default_timer 

from .processor import Processor
from .presets import MSG_LIMIT
logger = logging.getLogger(__package__)

channel_blacklist_path = os.path.join(os.path.dirname(__file__), 'channel_blacklist.txt')
with open(channel_blacklist_path) as f:
    CHANNEL_BLACKLIST = set(int(line.split()[0]) for line in f.read().split('\n'))

def get_datetime_from_snowflake(snowflake: int) -> datetime.datetime:
    '''given a discord ID (a snowflake), performs a calculation on the ID to retreieve its creation datetime in UTC'''
    return datetime.datetime.fromtimestamp(((snowflake >> 22) + 1420070400000) / 1000, pytz.UTC)

class Collector:
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild

    async def _read_history(self, channel, kwargs):
        self._last_message = None
        messages = [message async for message in channel.history(**kwargs)]
        for message in messages:
            if message.author.bot:
                continue
            if message.type is discord.MessageType.reply:
                reply_message = message.reference.resolved 
                if type(reply_message) is discord.DeletedReferencedMessage:
                    reply_message = None
                elif reply_message == None: # either the message is deleted or just wasn't resolved
                    logger.debug('Reply message wasn\'t resolved. Offending message:\n' + str(message.content))
                    try:
                        reply_message = await channel.fetch_message(message.reference.message_id)
                        logger.debug("Message was found")
                    except discord.NotFound:
                        logger.debug("Message was deleted")
                self.db_processor.process_message(message, reply_message)
            elif message.type is discord.MessageType.default:
                self.db_processor.process_message(message)

            self._last_message = message
            ### progress update
            self.messages_scraped += 1
            if self.messages_scraped % 500 == 0:
                logger.debug('Message #: ' + str(self.messages_scraped))
        
    async def collect_data(self):
        self.db_processor = Processor()
        self.messages_scraped = 0

        await self.db_processor.process_guild(self.guild)

        self.start_time = default_timer()
        for channel in self.guild.channels:
            perms = channel.permissions_for(self.guild.me)
            if not (type(channel) is discord.channel.TextChannel and perms.read_message_history):
                continue

            if channel.id in CHANNEL_BLACKLIST:
                continue

            last_processed_message_datetime = await self.db_processor.handle_channel(channel)

            # if the date of the last retreieved message is greater than or equal to the date of the last message in the channel,
            # then skip this channel
            last_message_datetime = get_datetime_from_snowflake(channel.last_message_id)
            if (last_processed_message_datetime is not None
                and last_processed_message_datetime >= last_message_datetime):
                continue

            # setup for message retrieval:
            # if the channel has been processed at least once, begin at the last processed message
            kwargs = {'limit': MSG_LIMIT}
            if last_processed_message_datetime is not None:
                kwargs['after'] = last_processed_message_datetime

            # if the channel has never been processed, start at the oldest message
            else:
                kwargs['oldest_first'] = True
            try:
                await self._read_history(channel, kwargs)
            finally:
                if self._last_message:
                    await self.db_processor.update_channel_last_message(channel, self._last_message)
                    logger.info(channel.name + ' saved')
                else:
                    logger.info(channel.name + ' skipped')