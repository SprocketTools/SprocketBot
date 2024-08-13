import discord, configparser, random, platform, asyncio
from discord.ext import commands
from discord import app_commands

import main
from cogs.SQLfunctions import SQLfunctions
class errorFunctions(commands.Cog):
    errorList = []
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @commands.command(name="resetErrorConfig", description="Reset everyone's server configurations")
    async def resetErrorConfig(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = "DROP TABLE IF EXISTS errorlist"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS errorlist (
                              error TEXT);''')
        await SQLfunctions.databaseExecute(prompt)
        await ctx.send("Done!  Now go add some errors in.")


    @commands.command(name="getError", description="higdffffffffffff")
    async def getError(self, ctx: commands.Context):
        if ctx.author.id == main.ownerID:
            await ctx.message.delete()

        await ctx.send(await errorFunctions.retrieveError(ctx))


    @commands.command(name="addError", description="higdffffffffffff")
    async def addError(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        responseMessage = "This is not supposed to happen!"
        await ctx.send("Type out your error message and send it.")

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responseMessage = msg.content
            print(responseMessage)
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return
        values = [responseMessage]
        await SQLfunctions.databaseExecuteDynamic(f'INSERT INTO errorlist VALUES ($1);', values)
        errorDict = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT error FROM errorlist')]
        errorFunctions.errorList = []
        for error in errorDict:
            errorFunctions.errorList.append(error["error"])
        await ctx.send("## Done!")

    async def getResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check)
            return msg.content
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))

    async def retrieveError(ctx: commands.Context):
        if len(errorFunctions.errorList) == 0:
            errorDict = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT error FROM errorlist')]
            for error in errorDict:
                errorFunctions.errorList.append(error["error"])
        return random.choice(errorFunctions.errorList)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(errorFunctions(bot))