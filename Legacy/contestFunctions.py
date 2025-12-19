import platform, discord, csv
from discord.ext import commands
import json
from pathlib import Path
from cogs.textTools import textTools
from cogs.blueprintFunctions import blueprintFunctions
# from cogs.githubTools import githubTools

if platform.system() == "Windows":
    botMode = "development"
    storageFilepath = "C:\\SprocketBot\\blueprint_vault\\"
    OSslashLine = "\\"
    prefix = "?"
else:
    # default settings (running on Rasbian)
    botMode = "official"
    storageFilepath = "/home/mumblepi/blueprint_vault/"
    OSslashLine = "/"
    prefix = "-"

class contestFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot



    @commands.command(name="resetContests", description="Reset all bot contests.")
    async def resetContests(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = "DROP TABLE IF EXISTS contests"
        await SQLfunctions.databaseExecute(prompt)
        prompt = "DROP TABLE IF EXISTS contests"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS contests (
                              name VARCHAR, 
                              ownerID BIGINT,
                              description VARCHAR,
                              rulesLink VARCHAR,
                              startTimestamp BIGINT,
                              endTimestamp BIGINT,
                              acceptEntries BOOL,
                              serverID BIGINT,
                              crossServer BOOL,
                              loggingChannelID BIGINT);''')
        await SQLfunctions.databaseExecute(prompt)
        prompt = '''select * from db.contests where condition = 1;'''
        Path(storageFilepath).mkdir(parents=True, exist_ok=True)
        # print(await SQLfunctions.databaseExecute(prompt))
        await ctx.send("Contest datasheet wiped!")

    @commands.command(name="resetContestCategories", description="Reset all bot contests.")
    async def resetContestCategories(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = "DROP TABLE IF EXISTS contestcategories"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS contestcategories (
                                            categoryName VARCHAR,
                                            contestName VARCHAR,
                                            ownerID BIGINT,
                                            era VARCHAR,
                                            gameVersion REAL,
                                            weightLimit REAL,
                                            enforceGameVersion BOOL,
                                            useBattleRating BOOL,
                                            requirePhotos BOOL,
                                            errorTolerance INT,
                                            crewMaxSpace REAL,
                                            crewMinSpace REAL,
                                            crewMin INT,
                                            crewMax INT,
                                            turretRadiusMin REAL,
                                            allowGCM BOOL,
                                            GCMratioMin REAL,
                                            GCMtorqueMax REAL,
                                            hullHeightMin REAL,
                                            hullWidthMax REAL,
                                            torsionBarLengthMin REAL,
                                            useDynamicTBLength BOOL,
                                            dynamicTBLength REAL,
                                            allowHVSS BOOL,
                                            beltWidthMin REAL,
                                            requireGroundPressure BOOL,
                                            groundPressureMax REAL,
                                            litersPerDisplacement REAL,
                                            litersPerTon REAL,
                                            minHPT REAL,
                                            minLFHP REAL,
                                            caliberLimit REAL,
                                            propellantLimit REAL,
                                            boreLimit REAL,
                                            shellLimit REAL,
                                            armorMin REAL,
                                            ATsafeMin INT,
                                            armorMax REAL);''')
        await SQLfunctions.databaseExecute(prompt)
        Path(storageFilepath).mkdir(parents=True, exist_ok=True)
        await ctx.send("Category datasheet wiped!")

    @commands.command(name="resetContestEntries", description="Reset all tanks entered.")
    async def resetContestEntries(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = "DROP TABLE IF EXISTS contesttanks"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS contesttanks (
                                            tankName VARCHAR,
                                            categoryName VARCHAR,
                                            contestName VARCHAR,
                                            ownerID BIGINT,
                                            tankWeight REAL,
                                            errorCount INT,
                                            fileLocation VARCHAR,
                                            valid BOOL,
                                            tankWidth REAL,
                                            crewCount INT,
                                            armorBTRating INT,
                                            cannonBTRating INT,
                                            mobilityBTRating INT,
                                            turretCount INT,
                                            GCMratioMin INT,
                                            maxArmor INT,
                                            gameVersion VARCHAR,
                                            gameEra VARCHAR,
                                            GCMcount INT,
                                            hullHeight REAL,
                                            tankLength REAL,
                                            armorvolume REAL,
                                            torsionBarLength REAL,
                                            suspensionType VARCHAR,
                                            beltWidth REAL,
                                            groundPressure REAL,
                                            HP REAL,
                                            HPT REAL,
                                            litersPerDisplacement REAL,
                                            litersPerTon REAL,
                                            topSpeed REAL,
                                            gunCount INT,
                                            maxCaliber INT,
                                            maxPropellant INT,
                                            maxBore REAL,
                                            maxShell INT,
                                            minArmor INT);''')
        await SQLfunctions.databaseExecute(prompt)
        await ctx.send("Contest Entry datasheet wiped!")

    @commands.command(name="registerContest", description="register a contest")


    async def registerContest(self, ctx: commands.Context):
        contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {ctx.guild.id}')][0]
        print(contestList["contestmanagerroleid"])
        print(ctx.author.roles)
        if str(contestList["contestmanagerroleid"]) not in str(ctx.author.roles):
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        await ctx.send("Beginning processing now.")
        contestHostID = ctx.author.id
        for attachment in ctx.message.attachments:
            config = json.loads(await attachment.read())
            contestName = config["contestName"]
            contestName = await textTools.sanitize(contestName)
            contestDescription = config["contestDescription"]
            contestRules = config["rulesLink"]
            crossServer = False
            if config["crossServer"].lower() == "true":
                crossServer = True
            startTimeStamp = config["startTimeStamp"]
            endTimeStamp = config["endTimeStamp"]

            contestName = str(await textTools.sanitize(contestName))
            allowWriting = True
            # try:
            existingContest = await SQLfunctions.databaseFetchrow(f'''SELECT * FROM contests WHERE name = '{contestName}' ''')
            try:
                contestData = dict(existingContest)
                print(contestData)

                if str(contestData["ownerid"]) != str(ctx.author.id):
                    await ctx.send(f"Someone else already has a contest registered under this name!")
                    allowWriting = False
                if str(contestData["ownerid"]) == str(ctx.author.id):
                    await ctx.send(f"You already have a contest registered under this name!  Use a different command to update or remove your contest accordingly.")
                    allowWriting = False
            except Exception:
                pass

            # except Exception:
            #     pass
            if allowWriting == True:
                submitDirectory = f"{storageFilepath}contests{OSslashLine}{contestName}"
                Path(submitDirectory).mkdir(parents=True, exist_ok=True)
                # create logging channel
                channel = self.bot.get_channel(ctx.channel.id)
                thread = await channel.create_thread(
                    name=contestName,
                    type=discord.ChannelType.private_thread
                )
                loggingChannelID = thread.id
                await SQLfunctions.databaseExecute(f'''
                INSERT INTO contests (name, ownerID, description, rulesLink, startTimestamp, endTimestamp, acceptEntries, serverID, crossServer, loggingChannelID)
                VALUES ('{contestName}','{ctx.author.id}','{contestDescription}','{contestRules}','{startTimeStamp}','{endTimeStamp}','False', '{ctx.message.guild.id}', '{crossServer}','{loggingChannelID}'); ''')
                # await backupFiles()
                await thread.send(
                    f"<@{contestHostID}>, the {contestName} is now registered!  Submissions are turned off for now - enable them once you are ready.  Once you do enable submissions, they will be logged here.")
                await ctx.send("Complete!")

    @commands.command(name="registerCategory", description="register a contest category")
    async def registerCategory(self, ctx: commands.Context):
        await ctx.send("Beginning processing now.")
        contestHostID = ctx.author.id
        contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM contests WHERE ownerID = {contestHostID}')]
        userPrompt = "Pick a contest you want to add your category to!"
        contestName = await ctx.bot.ui.getContestChoice(ctx, contestList, f'{userPrompt}')
        await ctx.send(f"You selected the {contestName}!  Beginning processing now.")
        contestConfig = [list(await SQLfunctions.databaseFetch(f"SELECT * FROM contests WHERE name = '{contestName}' AND ownerID = {contestHostID}"))]
        for attachment in ctx.message.attachments:

            config = json.loads(await attachment.read())
            categoryName = config["categoryName"]

            allowWriting = True
            try:
                existingContestList = [list(await SQLfunctions.databaseFetch(f'''SELECT * FROM contestcategories WHERE categoryName = '{categoryName}' AND contestName = '{contestName}';'''))]
                contestData = existingContestList[0]
                print(contestData["categoryName"])
                allowWriting = False
                await ctx.send("You already have a category with this name!  Use the appropriate command to update an already-existing category.")
            except Exception:
                pass
            if allowWriting == True:
                try:
                    submitDirectory = f"{storageFilepath}contests{OSslashLine}{contestName}"
                    Path(submitDirectory).mkdir(parents=True, exist_ok=True)
                    # create logging channel
                    config["categoryName"] = await textTools.sanitize(categoryName)
                    config["contestName"] = contestName
                    config["ownerid"] = ctx.author.id
                    promptVariableNames, promptValues = await textTools.getSQLprompt(config)
                    await SQLfunctions.databaseExecute(f'''INSERT INTO contestcategories ({promptVariableNames}) VALUES ({promptValues}); ''')
                    await ctx.send("Complete!")
                except Exception:
                    await ctx.send(f"There was an error in registering your category.")


    @commands.command(name="updateContest", description="update a contest")
    async def updateContest(self, ctx: commands.Context):
        await ctx.send("Beginning processing now.")
        contestHostID = ctx.author.id
        for attachment in ctx.message.attachments:
            config = json.loads(await attachment.read())
            contestHostID = ctx.author.id
            contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM contests WHERE ownerID = {contestHostID}')]
            userPrompt = "What contest are you looking to update the configuration of?"
            contestName = await ctx.bot.ui.getContestChoice(ctx, contestList, f'{userPrompt}')

            # except Exception:
            #     pass

            contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM contests WHERE ownerID = {contestHostID} AND name = {contestName}')][0]
            keystr, valuestr = await textTools.getSQLprompt(contestList)
            print(keystr)
            print(valuestr)
            await SQLfunctions.databaseExecute(f'''UPDATE contests SET ({keystr}) VALUES ({valuestr}) WHERE ownerID = {contestHostID} AND name = {contestName};''')
            await ctx.send("Complete!")


    @commands.command(name="listContests", description="list contests")
    async def listContests(self, ctx: commands.Context):
        contestData = await SQLfunctions.databaseFetch(f'''SELECT * FROM contests WHERE serverID = {ctx.message.guild.id} OR crossServer = 'True';''')
        print(contestData)
        contestList = [dict(row) for row in contestData]
        print (contestList)
        description = ""
        serverID = str(ctx.message.guild.id)
        for contestInfo in contestList:
            if serverID != contestInfo['serverid'] and contestInfo['crossserver'] != 'false':
                appendation = f" ** {contestInfo['name']} ** \nClosing time: <t:{contestInfo['endtimestamp']}:f> \n \n"
                description = description.__add__(appendation)
        embed = discord.Embed(title="Sprocket Community Contests",
                              description=description,
                              color=discord.Color.random())
        await ctx.send(embed=embed)

    @commands.command(name="listCategories", description="list a contest's categories")
    async def listCategories(self, ctx: commands.Context):
        contestHostID = ctx.author.id
        contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM contests WHERE serverID = {ctx.message.guild.id}')]
        userPrompt = "What contest are you looking to get details on?"
        contestName = await ctx.bot.ui.getContestChoice(ctx, contestList, f'{userPrompt}')
        categoryList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contestcategories WHERE contestname = '{contestName}';''')]

        print (categoryList)
        description = ""
        serverID = str(ctx.message.guild.id)
        for categoryInfo in categoryList:
            appendation = f" ** {categoryInfo['categoryname']} ** \nWeight limit: {categoryInfo['weightlimit']}T\n \n"
            description = description.__add__(appendation)
        embed = discord.Embed(title=f"{contestName}'s submission categories",
                              description=description,
                              color=discord.Color.random())
        await ctx.send(embed=embed)


