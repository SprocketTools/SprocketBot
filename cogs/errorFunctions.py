from datetime import datetime

import discord, configparser, random, platform, asyncio, re
from discord.ext import commands
from discord import app_commands
from discord.ui import view

import main
from cogs.SQLfunctions import SQLfunctions
from cogs.discordUIfunctions import discordUIfunctions


class errorFunctions(commands.Cog):
    errorList = []
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @commands.command(name="resetErrorConfig", description="Reset everyone's server configurations")
    async def resetErrorConfig(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        prompt = "DROP TABLE IF EXISTS errorlist"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS errorlist (error TEXT, status BOOLEAN, userid BIGINT);''')
        await SQLfunctions.databaseExecute(prompt)
        await ctx.send("Done!  Now go add some errors in.")

    @commands.command(name="getError", description="higdffffffffffff")
    async def getError(self, ctx: commands.Context):
        ttsp = False
        if ctx.author.id == main.ownerID or ctx.author.guild_permissions.administrator == True:
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
        if random.random() < 0.001:
            ttsp = True
        await ctx.send(await errorFunctions.retrieveError(ctx), tts=ttsp)

    @commands.command(name="getCError", description="higdffffffffffff")
    async def getCategorizedError(self, ctx: commands.Context):
        await ctx.send("What would you categorize this error under?")
        categories = [["Compliment", "compliment"], ["Insult", "insult"], ["Sprocket", "sprocket"],
                      ["Flyout", "flyout"], ["Video", "video"], ["GIF", "gif"], ["Joke/other", "joke"],
                      ["Campaign", "campaign"], ["Blueprint", "blueprint"],
                      ["Only a catgirl would say that", "catgirl"]]
        category = await discordUIfunctions.getButtonChoiceReturnID(ctx, categories)
        ttsp = False
        if ctx.author.id == main.ownerID or ctx.author.guild_permissions.administrator == True:
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
        if random.random() < 0.001:
            ttsp = True
        await ctx.send(await errorFunctions.retrieveCategorizedError(ctx, category), tts=ttsp)

    @commands.command(name="removeError", description="higdffffffffffff")
    async def removeError(self, ctx: commands.Context):
        errorMessage = await errorFunctions.getTextResponse(ctx, "What error message do you want to remove?")
        if ctx.author.id == 712509599135301673:
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''', [errorMessage])
        else:
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1 AND userid = $2;''', [errorMessage, ctx.author.id])
        await ctx.send("Deleted any that match.  Reload the cogs.")

    @commands.command(name="addError", description="higdffffffffffff")
    async def addError(self, ctx: commands.Context):

        if ctx.author.id == main.ownerID and main.botMode == "official":
            status = True
        else:
            status = False
        responseMessage = "This is not supposed to happen!"
        await ctx.send("Type out your error message and send it.\n-# To learn more about this command, click [here](<https://github.com/SprocketTools/SprocketBot/blob/main/TOOLS.md>)")

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responseMessage = msg.content
            print(responseMessage)
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return
        if len(responseMessage) > 1024:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("This error message is too big.  Please trim the length down and try again.")
        if "https://www.youtube.com/" in responseMessage or "https://youtu.be/" in responseMessage:
            category = "video"
        elif ".gif" in responseMessage and "https://" in responseMessage:
            category = "gif"
        elif "tenor.com" in responseMessage or "giphy" in responseMessage:
            category = "gif"
        else:
            await ctx.send("What would you categorize this error under?")
            categories = [["Compliment", "compliment"], ["Insult", "insult"], ["Sprocket", "sprocket"], ["Flyout", "flyout"], ["Joke/other", "joke"], ["Campaign", "campaign"], ["Blueprint", "blueprint"], ["Only a catgirl would say that", "catgirl"]]
            category = await discordUIfunctions.getButtonChoiceReturnID(ctx, categories)
        values = [responseMessage, status, ctx.author.id, category]
        await SQLfunctions.databaseExecuteDynamic(f'INSERT INTO errorlist VALUES ($1, $2, $3, $4);', values)
        errorDict = [dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT error FROM errorlist WHERE status = true;')]
        errorFunctions.errorList = []
        for error in errorDict:
            errorFunctions.errorList.append(error["error"])
        await ctx.send("## Done!")
        if status == False:
            await ctx.send("This error message has been sent off for approval.")

    @commands.command(name="adminSetErrortype", description="add a column to a SQL table")
    async def adminSetErrortype(self, ctx: commands.Context):
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1''', ["joke"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($1 in error) > 0''', ["blueprint"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["blueprint", "Blueprint"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($1 in error) > 0''', ["sprocket"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["sprocket", "Sprocket"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($1 in error) > 0''', ["flyout"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["flyout", "Flyout"])

        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["gif", ".gif"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["gif", ".mp4"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["gif", "tenor.com"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["gif", "giphy"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["video", "https://youtu.be"])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET errortype = $1 WHERE POSITION($2 in error) > 0''', ["video", "https://youtube.com/"])
        await ctx.send("## Done!")

    @commands.command(name="errorLeaderboard", description="Leaderboard of errors!")
    async def errorLeaderboard(self, ctx: commands.Context):
        totalErrors = len(await SQLfunctions.databaseFetchdict(f'SELECT error FROM errorlist;'))
        embed = discord.Embed(title="Error Stats", description=f'''There are {totalErrors} error messages in the bot's collection!''',color=discord.Color.random())
        userSetList = await SQLfunctions.databaseFetchdict(f'''SELECT userid, COUNT(userid) AS value_occurrence FROM errorlist GROUP BY userid ORDER BY value_occurrence DESC LIMIT 5;''')
        for user in userSetList:
            embed.add_field(name=self.bot.get_user(user['userid']), value=user['value_occurrence'], inline=False)
        currentUser = (await SQLfunctions.databaseFetchdictDynamic(f'''SELECT userid, COUNT(userid) AS value_occ FROM errorlist WHERE userid = $1 GROUP BY userid;''', [ctx.author.id]))[0]['value_occ']
        print(currentUser)
        embed.set_footer(text=f"You have {currentUser} errors registered with the bot!")
        await ctx.send(embed=embed)

    @commands.command(name="countErrors", description="higdffffffffffff")
    async def countErrors(self, ctx: commands.Context):
        totalErrors = len(await SQLfunctions.databaseFetchdict(f'SELECT error FROM errorlist;'))
        await ctx.send(f"There are {totalErrors} errors registered with the bot!")
        totalErrors = len(await SQLfunctions.databaseFetchdict(f'SELECT error FROM errorlist WHERE status = false;'))
        await ctx.send(f"{totalErrors} of these errors are unapproved.")
        totalErrors = len(await SQLfunctions.databaseFetchdict(f'SELECT error FROM errorlist WHERE status = true;'))
        await ctx.send(f"{totalErrors} of these errors are approved.")

    @commands.command(name="testText", description="higdffffffffffff")
    async def testText(self, ctx: commands.Context, *, error):
        error = error.replace('{user}', ctx.author.display_name)
        error = error.replace('{server}', ctx.guild.name)
        error = error.replace('{second}', str(datetime.now().strftime('%S')))
        error = error.replace('{minute}', str(datetime.now().strftime('%M')))
        error = error.replace('{hour}', str(datetime.now().strftime('%I')))
        error = error.replace('{meridian}', datetime.now().strftime('%p'))
        error = error.replace('{day}', datetime.now().strftime('%A'))
        error = error.replace('{month}', datetime.now().strftime('%B'))
        error = error.replace('{year}', datetime.now().strftime('%Y'))
        error = error.replace('@', '')
        await ctx.send(error)

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
            await ctx.send(content=f"Submitter: <@{error['userid']}>\nCategory: {error['errortype']}\nError message:")
            str = error['error'][:1000]
            if len(str) < 2:
                await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''',[error["error"]])
                await ctx.send("Deleted!")
                recipient = self.bot.get_user(int(error["userid"]))
                await recipient.send(
                    f"Your error message:\n{error['error']}\nwas removed automatically.  Images by themselves can't be processed by the bot.  Try resubmitting as a URL instead.")
            else:
                await ctx.send(str)
                url_pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, str)
                urls = list(set(urls))
                for url in urls:
                    if f"<{url}>" in str:
                        await ctx.send(url)
                categories = ["Approve", "Deny", "Modify text", "Modify category", "Modify both", "Stop processing errors"]
                value = await discordUIfunctions.getButtonChoice(ctx, categories)

                if value == "Approve":
                    await SQLfunctions.databaseExecuteDynamic('''UPDATE errorlist SET status = true WHERE error = $1;''', [error["error"]])
                    await ctx.send("Added!")
                    recipient = self.bot.get_user(int(error["userid"]))
                    await recipient.send(f"Your error message:\n{error['error']}\nHas been added to the catalog!  Thanks for the submission!")

                elif value == "Modify text":
                    newMessage = await errorFunctions.getTextResponse(ctx, "What do you want the modified error message to be?")
                    await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''', [error["error"]])
                    await SQLfunctions.databaseExecuteDynamic('''INSERT INTO errorlist VALUES ($1, $2, $3, $4);''',[newMessage, True, error["userid"], error["errortype"]])
                    await ctx.send("Modified message added!")
                    recipient = self.bot.get_user(int(error["userid"]))
                    await recipient.send(f"Your error message:\n{error['error']}\nwas modified to:\n{newMessage}\nIt has now entered the catalog.  Thanks for submitting it!")

                elif value == "Modify category":
                    await ctx.send("What would you categorize this error under?")
                    categories = [["Compliment", "compliment"], ["Insult", "insult"], ["Sprocket", "sprocket"],["Flyout", "flyout"], ["Video", "video"], ["GIF", "gif"], ["Joke/other", "joke"],["Campaign", "campaign"], ["Blueprint", "blueprint"],["Only a catgirl would say that", "catgirl"]]
                    category = await discordUIfunctions.getButtonChoiceReturnID(ctx, categories)
                    await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''', [error["error"]])
                    await SQLfunctions.databaseExecuteDynamic('''INSERT INTO errorlist VALUES ($1, $2, $3, $4);''',[error["error"], True, error["userid"], category])
                    await ctx.send("Modified message added!")
                    recipient = self.bot.get_user(int(error["userid"]))
                    await recipient.send(f"Your error message:\n{error['error'][:800]}\nwas modified to the category:\n{category}\nIt has now entered the catalog.  Thanks for submitting it!")

                elif value == "Modify both":
                    newMessage = await errorFunctions.getTextResponse(ctx, "What do you want the modified error message to be?")
                    await ctx.send("What would you categorize this error under?")
                    categories = [["Compliment", "compliment"], ["Insult", "insult"], ["Sprocket", "sprocket"], ["Flyout", "flyout"], ["Video", "video"], ["GIF", "gif"], ["Joke/other", "joke"], ["Campaign", "campaign"], ["Blueprint", "blueprint"], ["Only a catgirl would say that", "catgirl"]]
                    category = await discordUIfunctions.getButtonChoiceReturnID(ctx, categories)
                    await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''', [error["error"]])
                    await SQLfunctions.databaseExecuteDynamic('''INSERT INTO errorlist VALUES ($1, $2, $3, $4);''',[newMessage, True, error["userid"], category])
                    await ctx.send("Modified message added!")
                    recipient = self.bot.get_user(int(error["userid"]))
                    await recipient.send(f"Your error message:\n{error['error'][:800]}\nwas modified to:\n{newMessage}\n\nand modified to the category:\n{category}\n\nIt has now entered the catalog.  Thanks for submitting it!")

                elif value == "Deny":
                    await SQLfunctions.databaseExecuteDynamic('''DELETE FROM errorlist WHERE error = $1;''', [error["error"]])
                    await ctx.send("Deleted!")
                    recipient = self.bot.get_user(int(error["userid"]))
                    await recipient.send(f"Your error message:\n{error['error']}\nwas not accepted.")

                elif value == "Stop processing errors":
                    await ctx.send("### Lame... \nEnjoy your break I guess.")
                    return

                else:
                    return
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
        error = (await SQLfunctions.databaseFetchrow(f'SELECT error from errorlist WHERE status = true ORDER BY RANDOM() LIMIT 1;'))["error"]
        error = await errorFunctions.errorfyText(ctx, error)
        return error

    async def retrieveCategorizedError(ctx: commands.Context, category: str):
        error = (await SQLfunctions.databaseFetchrowDynamic(f'SELECT error from errorlist WHERE status = true AND errortype = $1 ORDER BY RANDOM() LIMIT 1;', [category]))["error"]
        error = await errorFunctions.errorfyText(ctx, error)
        return error

    async def sendCategorizedError(ctx: commands.Context, category: str):
        error = (await SQLfunctions.databaseFetchrowDynamic(f'SELECT error from errorlist WHERE status = true AND errortype = $1 ORDER BY RANDOM() LIMIT 1;', [category]))["error"]
        error = await errorFunctions.errorfyText(ctx, error)
        await ctx.send(error)
        return

    async def sendError(ctx: commands.Context):
        error = (await SQLfunctions.databaseFetchrow(f'SELECT error from errorlist WHERE status = true ORDER BY RANDOM() LIMIT 1;'))["error"]
        error = await errorFunctions.errorfyText(ctx, error)
        await ctx.send(error)
        return

    async def errorfyText(ctx: commands.Context, error):
        error = error.replace('{user}', ctx.author.display_name)
        error = error.replace('{server}', ctx.guild.name)
        error = error.replace('{second}', str(datetime.now().strftime('%S')))
        error = error.replace('{minute}', str(datetime.now().strftime('%M')))
        error = error.replace('{hour}', str(datetime.now().strftime('%I')))
        error = error.replace('{meridian}', datetime.now().strftime('%p'))
        error = error.replace('{day}', datetime.now().strftime('%A'))
        error = error.replace('{month}', datetime.now().strftime('%B'))
        error = error.replace('{year}', datetime.now().strftime('%Y'))
        error = error.replace('@', '')
        return error

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(errorFunctions(bot))

class YesNoMaybeButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.value = 0
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

    @discord.ui.button(label="Stop processing errors", style=discord.ButtonStyle.blurple)
    async def callbackStop(self, a, b):
        self.value = 4
        await a.response.defer()
        self.stop()