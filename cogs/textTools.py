import discord, configparser, random, platform, asyncio
from discord.ext import commands
from discord import app_commands
from cogs.SQLfunctions import SQLfunctions
errorList = ["I was not expecting to be served *this* conglomeration of exceptionally confused atomic matter."]



class textTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if message.author.id == self.bot.user.id:
    #         return
    #     try:
    #         # output = [dict(row) for row in await SQLfunctions.databaseFetch(f"SELECT response FROM autoresponderlist WHERE serverid = '{message.guild.id}' AND prompt = '{await textTools.sanitize(message.content.lower())}'")][0]["response"]
    #         valuesIn = [message.guild.id, message.content.lower()]
    #         output = await SQLfunctions.databaseFetchDynamic(f"SELECT response FROM autoresponderlist WHERE serverid = $1 AND prompt = $2 LIMIT 1", valuesIn)
    #         await message.channel.send(output[0]["response"])
    #     except Exception:
    #         pass
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
        await ctx.send("## Done!")

    async def retrieveError(ctx: commands.Context):
        errorDict = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT error FROM errorlist')]
        print(errorDict)
        errorList = []
        for error in errorDict:
            errorList.append(error["error"])
        return random.choice(errorList)


    async def addLine(inputOne: str, inputTwo: str):
        return f"{inputOne}\n{inputTwo}"

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(textTools(bot))

