import discord
from discord.ext import commands
promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions
from cogs.SQLfunctions import SQLfunctions
class serverFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot







async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(serverFunctions(bot))