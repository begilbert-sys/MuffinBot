# This example requires the 'message_content' intent.

import discord

from stats.discord_database import Dictionary_Database

from stats.presets import TOKEN, MSG_LIMIT, GUILD_ID

database = Dictionary_Database(GUILD_ID)
    
class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
        # register the guild's name 
        guild = self.get_guild(GUILD_ID)
        if not database.name:
            database.name = guild.name
        
        for channel in guild.channels:
            perms = channel.permissions_for(guild.me)
            channel_key = str(channel.id)
            # only iterates thru channels that: are text channels, it has perms to, and the last msg hasn't been processed
            if (type(channel) is discord.channel.TextChannel and perms.read_message_history 
                and channel.last_message_id != database.channel_endmsgs.get(channel_key)):

                # setup for message retrieval: allows both new and already-scraped channels to be scraped
                kwargs = {'limit': MSG_LIMIT}
                if channel_key in database.channel_endmsgs:
                    last_msg_id = database.channel_endmsgs[channel_key]
                    message_obj = await channel.fetch_message(last_msg_id)
                    kwargs['after'] = message_obj
                else:
                    kwargs['oldest_first'] = True

                async for message in channel.history(**kwargs):
                    if message.type in (discord.MessageType.default, discord.MessageType.reply):
                        database.process_message(message)
        print('done!')
        database.save()
        print(database.database_totals['channel_counts'])
        await self.close()
intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
if __name__ == '__main__':
    client.run(TOKEN)
