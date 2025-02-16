import discord, datetime, json, pandas
from discord.ext import commands
from discord import app_commands
from main import SQLfunctions
from cogs.campaignFunctions import campaignFunctions
from cogs.discordUIfunctions import discordUIfunctions
from discord.ext import commands
from discord.ui import Modal, TextInput
from cogs.errorFunctions import errorFunctions
from cogs.textTools import textTools

class campaignMapsFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="exampleCommand", description="This is an example command")
    async def exampleCommand(self, ctx: commands.Context):
        await ctx.send("Hello World!")
        await errorFunctions.sendError(ctx)
        await campaignFunctions.showSettings(ctx)
        factionData = await campaignFunctions.getUserFactionData(ctx)
        await campaignFunctions.showStats(ctx, variablesList=factionData)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignMapsFunctions(bot))