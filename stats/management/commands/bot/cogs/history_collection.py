import discord
from discord.ext import commands

import logging
from textwrap import dedent
from timeit import default_timer

from .utils.collector import History_Collector

logger = logging.getLogger('collection')

class History_Collection_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def collection_instance(self, guild: discord.Guild):
        if guild.id in self.active_collectors:
            logger.warning("Collection instance for guild no. " + str(guild.id) + " is already running!")
            return
        
        collector = History_Collector(self.bot, guild)
        self.active_collectors[guild.id] = collector
        try:
            await collector.collect_data()
        except Exception as e:
            # for some reason the exception is temporarily swallowed by the event loop
            # so I need to log it explicitly
            logger.error(e, exc_info=True)

        finally:
            end_time = default_timer()
            time_elapsed = end_time - collector.start_time
            mps = collector.messages_scraped / time_elapsed
            logger.info(dedent(
                f'''
                - - - 
                {guild.name}
                Time elapsed: {time_elapsed:.2f} seconds
                Messages scraped: {collector.messages_scraped}
                Messages per second: {mps:.2f}
                Total processing time: {collector._processing_time:.4f} seconds
                Last message in {collector.db_processor.current_channel_model_obj.name} created at {collector.db_processor.current_channel_model_obj.last_message_dt}
                '''
            ))
            logger.info('Saving. . . ')


            start_time = default_timer()
            await collector.db_processor.save()
            end_time = default_timer()
            time_elapsed = end_time - start_time
            logger.info(f'Database save complete! Took {time_elapsed:.4f} seconds.')
        
    @commands.Cog.listener()
    async def on_ready(self):
        #for guild in self.bot.guilds:
            #self.bot.loop.create_task(self.collection_instance(guild))
        guild = self.bot.get_guild(424942639906029568)
        self.bot.loop.create_task(self.collection_instance(guild))

    @commands.Cog.listener()
    async def on_disconnect(self):
        logger.error("CLIENT DISCONNECTED")
        for collector in self.active_collectors.values():
            await collector.db_processor.save()
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(History_Collection_Cog(bot))