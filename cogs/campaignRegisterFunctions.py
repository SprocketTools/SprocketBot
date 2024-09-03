import json, locale
import math

locale.setlocale(locale.LC_ALL, '')
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
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaigns (campaignname VARCHAR, campaignrules VARCHAR(50000), hostserverid BIGINT, campaignkey BIGINT, timescale BIGINT, currencyname VARCHAR, currencysymbol VARCHAR, publiclogchannelid BIGINT, privatemoneychannelid BIGINT, defaultgdp REAL, defaultpopgrowth REAL, populationperkm INT, defaulttaxestoplayer REAL, active BOOLEAN);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignservers (serverid BIGINT, campaignkey BIGINT);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignfactions (campaignkey BIGINT, factionkey BIGINT, approved BOOLEAN, factionname VARCHAR, description VARCHAR(50000), joinrole BIGINT, logchannel BIGINT, money BIGINT, population BIGINT);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        await ctx.send("## Done!")

    @commands.command(name="resetCampaignDatabase", description="generate a key that can be used to initiate a campaign")
    async def resetCampaignDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaigns''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaigns (campaignname VARCHAR, campaignrules VARCHAR(50000), hostserverid BIGINT, campaignkey BIGINT, timescale BIGINT, currencyname VARCHAR, currencysymbol VARCHAR, publiclogchannelid BIGINT, privatemoneychannelid BIGINT, defaultgdp REAL, defaultpopgrowth REAL, populationperkm INT, defaulttaxestoplayer REAL, active BOOLEAN);''')
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaignservers''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignservers (serverid BIGINT, campaignkey BIGINT);''')
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaignfactions''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignfactions (campaignkey BIGINT, factionkey BIGINT, approved BOOLEAN, factionname VARCHAR, description VARCHAR(50000), joinrole BIGINT, logchannel BIGINT, iscountry BOOL, money BIGINT, taxestoplayerpercent REAL, population BIGINT, landsize BIGINT, farmsize BIGINT, governance REAL, happiness REAL, financestability REAL, culturestability REAL, taxpoor REAL, taxrich REAL, gdp BIGINT, gdpgrowth REAL, incomeindex REAL, lifeexpectancy REAL, educationindex REAL);''')
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS campaignusers''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        await ctx.send("## Done!")
    @commands.command(name="startCampaign", description="Start a campaign")
    async def startCampaign(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        if ctx.author.id == main.ownerID:
            await ctx.send("The current registration key is " + str(self.activeRegistKey))
            userKey = int(self.activeRegistKey)
        else:
            userKey = await textTools.getIntResponse(ctx, "What is your campaign registration key?")
            if userKey != self.activeRegistKey:
                print(userKey)
                print(self.activeRegistKey)
                await ctx.send(await errorFunctions.retrieveError(ctx))
                return
        jsonFile = await textTools.getFileResponse(ctx, "Success!  Now upload your settings JSON file to launch the campaign.")
        # try:
        campaignData = json.loads(await jsonFile.read())
        datalist = [await textTools.sanitize(campaignData["Name of your campaign"]),
                    await textTools.sanitize(campaignData["Link to your campaign rules"]),
                    ctx.guild.id,
                    userKey,
                    campaignData["Speed of your campaign world clock compared to IRL"],
                    await textTools.sanitize(campaignData["Currency name"]),
                    await textTools.mild_sanitize(campaignData["Currency symbol"]),
                    campaignData["Public announcement channel id"],
                    campaignData["Manager logging channel id"],
                    campaignData["Default GDP growth"],
                    campaignData["Default population growth"],
                    campaignData["Population fed per farmland square km"],
                    campaignData["Default ratio of taxes available to play"],
                    False]
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)''', datalist)
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''', [ctx.guild.id, userKey])
        await ctx.send("## Done!\nRemember to save your campaign registration key, as other servers will need this in order to join the campaign.")
        inputKey = int(random.random() * 10000000)
        self.activeRegistKey = inputKey
        await campaignFunctions.updateCampaignSettings(ctx)
        await campaignFunctions.updateCampaignServerSettings(ctx)

        # except Exception:
        #     await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="overwriteCampaignSettings", description="generate a key that can be used to initiate a campaign")
    async def overwriteCampaignSettings(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await ctx.send(await errorFunctions.getError(ctx))
            return
        oldCampaignData = await campaignFunctions.getUserCampaignData(ctx)
        userKey = oldCampaignData["campaignkey"]

        if ctx.guild.id == oldCampaignData["hostserverid"]:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("This isn't your campaign!  You would need to make your own campaign in order to modify its settings.")
            return
        print(oldCampaignData)
        jsonFile = await textTools.getFileResponse(ctx, "Upload your settings JSON file to modify the campaign settings.")
        try:

            campaignData = json.loads(await jsonFile.read())
            datalist = [await textTools.sanitize(campaignData["Name of your campaign"]),
                        await textTools.sanitize(campaignData["Link to your campaign rules"]),
                        ctx.guild.id,
                        userKey,
                        campaignData["Speed of your campaign world clock compared to IRL"],
                        await textTools.sanitize(campaignData["Currency name"]),
                        await textTools.mild_sanitize(campaignData["Currency symbol"]),
                        campaignData["Public announcement channel id"],
                        campaignData["Manager logging channel id"],
                        campaignData["Default GDP growth"],
                        campaignData["Default population growth"],
                        campaignData["Population fed per farmland square km"],
                        campaignData["Default ratio of taxes available to play"],
                        False]
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaigns WHERE campaignkey = $1;''', [userKey])
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignservers WHERE campaignkey = $1;''',[userKey])
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)''', datalist)
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''', [ctx.guild.id, userKey])
            await ctx.send("## Done!")
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="addCampaignFaction", description="Add a faction to a campaign")
    async def addCampaignFaction(self, ctx: commands.Context):
        orgCampaignData = await campaignFunctions.getUserCampaignData(ctx)
        defaultTaxes = orgCampaignData["defaulttaxestoplayer"]
        defaultGDP = float(orgCampaignData["defaultgdp"])
        status = await campaignFunctions.isCampaignManager(ctx)
        campaignKeyList = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])
        print(campaignKeyList)
        campaignKey = campaignKeyList['campaignkey']
        jsonFile = await textTools.getFileResponse(ctx, "Upload your faction JSON file to add the faction.")
        try:
            campaignData = json.loads(await jsonFile.read())
            campaignData["Faction name"] = await textTools.sanitize(campaignData["Faction name"])
            campaignData["Faction name"] = campaignData["Faction name"][:64]
            campaignData["Short description"] = await textTools.sanitize(campaignData["Short description"])
            campaignData["Short description"] = campaignData["Short description"][:1024]
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("This file failed to parse.  Fix the errors in your JSON file and resubmit.")
            return
        try:
            print(await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''',[campaignKey, campaignData["Faction name"]]))
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send('You already have a faction with this name!')
            return
        except Exception:
            pass
        if len(campaignData["Faction name"]) == 0 or len(campaignData["Short description"]) == 0:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("Your creativity in breaking the bot is appreciated.  Make sure your name and description are valid and rerun the command.")
            return
        serverChannelData = str(ctx.guild.channels)
        if str(campaignData["Logging channel ID"]) not in serverChannelData:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("Your creativity in breaking the bot is appreciated.  Make sure your logging channel is in the same server you're submitting from, then try again.")
            return
        # campaignkey BIGINT, factionkey BIGINT, approved BOOLEAN, factionname VARCHAR, description VARCHAR(50000), joinrole BIGINT, logchannel BIGINT, money BIGINT, population BIGINT
        governanceScale = await campaignFunctions.getGovernmentType(ctx)
        #
        datalist = [campaignKey,
                    int(random.random()*50000000),
                    status,
                    campaignData["Faction name"],
                    campaignData["Short description"],
                    campaignData["Faction role ID"],
                    campaignData["Logging channel ID"],
                    campaignData["Is a country"],
                    campaignData["Military funds"],
                    defaultTaxes,
                    campaignData["Population"],
                    campaignData["Land size"],
                    campaignData["Farmland size"],
                    governanceScale,
                    round(0.70/governanceScale, 3),
                    round(0.75/governanceScale, 3),
                    round(0.72/governanceScale, 3),
                    round((0.15*governanceScale), 3),
                    round((0.10*governanceScale), 3),
                    campaignData["GDP"],
                    round(defaultGDP/governanceScale, 3),
                    math.log((int(campaignData["GDP"])/int(campaignData["Population"]))/91.25)/math.log(839/91.25),
                    round(70/governanceScale, 3),
                    0.25
                    ]

        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''', [ctx.guild.id, campaignData["Faction name"]])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignfactions VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)''', datalist)
        if status == True:
            await ctx.send(f"## Done!\n{campaignData['Faction name']} is now registered as a faction!")
        else:
            await ctx.send(f"## Done!\n{campaignData['Faction name']} now awaits moderator approval.")

        #except Exception:
            #await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="approveCampaignFactions", description="higdffffffffffff")
    async def approveCampaignFactions(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        factionDict = await SQLfunctions.databaseFetchdict('''SELECT * FROM campaignfactions WHERE approved = false;''')
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        for faction in factionDict:
            print(faction)
            embed = discord.Embed(title=faction['factionname'],description=faction['description'],color=discord.Color.random())
            embed.add_field(name="Money", value=f"{campaignData['currencysymbol']}{'{:,}'.format(int(faction['money']))} {campaignData['currencyname']}", inline=False)
            embed.add_field(name="Population", value='{:,}'.format(int(faction['population'])), inline=False)
            await ctx.send(embed=embed)
            answer = await discordUIfunctions.getYesNoChoice(ctx)
            recipient = self.bot.get_channel(int(faction["logchannel"]))
            if answer == True:
                await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET approved = true WHERE factionkey = $1;''', [faction['factionkey']])
                await ctx.send("Added!")
                await recipient.send(f"{faction['factionname']} has been added to {campaignData['campaignname']}!  Welcome in!")
            else:
                await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE factionkey = $1;''', [faction['factionkey']])
                await ctx.send("Deleted!")
                await recipient.send(f"{faction['factionname']} was not accepted into {campaignData['campaignname']}.")
        await ctx.send("All good here!")

    @commands.command(name="addServerToCampaign", description="Add a server to an ongoing campaign")
    async def addServerToCampaign(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
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
        campaignKey = campaignData['campaignkey']
        factionData = await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND approved = true;''', [campaignKey])
        factionNameList = []
        factionNameDict = {}
        for serverData in factionData:
            if str(serverData['joinrole']) in str(ctx.author.roles):
                factionNameList.append(serverData['factionname'])
                factionNameDict[serverData['factionname']] = serverData['factionkey']
        if len(factionNameList) == 0:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("No factions are available for you to join!  Ensure that you have the correct role.")
            return
        promptText = "Pick the faction you would like to join."
        answerName = await discordUIfunctions.getChoiceFromList(ctx, factionNameList, promptText)
        factionData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''', [campaignKey, answerName])

        factionkey = factionData["factionkey"]
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignusers SET status = false WHERE userid = $1 AND campaignkey = $2 AND factionkey = $3''',[ctx.guild.id, campaignKey, factionkey])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignusers VALUES ($1, $2, $3, true)''',[ctx.author.id, campaignKey, factionkey])
        await ctx.send(f"## Done!\nYou are now a part of {answerName}!")





async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignRegisterFunctions(bot))