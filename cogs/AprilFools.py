import discord, os, platform, asyncio, random
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from git import Repo
# Github config
from pathlib import Path
from cogs.textTools import textTools
from cogs.SQLfunctions import SQLfunctions
from cogs.blueprintFunctions import blueprintFunctions
from cogs.discordUIfunctions import discordUIfunctions


if platform.system() == "Windows":
    GithubURL = "https://github.com/SprocketTools/SprocketTools.github.io"
    GithubDirectory = "C:\\Users\\colson\\Documents\\GitHub\\Testing\\SprocketTools.github.io"
    OSslashLine = "\\"

else:
    # default settings (running on Rasbian)
    GithubURL = "https://github.com/SprocketTools/SprocketTools.github.io"
    GithubDirectory = "/home/mumblepi/SprocketTools.github.io"
    OSslashLine = "/"
imgCatalogFolder = "img"
imgCandidateFolder = "imgbin"

Path(GithubDirectory).mkdir(parents=True, exist_ok=True)
try:
    repo = Repo.clone_from(GithubURL, GithubDirectory)
except Exception:
    repo = Repo(GithubDirectory)

memePhrase = "The covenanter is the best tank."



class AprilFools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="resetCodeConfigs", description="Reset all bot contests.")
    async def resetCodeConfigs(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = "DROP TABLE IF EXISTS codeconfig"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS codeconfig (
                              serverID BIGINT,
                              channelID BIGINT,
                              message TEXT,
                              solved BIGINT);''')
        await SQLfunctions.databaseExecute(prompt)

        prompt = "DROP TABLE IF EXISTS errorcodemessages"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS errorcodemessages (
                              errorcode VARCHAR);''')
        await SQLfunctions.databaseExecute(prompt)

        await ctx.send("Code configs are wiped!")

    @commands.command(name="codeSetup", description="setup the server's code Puzzle")
    async def codeSetup(self, ctx: commands.Context):
        if ctx.author.guild_permissions.administrator == True:
            pass
        else:
            return
        responses = {}
        responses["serverid"] = ctx.guild.id
        responses["solved"] = 0

        await ctx.send("Before we begin: it is recommended to run this command in an admin channel, as you will be asked to enter information not meant to be visible.  Reply with 'continue' if this is an appropriate channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            if msg.content.lower() == "continue":
                pass
            else:
                return
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("Awesome!  Let's get started. \n\nWhat is your event chat?  Reply to this message with a mention of that channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["channelid"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What is your code phrase?")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["message"] = msg.content
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("## All data successfully collected!\nBeginning processing now...")
        keystr, valuestr = await textTools.getSQLprompt(responses)
        await SQLfunctions.databaseExecute(f'''DELETE FROM codeconfig WHERE serverid = {ctx.guild.id};''')
        await SQLfunctions.databaseExecute(f'''INSERT INTO codeconfig ({keystr}) VALUES ({valuestr});''')



        await ctx.send("## Done!")

    @commands.command(name="cog12", description="lol")
    async def cog12(self, ctx):
        await ctx.send(content="Hello!")

    @commands.command(name="resetCodeProgress", description="Reset the puzzle")
    async def resetCodeProgress(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        await SQLfunctions.databaseExecute(
            f'''UPDATE codeconfig SET solved = {0} WHERE serverid = {ctx.guild.id};''')
        await ctx.send('## Reset!')


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != self.bot.user.id:
            pass
        else:
            return
        serverID = message.guild.id
        msgChannel = message.channel.id
        codeConfigList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM codeconfig WHERE serverid = {serverID}')][0]
        position = int(codeConfigList['solved'])
        channel = int(codeConfigList['channelid'])
        if msgChannel != channel:
            return
        the_words = codeConfigList['message'].split(" ")
        print(the_words)
        if(message.content.lower() == the_words[position].lower()):
            await message.author.send('Correct!')
            await SQLfunctions.databaseExecute(f'''UPDATE codeconfig SET solved = {position + 1} WHERE serverid = {serverID};''')
        else:
            codeList = ["This meme has been removed due to voiding Sprocket Bot's patented content filter."]
            ConfigList = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM errorcodemessages')]
            for row in ConfigList:
                codeList.append(row["errorcode"])
            print(codeList)
            random_val = random.randrange(0, len(codeList))
            funny_response = codeList[random_val]

            await self.bot.get_channel(msgChannel).send(funny_response, delete_after=15)
            await message.delete()

    @commands.command(name="IAmError", description="setup the server's code Puzzle")
    async def IAmError(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        responseOut = ""
        await ctx.send("What is your phrase?")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responseOut = msg.content
            print(responseOut)
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("## All data successfully collected!\nBeginning processing now...")
        await SQLfunctions.databaseExecute(f'''INSERT INTO errorcodemessages (errorcode) VALUES ('{responseOut}');''')
        await ctx.send("## Done!")

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(AprilFools(bot))

