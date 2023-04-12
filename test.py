# This example requires the 'message_content' intent.

import discord

from discord_database import Dictionary_Database

from API_Key import KEY

GUILD_ID = 100770673609150464

MSG_LIMIT = 25

database = Dictionary_Database(GUILD_ID)
    
class MyClient(discord.Client):
    async def on_ready(self):
        global guild
        print(f'Logged on as {self.user}!')
        
        guild = self.get_guild(GUILD_ID)
        
        n = 0
        for channel in guild.channels:
            perms = channel.permissions_for(guild.me)
            if type(channel) is discord.channel.TextChannel and perms.read_message_history:
                channel_key = str(channel.id)
                kwargs = {'limit': MSG_LIMIT}
                if channel_key in database.channel_endmsgs:
                    msg_id = database.channel_endmsgs[channel_key]
                    print(msg_id)
                    message_obj = await channel.fetch_message(msg_id)
                    kwargs['after'] = message_obj
                else:
                    kwargs['oldest_first'] = True
                    
                async for message in channel.history(**kwargs):
                    n += 1
                    if n % 1000 == 0:
                        print(n)
                    if message.type in (discord.MessageType.default, discord.MessageType.reply):
                        database.process_message(message)
            database.channel_endmsgs[channel_key] = message.id
        print('done!')
        database.save()
        print(database.database_totals['channel_counts'])
        await self.close()
intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(KEY)
