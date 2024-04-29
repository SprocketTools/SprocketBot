import discord
from discord.ext import commands
from discord import app_commands
from cogs.textTools import textTools
class SprocketOfficialFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="gameSuggestion", description="Make a game suggestion")
    async def gameSuggestion(self, ctx: commands.Context):

        await ctx.send(f"Process started. \nSend a message containing your game suggestion and any attached media.")
        message = "This is a default response"
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = ""
        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=1800.0)
            message = await textTools.sanitize(msg.content)
        except Exception:
            pass

        avatarURL = ctx.author.display_avatar.url
        embed = discord.Embed(title=ctx.author.name, description=message, color=discord.Color.random())
        embed.set_thumbnail(url=avatarURL)
        channel = self.bot.get_channel(788352773086904321)
        sent_message = await channel.send(embed=embed)
        await sent_message.add_reaction(":plus1:881246627510239323")
        await sent_message.add_reaction(":minus1:881246627770282015")
        for attachment in msg.attachments:
            file = await attachment.to_file()
            await channel.send(file=file, content="")

    @commands.command(name="serverSuggestion", description="Make a server suggestion")
    async def serverSuggestion(self, ctx: commands.Context):

        await ctx.send(f"Process started. \nSend a message containing your game suggestion and any attached media.")
        message = "This is a default response"
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = ""
        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=1800.0)
            message = await textTools.sanitize(msg.content)
        except Exception:
            pass

        avatarURL = ctx.author.display_avatar.url
        embed = discord.Embed(title=ctx.author.name, description=message, color=discord.Color.random())
        embed.set_thumbnail(url=avatarURL)
        channel = self.bot.get_channel(1033317092876881991)
        sent_message = await channel.send(embed=embed)
        await sent_message.add_reaction(":plus1:881246627510239323")
        await sent_message.add_reaction(":minus1:881246627770282015")
        for attachment in msg.attachments:
            file = await attachment.to_file()
            await channel.send(file=file, content="")




async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(SprocketOfficialFunctions(bot))