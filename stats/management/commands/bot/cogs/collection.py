import discord
from discord.ext import commands, tasks

import logging
from timeit import default_timer

from .utils.collector import Collector

logger = logging.getLogger(__package__)

class Collection_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_collectors = dict()

    @tasks.loop(count=1)
    async def collection_instance(self, guild: discord.Guild):
        collector = Collector(self.bot, guild)
        self.active_collectors[guild.id] = collector
        try:
            await collector.collect_data()
        finally:
            end_time = default_timer()
            time_elapsed = end_time - collector.start_time
            logger.info('Time elapsed: ' + str(time_elapsed))
            logger.info('Messages scraped: ' +  str(collector.messages_scraped))
            if collector.messages_scraped: 
                logger.info('Messages per second: ' + str(collector.messages_scraped / time_elapsed))
            logger.info('Saving. . . ')


            start_time = default_timer()
            await collector.db_processor.save()
            end_time = default_timer()
            time_elapsed = end_time - start_time
            logger.info('Database save complete! Took ' + str(time_elapsed) + ' seconds.')
        
    @commands.command()
    async def start(self,ctx):
        guild = ctx.guild
        if guild.id not in self.active_collectors:
            self.collection_instance.start(guild)

async def setup(bot):
    await bot.add_cog(Collection_Cog(bot))