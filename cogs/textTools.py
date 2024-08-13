import discord, configparser, random, platform, asyncio
from discord.ext import commands
from cogs.errorFunctions import errorFunctions
from discord import app_commands
class textTools(commands.Cog):
    errorList = []
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def sanitize(inputPhrase: str):
        sanitizeKeywords = ["@", "/", ";", "invalid_tank"]
        outputPhrase = inputPhrase
        for phrase in sanitizeKeywords:
          outputPhrase = outputPhrase.replace(phrase, "")
        return outputPhrase

    async def mild_sanitize(inputPhrase: str):
        sanitizeKeywords = ["@", "invalid_tank"]
        outputPhrase = inputPhrase
        for phrase in sanitizeKeywords:
            outputPhrase = outputPhrase.replace(phrase, "")
        return outputPhrase

    async def getSQLprompt(inputList: list):
        names = list(inputList.keys())
        values = list(inputList.values())
        names_string = str(names[0])
        values_string = "'" + str(values[0]) + "'"
        i = 1
        while i < len(names):
            names_string = names_string + f', {names[i]}'
            values_string = values_string + f", '{values[i]}'"
            i += 1
        #print(names_string)
        #print(values_string)
        return names_string, values_string

    async def getResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check)
            return msg.content
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))

    async def getIntResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check)
            return int(msg.content)
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))

    async def getFileResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check)
            return msg.attachments[0]
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))

    async def getResponseThenDelete(ctx: commands.Context, prompt):
        messageOut = await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check)
            outVal = msg.content
            await msg.delete()
            return outVal
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))
        await messageOut.delete()

    async def generateCampaignKey(self, ctx: commands.Context):
        await ctx.send(f"Type out the campaign key you wish to use.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check)
            return msg.content
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return ""

    async def addLine(inputOne: str, inputTwo: str):
        return f"{inputOne}\n{inputTwo}"

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(textTools(bot))

