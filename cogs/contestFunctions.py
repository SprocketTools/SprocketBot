import discord
from discord.ext import commands
from discord import app_commands
import json
from cogs.textTools import textTools
from cogs.SQLfunctions import SQLfunctions
class contestFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="resetAllContests", description="Reset all bot contests.")
    async def resetAllContests(self, ctx: commands.Context):
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
                              crossServer BOOL);''')
        await SQLfunctions.databaseExecute(prompt)
        prompt = '''select * from db.contests where condition = 1;'''
        print(await SQLfunctions.databaseExecute(prompt))
        await ctx.send("Contest datasheet wiped!")

    @commands.command(name="adminExecute", description="register a contest")
    async def adminExecute(self, ctx: commands.Context, *, prompt):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        await ctx.send(await SQLfunctions.databaseExecute(prompt))

    @commands.command(name="adminFetch", description="register a contest")
    async def adminExecute(self, ctx: commands.Context, *, prompt):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return

        result = await SQLfunctions.databaseFetch(prompt)
        print(result)
        await ctx.send(result)



    @commands.command(name="registerContest", description="register a contest")
    async def registerContest(self, ctx: commands.Context):
        await ctx.send("Beginning processing now.")
        contestHostID = ctx.author.id
        for attachment in ctx.message.attachments:
            fileData = json.loads(await attachment.read())
            contestName = fileData["contestName"]
            contestName = await textTools.sanitize(contestName)
            allowWriting = True
            try:
                if contestsList["contests"][contestName]["contestHost"] != contestHostID:
                    await ctx.send(f"Someone else already has a contest registered under this name!")
                    allowWriting = False
            except Exception:
                pass
            if allowWriting == True:
                submitDirectory = TANKrepository + f"{contestName}"
                Path(submitDirectory).mkdir(parents=True, exist_ok=True)
                contestsList["contests"][contestName] = fileData
                contestsList["contests"][contestName]["categories"] = {}
                contestsList["contests"][contestName]["submissions"] = {}
                contestsList["contests"][contestName]["contestHost"] = contestHostID
                contestsList["contests"][contestName]["acceptEntries"] = "False"

                # create logging channel
                channel = bot.get_channel(ctx.channel.id)
                thread = await channel.create_thread(
                    name=contestName,
                    type=discord.ChannelType.private_thread
                )
                contestsList["loggingChannel"][contestName] = thread.id

                # await backupFiles()
                await thread.send(
                    f"<@{contestHostID}>, the {contestName} is now registered!  Submissions are turned off for now - enable them once you are ready.  Once you do enable submissions, they will be logged here.")



async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(contestFunctions(bot))