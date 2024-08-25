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
        if ctx.author.id != main.ownerID:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaigns (campaignname VARCHAR, campaignrules VARCHAR(50000), hostserverid BIGINT, campaignkey BIGINT, timescale BIGINT, currencyname VARCHAR, currencysymbol VARCHAR, publiclogchannelid BIGINT, privatemoneychannelid BIGINT, active BOOLEAN);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignservers (serverid BIGINT, campaignkey BIGINT);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignfactions (campaignkey BIGINT, factionkey BIGINT, factionname VARCHAR, description VARCHAR(50000), joinrole BIGINT, money BIGINT);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        await ctx.send("## Done!")

    @commands.command(name="resetCampaignDatabase", description="generate a key that can be used to initiate a campaign")
    async def resetCampaignDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaigns''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaigns (campaignname VARCHAR, campaignrules VARCHAR(50000), hostserverid BIGINT, campaignkey BIGINT, timescale BIGINT, currencyname VARCHAR, currencysymbol VARCHAR, publiclogchannelid BIGINT, privatemoneychannelid BIGINT, active BOOLEAN);''')
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaignservers''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignservers (serverid BIGINT, campaignkey BIGINT);''')
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaignfactions''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignfactions (campaignkey BIGINT, factionkey BIGINT, factionname VARCHAR, description VARCHAR(50000), joinrole BIGINT, money BIGINT);''')
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaignusers''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        await ctx.send("## Done!")
    @commands.command(name="startCampaign", description="Start a campaign")
    async def startCampaign(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await ctx.send(await errorFunctions.retrieveError(ctx))
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
            datalist = [await textTools.sanitize(campaignData["Name of your campaign"]), await textTools.sanitize(campaignData["Link to your campaign rules"]), ctx.guild.id, userKey, campaignData["Speed of your campaign world clock compared to IRL"], await textTools.sanitize(campaignData["Currency name"]), await textTools.sanitize(campaignData["Currency symbol"]), campaignData["Public announcement channel id"], campaignData["Private finances logging channel id"], False]
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)''', datalist)
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''', [ctx.guild.id, userKey])
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
        oldCampaignData = await campaignFunctions.getCampaignSettings(ctx)
        print(oldCampaignData)
        jsonFile = await textTools.getFileResponse(ctx, "Upload your settings JSON file to modify the campaign settings.")
        try:
            campaignData = json.loads(await jsonFile.read())
            datalist = [campaignData["Name of your campaign"].strip(), campaignData["Link to your campaign rules"].strip(), ctx.guild.id, oldCampaignData["campaignkey"], campaignData["Speed of your campaign world clock compared to IRL"]]
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5)''', datalist)
            await ctx.send("## Done!")
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="addCampaignFaction", description="Add a faction to a campaign")
    async def addCampaignFaction(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        campaignKeyList = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])
        print(campaignKeyList)
        campaignKey = campaignKeyList['campaignkey']
        jsonFile = await textTools.getFileResponse(ctx, "Upload your faction JSON file to add the faction.")
        try:
            campaignData = json.loads(await jsonFile.read())
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("This file failed to parse.  Fix the errors in your JSON file and resubmit.")
            return
        try:
            print(await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''',[campaignKey, campaignData["Faction name"].strip()]))
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("You already have a faction with this name!")
            return
        except Exception:
            pass
        if len(campaignData["Faction name"].strip()) == 0 or len(campaignData["Short description"].strip()) == 0:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("Your creativity in breaking the bot is appreciated.  Fix the errors in your JSON file and resubmit.")
            return
        datalist = [campaignKey, int(random.random()*50000000), await textTools.sanitize(campaignData["Faction name"]), await textTools.sanitize(campaignData["Short description"]), campaignData["Discord role ID required to join the faction"], campaignData["Starting money balance"]]
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''', [ctx.guild.id, campaignData["Faction name"]])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignfactions VALUES ($1, $2, $3, $4, $5, $6)''', datalist)
        await ctx.send(f"## Done!\n{await textTools.sanitize(campaignData['Faction name'])} is now registered as a faction!")
        #except Exception:
            #await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="campaignSettings", description="generate a key that can be used to initiate a campaign")
    async def campaignSettings(self, ctx: commands.Context):
        data = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])
        embed = discord.Embed(title=f"{data['campaignname']} settings", description="These are the settings encompassing your entire campaign!", color=discord.Color.random())
        embed.add_field(name="Campaign rules", value=f"[link](<{data['campaignrules']}>)", inline=False)
        embed.add_field(name="Time scale", value=f"{data['timescale']}x", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="addServerToCampaign", description="Add a server to an ongoing campaign")
    async def addServerToCampaign(self, ctx: commands.Context):
        userKey = int(await textTools.getIntResponse(ctx, "What is the campaign registration key?"))
        resultKeyData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE campaignkey = $1;''',[userKey])
        resultKey = resultKeyData["campaignkey"]
        if userKey != resultKey:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''',[ctx.guild.id, str(userKey)])
        await ctx.send(f"## Done!\nYour server is now participating in {await campaignFunctions.getCampaignName(userKey)}")

    @commands.command(name="joinCampaign", description="Add a server to an ongoing campaign")
    async def joinCampaign(self, ctx: commands.Context):
        # await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        campaignData = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        print(campaignData)
        campaignKey = campaignData['campaignkey']
        factionData = await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1;''', [campaignKey])
        factionNameList = []
        factionNameDict = {}
        for serverData in factionData:
            print(serverData['joinrole'])
            print(ctx.author.roles)
            if str(serverData['joinrole']) in str(ctx.author.roles):
                factionNameList.append(serverData['factionname'])
                factionNameDict[serverData['factionname']] = serverData['factionkey']
        print(factionNameList)
        if len(factionNameList) == 0:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("No factions are available for you to join!  Ensure that you have the correct role.")
            return
        promptText = "Pick the faction you would like to join."
        answerName = await discordUIfunctions.getChoiceFromList(ctx, factionNameList, promptText)
        print(answerName)
        print(factionNameDict[answerName])
        print(await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1;''', [campaignKey]))
        factionData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''', [campaignKey, answerName])
        factionkey = factionData["factionkey"]
        print(factionkey)
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignusers SET status = false WHERE userid = $1 AND campaignkey = $2 AND factionkey = $3''',[ctx.guild.id, campaignKey, factionkey])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignusers VALUES ($1, $2, $3, true)''',[ctx.author.id, campaignKey, factionkey])
        await ctx.send(f"## Done!\nYou are now a part of {answerName}!")





async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignRegisterFunctions(bot))