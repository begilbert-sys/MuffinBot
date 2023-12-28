import discord

import asyncio

import logging

from aiohttp.client_exceptions import ClientOSError

from timeit import default_timer 


from .processor import Processor

MSG_LIMIT = 100
TIMEOUT = 15

logger = logging.getLogger('collection')

class History_Collector:
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild

        self._processing_time = 0 

        logger.debug("\n\nStarting scraping on:" + guild.name)



    async def _read_channel(self, channel):
        await self.db_processor.process_channel(channel)
        logger.debug(f"---\nStarting {channel.name} . . .")
        if self.db_processor.current_channel_model_obj.last_message_dt is not None:
            logger.debug(f"at {self.db_processor.current_channel_model_obj.last_message_dt}")
        
        while True:
            last_message_dt = self.db_processor.current_channel_model_obj.last_message_dt
            collection_start = default_timer()
            try:
                async with asyncio.timeout(TIMEOUT):
                    messages = [message async for message in channel.history(
                        oldest_first=True,
                        after=last_message_dt,
                        limit=MSG_LIMIT
                    )]
            except TimeoutError as e:
                logger.warning(f'{self.guild.name} timeout in channel {channel.name} at {last_message_dt}')
                continue
            except ClientOSError as e:
                if e.errno == 60:
                    # error code 60 denotes a timeout error 
                    logger.error(e, exc_info=True)
                    continue
                else:
                    raise
            finally: 
                collection_end = default_timer()
                logger.debug(self.guild.name + ' Actual message Scraping: ' +  str((collection_end-collection_start)) + ' seconds')


            process_start = default_timer()
            for message in messages:
                if not await self.db_processor.is_blacklisted(message.author):
                    self.db_processor.process_message(message)
            
                ### progress update
                self.messages_scraped += 1
                if self.messages_scraped % 500 == 0:
                    logger.debug(self.guild.name + ' Message #: ' + str(self.messages_scraped))
            
            process_end = default_timer()
            self._processing_time += (process_end-process_start)
            logger.debug(self.guild.name + ' Processing time: ' + str((process_end-process_start)) + ' seconds')

            if len(messages) < MSG_LIMIT:
                break

        self.bot.loop.create_task(self.db_processor.save())
        
    async def collect_data(self):
        self.db_processor = Processor(history=True)
        self.messages_scraped = 0

        await self.db_processor.process_guild(self.guild)

        self.start_time = default_timer()
        for channel in self.guild.channels:
            perms = channel.permissions_for(self.guild.me)
            if not (type(channel) is discord.channel.TextChannel and perms.read_message_history):
                continue
            await self._read_channel(channel)