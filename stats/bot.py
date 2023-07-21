import discord

from .presets import MSG_LIMIT, GUILD_ID

from .data_processor import Data_Processor
from . import models

import asyncio
import datetime
import pytz
import timeit

# gets the blacklist of user IDs
with open('stats/blacklists/user_blacklist.txt') as f:
    USER_BLACKLIST = [int(user_id) for user_id in f.read().split('\n')]

def get_datetime_from_snowflake(snowflake: int) -> datetime.datetime:
    ''' given a discord ID (a snowflake), performs a calculation on the ID to retreieve its creation datetime in UTC'''
    return datetime.datetime.fromtimestamp(((snowflake >> 22) + 1420070400000) / 1000, pytz.UTC)

class ProcessorClient(discord.Client):
    async def process_messages(self):
        processor = Data_Processor()
        # register the guild
        guild = self.get_guild(GUILD_ID)
        if not await models.Guild.objects.aexists():
            guild_model_object = await models.Guild.objects.acreate(id=guild.id, name=guild.name, icon=guild.icon.url)
            await guild_model_object.asave()
        
        messages_scraped = 0 
        start_time = timeit.default_timer()
        
        for channel in guild.channels:
            # only iterates thru channels that are text channels it has perms to
            perms = channel.permissions_for(guild.me)
            if not (type(channel) is discord.channel.TextChannel and perms.read_message_history):
                continue

            channel_model_object, channel_created = await models.Channel.objects.aget_or_create(
                id=channel.id,
                defaults={'name': channel.name}
            )
            # if the date of the last retreieved message is greater than or equal to the date of the last message in the channel,
            # then skip this channel
            last_message_datetime = get_datetime_from_snowflake(channel.last_message_id)
            if (not channel_created and 
                channel_model_object.last_processed_message_datetime >= last_message_datetime):
                continue
            
            # setup for message retrieval:
            # if the channel has been processed at least once, begin at the last processed message
            kwargs = {'limit': MSG_LIMIT}
            if not channel_created: 
                kwargs['after'] = channel_model_object.last_processed_message_datetime

            # if the channel has never been processed, start at the oldest message
            else:
                kwargs['oldest_first'] = True

            async for message in channel.history(**kwargs):
                # skip all messages by bots
                if message.author.bot:
                    continue

                # skip all messages by users on the blacklist 
                if message.author.id in USER_BLACKLIST:
                    continue 

                # if the message is a reply, get the reply and pass it with the original message
                if message.type is discord.MessageType.reply:
                    reply_message = message.reference.resolved
                    if not reply_message:
                        print(message.content)
                        print(message.created_at)
                        raise AssertionError("Reply Message Failed")
                    if reply_message:
                        processor.process_message(message, reply_message)
                
                # if the message is not a reply, process it normally
                elif message.type is discord.MessageType.default:
                    processor.process_message(message)

                ### progress update
                messages_scraped += 1
                if messages_scraped % 100 == 0:
                    print('Message #: ', messages_scraped)
                        # save the datetime of the last processed message

            channel_model_object.last_processed_message_datetime = message.created_at
            await channel_model_object.asave()
        await processor.asave_to_database()
        print('\ndone!')
        end_time = timeit.default_timer()
        time_elapsed = end_time - start_time
        print('Time elapsed:', end_time - start_time)
        print('Messages scraped: ', messages_scraped)
        if messages_scraped: 
            print('Time per message:', time_elapsed / messages_scraped)

    async def on_ready(self):

        print(f'Logged on as {self.user}!')
        await self.process_messages()
        print('done!')
        await self.close()


intents = discord.Intents.default()
intents.message_content = True

client = ProcessorClient(intents=intents)

# Due to how Django is structured, this bot must be run as a management command
# The file where it runs is stats/management/commands/MuffinBot.py