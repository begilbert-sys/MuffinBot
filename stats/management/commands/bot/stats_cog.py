import discord
from discord.ext import commands, tasks

import datetime
import logging
import pytz
import timeit
import traceback

from .presets import MSG_LIMIT, GUILD_ID

from .data_processor import Data_Processor


DELETED_USER_ID = 456226577798135808

def get_datetime_from_snowflake(snowflake: int) -> datetime.datetime:
    '''given a discord ID (a snowflake), performs a calculation on the ID to retreieve its creation datetime in UTC'''
    return datetime.datetime.fromtimestamp(((snowflake >> 22) + 1420070400000) / 1000, pytz.UTC)


class Processor_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.messages_scraped = 0
        self.db_processor = Data_Processor()
        
        self.process_data.start()

    

    async def _read_history(self, channel, kwargs):
        self._last_message = None
        async for message in channel.history(**kwargs):
            if message.author.bot:
                continue
            if message.author.id == DELETED_USER_ID:
                continue
            if message.type is discord.MessageType.reply:
                reply_message = message.reference.resolved
                if not reply_message: # either the message is deleted or just wasn't resolved
                    logging.debug('Reply message wasn\'t resolved. Offending message:\n' + str(message.content))
                    logging.debug('Reference info:' + str({k: getattr(message.reference, k) for k in message.reference.__slots__})) # print all attrs for debugging purposes
                    if type(reply_message) is not discord.DeletedReferencedMessage:
                        try:
                            reply_message = await channel.fetch_message(message.reference.message_id)
                            logging.debug("Message was found")
                        except discord.NotFound:
                            reply_message = None
                            logging.debug("Message was deleted")
                    else:
                        reply_message = None
                self.db_processor.process_message(message, reply_message)
            elif message.type is discord.MessageType.default:
                self.db_processor.process_message(message)
                
            self._last_message = message
                
            ### progress update
            self.messages_scraped += 1
            if self.messages_scraped % 500 == 0:
                logging.debug('Message #: ' + str(self.messages_scraped))

    @tasks.loop(count=1)
    async def process_data(self):
        self.guild = self.bot.get_guild(GUILD_ID)
        await self.db_processor.process_guild(self.guild)

        start_time = timeit.default_timer()
        for channel in self.guild.channels:
            perms = channel.permissions_for(self.guild.me)
            if not (type(channel) is discord.channel.TextChannel and perms.read_message_history):
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
            except:
                traceback.print_exc()
            finally:
                if self._last_message:
                    await self.db_processor.update_channel_last_message(channel, self._last_message)
                    logging.info(channel.name + ' saved')
                else:
                    logging.info(channel.name + ' skipped')

        end_time = timeit.default_timer()
        time_elapsed = end_time - start_time
        logging.info('Time elapsed: ' + str(end_time - start_time))
        logging.info('Messages scraped: ' +  str(self.messages_scraped))
        if self.messages_scraped: 
            logging.info('Time per message: ' + str(time_elapsed / self.messages_scraped))

    @process_data.before_loop
    async def before_process(self):
        await self.bot.wait_until_ready()
    
    @process_data.after_loop
    async def after_process(self):
        logging.info('Saving. . . ')
        start_time = timeit.default_timer()
        try:
            await self.db_processor.save()
            end_time = timeit.default_timer()
            time_elapsed = end_time - start_time 
            logging.info('Database save complete! Took ' + str(time_elapsed) + ' seconds.')
        except:
            traceback.print_exc()
        finally:
            await self.bot.close()

    ### Bot Commands Start Here

    @commands.command()
    async def stats(self, ctx):
        await ctx.send("https://bengilbert.net/stats/statsindex")

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