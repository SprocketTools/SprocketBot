import discord, configparser, random, platform, asyncio
from discord.ext import commands
from discord import app_commands
from discord.ui import view

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
                              error TEXT, status BOOLEAN);''')
        await SQLfunctions.databaseExecute(prompt)
        await ctx.send("Done!  Now go add some errors in.")


    @commands.command(name="getError", description="higdffffffffffff")
    async def getError(self, ctx: commands.Context):
        if ctx.author.id == main.ownerID:
            await ctx.message.delete()
        else:
            serverID = (ctx.guild.id)
            try:
                channel = int([dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
                if ctx.channel.id != channel:
                    await ctx.send(f"This command is restricted to <#{channel}>")
                    return
            except Exception:
                    error = await errorFunctions.retrieveError(ctx)
                    await ctx.send(f"{error}\n\nUtility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
                    return
        await ctx.send(await errorFunctions.retrieveError(ctx))

    @commands.command(name="removeError", description="higdffffffffffff")
    async def removeError(self, ctx: commands.Context):
        if ctx.author.id != 712509599135301673:
            return
        errorMessage = await errorFunctions.getTextResponse(ctx, "What error message do you want to remove?")
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''', [errorMessage])
        await ctx.send("Deleted!  Reload the cogs.")

    @commands.command(name="addError", description="higdffffffffffff")
    async def addError(self, ctx: commands.Context):

        if ctx.author.id == 712509599135301673:
            status = True
        else:
            status = False
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
        values = [responseMessage, status, ctx.author.id]
        await SQLfunctions.databaseExecuteDynamic(f'INSERT INTO errorlist VALUES ($1, $2, $3);', values)
        errorDict = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT error FROM errorlist WHERE status = true;')]
        errorFunctions.errorList = []
        for error in errorDict:
            errorFunctions.errorList.append(error["error"])
        await ctx.send("## Done!")
        if status == False:
            await ctx.send("This error message has been sent off for approval.")


    @commands.command(name="countErrors", description="higdffffffffffff")
    async def countErrors(self, ctx: commands.Context):
        totalErrors = len(await SQLfunctions.databaseFetchdict(f'SELECT error FROM errorlist;'))
        await ctx.send(f"There are {totalErrors} errors registered with the bot!")
        totalErrors = len(await SQLfunctions.databaseFetchdict(f'SELECT error FROM errorlist WHERE status = false;'))
        await ctx.send(f"{totalErrors} of these errors are unapproved.")
        totalErrors = len(await SQLfunctions.databaseFetchdict(f'SELECT error FROM errorlist WHERE status = true;'))
        await ctx.send(f"{totalErrors} of these errors are approved.")

    @commands.command(name="approveErrors", description="higdffffffffffff")
    async def approveErrors(self, ctx: commands.Context):

        if ctx.author.id != main.ownerID:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("You aren't authorized to run this command!")
            return
        errorDict = await SQLfunctions.databaseFetchdict('''SELECT * FROM errorlist WHERE status = false;''')
        print(errorDict)
        for error in errorDict:
            view = YesNoMaybeButtons()
            await ctx.send(content=f"Submitter: <@{error['userid']}>\nError message: {error['error']}", view=view)
            await view.wait()
            if view.value == 1:
                await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET status = true WHERE error = $1;''', [error["error"]])
                await ctx.send("Added!")
                recipient = self.bot.get_user(int(error["userid"]))
                await recipient.send(f"Your error message:\n{error['error']}\nHas been added to the catalog!  Thanks for the submission!")

            if view.value == 2:
                newMessage = await errorFunctions.getTextResponse(ctx, "What do you want the modified error message to be?")
                await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''', [error["error"]])
                await SQLfunctions.databaseExecuteDynamic('''INSERT INTO errorlist VALUES ($1, $2, $3);''',[newMessage, True, error["userid"]])
                await ctx.send("Modified message added!")
                recipient = self.bot.get_user(int(error["userid"]))
                await recipient.send(f"Your error message:\n{error['error']}\nwas modified to:\n{newMessage}\nIt has now entered the catalog.  Thanks for submitting it!")

            if view.value == 3:
                await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''', [error["error"]])
                await ctx.send("Deleted!")
                recipient = self.bot.get_user(int(error["userid"]))
                await recipient.send(f"Your error message:\n{error['error']}\nwas not accepted.")
        await ctx.send("All good here!")

    async def getTextResponse(ctx: commands.Context, prompt):
        await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check)
            return msg.content
        except Exception:
            await ctx.send(await errorFunctions.retrieveError(ctx))





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
            errorDict = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT error FROM errorlist WHERE status = true;')]
            for error in errorDict:
                errorFunctions.errorList.append(error["error"])
        return random.choice(errorFunctions.errorList)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(errorFunctions(bot))

class YesNoMaybeButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.value = None
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def callbackYes(self, a, b):
        self.value = 1
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="Modify", style=discord.ButtonStyle.gray)
    async def callbackModify(self, a, b):
        self.value = 2
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def callbackNo(self, a, b):
        self.value = 3
        await a.response.defer()
        self.stop()