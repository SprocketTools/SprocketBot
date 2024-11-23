import datetime
import json, locale
import math
import time
from urllib.request import urlopen

from cogs.adminFunctions import adminFunctions

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
    activeRegistKey = 569801354
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="generateCampaignKey", description="generate a key that can be used to initiate a campaign")
    async def generateCampaignKey(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you are the bot owner and try again.")
            return
        inputKey = int(random.random()*10000000)
        self.activeRegistKey = inputKey
        await ctx.send(f"The registration key has been set to {inputKey}.")
        print(self.activeRegistKey)

    @commands.command(name="setupCampaignDatabase", description="generate a key that can be used to initiate a campaign")
    async def setupCampaignDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaigns (campaignname VARCHAR, campaignrules VARCHAR(50000), hostserverid BIGINT, campaignkey BIGINT, timescale BIGINT, currencyname VARCHAR, currencysymbol VARCHAR, publiclogchannelid BIGINT, privatemoneychannelid BIGINT, defaultgdpgrowth REAL, defaultpopgrowth REAL, populationperkm INT, taxestoplayer REAL, poptoworkerratio REAL, active BOOLEAN, timedate TIMESTAMP, lastupdated TIMESTAMP);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignservers (serverid BIGINT, campaignkey BIGINT);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignfactions (campaignkey BIGINT, factionkey BIGINT, landlordfactionkey BIGINT, approved BOOLEAN, hostactive BOOLEAN, factionname VARCHAR, description VARCHAR(50000), flagurl VARCHAR(50000), joinrole BIGINT, logchannel BIGINT, iscountry BOOL, money BIGINT, population BIGINT, landsize BIGINT, governance REAL, happiness REAL, financestability REAL, culturestability REAL, taxpoor REAL, taxrich REAL, gdp BIGINT, gdpgrowth REAL, incomeindex REAL, lifeexpectancy REAL, educationindex REAL, educationspend REAL, socialspend REAL, infrastructurespend REAL, averagesalary REAL, popworkerratio REAL, espionagespend REAL, espionagestaff INT);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignautopurchases (campaignkey BIGINT, factionkey BIGINT, userid BIGINT, name VARCHAR, amount BIGINT, lastupdated TIMESTAMP, monthfrequency INT, status BOOLEAN);''')
        await ctx.send("## Done!")

    @commands.command(name="clearCampaignFactions", description="generate a key that can be used to initiate a campaign")
    async def clearCampaignFactions(self, ctx: commands.Context):
        if campaignFunctions.isCampaignHost(ctx) == False:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        campaignKey = campaignData["campaignkey"]
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1;''', [campaignKey])
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignusers WHERE campaignkey = $1;''', [campaignKey])
        await ctx.send("## Done!\nYour campaign has been cleared of all factions.")

    @commands.command(name="startCampaign", description="Start a campaign")
    async def startCampaign(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return
        if ctx.author.id == main.ownerID:
            await ctx.send("The current registration key is " + str(self.activeRegistKey))
            userKey = int(self.activeRegistKey)
        else:
            userKey = await textTools.getIntResponse(ctx, "What is your campaign registration key?")
            if userKey != self.activeRegistKey:
                print(userKey)
                print(self.activeRegistKey)
                await errorFunctions.sendCategorizedError(ctx, "campaign")
                return

        campaignName = await textTools.getCappedResponse(ctx, "What is the name of your campaign?", 128)
        campaignRules = await textTools.getCappedResponse(ctx, "Provide a link to your campaign's rules.  This can be a google document, website, or similar.", 512)
        speed = await textTools.getFlooredFloatResponse(ctx, "What is the speed of your campaign's time progression compared to IRL?", 1)
        currencyName = await textTools.getCappedResponse(ctx, "What is the name of your currency?", 32)
        currencySymbol = await textTools.getCappedResponse(ctx, "What is your currency's symbol?", 2)
        publicAnnouncement = await textTools.getChannelResponse(ctx, "What channel do you want publicly-visible announcements to be sent to?  Reply with a mention of a channel.")
        privateLogging = await textTools.getChannelResponse(ctx, "What channel do you want logs and other private information to be sent to?  Reply with a mention of a channel.")
        defaultGDPgrowth = await textTools.getPercentResponse(ctx, "What is your average economic growth under ideal circumstances?  Reply with a percentage value.")
        defaultpopgrowth = await textTools.getPercentResponse(ctx, "What is your average population growth under nominal circumstances?  Reply with a percentage value.")
        poppersquarekm = await textTools.getFlooredIntResponse(ctx, "How many people should be able to live off a square kilometer of land?\n-# Real-world values average around 1,000 to 2,000 people", 100)
        discretionaryratio = await textTools.getPercentResponse(ctx, "How much of your country's tax revenue should be available to the player?  Reply with a percentage value.")
        popworkerratio = await textTools.getFlooredIntResponse(ctx, "What ratio of people to workers should countries start with?\nThis value should be a whole number between 2 and 4.", 2)
        startingyear = await textTools.getIntResponse(ctx, "What calender year is your campaign starting with?")

        datalist = [campaignName,
                    campaignRules,
                    ctx.guild.id,
                    userKey,
                    speed,
                    currencyName,
                    currencySymbol,
                    publicAnnouncement,
                    privateLogging,
                    defaultGDPgrowth,
                    defaultpopgrowth,
                    poppersquarekm,
                    discretionaryratio,
                    popworkerratio,
                    False,
                    datetime.datetime(startingyear, 1, 1)]
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)''',datalist)
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignservers WHERE serverid = $1''',[ctx.guild.id])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''',[ctx.guild.id, userKey])
        await ctx.send(f"## Done!\nRemember to save your campaign registration key (**{userKey}**), as other servers will need this in order to join the campaign.")
        inputKey = int(random.random() * 10000000)
        self.activeRegistKey = inputKey
        await campaignFunctions.updateCampaignSettings(ctx)
        await campaignFunctions.updateCampaignServerSettings(ctx)

        # except Exception:
        #     await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="overwriteCampaignSettings", description="generate a key that can be used to initiate a campaign")
    async def overwriteCampaignSettings(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignHost(ctx) == False:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        oldCampaignData = await campaignFunctions.getUserCampaignData(ctx)
        userKey = oldCampaignData["campaignkey"]

        if ctx.guild.id == oldCampaignData["hostserverid"]:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
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
            await errorFunctions.sendCategorizedError(ctx, "campaign")

    @commands.command(name="startFaction", description="Add a faction to a campaign")
    async def startFaction(self, ctx: commands.Context):
        # try:
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        defaultPWR = float(campaignData["poptoworkerratio"])
        landlordid = 0
        approvalStatus = await campaignFunctions.isCampaignHost(ctx)
        campaignKeyList = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignKey = campaignKeyList['campaignkey']
        await ctx.send("## Welcome!\nYou will now be asked between 7 and 15 questions about your country (dependent on its type)\nLet's begin: is your faction a country?")
        isCountry = await discordUIfunctions.getYesNoChoice(ctx)
        factionName = await textTools.getResponse(ctx, "What is the name of your faction?")
        nameStatus = False
        while nameStatus == False:
            nameTest = await SQLfunctions.databaseFetchdictDynamic(f'''SELECT factionname FROM campaignfactions WHERE factionname = $1 AND campaignkey = $2;''', [factionName, campaignKey])
            if len(nameTest) > 0:
                await ctx.send("A faction already exists with this name!")
                return
            nameStatus = True
        factionDescription = await textTools.getResponse(ctx, "What is your faction's description?")
        factionRoleID = await textTools.getRoleResponse(ctx, "What role do you require for players to be able to join your faction?\n-# Reply with a ping of that role.")
        logChannelID = await textTools.getChannelResponse(ctx, "What channel do you want updates about your faction to be sent to?\n-# Reply with a mention of that channel.")
        # https://stackoverflow.com/questions/10543940/check-if-a-url-to-an-image-is-up-and-exists-in-python
        image_formats = ("image/png", "image/jpeg", "image/gif")
        # site = urlopen(flagURL)
        # meta = site.info()  # get header of the http request
        factionkey = time.time() + round(random.random()*10000)
        # if meta["content-type"] not in image_formats:  # check if the content-type is a image
        #     await errorFunctions.sendError(ctx)
        #     while meta["content-type"] not in image_formats:
        #         flagURL = await textTools.getResponse(ctx, "Try again: what is your country's flag?\nReply with a direct URL to your flag's picture.")
        #         site = urlopen(flagURL)
        #         meta = site.info()  # get header of the http request
        #         if meta["content-type"] not in image_formats:  # check if the content-type is a image
        #             await errorFunctions.sendError(ctx)
        if isCountry == True: # country
            flagURL = await textTools.getFileURLResponse(ctx,"What is your country's flag?\n-# Upload a picture of your flag.")
            discretionaryFunds = await textTools.getFlooredIntResponse(ctx, "How much money does your country's military have in the bank?  Consider this your starting discretionary funds.", 10000)
            population = await textTools.getFlooredIntResponse(ctx,"What is the population of your country?\n-# For numerical replies like this one, do not include any commas.", 1000)
            popworkerratio = campaignData['poptoworkerratio']
            await ctx.send("This next question will set your country's GDP and median salary.  You can plug in either value, and the other one will be auto-calculated from it.")
            EEE = await textTools.getFlooredIntResponse(ctx, "Reply with any number below 5,000 to set your country's median salary.\nReply with any number greater than 10,000 to set your country's GDP.", 1)
            if EEE < 5000:
                salary = EEE
                gdp = round(salary*population/popworkerratio)
            else:
                gdp = EEE
                salary = round((gdp/population)*popworkerratio, 3)
            latitude = await textTools.getFloatResponse(ctx,"What is the average latitude of your country on the globe?  Reply with a number in degrees.")
            land = await textTools.getFlooredFloatResponse(ctx, "How many square kilometers of land does your country control?", 1)
            governanceScale = await campaignFunctions.getGovernmentType(ctx)
            landlordid = 0
        else: #company
            discretionaryFunds = await textTools.getFlooredIntResponse(ctx,"How much money does your company currently have in the bank?",10000)
            flagURL = await textTools.getFileURLResponse(ctx,"What is your company's logo?\n-# Upload a picture of your flag.")
            population = 1000
            salary = 1000
            popworkerratio = 1
            latitude = 0
            land = 2000
            governanceScale = 1.0
            landlorddata = await campaignFunctions.pickCampaignCountry(ctx, prompt="What country is your faction operating from?\n-# Note: this will affect your income taxes, so choose wisely.")
            landlordid = landlorddata['factionkey']
        # except ValueError as e:
            # await ctx.send(f"Command has stopped:\n\n{e}")



        datalist = [campaignKey,
                    factionkey,
                    landlordid,
                    approvalStatus,
                    campaignData["active"],
                    factionName,
                    factionDescription,
                    flagURL,
                    factionRoleID,
                    logChannelID,
                    isCountry,
                    discretionaryFunds, #money
                    population, #population
                    land, #landsize
                    governanceScale, #governance
                    round(0.70/governanceScale, 3), #happiness
                    round(0.75/governanceScale, 3), #financestability
                    round(0.72/governanceScale, 3), #culturestability
                    round((0.15*governanceScale), 3), #taxpoor
                    round((0.10*governanceScale), 3), #taxrich
                    int(population/popworkerratio * (salary)), #gdp
                    campaignData["defaultgdpgrowth"], #gdpgrowth
                    math.log((population/popworkerratio * (salary) / governanceScale)/int(population)/91.25)/math.log(839/91.25), #incomeindex
                    round(70/governanceScale, 3), #lifeexpectency
                    0.9, #educationindex
                    0.05, #educationspend
                    0.05, #socialspend
                    0.05, #infastructurespend
                    salary, #averagesalary
                    popworkerratio, #pop to worker ratio
                    0.01, #espionagespend
                    0
                    ]

        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''', [ctx.guild.id, factionName])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignfactions VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32)''', datalist)
        nameTest = await SQLfunctions.databaseFetchdictDynamic(f'''SELECT factionname FROM campaignfactions WHERE factionname = $1 AND campaignkey = $2;''', [factionName, campaignKey])
        if len(nameTest) > 1:
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2 AND factionkey = $3;''',[ctx.guild.id, factionName, factionkey])
            await ctx.send("Somehow... there are now multiple factions with names matching this one.  As this is theoretically impossible without running bot exploits, I have cancelled the registration of this faction.")
            return
        if approvalStatus == True:
            await ctx.send(f"## Done!\n{factionName} is now registered as a faction!")
        else:
            await ctx.send(f"## Done!\n{factionName} now awaits moderator approval.")
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignusers VALUES ($1, $2, $3, true)''',[ctx.author.id, campaignKey, factionkey])
            log_channel = self.bot.get_channel(campaignData['privatemoneychannelid'])
            await log_channel.send(f'### {ctx.author.mention} has submitted the faction "{factionName}" to {campaignData["campaignname"]} and now awaits approval!\n\n-# Use `-approveCampaignFactions` to approve queued faction submissions.')

        #except Exception:
            #await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="approveCampaignFactions", description="higdffffffffffff")
    async def approveCampaignFactions(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignHost(ctx) == False:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return

        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        factionDict = await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM campaignfactions WHERE approved = false AND campaignkey = $1;''', [campaignData["campaignkey"]])
        if campaignData["hostserverid"] != ctx.guild.id:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        for faction in factionDict:
            await campaignFunctions.showStats(ctx, faction)
            await campaignFunctions.showFinances(ctx, faction)
            answer = await discordUIfunctions.getYesNoModifyStopChoice(ctx)

            recipient = self.bot.get_channel(int(faction["logchannel"]))
            if answer == "yes":
                await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET approved = true WHERE factionkey = $1;''', [faction['factionkey']])
                await ctx.send("Added!")
                await recipient.send(f"{faction['factionname']} has been added to {campaignData['campaignname']}!  Welcome in!")
            elif answer == "no":
                await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE factionkey = $1;''', [faction['factionkey']])
                await ctx.send("Deleted!")
                await recipient.send(f"{faction['factionname']} was not accepted into {campaignData['campaignname']}.")
                await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignusers SET status = False WHERE factionkey = $1 AND campaignkey = $2;''',[faction['factionkey'], campaignData['campaignkey']])
            elif answer == "modify":
                scalar = await textTools.getFlooredFloatResponse(ctx, "Enter a ratio value for how much you want to multiply the faction's average salary.\n-# As an example, 0.5 will halve the salary.\nNote that changes to this value will directly affect the GDP, along with other stats, as a result.", 0)
                await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET averagesalary = averagesalary * $2 WHERE factionkey = $1;''',[faction['factionkey'], scalar])
                await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET approved = true WHERE factionkey = $1;''', [faction['factionkey']])
                await ctx.send("Approved!")
                await recipient.send(f"{faction['factionname']} has been added to {campaignData['campaignname']} - with some modified stats.  Welcome in!")
            else:
                await ctx.send("Alright, stopping here.")
                return
        await ctx.send("All good here!")

    @commands.command(name="joinExternalCampaign", description="Add a server to an ongoing campaign")
    async def joinExternalCampaign(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignManager(ctx) == False:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return
        userKey = int(await textTools.getIntResponse(ctx, "What is the campaign registration key?"))
        resultKeyData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE campaignkey = $1;''',[userKey])
        resultKey = resultKeyData["campaignkey"]
        if userKey != resultKey:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''',[ctx.guild.id, userKey])
        await ctx.send(f"## Done!\nYour server is now participating in {await campaignFunctions.getCampaignName(userKey)}")

    @commands.command(name="joinFaction", description="Add a server to an ongoing campaign")
    async def joinFaction(self, ctx: commands.Context):
        # await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        campaignData = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignKey = campaignData['campaignkey']
        factionData = await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND approved = true;''', [campaignKey])
        factionNameList = []
        factionNameDict = {}
        for serverData in factionData:
            if str(serverData['joinrole']) in str(ctx.author.roles):
                if serverData['factionname'] not in factionNameList:
                    factionNameList.append(serverData['factionname'])
                    factionNameDict[serverData['factionname']] = serverData['factionkey']
        if len(factionNameList) == 0:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            await ctx.send("No factions are available for you to join!  Ensure that you have the correct role.")
            return
        promptText = "Pick the faction you would like to join."
        answerName = await discordUIfunctions.getChoiceFromList(ctx, factionNameList, promptText)
        factionData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''', [campaignKey, answerName])

        factionkey = factionData["factionkey"]
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO campaignusers VALUES ($1, $2, $3, true)''',[ctx.author.id, campaignKey, factionkey])
        await ctx.send(f"## Done!\nYou are now a part of {answerName}!")

    @commands.command(name="leaveFactions", description="Add a server to an ongoing campaign")
    async def leaveFactions(self, ctx: commands.Context):
        campaignData = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignKey = campaignData['campaignkey']
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignusers SET status = False WHERE userid = $1 AND campaignkey = $2;''',[ctx.author.id, campaignKey])
        await ctx.send(f"## Done!\nYou are no longer in a faction!")

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignRegisterFunctions(bot))