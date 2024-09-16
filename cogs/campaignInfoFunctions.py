import datetime
from datetime import datetime
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

    @commands.command(name="campaignSettings", description="generate a key that can be used to initiate a campaign")
    async def campaignSettings(self, ctx: commands.Context):
        data = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])
        embed = discord.Embed(title=f"{data['campaignname']} settings", description="These are the settings encompassing your entire campaign!", color=discord.Color.random())
        embed.add_field(name="Campaign rules", value=f"{data['campaignrules']}", inline=False)
        embed.add_field(name="Time scale", value=f"{data['timescale']}x", inline=False)
        embed.add_field(name="Currency symbol", value=f"{data['currencysymbol']}", inline=False)
        embed.add_field(name="Currency name", value=f"{data['currencyname']}", inline=False)
        if data['active'] == True:
            embed.add_field(name="Current status", value=f"**Campaign is running**", inline=False)
        if data['active'] == False:
            embed.add_field(name="Current status", value=f"**Campaign is NOT running**", inline=False)
        embed.set_footer(text="To start and pause a campaign, use `-toggelCampaignProgress`")
        await ctx.send(embed=embed)

    @commands.command(name="viewStats", description="View the statistics of your faction")
    async def viewStats(self, ctx: commands.Context):
        variablesList = await campaignFunctions.getUserFactionData(ctx)
        campaignInfoList = await campaignFunctions.getUserCampaignData(ctx)
        print(campaignInfoList)
        date_string = str(campaignInfoList['timedate'])
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(date_string, format_string)
        print(dt.year)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        embed = discord.Embed(title=variablesList["factionname"],description=variablesList["description"], color=discord.Color.random())
        embed.add_field(name="Discretionary funds", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["money"]))) + " " + campaignInfoList["currencyname"], inline=False)
        if variablesList["iscountry"] == True:
            embed.add_field(name="Land", value="{:,}".format(int(variablesList["landsize"])) + " km²",inline=False)
            embed.add_field(name="Population size", value=("{:,}".format(int(variablesList["population"]))),inline=False)
            embed.add_field(name="Government type", value=await campaignFunctions.getGovernmentName(variablesList["governance"]), inline=False)
            embed.add_field(name="GDP",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["gdp"]))), inline=False)
            embed.add_field(name="Populace happiness", value=str(round(float(variablesList["happiness"])*100, 1)) + "%", inline=False)
            embed.add_field(name="Average lifespan", value=str(round(float(variablesList["lifeexpectancy"]), 1)) + " years", inline=False)
            embed.add_field(name="Economic index", value=str(round(float(variablesList["incomeindex"]) * 100, 1)) + "%", inline=False)
            embed.add_field(name="Education index", value=str(round(float(variablesList["educationindex"]) * 100, 1)) + "%", inline=False)
        else:
            embed.add_field(name="Country of origin",value=await campaignFunctions.getFactionName(variablesList["landlordfactionkey"]), inline=False)
        embed.set_footer(text=f"\nIt is {hour}:{min} on {day}, {dt.year}")
        embed.set_thumbnail(url=variablesList["flagurl"])
        await ctx.send(embed=embed)


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignInfoFunctions(bot))