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
        if created:
            await guild_model_object.asave()
        
        messages_scraped = 0 
        start_time = timeit.default_timer()

        bulk_channel_model_objects = list()


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
                last_message_datetime = channel_model_object.last_processed_message_datetime
                kwargs['after'] = last_message_datetime

            else:
                kwargs['oldest_first'] = True

            async for message in channel.history(**kwargs):
                # skip all messages by bots
                if message.author.bot:
                    continue


                if message.type is discord.MessageType.default:
                    processor.process_message(message)
                    
                # first we check if the reply is deleted, or still in the cache (fast af)
                # if not, we fetch the message (slow af)
                elif message.type is discord.MessageType.reply:
                    reply_message = message.reference.resolved
                    if not message.reference.fail_if_not_exists: # checks if the reply was deleted
                        if message.reference.resolved is None: # this means the message isn't in the cache
                            raise Exception('examine this reply. message contents: ' + message.contents)
                            reply_message = await channel.fetch_message(message.reference.message_id)
                    processor.process_message(message, reply_message)

                ### progress update
                messages_scraped += 1
                if messages_scraped % 100 == 0:
                    print('Message #: ', messages_scraped)
                    
            # save the datetime of the last processed message
            channel_model_object.last_processed_message_datetime = message.created_at
            bulk_channel_model_objects.append(channel_model_object)

        print('\ndone!')
        end_time = timeit.default_timer()
        time_elapsed = end_time - start_time
        print('Time elapsed:', end_time - start_time)
        print('Messages scraped: ', messages_scraped)
        print('Time per message:', time_elapsed / messages_scraped)

        print('Updating database. . .')
        await models.Channel.objects.abulk_create(
            bulk_channel_model_objects, 
            update_conflicts=True,
            update_fields = ['last_processed_message_datetime'],
            unique_fields  = ['id']
        )
        await processor.asave_to_database()
        await self.close()
        

intents = discord.Intents.default()
intents.message_content = True

client = ProcessorClient(intents=intents)

# Due to how Django is structured, this bot must be run as a management command
# The file where it runs is stats/management/commands/MuffinBot.py