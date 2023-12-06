import discord

import asyncio

import logging

from timeit import default_timer 


from .processor import Processor

MSG_LIMIT = 100
TIMEOUT = 10

logger = logging.getLogger('collection')

async def _get_messages(channel: discord.TextChannel, last_message_dt):
    # this function exists for the sole reason that in order to set a timeout using asyncio.wait_for(),
    # it needs to be able to call an awaitable function 
    # I'd use a lambda but sadly, async lambdas don't exist
    return [message async for message in channel.history(
        oldest_first=True,
        after=last_message_dt,
        limit=MSG_LIMIT
    )]

class Collector:
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild

        self._processing_time = 0 

        logger.debug("\n\nStarting scraping on:" + guild.name)

    async def _read_channel(self, channel):
        await self.db_processor.process_channel(channel)
        logger.debug(f"---\nStarting {channel.name} . . .")
        if not self.db_processor.current_channel_model_obj is None:
            logger.debug(f"at {self.db_processor.current_channel_model_obj.last_message_dt}")
        till_reset = 0

        while True:
            last_message_dt = self.db_processor.current_channel_model_obj.last_message_dt
            start = default_timer()
            try:
                messages = await asyncio.wait_for(
                    _get_messages(channel, last_message_dt), 
                    timeout=TIMEOUT
                )
            except TimeoutError as e:
                logger.error(e, exc_info=True)
                continue
            finally:
                end = default_timer()
                logger.debug('Actual message Scraping: ' +  str((end-start)) + ' seconds')
            
            start = default_timer()
            for message in messages:
                if message.author.bot:
                    self.db_processor.current_channel_model_obj.last_message_dt = message.created_at
                    continue
                if message.type is discord.MessageType.reply:
                    reply_message = message.reference.resolved 
                    if type(reply_message) is discord.DeletedReferencedMessage or reply_message == None:
                        reply_message = None
                    #elif reply_message == None: # either the message is deleted or just wasn't resolved
                        #logger.debug('Reply message wasn\'t resolved. Offending message:\n' + str(message.content))
                        #try:
                            #reply_message = await channel.fetch_message(message.reference.message_id)
                            #logger.debug("Message was found")
                        #except discord.NotFound:
                            #logger.debug("Message was deleted")
                    self.db_processor.process_message(message, reply_message)
                elif message.type is discord.MessageType.default:
                    self.db_processor.process_message(message)
                self.db_processor.current_channel_model_obj.last_message_dt = message.created_at
                
                ### progress update
                self.messages_scraped += 1
                till_reset += 1
                if self.messages_scraped % 500 == 0:
                    logger.debug(self.guild.name + ' Message #: ' + str(self.messages_scraped))

                if till_reset >= 100000: # cull the database
                    await self.db_processor.save()
                    
                    till_reset = 0
            end = default_timer()
            self._processing_time += (end-start)
            logger.debug('Processing time: ' + str((end-start)) + ' seconds')

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