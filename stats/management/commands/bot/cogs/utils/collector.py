import discord

import datetime
import logging
import os
import pytz

from timeit import default_timer 

from .processor import Processor

MSG_LIMIT = 900
logger = logging.getLogger('collection')

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
        logger.debug("\n\nStarting scraping on:" + guild.name)

    async def _read_channel(self, channel):
        await self.db_processor.process_channel(channel)
        logger.debug(f"Starting {channel.name} . . . ")
        last_message = None
        till_reset = 0
        while True:
            messages = [message async for message in channel.history(
                oldest_first=True, 
                after=last_message.created_at if last_message else None,
                limit = MSG_LIMIT
            )]

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

                last_message = message

                ### progress update
                self.messages_scraped += 1
                till_reset += 1
                if self.messages_scraped % 500 == 0:
                    logger.debug(self.guild.name + ' Message #: ' + str(self.messages_scraped))

                if till_reset >= 100000: # cull the database
                    await self.db_processor.save()
                    
                    till_reset = 0 
            if len(messages) < MSG_LIMIT:
                logging.debug('Last message created at:', last_message.created_at)
                break
        await self.db_processor.save()
        
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

            await self._read_channel(channel)