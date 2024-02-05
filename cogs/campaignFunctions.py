import discord
from discord.ext import commands
from discord import app_commands
from cogs.textTools import textTools
class campaignFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="registerContest2", description="Register a contest for the server.")
    async def weather2(self, ctx: commands.Context):
        print("Hi!")




async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignFunctions(bot))