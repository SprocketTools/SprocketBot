import datetime
import sys

import discord, configparser, random, platform, asyncio, re
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
        pattern = r'[^a-zA-Z0-9\s\!\#\$\%\^\:\&\*\(\)\+\=\-_\|\<\>\?,\.;:\']'
        outputPhrase = re.sub(pattern, '', outputPhrase)
        outputPhrase = outputPhrase.strip()
        # ^\x00-\x7f
        return outputPhrase

    @commands.command(name="sanitizeTest", description="Ask Hamish a question.")
    async def sanitizeTest(self, ctx: commands.Context, *, testString):
        await ctx.send(await textTools.sanitize(testString))

    async def mild_sanitize(inputPhrase: str):
        sanitizeKeywords = ["@", ";"]
        outputPhrase = inputPhrase
        for phrase in sanitizeKeywords:
            outputPhrase = outputPhrase.replace(phrase, "")
        return outputPhrase

    async def getUnixTimestamp(inStr: datetime.datetime):
        date_string = str(inStr).split('.')[0]
        format_string = "%Y-%m-%d %H:%M:%S"
        return int(datetime.datetime.strptime(date_string, format_string).timestamp())

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
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
            raise ValueError("User termination")
        return await textTools.mild_sanitize(msg.content)

    async def sendThenDelete(ctx: commands.Context, prompt):
        message = await ctx.reply(prompt)
        await asyncio.sleep(15)
        await message.delete()

    async def getCappedResponse(ctx: commands.Context, prompt, leng):
        while True:
            await ctx.send(prompt)
            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
            msg = await ctx.bot.wait_for('message', check=check, timeout=900)
            if msg.content.lower() == "cancel":
                await errorFunctions.sendError(ctx)
                raise ValueError("User termination")
            if len(msg.content) <= leng:
                return await textTools.mild_sanitize(msg.content)
            await errorFunctions.sendError(ctx)
            await ctx.send(f"Error: response should not exceed {leng} characters in length.")

    async def getIntResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
            raise ValueError("User termination")
        textOut = msg.content.replace(",", "")
        textSplit = textOut.split(".")
        if len(textSplit) > 1:
            await ctx.send(f"Interpreting input as {textSplit[0]}")
        return int(textSplit[0])


    async def getFlooredIntResponse(ctx: commands.Context, prompt: str, min: int):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
            raise ValueError("User termination")
        textOut = msg.content.replace(",", "")
        textSplit = textOut.split(".")
        val = int(textSplit[0])
        if len(textSplit) > 1:
            await ctx.send(f"Interpreting input as {textSplit[0]}")
        if val < min:
            return min
        return val

    async def getFlooredFloatResponse(ctx: commands.Context, prompt: str, min: int):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
            raise ValueError("User termination")
        val = float(msg.content)
        val = round(val, 7)
        if val < min:
            return min
        return val


    async def getFloatResponse(ctx: commands.Context, prompt: str):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
            raise ValueError("User termination")
        return round(float(msg.content), 7)

    async def getPercentResponse(ctx: commands.Context, prompt: str):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        response = msg.content.replace("%", "")
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
            raise ValueError("User termination")
        value = float(response)/100
        return round(value, 6)

    async def getChannelResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
            raise ValueError("User termination")
        if str(msg.channel_mentions) == '[]':
            if "https://discord.com/channels/" in msg.content:
                return int(msg.content.split("/")[-2])
            else:
                raise ValueError("User termination")
        return int(msg.channel_mentions[0].id)


    async def getRoleResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        while True:
            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
            msg = await ctx.bot.wait_for('message', check=check, timeout=900)
            if msg.content.lower() == "cancel":
                await errorFunctions.sendError(ctx)
                raise ValueError("User termination")
            try:
                return int(msg.content)
            except Exception:
                if len(msg.role_mentions) > 0:
                    return int(msg.role_mentions[0].id)
            await ctx.send("Try again.  Send either a ping of the role or its ID.")

    async def getFileResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
        return msg.attachments[0]

    async def getFileURLResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
        return msg.attachments[0].url

    async def getManyFilesResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
        return msg.attachments

    async def getResponseThenDelete(ctx: commands.Context, prompt):
        messageOut = await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            await errorFunctions.sendError(ctx)
            raise ValueError("User termination")
        outVal = msg.content
        await msg.delete()
        await messageOut.delete()
        return outVal

    async def generateCampaignKey(self, ctx: commands.Context):
        await ctx.send(f"Type out the campaign key you wish to use.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=900)
            return msg.content
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return ""

    async def addLine(inputOne: str, inputTwo: str):
        return f"{inputOne}\n{inputTwo}"

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(textTools(bot))

