import discord
from discord.ext import commands

class Interface_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
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
    async def hide(self, ctx):
        status = await self.db_processor.blacklist(ctx.author)
        await ctx.send(status)
    
    @commands.command()
    async def unhide(self, ctx):
        status = await self.db_processor.whitelist(ctx.author)
        await ctx.send(status)
    
    @commands.command()
    async def blacklist(self, ctx):
        pass

    @commands.command()
    async def test(self, ctx):
        channel = ctx.channel
        counter = 0
        async for message in channel.history(limit=3000):
            counter += 1
            if counter % 50 == 0:
                print('UCLA message:', counter)


async def setup(bot):
    await bot.add_cog(Interface_Cog(bot))