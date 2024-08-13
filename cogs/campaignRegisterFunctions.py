import json
import random

import discord
from discord.ext import commands
from discord import app_commands

from cogs.SQLfunctions import SQLfunctions
from cogs.campaignFunctions import campaignFunctions
from cogs.errorFunctions import errorFunctions
from cogs.textTools import textTools
class campaignRegisterFunctions(commands.Cog):
    activeRegistKey = 569802354
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="generateCampaignKey", description="generate a key that can be used to initiate a campaign")
    async def generateCampaignKey(self, ctx: commands.Context):
        inputKey = int(random.random()*10000000)
        self.activeRegistKey = inputKey
        await ctx.send(f"The registration key has been set to {inputKey}.")
        print(self.activeRegistKey)

    @commands.command(name="setupCampaignDatabase", description="generate a key that can be used to initiate a campaign")
    async def setupCampaignDatabase(self, ctx: commands.Context):
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaigns''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaigns (campaignname VARCHAR, campaignrules VARCHAR(50000), hostserverid BIGINT, campaignkey BIGINT, timescale BIGINT);''')
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaignservers''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignservers (serverid BIGINT, campaignname VARCHAR, campaignkey BIGINT);''')
        await ctx.send("## Done!")
    @commands.command(name="startCampaign", description="Start a campaign")
    async def startCampaign(self, ctx: commands.Context):
        if campaignFunctions.isCampaignManager(ctx) == False:
            await ctx.send(await errorFunctions.getError(ctx))
            return
        userKey = await textTools.getIntResponse(ctx, "What is your campaign registration key?")
        if userKey != self.activeRegistKey:
            print(userKey)
            print(self.activeRegistKey)
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        jsonFile = await textTools.getFileResponse(ctx, "Success!  Now upload your settings JSON file to launch the campaign.")
        try:
            campaignData = json.loads(await jsonFile.read())
            datalist = [campaignData["Name of your campaign"], campaignData["Link to your campaign rules"], ctx.guild.id, userKey, campaignData["Speed of your campaign world clock compared to IRL"]]
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5)''', datalist)
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2, $3)''', [ctx.guild.id, campaignData["Name of your campaign"], userKey])
            await ctx.send("## Done!\nRemember to save your campaign registration key, as other servers will need this in order to join the campaign.")
            inputKey = int(random.random() * 10000000)
            self.activeRegistKey = inputKey
            await campaignFunctions.updateCampaignSettings(ctx)
            await campaignFunctions.updateCampaignServerSettings(ctx)

        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="overwriteCampaignSettings", description="generate a key that can be used to initiate a campaign")
    async def overwriteCampaignSettings(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await ctx.send(await errorFunctions.getError(ctx))
            return
        oldCampaignData = await campaignFunctions.fetchCampaignSettings(ctx)
        print(oldCampaignData)
        jsonFile = await textTools.getFileResponse(ctx, "Upload your settings JSON file to modify the campaign settings.")
        try:
            campaignData = json.loads(await jsonFile.read())
            datalist = [campaignData["Name of your campaign"], campaignData["Link to your campaign rules"], ctx.guild.id, self.activeRegistKey, campaignData["Speed of your campaign world clock compared to IRL"]]
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5)''', datalist)
            await ctx.send("## Done!")
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="campaignSettings", description="generate a key that can be used to initiate a campaign")
    async def campaignSettings(self, ctx: commands.Context):
        data = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])
        embed = discord.Embed(title=f"{data['campaignname']} settings", description="These are the settings encompassing your entire campaign!", color=discord.Color.random())
        embed.add_field(name="Campaign rules", value=f"[link](<{data['campaignrules']}>)", inline=False)
        embed.add_field(name="Time scale", value=f"{data['timescale']}x", inline=False)
        await ctx.send(embed=embed)


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignRegisterFunctions(bot))