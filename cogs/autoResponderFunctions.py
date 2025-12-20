import discord, asyncio
from discord.ext import commands
import type_hints
class autoResponderFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.command(name="resetHelpConfig", description="Reset everyone's server configurations")
    async def resetHelpConfig(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = "DROP TABLE IF EXISTS sprockethelplist"
        await self.bot.sql.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS sprockethelplist (
                              prompt TEXT,
                              serverid BIGINT,
                              response TEXT);''')
        await self.bot.sql.databaseExecute(prompt)
        await ctx.send("Done!  Now go add some help answers in.")

    @commands.command(name="addHelpResponse", description="Add a help button")
    async def addHelpResponse(self, ctx: commands.Context):
        contestList = [dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {ctx.guild.id}')][0]
        if str(contestList["botmanagerroleid"]) not in str(ctx.author.roles):
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        await ctx.send("What will the help entry be titled?")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            promptMessage = msg.content.lower()
        except asyncio.TimeoutError:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return

        await ctx.send("What is your response message going to be?")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responseMessage = msg.content
            print(responseMessage)
        except asyncio.TimeoutError:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return

        values = [promptMessage, ctx.guild.id, responseMessage]

        await self.bot.sql.databaseExecuteDynamic(f'INSERT INTO sprockethelplist VALUES ($1, $2, $3);', values)
        await ctx.send("## Done!")

    @commands.command(name="removeHelpResponse", description="Add a help button")
    async def removeHelpResponse(self, ctx: commands.Context):
        await ctx.send("Beginning processing now...")
        contestList = [dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT botmanagerroleid FROM serverconfig WHERE serverid = {ctx.guild.id}')][0]
        print(contestList)
        if str(contestList["botmanagerroleid"]) not in str(ctx.author.roles):
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        helpList = [dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM sprockethelplist')]
        helpPrompts = []
        for prompt in helpList:
            helpPrompts.append(prompt["prompt"])
        userPrompt = "What entry are you looking to remove?"
        promptMessage = await ctx.bot.ui.getChoiceFromList(ctx, helpPrompts, userPrompt)
        values = [promptMessage]
        await self.bot.sql.databaseExecuteDynamic(f'DELETE FROM sprockethelplist WHERE prompt = $1;', values)
        await ctx.send("## Done!")

    @commands.command(name="SprocketHelp", description="Add a help button")
    async def SprocketHelp(self, ctx: commands.Context):
        helpList = [dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM sprockethelplist')]
        helpPrompts = []
        for prompt in helpList:
            helpPrompts.append(prompt["prompt"])
        userPrompt = "What do you need help with today?"
        selection = await ctx.bot.ui.getChoiceFromList(ctx, helpPrompts, userPrompt)
        helpResults = {}
        for prompt in helpList:
            helpResults[prompt["prompt"]] = prompt["response"]
        await ctx.send(helpResults[selection])



async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(autoResponderFunctions(bot))

