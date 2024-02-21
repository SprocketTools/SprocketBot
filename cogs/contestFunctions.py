import os, platform, discord, configparser, ast, json
from discord.ext import commands
from discord import app_commands
import json, asyncio
from pathlib import Path
from cogs.textTools import textTools
from cogs.SQLfunctions import SQLfunctions


if platform.system() == "Windows":
    botMode = "development"
    storageFilepath = "C:\\SprocketBot\\"
    OSslashLine = "\\"
    prefix = "?"
else:
    # default settings (running on Rasbian)
    botMode = "official"
    storageFilepath = "/home/mumblepi/"
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

    @commands.command()
    async def dropdown_test(self, ctx: commands.Context):
        menu = discord.Menu(ctx)
        options=[
        ("Option 1", "value1"),
        ("Option 2", "value2"),
        ("Option 3", "value3")
        ]

        selected_option = await ctx.show_menu(menu)
        print(f"Selected option: {selected_option}")

    @commands.command(name="registerContest", description="register a contest")
    async def registerContest(self, ctx: commands.Context):
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
                await SQLfunctions.databaseFetch('SELECT * FROM tanks')
                # await backupFiles()
                await thread.send(
                    f"<@{contestHostID}>, the {contestName} is now registered!  Submissions are turned off for now - enable them once you are ready.  Once you do enable submissions, they will be logged here.")
                await ctx.send("Complete!")

    @commands.command(name="registerCategory", description="register a contest category")
    async def registerCategory(self, ctx: commands.Context):
        await ctx.send("Beginning processing now.")
        contestHostID = ctx.author.id
        contestList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM contests WHERE ownerID = {contestHostID}')]
        print(contestList)
        await ctx.send("Select a contest below.")
        view = contestView(contestList)
        await ctx.send(view=view)
        await view.wait()
        contestNameOut = contestSelect().
        await ctx.send("Let's get back to it.")
        print(contestNameOut)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=90.0)
            imageInput = str(msg.content)
            if imageInput.lower() == "default":
                pass
            else:
                if "https://i.imgur.com/9SAQYUm.png" in imageInput or "https://sprockettools.github.io/" in imageInput:
                    imageLink = imageInput
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return
        await ctx.send("Beginning processing now.  This will take some time.")

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
            existingContest = await SQLfunctions.databaseFetchrow(
                f'''SELECT * FROM contests WHERE name = '{contestName}' ''')
            contestData = dict(existingContest)
            print(contestData)

            if str(contestData["ownerid"]) != str(ctx.author.id):
                await ctx.send(f"Someone else already has a contest registered under this name!")
                allowWriting = False
            if str(contestData["ownerid"]) == str(ctx.author.id):
                await ctx.send(
                    f"You already have a contest registered under this name!  Use a different command to update or remove your contest accordingly.")
                allowWriting = False

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
                await SQLfunctions.databaseFetch('SELECT * FROM tanks')
                # await backupFiles()
                await thread.send(
                    f"<@{contestHostID}>, the {contestName} is now registered!  Submissions are turned off for now - enable them once you are ready.  Once you do enable submissions, they will be logged here.")
                await ctx.send("Complete!")





    @commands.command(name="listContests", description="register a contest")
    async def listContests(self, ctx: commands.Context):
        contestData = await SQLfunctions.databaseFetch('SELECT * FROM contests')
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

# Assistance from https://github.com/richardschwabe/discord-bot-2022-course/blob/main/initial_select.py
class contestSelect(discord.ui.Select):
    chosenContest = ""
    def __init__(self, contestList):
        options = []
        self.contestlist = contestList

        i = 0
        for contest in contestList:
            options.append(discord.SelectOption(label=contest["name"], emoji='🏆', value=contest["name"]))
            i += 1
        super().__init__(placeholder='Pick a contest here', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        chosenContest = self.values[0]
        self.view.chosenContest = chosenContest
        await interaction.response.send_message(f"{chosenContest} is chosen!")

class contestView(discord.ui.View):
    def __init__(self, contestList):
        super().__init__()
        self.contestList = contestList
        # Adds the dropdown to our view object.
        self.add_item(contestSelect(contestList))

















async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(contestFunctions(bot))