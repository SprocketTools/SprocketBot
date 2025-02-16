import datetime
from datetime import datetime
import json
import random
from io import StringIO
import pandas as pd
import discord
from discord.ext import commands
from discord import app_commands


from main import SQLfunctions
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
        await campaignFunctions.showSettings(ctx)

    @commands.command(name="viewFactionHistory", description="Get a list of all the factions in your campaign")
    async def viewFactionHistory(self, ctx: commands.Context, *, userid: int=None):
        if not userid:
            userid = ctx.author.id
        campaignKey = await campaignFunctions.getUserCampaignData(ctx)
        print(campaignKey['campaignkey'])
        data = await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM campaignusers WHERE userid = $1 AND campaignkey = $2;''',[userid, campaignKey['campaignkey']])
        if len(data) == 0:
            await errorFunctions.sendError(ctx)
        else:
            embed = discord.Embed(title=f"{self.bot.get_user(userid).name}'s faction history", color=discord.Color.random())
            for faction in data:
                if faction['status'] == True:
                    embed.add_field(name=await campaignFunctions.getFactionName(faction['factionkey']), value="Active member", inline=False)
                if faction['status'] == False:
                    embed.add_field(name=await campaignFunctions.getFactionName(faction['factionkey']), value="Former member", inline=False)
            embed.set_thumbnail(url=self.bot.get_user(userid).avatar.url)
            await ctx.send(embed=embed)



    @commands.command(name="viewFactions", description="Get a list of all the factions in your campaign")
    async def viewFactions(self, ctx: commands.Context):
        campaignKey = await campaignFunctions.getUserCampaignData(ctx)
        print(campaignKey)
        data = await SQLfunctions.databaseFetchdictDynamic('''SELECT factionname FROM campaignfactions WHERE campaignkey = $1;''', [campaignKey["campaignkey"]])
        if len(str(data)) > 200:
            text = ""
            print(data)
            for i in data:
                text = f"{i['factionname']}\n{text}"
            # Create a File object from the StringIO object
            fileOut = StringIO(text)
            file = discord.File(fileOut, "data.txt")
            await ctx.send(content="Since your info was too big, here's a file instead.", file=file)
        else:
            embed = discord.Embed(title=f"Faction list", description="This is a list of all the factions in your campaign!", color=discord.Color.random())
            for i in data:
                embed.add_field(name=i['factionname'], value = " ", inline=False)
            await ctx.send(embed=embed)

    @commands.command(name="campaignHelp", description="View all the bot commands")
    async def campaignHelp(self, ctx: commands.Context):
        embed = discord.Embed(title=f"**Campaign Commands**",
                              description="*Sprocket Bot's prefix is* `-`\n",
                              color=discord.Color.random())
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="startFaction", value="Start a brand new faction", inline=False)
        embed.add_field(name="joinFaction", value="Join a faction", inline=False)
        embed.add_field(name="leaveFactions", value="Leave all factions", inline=False)
        embed.add_field(name="campaignSettings", value="View campaign settings", inline=False)
        embed.add_field(name="viewStats", value="View your faction's stats", inline=False)
        embed.add_field(name="viewFinances", value="View your faction's finances", inline=False)
        embed.add_field(name="purchase", value="Purchase an item", inline=False)
        embed.add_field(name="logMaintenance", value="[Placeholder] Pay for something", inline=False)
        embed.add_field(name="settaxes", value="Purchase an item", inline=False)
        embed.add_field(name="logCivilSale", value="[Placeholder] Log revenue from civilians", inline=False)
        embed.add_field(name="sendMessage", value="Send a message in-character to another faction", inline=False)
        embed.set_thumbnail(url='https://sprockettools.github.io/SprocketToolsLogo.png')
        embed.set_footer(text="Campaign managers can view administrative commands with `-campaignManagerHelp`")
        await ctx.send(embed=embed)

    @commands.command(name="campaignManagerHelp", description="View all the bot commands")
    async def campaignManagerHelp(self, ctx: commands.Context):
        embed = discord.Embed(title=f"**Campaign Commands**",
                              description="*Sprocket Bot's prefix is* `-`\n",
                              color=discord.Color.random())
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="startCampaign", value="Start a brand new campaign", inline=False)
        embed.add_field(name="startFaction", value="Start a brand new faction", inline=False)
        embed.add_field(name="joinExternalCampaign", value="Join a campaign in another server", inline=False)
        embed.add_field(name="approveCampaignFactions", value="Approve new factions", inline=False)
        embed.add_field(name="recruitToCampaign", value="Add members to a faction", inline=False)
        embed.add_field(name="campaignSettings", value="View campaign settings", inline=False)
        embed.add_field(name="manageCampaign", value="Manage the campaign settings", inline=False)
        embed.add_field(name="manageFaction", value="Manage a faction's settings", inline=False)
        embed.add_field(name="viewFactionHistory", value="View a player's affiliations", inline=False)
        embed.add_field(name="manageAllFactions", value="Use a spreadsheet to update everything", inline=False)
        embed.add_field(name="addMoney", value="Add money to a faction", inline=False)
        embed.set_thumbnail(url='https://sprockettools.github.io/SprocketToolsLogo.png')
        embed.set_footer(text="Campaign managers can view administrative commands with `-campaignManagerHelp`")
        await ctx.send(embed=embed)

    @commands.command(name="downloadStats", description="Download the campaign data")
    async def downloadStats(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignHost(ctx) == False:
            return
        data = await SQLfunctions.databaseFetchdictDynamic('''SELECT factionkey, approved, factionname, iscountry, money, population, landsize, gdp, averagesalary, popworkerratio FROM campaignfactions where campaignkey = $1;''', [await campaignFunctions.getCampaignKey(ctx)])
        # credits: brave AI
        df = pd.DataFrame(data)
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        # Send CSV file
        buffer.seek(0)
        await ctx.channel.send(file=discord.File(buffer, "data.csv"))

    @commands.command(name="viewStats", description="View the statistics of your faction")
    async def viewStats(self, ctx: commands.Context):
        variablesList = await campaignFunctions.getUserFactionData(ctx)
        await campaignFunctions.showStats(ctx, variablesList)

    @commands.command(name="viewTime", description="View the statistics of your faction")
    async def viewTime(self, ctx: commands.Context):
        campaignInfoList = await campaignFunctions.getUserCampaignData(ctx)
        print(campaignInfoList)
        date_string = str(campaignInfoList['timedate'])
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(date_string, format_string)
        print(dt.year)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        embed = discord.Embed(title=f"\nIt is {hour}:{min} on {day}, {dt.year} in {campaignInfoList['campaignname']}", color=discord.Color.random())
        embed.add_field(name="Time scale", value=f"{campaignInfoList['timescale']}x", inline=True)
        embed.set_footer(text=(await errorFunctions.retrieveCategorizedError(ctx, "campaign")))
        await ctx.send(embed=embed)

    async def showStats(ctx: commands.Context, variablesList):
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
            embed.add_field(name="Espionage funding", value=str(round(float(variablesList["espionagespend"]) * 100, 1)) + "% of GDP", inline=False)
            embed.add_field(name="Spy agency staff", value=str(variablesList["espionagestaff"]) + " employees", inline=False)
        else:
            embed.add_field(name="Country of origin",value=await campaignFunctions.getFactionName(variablesList["landlordfactionkey"]), inline=False)
        embed.set_footer(text=f"\nIt is {hour}:{min} on {day}, {dt.year}")
        embed.set_thumbnail(url=variablesList["flagurl"])
        await ctx.send(embed=embed)


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignInfoFunctions(bot))