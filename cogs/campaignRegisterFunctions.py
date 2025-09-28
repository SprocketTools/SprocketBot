import datetime
import json, locale
import math
import time
locale.setlocale(locale.LC_ALL, '')
import random
import discord
from discord.ext import commands
from scipy.spatial.transform import Rotation as R
import main
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions
class campaignRegisterFunctions(commands.Cog):
    activeRegistKey = 569801354
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="generateCampaignKey", description="generate a key that can be used to initiate a campaign")
    async def generateCampaignKey(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
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
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        await ctx.send("Confirm you want to wipe the database.")
        if not await ctx.bot.ui.getYesNoChoice(ctx):
            return
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS campaigns, campaignservers, campaignfactions, campaignusers, campaignautopurchases;''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaigns (campaignname VARCHAR, campaignrules VARCHAR(50000), hostserverid BIGINT, campaignkey BIGINT, timescale BIGINT, currencyname VARCHAR, currencysymbol VARCHAR, publiclogchannelid BIGINT, privatemoneychannelid BIGINT, companychannelid BIGINT, managerchannelid BIGINT, defaultgdpgrowth REAL, defaultpopgrowth REAL, populationperkm INT, steelcost REAL, energycost REAL, active BOOLEAN, timedate TIMESTAMP, lastupdated TIMESTAMP);''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignservers (serverid BIGINT, campaignkey BIGINT);''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignfactions (campaignkey BIGINT, factionkey BIGINT, landlordfactionkey BIGINT, approved BOOLEAN, hostactive BOOLEAN, companyowner BIGINT, factionname VARCHAR, description VARCHAR(50000), flagurl VARCHAR(50000), joinrole BIGINT, logchannel BIGINT, iscountry BOOL, money BIGINT, population BIGINT, landsize BIGINT, governance REAL, happiness REAL, financestability REAL, culturestability REAL, taxpoor REAL, taxrich REAL, gdp BIGINT, gdpgrowth REAL, lifeexpectancy REAL, educationindex REAL, socialspend REAL, infrastructurespend REAL, averagesalary REAL, popworkerratio REAL, espionagespend REAL, espionagestaff INT, povertyrate REAL, latitude INT, infrastructureindex REAL, defensespend REAL, corespend REAL, educationspend REAL, popgrowth REAL);''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignautopurchases (campaignkey BIGINT, factionkey BIGINT, userid BIGINT, name VARCHAR, amount BIGINT, lastupdated TIMESTAMP, monthfrequency INT, status BOOLEAN);''')
        await ctx.send("## Done!")

    @commands.command(name="clearCampaignFactions", description="generate a key that can be used to initiate a campaign")
    async def clearCampaignFactions(self, ctx: commands.Context):
        if ctx.bot.campaignTools.isCampaignHost(ctx) == False:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        campaignData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        campaignKey = campaignData["campaignkey"]
        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1;''', [campaignKey])
        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignusers WHERE campaignkey = $1;''', [campaignKey])
        await ctx.send("## Done!\nYour campaign has been cleared of all factions.")

    @commands.command(name="startCampaign", description="Start a campaign")
    async def startCampaign(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignManager(ctx) == False:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return
        if ctx.author.id == main.ownerID:
            await ctx.send("The current registration key is " + str(self.activeRegistKey))
            userKey = int(self.activeRegistKey)
        else:
            await ctx.send("Let's get started!\nYou will now be asked 6 questions to initialize the campaign, starting with this one.")
            userKey = await textTools.getIntResponse(ctx, "What is your campaign registration key?\n-# If you do not have a registration key, contact the bot host in order to get one.")
            if userKey != self.activeRegistKey:
                print(userKey)
                print(self.activeRegistKey)
                await self.bot.error.sendCategorizedError(ctx, "campaign")
                return

        campaignName = await textTools.getCappedResponse(ctx, "What is the name of your campaign?", 128)
        campaignRules = "N/A"
        speed = 7
        currencyName = "dollars"
        currencySymbol = "$"
        publicAnnouncement = await textTools.getChannelResponse(ctx, "What Discord channel do you want publicly-visible announcements to be sent to?  This will include things like new-year celebrations and important events.\nReply with a mention of the desired channel.")
        privateLogging = await textTools.getChannelResponse(ctx, "What Discord channel do you want to use to log player actions?  This will contain alot of stuff that players should not be able to see, such as purchases made by countries.\nReply with a mention of the desired channel.")
        companyChannel = await textTools.getChannelResponse(ctx,"What Discord channel do you want to use for companies?  Sprocket Bot will use this channel to create threads for companies so that they can conduct business. \nReply with a mention of a channel.")
        managerChannel = await textTools.getChannelResponse(ctx,"What Discord channel do you want to use for processing new vehicle submissions?  This channel should only be visible to campaign managers. \nReply with a mention of a channel.")
        defaultGDPgrowth = 0.05
        defaultpopgrowth = 0.01
        poppersquarekm = 1500
        steelcost = 50
        energycost = 3
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
                    companyChannel,
                    managerChannel,
                    defaultGDPgrowth,
                    defaultpopgrowth,
                    poppersquarekm,
                    steelcost,
                    energycost,
                    False,
                    datetime.datetime(startingyear, 1, 1),
                    datetime.datetime.now()
                    ]
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)''',datalist)
        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignservers WHERE serverid = $1''',[ctx.guild.id])
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''',[ctx.guild.id, userKey])
        await ctx.send(f"## Done!\nRemember to save your campaign registration key (**{userKey}**), as other servers will need this in order to join the campaign.")
        inputKey = int(random.random() * 10000000)
        self.activeRegistKey = inputKey
        await ctx.bot.campaignTools.updateCampaignSettings(ctx)
        await ctx.bot.campaignTools.updateCampaignServerSettings(ctx)

        # except Exception:
        #     await ctx.send(await self.bot.error.retrieveError(ctx))

    @commands.command(name="overwriteCampaignSettings", description="generate a key that can be used to initiate a campaign")
    async def overwriteCampaignSettings(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignHost(ctx) == False:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        oldCampaignData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        userKey = oldCampaignData["campaignkey"]

        if ctx.guild.id == oldCampaignData["hostserverid"]:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
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
            await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaigns WHERE campaignkey = $1;''', [userKey])
            await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignservers WHERE campaignkey = $1;''',[userKey])
            await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaigns VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)''', datalist)
            await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''', [ctx.guild.id, userKey])
            await ctx.send("## Done!")
        except Exception:
            await self.bot.error.sendCategorizedError(ctx, "campaign")

    @commands.command(name="startFaction", description="Add a faction to a campaign")
    async def startFaction(self, ctx: commands.Context):
        campaignData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        approvalStatus = await ctx.bot.campaignTools.isCampaignHost(ctx)
        campaignKeyList = await self.bot.sql.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignKey = campaignKeyList['campaignkey']
        await ctx.send("## Welcome!\nYou will now be asked several questions about your country to start the setup process!  Keep in mind that most of these settings can be changed later using the `-manageFaction` command.\nLet's begin: is your faction a country?")
        isCountry = await ctx.bot.ui.getYesNoChoice(ctx)
        factionName = await textTools.getResponse(ctx, "What is the name of your faction?")
        nameStatus = False
        while nameStatus == False:
            nameTest = await self.bot.sql.databaseFetchdictDynamic(f'''SELECT factionname FROM campaignfactions WHERE factionname = $1 AND campaignkey = $2;''', [factionName, campaignKey])
            if len(nameTest) > 0:
                await ctx.send("A faction already exists with this name!")
                return
            nameStatus = True
        factionDescription = "Add a fancy description here!"
        if ctx.guild.id == campaignData["hostserverid"] and isCountry == False:
            channel = ctx.bot.get_channel(campaignData["companychannelid"])
            logChannel = await channel.create_thread(name=factionName, type=discord.ChannelType.private_thread)
            logChannelID = logChannel.id
        else:
            logChannelID = ctx.channel.id

        factionkey = time.time() + round(random.random()*10000)
        if isCountry == True: # country
            factionRoleID = await textTools.getRoleResponse(ctx, "What Discord role is going to be required for players to be able to join your faction?\n-# Reply with a ping of that role, or its role id.")
            flagURL = await textTools.getFileURLResponse(ctx,"What is your country's flag?\n-# Upload a picture of your flag.")
            population = await textTools.getFlooredIntResponse(ctx,"What is the population of your country?\n-# For numerical replies like this one, do not include any commas.", 1000)
            salary = await textTools.getFlooredIntResponse(ctx, "What is your country's average monthly salary?  Do not include unemployed people in your average.", 1)
            latitude = await textTools.getFloatResponse(ctx,"What is the average latitude of your country on the globe?  Reply with a number in degrees.\nNote that this value does not need to be precise and can be estimated.")
            land = await textTools.getFlooredFloatResponse(ctx, "How many square kilometers of land does your country control?", 1)
            governanceScale = await ctx.bot.campaignTools.getGovernmentType(ctx)
            companyOwner = 0
            landlordid = 0
            taxpoor = round((0.15*governanceScale + 0.2), 3)
            popworkerratio = 3 - math.atan(salary/((campaignData['energycost'] + campaignData['steelcost'] + taxpoor*10)/10))
            gdp = round(salary*population/popworkerratio)
            discretionaryFunds = gdp/20
        else: #company
            factionRoleID = 0
            discretionaryFunds = campaignData["steelcost"]*50000 + campaignData["energycost"]*50000
            flagURL = await textTools.getFileURLResponse(ctx,"What is your company's logo?\n-# Upload a picture of your flag.")
            population = 1000
            salary = 1000
            popworkerratio = 3
            latitude = 0
            companyOwner = ctx.author.id
            land = 2000
            governanceScale = 1.0
            landlorddata = await ctx.bot.campaignTools.pickCampaignCountry(ctx, prompt="What country is your faction operating from?\n-# Note: this will affect your income taxes, so choose wisely.")
            landlordid = landlorddata['factionkey']

        await ctx.send("Starting processing...")
        datalist = [campaignKey,
                    factionkey,
                    landlordid,
                    approvalStatus,
                    campaignData["active"],
                    companyOwner,
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
                    round(0.8, 3), #happiness
                    round((0.15*governanceScale + 0.2), 3), #taxpoor
                    round((0.20*governanceScale + 0.2), 3), #taxrich
                    int(population/popworkerratio * (salary)), #gdp
                    campaignData["defaultgdpgrowth"], #gdpgrowth
                    round(60 + 10*governanceScale, 3), #lifeexpectency
                    0.9, #educationindex
                    0.05, #socialspend
                    0.05, #infrastructurespend
                    salary, #averagesalary
                    popworkerratio, #pop to worker ratio
                    0.01, #espionagespend
                    0, #staff
                    0, #povertyrate
                    round(latitude), #latitude
                    0, #infrastructureindex
                    0, #defense spending
                    0, #corespend
                    0.05, #educationspend
                    0.01 #population growth
                    ]
        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''', [ctx.guild.id, factionName])
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaignfactions VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36)''', datalist)
        nameTest = await self.bot.sql.databaseFetchdictDynamic(f'''SELECT factionname FROM campaignfactions WHERE factionname = $1 AND campaignkey = $2;''', [factionName, campaignKey])
        if len(nameTest) > 1:
            await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2 AND factionkey = $3;''',[ctx.guild.id, factionName, factionkey])
            await ctx.send("Somehow... there are now multiple factions with names matching this one.  As this is theoretically impossible without running bot exploits, I have cancelled the registration of this faction.")
            return
        logChannel = ctx.bot.get_channel(logChannelID)
        if isCountry == False:
            await logChannel.send(ctx.author.mention)
            await logChannel.send("Use this channel to conduct private operations.  If you wish to use another location, this can be set using `-manageFaction`.")
        if approvalStatus == True:
            await ctx.send(f"## Done!\n{factionName} is now registered as a faction!")
        else:
            await logChannel.send(f"## Done!\n{factionName} now awaits moderator approval.\n")
            log_channel = self.bot.get_channel(campaignData['privatemoneychannelid'])
            await log_channel.send(f'### {ctx.author.mention} has submitted the faction "{factionName}" to {campaignData["campaignname"]} and now awaits approval!\n\n-# Use `-approveCampaignFactions` to approve queued faction submissions.')
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaignusers VALUES ($1, $2, $3, true)''',[ctx.author.id, campaignKey, factionkey])


        #except Exception:
            #await ctx.send(await self.bot.error.retrieveError(ctx))



    @commands.command(name="approveCampaignFactions", description="higdffffffffffff")
    async def approveCampaignFactions(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignHost(ctx) == False:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return

        campaignData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        factionDict = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM campaignfactions WHERE approved = false AND campaignkey = $1;''', [campaignData["campaignkey"]])
        if campaignData["hostserverid"] != ctx.guild.id:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        for faction in factionDict:
            await ctx.bot.campaignTools.showStats(ctx, faction)
            await ctx.bot.campaignTools.showFinances(ctx, faction)
            answer = await ctx.bot.ui.getYesNoModifyStopChoice(ctx)

            recipient = self.bot.get_channel(int(faction["logchannel"]))
            if answer == "yes":
                await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET approved = true WHERE factionkey = $1;''', [faction['factionkey']])
                await ctx.send("Added!")
                await recipient.send(f"{faction['factionname']} has been added to {campaignData['campaignname']}!  Welcome in!")
            elif answer == "no":
                await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE factionkey = $1;''', [faction['factionkey']])
                await ctx.send("Deleted!")
                await recipient.send(f"{faction['factionname']} was not accepted into {campaignData['campaignname']}.")
                await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignusers SET status = False WHERE factionkey = $1 AND campaignkey = $2;''',[faction['factionkey'], campaignData['campaignkey']])
            elif answer == "modify":
                scalar = await textTools.getFlooredFloatResponse(ctx, "Enter a ratio value for how much you want to multiply the faction's average salary.\n-# As an example, 0.5 will halve the salary.\nNote that changes to this value will directly affect the GDP, along with other stats, as a result.", 0)
                await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET averagesalary = averagesalary * $2 WHERE factionkey = $1;''',[faction['factionkey'], scalar])
                await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET approved = true WHERE factionkey = $1;''', [faction['factionkey']])
                await ctx.send("Approved!")
                await recipient.send(f"{faction['factionname']} has been added to {campaignData['campaignname']} - with some modified stats.  Welcome in!")
            else:
                await ctx.send("Alright, stopping here.")
                return
        await ctx.send("All good here!")

    @commands.command(name="joinExternalCampaign", description="Add a server to an ongoing campaign")
    async def joinExternalCampaign(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignManager(ctx) == False:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return
        userKey = int(await textTools.getIntResponse(ctx, "What is the campaign registration key?"))
        resultKeyData = await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE campaignkey = $1;''',[userKey])
        resultKey = resultKeyData["campaignkey"]
        if userKey != resultKey:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaignservers VALUES ($1, $2)''',[ctx.guild.id, userKey])
        await ctx.send(f"## Done!\nYour server is now participating in {await ctx.bot.campaignTools.getCampaignName(userKey)}")

    @commands.command(name="leaveExternalCampaign", description="Add a server to an ongoing campaign")
    async def leaveExternalCampaign(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignHost(ctx):
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            await ctx.send("\nYou cannot leave your own campaign!")
            return
        if await ctx.bot.campaignTools.isCampaignManager(ctx) == False:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return

        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        await ctx.send(f"## Done!\nYour server is no longer a part of an external campaign.")

    @commands.command(name="joinFaction", description="Add a server to an ongoing campaign")
    async def joinFaction(self, ctx: commands.Context):
        # await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaignusers (userid BIGINT, campaignkey BIGINT, factionkey BIGINT, status BOOLEAN);''')
        campaignData = await self.bot.sql.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignKey = campaignData['campaignkey']
        factionData = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND approved = true;''', [campaignKey])
        factionNameList = []
        factionNameDict = {}
        for serverData in factionData:
            if str(serverData['joinrole']) in str(ctx.author.roles):
                if serverData['factionname'] not in factionNameList:
                    factionNameList.append(serverData['factionname'])
                    factionNameDict[serverData['factionname']] = serverData['factionkey']
        if len(factionNameList) == 0:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            await ctx.send("No factions are available for you to join!  Ensure that you have the correct role.")
            return
        promptText = "Pick the faction you would like to join."
        answerName = await ctx.bot.ui.getChoiceFromList(ctx, factionNameList, promptText)
        factionData = await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND factionname = $2;''', [campaignKey, answerName])

        factionkey = factionData["factionkey"]
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaignusers VALUES ($1, $2, $3, true)''',[ctx.author.id, campaignKey, factionkey])
        await ctx.send(f"## Done!\nYou are now a part of {answerName}!")

    @commands.command(name="recruitToFaction", description="Add a server to an ongoing campaign")
    async def recruitToFaction(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignHost(ctx) == False:
            return
        campaignKey = await ctx.bot.campaignTools.getCampaignKey(ctx)
        factionData = await ctx.bot.campaignTools.pickCampaignFaction(ctx, "What faction are you adding players to?")
        rawtext = await textTools.getResponse(ctx, f"Reply with a list of the members you wish to add to {factionData['factionname']}.\n-# Separate entries by spaces.  Both pings and user IDs can be used.")
        userids = rawtext.replace('<', '').replace('>', '').split(' ')
        for user in userids:
            if abs(len(user) - 18) < 2:
                await self.bot.sql.databaseExecuteDynamic('''INSERT INTO campaignusers VALUES ($1, $2, $3, true)''',[ctx.author.id, campaignKey, factionData['factionkey']])
            print(user)
        await ctx.send(f"## Done!")

    @commands.command(name="leaveFactions", description="Add a server to an ongoing campaign")
    async def leaveFactions(self, ctx: commands.Context):
        campaignData = await self.bot.sql.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignKey = campaignData['campaignkey']
        await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignusers SET status = False WHERE userid = $1 AND campaignkey = $2;''',[ctx.author.id, campaignKey])
        await ctx.send(f"## Done!\nYou are no longer in a faction!")

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignRegisterFunctions(bot))