import discord

import asyncio

import logging

from aiohttp.client_exceptions import ClientOSError

from timeit import default_timer 
from textwrap import dedent


from .processor import Processor

MSG_LIMIT = 100
TIMEOUT = 15

logger = logging.getLogger('collection')

class History_Collector:
    def __init__(self, bot, guild, processor):
        self.bot = bot
        self.guild = guild

        self.processor = processor
        processor.history = True

        self.messages_scraped = 0
        self._processing_time = 0 

        logger.info("\n\nStarting scraping on:" + guild.name)



    async def _read_channel(self, channel):
        await self.processor.set_channel(channel)
        if self.processor.current_channel_model_obj.enabled == False:
            return
        logger.info(f"---\nStarting {channel.name} . . .")
        if self.processor.current_channel_model_obj.last_message_dt is not None:
            logger.debug(f"at {self.processor.current_channel_model_obj.last_message_dt}")
        
        while True:
            last_message_dt = self.processor.current_channel_model_obj.last_message_dt
            collection_start = default_timer()
            try:
                async with asyncio.timeout(TIMEOUT):
                    messages = [message async for message in channel.history(
                        oldest_first=True,
                        before=self.processor.guild_model_obj.start_dt,
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
                if not await self.processor.is_blacklisted(message.author):
                    self.processor.process_message(message, history = True)
            
                ### progress update
                if self.processor.cache_count % 500 == 0:
                    logger.debug(self.guild.name + ' Message #: ' + str(self.messages_scraped))
                
                # save on every 20,000th message 
                if self.processor.cache_count % 20000 == 0:
                    self.bot.loop.create_task(self.processor.save(), name = f"Processor Save {self.guild.id}")
                self.messages_scraped += 1

            process_end = default_timer()
            self._processing_time += (process_end-process_start)
            logger.debug(self.guild.name + ' Processing time: ' + str((process_end-process_start)) + ' seconds')
            logger.debug(self.guild.name + ' Latency:' + str(self.bot.latency))

            if len(messages) < MSG_LIMIT:
                break

        self.bot.loop.create_task(self.processor.save(), name = f"Processor Save {self.guild.id}")
        
    async def _collect_data(self):

        self.start_time = default_timer()
        for channel in self.guild.channels:
            perms = channel.permissions_for(self.guild.me)
            if not (type(channel) is discord.channel.TextChannel and perms.read_message_history):
                continue
            await self._read_channel(channel)

    async def collect_data(self):
        try:
            await self._collect_data()
        except Exception as e:
            # for some reason the exception is temporarily swallowed by the event loop
            # so I need to log it explicitly
            logger.error(e, exc_info=True)
        finally: 
            end_time = default_timer()
            time_elapsed = end_time - self.start_time
            mps = self.messages_scraped / time_elapsed
            logger.info(dedent(
                f'''
                - - - 
                {self.processor.guild_model_obj.name}
                Time elapsed: {time_elapsed:.2f} seconds
                Messages scraped: {self.messages_scraped}
                Messages per second: {mps:.2f}
                Total processing time: {self._processing_time:.4f} seconds
                Last message in {self.processor.current_channel_model_obj.name} created at {self.processor.current_channel_model_obj.last_message_dt}
                '''
            ))
            logger.info('Saving. . . ')


            start_time = default_timer()
            await self.processor.save()
            end_time = default_timer()
            time_elapsed = end_time - start_time
            logger.info(f'Database save complete! Took {time_elapsed:.4f} seconds.')