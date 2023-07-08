import discord

from .presets import MSG_LIMIT, GUILD_ID

from .data_processor import Data_Processor
from . import models


import timeit

class ProcessorClient(discord.Client):
    async def on_ready(self):

        print(f'Logged on as {self.user}!')
        processor = Data_Processor()
        # register the guild's name 
        guild = self.get_guild(GUILD_ID)
        guild_model_object, created = await models.Guild.objects.aget_or_create(
            id=guild.id,
            defaults={'name': guild.name, 'icon': guild.icon.url}
            )
        
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
            # setup for message retrieval:
            # if the channel has been processed at least once, begin at the last processed message
            # if the channel has never been processed, start at the oldest message
            kwargs = {'limit': MSG_LIMIT}
            if not channel_created: # this means the channel has been processed at least once
                # skip the channel if all messages have been processed 
                # note: this is the only way to reliably get the last *readable* message in a channel
                last_readable_message_id = [message async for message in channel.history(limit=1)][0].id
                if last_readable_message_id == channel_model_object.last_processed_message_id:
                    continue

                message_obj = await channel.fetch_message(channel_model_object.last_processed_message_id)
                kwargs['after'] = message_obj

            else:
                kwargs['oldest_first'] = True

            async for message in channel.history(**kwargs):

                ### progress update 
                messages_scraped += 1
                if messages_scraped%10000 == 0:
                    print(f'{messages_scraped // 1000}k/', end='')

                # skip all messages by bots
                if message.author.bot:
                    continue

                await processor.process_message(message)

                '''
                ### actual code
                if message.type is discord.MessageType.default:
                    database.process_message(message)
                    
                # first we check if the reply is deleted, or still in the cache (fast af)
                # if not, we fetch the message (slow af)
                elif message.type is discord.MessageType.reply:
                    reply_message = message.reference.resolved
                    if not message.reference.fail_if_not_exists: # checks if the reply was deleted
                        if message.reference.resolved is None: # this means the message isn't in the cache
                            reply_message = channel.fetch_message(message.reference.message_id)
                            #
                            # REVISIT THIS - suspicious that there's no error even though it's 
                            # a coroutine
                            #
                    database.process_message(message, reply_message)
                '''
            # save the ID of the last processed message
            channel_model_object.last_processed_message_id = message.id
            await channel_model_object.asave()

        print('\ndone!')
        end_time = timeit.default_timer()
        time_elapsed = end_time - start_time
        print('Time elapsed:', end_time - start_time)
        print('Messages scraped: ', messages_scraped)
        print('Time per message:', time_elapsed / messages_scraped)
        await self.close()
        

intents = discord.Intents.default()
intents.message_content = True

client = ProcessorClient(intents=intents)

# Due to how Django is structured, this bot must be run as a management command
# The file where it runs is stats/management/commands/MuffinBot.py