# Assistance from https://github.com/richardschwabe/discord-bot-2022-course/blob/main/initial_select.py
    @commands.command(name="submitTank", description="submit a tank to a contest")
    async def submitTank(self, ctx: commands.Context):
        import asyncio
        name = "invalid"
        weight = -1
        errors = 0
        contestName = ""
        contestListText = ""
        allowEntry = True
        contestType = await ctx.bot.ui.getContestTypeChoice(ctx)
        if contestType == "Global":
            contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contests WHERE crossServer = 'True';''')]
        if contestType == "Server":
            contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contests WHERE serverID = {ctx.message.guild.id} AND crossServer != 'True';''')]
        if len(contestList) < 1:
            await ctx.send(f"There are no {contestType.lower()} contests running!")
            return
        userPrompt = "What contest are you submitting to?"
        contestName = await ctx.bot.ui.getContestChoice(ctx, contestList, f'{userPrompt}')
        contestConfigList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contests WHERE name = '{contestName}';''')]
        contestConfig = contestConfigList[0]

        # get the category
        categoryList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contestcategories WHERE contestname = '{contestName}';''')]
        if len(categoryList) == 3:
            categoryName = categoryList[0]["categoryname"]
        else:
            userPrompt = "What category are you submitting to?"
            categoryName = await ctx.bot.ui.getCategoryChoice(ctx, categoryList, f'{userPrompt}')
        await ctx.send(f"You are submitting to the {categoryName} category!")
        configuration = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contestcategories WHERE contestname = '{contestName}' AND categoryname = '{categoryName}';''')]
        config = configuration[0]
        # run the blueprint checks
        for attachment in ctx.message.attachments:
            results = await blueprintFunctions.runBlueprintCheck(ctx, attachment, config)
            await ctx.reply("Blueprint processing complete.")
            name = results["tankName"]
            weight = results["tankWeight"]
            valid = results["valid"]
            crewCount = results["crewCount"]
            maxVehicleArmor = float(results["maxArmor"])
            tankWidth = results["tankWidth"]
            results["ownerid"] = ctx.author.id

            existingSubsList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contesttanks WHERE contestname = '{contestName}' AND tankname = '{name}' AND categoryname = '{categoryName}' AND ownerid = {ctx.author.id};''')]
            if len(existingSubsList) > 0:
                    await ctx.reply("Someone else has already submitted a tank with this name!  Please choose a different name.")
                    valid = False

            if valid == True:
                if config["requirephotos"] == True:
                    await ctx.send(f"## Attach the specified photos of the {name} here.  \n**Picture 1** needs to be a well-lit picture of the tank's front and side.\n**Picture 2** needs to be a well-lit picture of the tank's rear and side.\n**Picture 3** needs to be a front view of the tank using the \"Internals\" overlay **while looking at the ammunition rack editor.**\n**Picture 4** needs to be a top+side view of the tank using the \"Internals\" overlay **while looking at the ammunition rack editor.**\n### Note: at least one of your screenshots needs to include the full page and Sprocket UI.")
                    def check(m: discord.Message):
                        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=5000.0)
                    except asyncio.TimeoutError:
                        await ctx.reply("Operation timed out due to no photos.  This vehicle has not been registered into the contest.")
                        return

                blueprintData = json.loads(await attachment.read())
                json_output = json.dumps(blueprintData, indent=4)
                file_location = f"{storageFilepath}{OSslashLine}{'contests'}{OSslashLine}{contestName}{OSslashLine}{categoryName}"
                results["filelocation"] = file_location
                from pathlib import Path
                Path(file_location).mkdir(parents=True, exist_ok=True)
                with open(str(file_location + "/" + str(name) + ".blueprint"), "w") as outfile:
                    outfile.write(json_output)
                armorBTRating, cannonBTRating, mobilityBTRating = await blueprintFunctions.getBattleRating(results)
                # temporary
                results["armorbtrating"] = int(armorBTRating)
                results["cannonbtrating"] = int(cannonBTRating)
                results["mobilitybtrating"] = int(mobilityBTRating)
                results["categoryname"] = categoryName
                results["contestname"] = contestName

                keystr, valuestr = await textTools.getSQLprompt(results)
                print(keystr)
                print(valuestr)
                await SQLfunctions.databaseExecute(f'''INSERT INTO contesttanks ({keystr}) VALUES ({valuestr});''')
                msg = ctx.message
                url = msg.jump_url
                chnl = self.bot.get_channel(int(contestConfig["loggingchannelid"]))

                await chnl.send(f"### You have a new entry into the {contestName}! \nName: {name} \nCrew count: {crewCount} \n## Vehicle submission: [here]({url})")
                await chnl.send(f"** ** \n\n** **")
                await ctx.send(f"The {name} has been submitted!  Thanks for participating in the {contestName}!")
            else:
                await ctx.send(
                    "The " + name + " needs fixes to the problems listed above before it can be registered.")

    @commands.command(name="getContestCSV", description="list a contest's submissions")
    async def getContestCSV(self, ctx: commands.Context):
        contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {ctx.guild.id}')][0]
        print(contestList["contestmanagerroleid"])
        print(ctx.author.roles)
        if str(contestList["contestmanagerroleid"]) not in str(ctx.author.roles):
            await ctx.send("Unfortunately you are not authorized to do this.")
            return
        contestHostID = ctx.author.id
        contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM contests WHERE ownerID = {contestHostID}')]
        userPrompt = "What contest are you looking to get a list of submissions for?"
        contestName = await ctx.bot.ui.getContestChoice(ctx, contestList, f'{userPrompt}')

        file_location = f"{storageFilepath}{OSslashLine}{'contests'}{OSslashLine}{contestName}{OSslashLine}{contestName}Entries.csv"
        tanksList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contesttanks WHERE contestname = '{contestName}';''')]
        i = 0
        for tank in tanksList:
            del tanksList[i]['filelocation']
            i += 1
        with open(file_location, 'w', newline='\n') as file:
            writer = csv.DictWriter(file, fieldnames=tanksList[0].keys())
            writer.writeheader()
            writer.writerows(tanksList)

        await ctx.send(file=discord.File(file_location))

    @commands.command(name="listSubmissions", description="list a contest's submissions")
    async def listSubmissions(self, ctx: commands.Context):
        contestHostID = ctx.author.id
        contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM contests WHERE serverID = {ctx.message.guild.id}')]
        userPrompt = "What contest are you looking to get a list of submissions for?"
        contestName = await ctx.bot.ui.getContestChoice(ctx, contestList, f'{userPrompt}')
        categoryList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT categoryname FROM contestcategories WHERE contestname = '{contestName}';''')]
        print(categoryList)
        for categoryname in categoryList:
            print(categoryname["categoryname"])
            tanksList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contesttanks WHERE contestname = '{contestName}' AND categoryname = '{categoryname["categoryname"]}';''')]
            print(tanksList)
            if len(tanksList) > 0:
                description = ""
                for tank in tanksList:
                    appendation = f''' **{tank["tankname"]}** \nContestant: {self.bot.get_user(int(tank["ownerid"]))}\nWeight: {round(float(tank["tankweight"]), 3)}T\n \n'''
                    description = description.__add__(appendation)
                embed = discord.Embed(title=f"{contestName}: {categoryname['categoryname']} Submissions",
                                      description=description,
                                      color=discord.Color.random())
                await ctx.send(embed=embed)















async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(contestFunctions(bot))