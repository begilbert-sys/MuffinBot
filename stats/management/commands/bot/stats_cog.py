import discord
from discord.ext import commands, tasks

import datetime
import logging
import os
import pytz
import timeit
from .presets import MSG_LIMIT, GUILD_ID, REPEATS

from .data_processor import Data_Processor
logger = logging.getLogger(__package__)

channel_blacklist_path = os.path.join(os.path.dirname(__file__), 'channel_blacklist.txt')
with open(channel_blacklist_path) as f:
    CHANNEL_BLACKLIST = set(int(line.split()[0]) for line in f.read().split('\n'))

def get_datetime_from_snowflake(snowflake: int) -> datetime.datetime:
    '''given a discord ID (a snowflake), performs a calculation on the ID to retreieve its creation datetime in UTC'''
    return datetime.datetime.fromtimestamp(((snowflake >> 22) + 1420070400000) / 1000, pytz.UTC)


class Processor_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        #self.processor_loop.start()

    async def _read_history(self, channel, kwargs):
        self._last_message = None
        async for message in channel.history(**kwargs):
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

    async def process_data(self):
        self.db_processor = Data_Processor()
        self.messages_scraped = 0

        self.guild = self.bot.get_guild(GUILD_ID)
        await self.db_processor.process_guild(self.guild)

        self.start_time = timeit.default_timer()
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

    @tasks.loop(count=REPEATS)
    async def processor_loop(self):
        try:
            await self.process_data()
        finally:
            end_time = timeit.default_timer()
            time_elapsed = end_time - self.start_time
            logger.info('Time elapsed: ' + str(time_elapsed))
            logger.info('Messages scraped: ' +  str(self.messages_scraped))
            if self.messages_scraped: 
                logger.info('Time per message: ' + str(time_elapsed / self.messages_scraped))
            logger.info('Saving. . . ')


            start_time = timeit.default_timer()
            await self.db_processor.save()
            end_time = timeit.default_timer()
            time_elapsed = end_time - start_time
            logger.info('Database save complete! Took ' + str(time_elapsed) + ' seconds.')

    @processor_loop.before_loop
    async def before_process(self):
        await self.bot.wait_until_ready()

    @processor_loop.after_loop
    async def after_process(self):
        await self.bot.close()
    

    ### Bot Commands Start Here

    @commands.command()
    async def stats(self, ctx):
        await ctx.send("http://muffinstats.net/stats/")
    
    @commands.command()
    async def mystats(self, ctx):
        user = ctx.author
        if user.discriminator == '0':
            tag = user.name
        else:
            tag = user.name + '＃' + user.discriminator 
        await ctx.send("http://muffinstats.net/stats/users/" + tag)
    
    @commands.command()
    async def source(self, ctx):
        await ctx.send("https://github.com/begilbert-sys/MuffinBot")
    
    @commands.command()
    async def blacklist(self, ctx):
        status = await self.db_processor.blacklist(ctx.author)
        await ctx.send(status)
    
    @commands.command()
    async def whitelist(self, ctx):
        status = await self.db_processor.whitelist(ctx.author)
        await ctx.send(status)
    
    
async def setup(bot):
    await bot.add_cog(Processor_Cog(bot))