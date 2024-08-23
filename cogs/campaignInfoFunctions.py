import json
import random

import discord
from discord.ext import commands
from discord import app_commands

import main
from cogs.SQLfunctions import SQLfunctions
from cogs.campaignFunctions import campaignFunctions
from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions
from cogs.textTools import textTools
class campaignInfoFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignfactions (campaignkey BIGINT, factionkey BIGINT, factionname VARCHAR, description VARCHAR(5000), joinrole BIGINT, money BIGINT);''')

    @commands.command(name="viewStats", description="View the statistics of your faction")
    async def viewStats(self, ctx: commands.Context):
        variablesList = await campaignFunctions.getUserFactionData(ctx)
        campaignInfoList = await campaignFunctions.getUserCampaignData(ctx)
        print(campaignInfoList)
        embed = discord.Embed(title=variablesList["factionname"],description=variablesList["description"], color=discord.Color.random())
        # embed.add_field(name="Land size", value="{:,}".format(int(variablesList["land"])) + "mi",inline=False)
        embed.add_field(name="Money in storage",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["money"]))) + " " + campaignInfoList["currencyname"], inline=False)
        # embed.add_field(name="Population size",value=str(round(int(variablesList[country][0]["populationCount"]) / 1000000, 2)) + "M",inline=False)
        # embed.add_field(name="Populace happiness",value=(str(int(variablesList[country][0]["populationHappiness"]))) + "%", inline=False)
        # embed.add_field(name="Average worker's income",value="฿" + str(int(100 * int(variablesList[country][0]["averageIncome"])) / 100),inline=False)
        # embed.add_field(name="Taxation rate", value=(str(variablesList[country][0]["taxRate"])) + "%", inline=False)
        # embed.add_field(name="Army funding percent",value=(str(variablesList[country][0]["taxPercentToArmy"])) + "%", inline=False)
        # embed.add_field(name="Railway Gauge", value=railwayGauges[variablesList[country][0]["railwayTech"]],inline=False)
        await ctx.send(embed=embed)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignInfoFunctions(bot))