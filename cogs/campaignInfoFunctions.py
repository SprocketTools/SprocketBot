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
        await ctx.send(embed=embed)

    @commands.command(name="viewStats", description="View the statistics of your faction")
    async def viewStats(self, ctx: commands.Context):
        variablesList = await campaignFunctions.getUserFactionData(ctx)
        campaignInfoList = await campaignFunctions.getUserCampaignData(ctx)
        print(campaignInfoList)
        embed = discord.Embed(title=variablesList["factionname"],description=variablesList["description"], color=discord.Color.random())
        # embed.add_field(name="Land size", value="{:,}".format(int(variablesList["land"])) + "mi",inline=False)
        embed.add_field(name="Money in storage", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["money"]))) + " " + campaignInfoList["currencyname"], inline=False)
        embed.add_field(name="Population size", value=("{:,}".format(int(variablesList["population"]))),inline=False)
        embed.add_field(name="Government type", value=await campaignFunctions.getGovernmentName(variablesList["governance"]), inline=False)
        embed.add_field(name="money", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["money"]))), inline=False)
        embed.add_field(name="GDP",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["gdp"]))), inline=False)
        embed.add_field(name="GDP growth", value=str(round(float(variablesList["gdpgrowth"]) * 100, 3)) + "%", inline=False)
        embed.add_field(name="Poor tax rate", value=f"{round(float(variablesList['taxpoor'])*100, 3)} %", inline=False)
        embed.add_field(name="Rich tax rate", value=f"{round(float(variablesList['taxrich']) * 100, 3)} %", inline=False)
        embed.add_field(name="Populace happiness", value=str(round(float(variablesList["happiness"])*100, 3)) + "%", inline=False)
        embed.add_field(name="Cultural stability", value=str(round(float(variablesList["culturestability"]) * 100, 4)) + "%",inline=False)
        embed.add_field(name="Average lifespan", value=str(round(float(variablesList["lifeexpectancy"]), 1)) + " years", inline=False)
        embed.add_field(name="Economic index", value=str(round(float(variablesList["incomeindex"]) * 100, 4)) + "%", inline=False)
        embed.add_field(name="Education index", value=str(round(float(variablesList["educationindex"]) * 100, 4)) + "%", inline=False)
        estimatedIncome = int(variablesList["gdp"])*variablesList["taxestoplayerpercent"]*(variablesList["taxpoor"] + variablesList["taxrich"])/2
        embed.add_field(name="Estimated yearly budget",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(estimatedIncome))), inline=False)
        # embed.add_field(name="Railway Gauge", value=railwayGauges[variablesList[country][0]["railwayTech"]],inline=False)
        await ctx.send(embed=embed)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignInfoFunctions(bot))