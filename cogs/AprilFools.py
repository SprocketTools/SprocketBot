import discord, asyncio, random
from discord.ext import commands
# Github config

from cogs.textTools import textTools

import difflib

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
        await self.bot.sql.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS codeconfig (
                              serverid BIGINT,
                              channelid BIGINT,
                              logid BIGINT,
                              message TEXT,
                              solved BIGINT);''')
        await self.bot.sql.databaseExecute(prompt)

        prompt = "DROP TABLE IF EXISTS errorcodemessages"
        await self.bot.sql.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS errorcodemessages (
                              errorcode VARCHAR);''')
        await self.bot.sql.databaseExecute(prompt)

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

        await ctx.send("Where do you want posts to be logged to?  Reply to this message with a mention of that channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["logid"] = msg.channel_mentions[0].id
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
        await self.bot.sql.databaseExecute(f'''DELETE FROM codeconfig WHERE serverid = {ctx.guild.id};''')
        await self.bot.sql.databaseExecute(f'''INSERT INTO codeconfig ({keystr}) VALUES ({valuestr});''')



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
        await self.bot.sql.databaseExecute(
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
        codeConfigList = [dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM codeconfig WHERE serverid = {serverID}')][0]
        position = int(codeConfigList['solved'])
        channel = int(codeConfigList['channelid'])
        if msgChannel != channel:
            return
        the_words = codeConfigList['message'].split(" ")
        print(the_words)
        the_bool = False
        try:
            print(len(message.attachments))
            if message.content.lower() == the_words[position].lower() and len(message.attachments) == 0:
                the_bool = True
        except Exception:
            pass
        if the_bool == True:
            await message.add_reaction('✅')
            #await message.author.send('Correct!')
            await self.bot.sql.databaseExecute(f'''UPDATE codeconfig SET solved = {position + 1} WHERE serverid = {serverID};''')
            if position + 1 == len(the_words):
                await message.channel.send("## Congrats!  \nThe puzzle has been solved!\nGreat job everyone.")
        else:
            codeList = ["This meme has been removed due to voiding my patented content filter."]
            ConfigList = [dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM errorcodemessages')]
            for row in ConfigList:
                codeList.append(row["errorcode"])
            await self.bot.get_channel(int(codeConfigList['logid'])).send(f"From <@{message.author.id}>: `" + message.content + "`")
            for attachm in message.attachments:
                await self.bot.get_channel(int(codeConfigList['logid'])).send(attachm)
            funny_response = await self.bot.error.retrieveCategorizedError(message, category="catgirl")
            try:
                ratio = difflib.SequenceMatcher(None, message.content.lower(), the_words[position].lower()).ratio()
                if ratio > 0.1:
                    funny_response = funny_response + (f"\n**Similarity of '{message.content}': {round(ratio*100)}%**\nDifference: {abs(len(message.content) - len(the_words[position]))}")
                if random.random() < 0.05:
                    try:
                        funny_response = funny_response + (f"\nTry the letter {the_words[position][0]}!")
                    except Exception:
                        pass
                if random.random() > 0.95:
                    try:
                        funny_response = funny_response + (f"\nTry the letter {the_words[position][len(the_words[position])]} at the end!")
                    except Exception:
                        pass
            except Exception:
                pass
            await message.reply(funny_response, delete_after=20)
            await asyncio.sleep(5)
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
        await self.bot.sql.databaseExecuteDynamic(f'''UPDATE codeconfig SET message = $1 WHERE serverid = $2;''', [responseOut, ctx.guild.id])
        await ctx.send("## Done!")

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(AprilFools(bot))

