# This example requires the 'message_content' intent.

import discord

from stats.discord_database import Dictionary_Database

from stats.presets import TOKEN, MSG_LIMIT, GUILD_ID

import timeit

database = Dictionary_Database(GUILD_ID)
    
class MyClient(discord.Client):
    async def on_ready(self):

        print(f'Logged on as {self.user}!')
        # register the guild's name 
        guild = self.get_guild(GUILD_ID)
        if not database.name:
            database.name = guild.name
        
        messages_scraped = 0 
        start_time = timeit.default_timer()

        for channel in guild.channels:
            perms = channel.permissions_for(guild.me)
            channel_key = str(channel.id)


            # only iterates thru channels that are text channels it has perms to
            if not (type(channel) is discord.channel.TextChannel and perms.read_message_history):
                continue

            # this is the only way to reliably get the last *readable* message in a channel
            last_readable_message_id = [message async for message in channel.history(limit=1)][0].id
            if last_readable_message_id == database.channel_endmsgs.get(channel_key):
                continue


            # setup for message retrieval: allows both new and already-scraped channels to be scraped
            kwargs = {'limit': MSG_LIMIT}
            if channel_key in database.channel_endmsgs:
                last_msg_id = database.channel_endmsgs[channel_key]
                message_obj = await channel.fetch_message(last_msg_id)
                kwargs['after'] = message_obj
            else:
                kwargs['oldest_first'] = True

            async for message in channel.history(**kwargs):
                # custom emojis must be read by the client 
                messages_scraped += 1
                if message.type is discord.MessageType.default:
                    database.process_message(message)
                    
                # first we check if the reply is deleted, or still in the cache (fast af)
                # if not, we fetch the message (slow af)
                elif message.type is discord.MessageType.reply:
                    reply_message = message.reference.resolved
                    if not message.reference.fail_if_not_exists: # checks if the reply was deleted
                        if message.reference.resolved is None: # this means the message isn't in the cache
                            reply_message = channel.fetch_message(message.reference.message_id)
                    database.process_message(message, reply_message)
            database.channel_endmsgs[channel_key] = message.id

        print('done!')
        end_time = timeit.default_timer()
        time_elapsed = end_time - start_time
        print('Time elapsed:', end_time - start_time)
        print('Messages scraped: ', messages_scraped)
        print('Time per message:', time_elapsed / messages_scraped)
        database.save()
        await self.close()

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
if __name__ == '__main__':
    client.run(TOKEN)
