from google import genai
import time, io
import os, discord
from discord.ext import commands
import json, requests
import random, asyncio, datetime
from discord import Webhook
import aiohttp
import main
from cogs.textTools import textTools

serverConfig = {}
userStrikes = {}
nudeFlags = ["18+", "3.jpg", "3.png", "3.jpeg", "teen", "girls", "onlyfans", "hot", "nude", "e-womans", "plug", "invite", "free gifts", "gift", "leak", "executor roblox", "roblox executor", "earn", "earning"]
scamFlags = ["$", "steam", "asdfghjkl", "cdn.discordapp.com/attachments", "@everyone", "3.jpg", "3.png", "3.jpeg",]
linkFlags = ["steamcommunity.com/gift", "bit.ly", "sc.link", "1.jpg", "1.png", "1.jpeg", "2.jpg", "2.png", "2.jpeg", "qptr.ru", "https://temu.com/s/", "canary.discord.com", "https://", "http://", "discord.gg", "discordapp.com", "discord.com/invite", "https://t.me/"]
whitelist = ["https://tenor.com/view/", "https://cdn.discordapp.com/attachments"]
strikethreshold = 3
piratedVersions = ["0.2.8", "0.2.4", "0.2.16b", "0.2.18c", "0.2.19.5", "0.2.30.0", "0.2.32.1"]
colorint = -1
class adminFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldown = 0
        ##self.printOut.start()
        self.colorint = colorint
        self.color1 = (250, 250, 120)
        self.color2 = (119, 86, 35)
        self.operational = True
        #self.bot.add_check(adminFunctions.blacklist_test)
        print("Hi")

    async def updateServerConfig(self):
        for guild in self.bot.guilds:
            try:
                serverConfig[guild.id] = [dict(row) for row in await self.bot.sql.databaseFetchFast(
                f'SELECT * FROM serverconfig WHERE serverid = {guild.id}')][0]
            except Exception:
                pass
        await adminFunctions.printServerConfig(self)
    async def printServerConfig(self):
        print(serverConfig)

    async def bot_check(self, ctx):
        try:
            await ctx.message.add_reaction('310177266011340803')
        except discord.Forbidden:
            await self.bot.error.sendCategorizedError(ctx, "compliment")
            await ctx.send("Sprocket Bot has noticed that you have blocked him.  Unblock the bot and run the command again.")
            return False
        except Exception as e:
            # if "Forbidden" in str(e):
            #     await self.bot.error.sendCategorizedError(ctx, "compliment")
            #     await ctx.send("Sprocket Bot has noticed that you have blocked him.  Unblock the bot and run the command again.")
            #     return False
            pass

        # try:
        #     print("hi")
        # except discord.Forbidden:
        #     await self.bot.error.sendCategorizedError(ctx, "compliment")
        #     await ctx.send("Sprocket Bot has noticed that you have blocked him.  Unblock the bot and run the command again.")
        #     return False
        # except Exception:
        #     pass

        if ctx.author.id in [439836738064613378, 670531747972251676, 171352085340618753]: # blacklist
            await self.bot.error.sendCategorizedError(ctx, "insult")
            return False
        if ctx.author.id == main.ownerID:
            print("Overriding shutdown")
            return True
        if self.bot.operational == True:
            return True
        else:
            await self.bot.error.sendCategorizedError(ctx, "catgirl")
            await ctx.send("Sprocket Bot is a bit too sleepy right now.  Come back when I've finished my catnap, please?")

    # @main.bot.event
    # async def on_command_error(ctx, error):
    #
    #     if isinstance(error, commands.MissingRequiredArgument):
    #         await ctx.send('Missing required argument.')
    #     elif isinstance(error, commands.CommandNotFound):
    #         # if "-#" not in ctx.message.content and len(ctx.message.content) >= 3:
    #         #     await self.bot.error.sendCategorizedError(ctx, "compliment")
    #         #     await ctx.send("To see my list of commands, try using \n`-help`\n`-sprockethelp`\n`-campaignhelp`")
    #         pass
    #     elif isinstance(error, commands.HybridCommandError):
    #         await ctx.send("Cannot find that user.  They are either already banned or something else went wrong.")
    #         channel = main.bot.get_channel(1152377925916688484)
    #         await channel.send(error)
    #         await channel.send(f"<@{main.ownerID}>")
    #     else:
    #         await ctx.bot.error.sendError(ctx)
    #         channel = main.bot.get_channel(1152377925916688484)
    #         await channel.send(error)
    #         raise error  # Re-raise the error to see it in the console

    @commands.command(name="toggleOperation", description="Toggle operation of the bot")
    async def toggleOperation(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        self.operational = not self.operational
        await ctx.send(f'## Operational status is {self.operational}')

    @commands.command(name="commandCount", description="Toggle operation of the bot")
    async def commandCount(self, ctx: commands.Context):
        command_count = len(self.bot.commands)
        await ctx.send(f"Number of commands: {command_count}")
    @commands.command(name="killswitch", description="Toggle operation of the bot")
    async def killswitch(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        exit()

    @commands.command(name="testLatency", description="test the bot's latency")
    #@commands.check(adminFunctions.commands_check)
    async def testLatency(self, ctx: commands.Context):
        start_time = time.time()
        await self.bot.sql.databaseExecute("SELECT * FROM serverconfig")
        time2 = time.time()
        await ctx.send("Simple database selecting: --- %.10s seconds ---" % (time2 - start_time))

        start_time = time.time()
        await self.bot.sql.databaseFetchdict("SELECT * FROM serverconfig")
        time2 = time.time()
        await ctx.send("Database dict selecting: --- %.10s seconds ---" % (time2 - start_time))

        start_time = time.time()
        await self.bot.sql.databaseExecute("UPDATE serverconfig SET serverid = 2 WHERE serverid = 59;")
        time2 = time.time()
        await ctx.send("Blank database updating: --- %.10s seconds ---" % (time2 - start_time))

        start_time = time.time()
        await self.bot.sql.databaseExecute("SELECT * FROM serverconfig; SELECT * FROM serverconfig; UPDATE serverconfig SET serverid = 2 WHERE serverid = 59;")
        time2 = time.time()
        await ctx.send("All 3 queries at once: --- %.10s seconds ---" % (time2 - start_time))

        start_time = time.time()
        await self.bot.sql.databaseFetchFast("SELECT * FROM serverconfig;")
        time2 = time.time()
        await ctx.send("Non-pooled database updating: --- %.10s seconds ---" % (time2 - start_time))

        start_time = time.time()
        await self.bot.sql.databaseMultiFetch("SELECT * FROM serverconfig; SELECT * FROM serverconfig; UPDATE serverconfig SET serverid = 2 WHERE serverid = 59;")
        time2 = time.time()
        await ctx.send("multi-fetch pooled database updating: --- %.10s seconds ---" % (time2 - start_time))

    @commands.command(name="reloadCogs", description="reload all extensions")
    async def reloadCogs(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        for cog in main.cogsList:
            await self.bot.reload_extension(cog)
        if main.updateGithub == "Y":
            await self.bot.reload_extension("cogs.githubTools")
        await ctx.send("Reloaded!")
        await asyncio.sleep(10)
        await ctx.send("Update slash command tree?")
        if await ctx.bot.ui.getYesNoChoice(ctx) == True:
            for guild in self.bot.guilds:
                self.bot.tree.clear_commands(guild=guild)
                await self.bot.tree.sync(guild=guild)
                await ctx.send(f"Commands synced in {guild.name}!")
                await asyncio.sleep(2)
            await self.bot.tree.sync()


    def authorize(ctx: commands.Context, bot):
        print("Hi")
        return False

    # detect the latest piratable version of Sprocket on websites like steamunlocked.  This will get plugged into the piracy scanner.

    @commands.Cog.listener()
    async def on_message(self, message):

        #await message.add_reaction('310177266011340803')
        if message.author.bot:
            return
        # blueprint scanner
        if message.attachments:
            #print(message.attachments)
            for attachment in message.attachments:
                if ".blueprint" in attachment.filename:
                    blueprintData = json.loads(await attachment.read())
                    if blueprintData["header"]["gameVersion"] in piratedVersions:
                        channel = self.bot.get_channel(1142053423370481747)
                        await channel.send(f"Out-of-date blueprint was sent by <@{message.author.id}> (id: {message.author.id})\nVersion: {blueprintData['header']['gameVersion']}\nMessage: {message.jump_url}")

        if serverConfig == {}:
            await adminFunctions.updateServerConfig(self)
            return

        #scam scanner
        messageParse = message.content.lower()
        nudeTrigger = 0
        scamTrigger = 0
        linkTrigger = 0
        for flag in nudeFlags:
            if flag in messageParse:
                nudeTrigger += 1
        for flag in scamFlags:
            if flag in messageParse:
                scamTrigger += 1
        for flag in linkFlags:
            if flag in messageParse:
                linkTrigger += 1

        if linkTrigger == 0 and (nudeTrigger == 0 or scamTrigger == 0) and len(message.content) > 0 and not any(keyword in message.content for keyword in whitelist):
            userStrikes[message.author.id] = 0
        if linkTrigger > 0 and (nudeTrigger > 0 or scamTrigger > 0) and len(message.content) > 0 and not any(keyword in message.content for keyword in whitelist):
            print(f"{nudeTrigger}{scamTrigger}{linkTrigger}")
            logChannel = self.bot.get_channel(1152377925916688484)
            try:
                userStrikes[message.author.id] = int(userStrikes[message.author.id]) + 1
            except Exception:
                userStrikes[message.author.id] = 1
            action = serverConfig[message.guild.id]['flagaction']
            pingAction = serverConfig[message.guild.id]['flagping']
            preppedMessage = f"This message matches the criteria set for a hacked account:\nUser ID: {message.author.id}\nUser ping: <@{message.author.id}>\nMessage content:\n{message.content}"
            embed = discord.Embed(title=f"A hacked account has been detected!", color=discord.Color.blurple())
            if userStrikes[message.author.id] >= int(serverConfig[message.guild.id]['flagthreshold']):
                embed = discord.Embed(title=f"Action taken on a hacked account", color=discord.Color.red())
                embed.set_footer(text=f"Action taken: {action}")
            embed.add_field(name="Username", value=f"{message.author.name}", inline=False)
            embed.add_field(name="A.K.A.", value=f"{message.author.display_name}", inline=False)
            embed.add_field(name="User ID", value=f"{message.author.id}", inline=False)
            embed.add_field(name="User ping", value=f"<@{message.author.id}>", inline=False)
            embed.add_field(name="Server", value=f"<@{message.guild.name}>", inline=False)
            await logChannel.send(embed=embed)
            await logChannel.send(f'Message content:\n`{message.content}`')
            if userStrikes[message.author.id] == int(serverConfig[message.guild.id]['flagthreshold']) - 1:
                await message.author.send(
                    f"## Warning: you are triggering Sprocket Bot's anti scam functions and risk a {action} in *{message.guild.name}.*  \nSend a message that does not contain a link or questionable words, such as \"a\". \nIf you believe this was an error, please report this at https://github.com/SprocketTools/SprocketBot/issues")
            if userStrikes[message.author.id] >= int(serverConfig[message.guild.id]['flagthreshold']):
                if action == "kick":
                    await message.author.send(f"You have been kicked from {message.guild.name} by Sprocket Bot's automated anti-scam functions.  \n This is not a permanent ban - rejoin the server once you gain control of your account again and have 2FA enabled.\nIf you believe this was an error, please report this at https://github.com/SprocketTools/SprocketBot/issues")
                    await message.author.ban(reason="Automated anti-scam functions", delete_message_seconds=600)
                    await message.author.unban(reason="Automated anti-scam functions")
                if action == "timeout for 12 hours":
                    await message.author.send(f"You have been timed out in {message.guild.name} by Sprocket Bot's automated anti-scam functions.  \nIf you believe this was an error, please report this at https://github.com/SprocketTools/SprocketBot/issues")
                    delta = (datetime.datetime.now().astimezone() + datetime.timedelta(hours=12))
                    await message.author.timeout(delta, reason="Hacked account")
                channel = self.bot.get_channel(serverConfig[message.guild.id]['managerchannelid'])
                await channel.send(embed=embed)
                await channel.send(f'Message content:\n`{message.content}`')
                if pingAction == "nobody":
                    pass
                elif pingAction == "custom":
                    await channel.send(f"<@&{serverConfig[message.guild.id]['flagpingid']}>")
                else:
                    await channel.send(f"@{serverConfig[message.guild.id]['flagping']}")

        # fun module
        special_list = {
            "amogus": "compliment",
            "skibidi": "insult",
            "colon": "insult"
            }
        if self.cooldown <= 0:
            self.cooldown += 1
        if self.cooldown >= 3:
            self.cooldown += -1
        print(self.cooldown)
        if (serverConfig[message.guild.id]["allowfunny"] == True and message.channel.id == serverConfig[message.guild.id]["generalchannelid"] or message.author.id == main.ownerID) and message.guild.id != 788349365466038283:
            guild = self.bot.get_guild(message.guild.id)
            prob = 1500 + len(guild.members)
            i = int(random.random()*prob)
            j = random.random()
            print("e")
            if message.content.lower() == "hi" and self.cooldown > 0:
                self.cooldown += 100
                print(message.author.id)
                if self.cooldown > 300:
                    await message.reply(await self.bot.error.retrieveCategorizedError(ctx=message, category="insult"))
                    self.cooldown = -500
                elif message.author.id == 712509599135301673:
                    if j < 0.15:
                        await message.reply(await self.bot.error.retrieveCategorizedError(ctx=message, category="catgirl"))
                    elif j > 0.6:
                        await message.reply(await self.bot.error.retrieveCategorizedError(ctx=message, category="insult"))
                    else:
                        await message.reply(await self.bot.error.retrieveCategorizedError(ctx=message, category="gif"))
                elif message.author.id == 437324319102730263:
                    if j < 0.35:
                        await message.reply(await self.bot.error.retrieveCategorizedError(ctx=message, category="compliment"))
                    elif j > 0.85:
                        await message.reply(await self.bot.error.retrieveCategorizedError(ctx=message, category="insult"))
                    else:
                        await message.reply("hi")
                elif message.author.id == 220134579736936448:
                    if j < 0.6:
                        await message.reply(await self.bot.error.retrieveCategorizedError(ctx=message, category="compliment"))
                    elif j > 0.9:
                        await message.reply(await self.bot.error.retrieveCategorizedError(ctx=message, category="catgirl"))
                    else:
                        await message.reply("hi")
                elif message.author.id == 834279720279474176:
                    if j > 0.5:
                        await message.reply(await self.bot.error.retrieveCategorizedError(category="mlp"))
                else:
                    if j < 0.3:
                        await message.reply("hi")
                    elif j < 0.6:
                        await message.reply("hello")
                    elif j < 0.86:
                        await message.reply("hello there")
                    elif j < 0.93:
                        await message.reply("https://tenor.com/2OkW.gif")
                    else:
                        await message.reply("https://tenor.com/bWVjr.gif")

            #print(i)
            if i == 1:
                serverConfig[message.guild.id]["funnycounter"] = int((random.random()**2)*2+1)
            if i <= prob/4:
                for x in special_list:
                    if x in message.content.lower():
                        await textTools.sendThenDelete(message, await self.bot.error.retrieveCategorizedError(message, special_list[x]))
            try:
                if serverConfig[message.guild.id]["funnycounter"] > 0 and i < 700:
                    serverConfig[message.guild.id]["funnycounter"] = serverConfig[message.guild.id]["funnycounter"] - 1
                    category = random.choice(["compliment", "insult", "sprocket", "flyout", "video", "gif", "joke", "campaign", "blueprint"])
                    await message.reply(await self.bot.error.retrieveCategorizedError(message, category))
            except Exception:
                serverConfig[message.guild.id]["funnycounter"] = 0

    @commands.command(name="setTrollCount", description="reload all extensions")
    async def setTrollCount(self, ctx: commands.Context):
        try:
            if ctx.author.id != 712509599135301673:
                return
            serverID = await textTools.getIntResponse(ctx, "What is the server ID?")
            if serverConfig[serverID]["allowfunny"] != True:
                await ctx.send("WARNING: This server has the fun module disabled; the command will NOT work!")
                return
            count = await textTools.getIntResponse(ctx, "What do you want to set the troll count to?")
            serverConfig[serverID]["funnycounter"] = count
            await ctx.send("## Done!")
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(name="resetServerConfig", description="Reset everyone's server configurations")
    async def resetServerConfig(self, ctx: commands.Context):
        print("hi")
        if ctx.author.id != 712509599135301673:
            # This message will show if the ID check fails
            await ctx.send(f"Permission denied. Your ID is {ctx.author.id}.")
            return

        # Drop the? old table to ensure a clean reset
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS serverconfig;''')
        print("hi")
        # Create the new table with the updated schema
        prompt = ('''CREATE TABLE IF NOT EXISTS serverconfig (
                              serverid BIGINT,
                              ownerID BIGINT,
                              generalchannelID BIGINT,
                              allowfunny BOOL,
                              updateschannelID BIGINT,
                              commandschannelID BIGINT,
                              managerchannelID BIGINT,
                              serverboosterroleID BIGINT,
                              contestmanagerroleID BIGINT,
                              botmanagerroleID BIGINT,
                              campaignmanagerroleID BIGINT,
                              flagthreshold INT,
                              flagaction VARCHAR,
                              flagping VARCHAR,
                              flagpingid BIGINT,
                              musicroleid BIGINT,
                              banmessage VARCHAR,
                              clickupkey VARCHAR);''')  # Added musicroleid and banmessage
        await self.bot.sql.databaseExecute(prompt)
        await ctx.send("Done!  Now go DM everyone that their config was reset...")

    @commands.command(name="addScamConfig", description="Reset everyone's server configurations")
    async def resetScamConfig(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = ('''ALTER TABLE serverconfig 
                              ADD COLUMN IF NOT EXISTS flagthreshold INT,
                              ADD COLUMN IF NOT EXISTS flagaction VARCHAR,
                              ADD COLUMN IF NOT EXISTS flagping VARCHAR,
                              ADD COLUMN IF NOT EXISTS flagpingid BIGINT;''')
        await self.bot.sql.databaseExecute(prompt)
        await ctx.send("Done!")
        await adminFunctions.updateServerConfig(self)

    @commands.command(name="help", description="View all the bot commands")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(title=f"**Sprocket Bot Commands**",
                              description="*Sprocket Bot's prefix is* `-`\n",
                              color=discord.Color.random())
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="SprocketHelp", value="Get help with building in Sprocket", inline=False)
        embed.add_field(name="getAddon", value="Make an addon structure out of a tank blueprint", inline=False)
        embed.add_field(name="bakeGeometry", value="Bake 0.127 compartments together", inline=False)
        embed.add_field(name="trasplant", value="Copy turrets between 0.2 tanks", inline=False)
        embed.add_field(name="tunePowertrain", value="Calibrate your tank's powertrain", inline=False)
        embed.add_field(name="submitTank", value="Submit a tank to an ongoing contest", inline=False)
        embed.add_field(name="submitDecal", value="Submit decals to the SprocketTools decal repository", inline=False)
        embed.add_field(name="addError", value="Add a funny response to Sprocket Bot's error catalog", inline=False)
        embed.add_field(name="weather", value="Apply wear and tear effects to attached photos", inline=False)
        embed.add_field(name="play [search term]", value="Play YouTube music in your voice chat", inline=False)
        embed.add_field(name="skip", value="Skip the current music track", inline=False)
        embed.add_field(name="help", value="Shows this message", inline=False)
        embed.add_field(name="settings", value="Adjust the server configuration", inline=False)
        embed.set_thumbnail(url='https://sprockettools.github.io/SprocketToolsLogo.png')
        embed.set_footer(text=await self.bot.error.retrieveError(ctx))
        await ctx.send(embed=embed)

    # @commands.command(name="viewServerConfig", description="View my server configurations")
    # async def viewServerConfig(self, ctx: commands.Context):
    #     if ctx.author.guild_permissions.administrator == False and ctx.author.id != main.ownerID:
    #         await ctx.send(await self.bot.error.retrieveError(ctx))
    #     else:
    #         try:
    #             serverData = [dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {ctx.guild.id}')][0]
    #             description = f'''
    #             General chat:         <#{serverData['updateschannelid']}>
    #             Bot commands chat:    <#{serverData['commandschannelid']}>
    #             Server managers chat: <#{serverData['managerchannelid']}>
    #
    #             Server booster role:   {ctx.guild.get_role(int(serverData['serverboosterroleid']))}
    #             Contest managers role: {ctx.guild.get_role(int(serverData['contestmanagerroleid']))}
    #             Bot manager role:      {ctx.guild.get_role(int(serverData['botmanagerroleid']))}
    #             Campaign manager role: {ctx.guild.get_role(int(serverData['campaignmanagerroleid']))}
    #             Music player role: {ctx.guild.get_role(int(serverData['musicroleid']))}
    #
    #             Allow the bot to try and be funny: {serverData['allowfunny']}
    #             '''
    #             embed = discord.Embed(title=f"Server Config: {ctx.guild.name}",
    #                                   description=description,
    #                                   color=discord.Color.random())
    #             embed.set_thumbnail(url=ctx.guild.icon)
    #             await ctx.send(embed=embed)
    #         except Exception:
    #             await ctx.send(await self.bot.error.retrieveError(ctx))
    #             await ctx.send("It appears that your configuration is out of date and needs to be updated.  Use `-setup` to update your server settings.")

    @commands.command(name="setSlowmode", description="Set a slowmode.")
    async def setSlowmode(self, ctx: commands.Context, duration: int):
        serverConfig = await adminFunctions.getServerConfig(self, ctx)
        if str(serverConfig['botmanagerroleid']) not in str(ctx.author.roles):
            if ctx.author.id == ctx.bot.ownerid:
                await ctx.send("You do not have permission to perform this action.  Proceed forward and override this?")
                answer = await ctx.bot.ui.getYesNoChoice(ctx)
                if not answer:
                    return
            else:
                return
        await ctx.channel.edit(slowmode_delay = duration)
        await ctx.send(f"Slowmode is now set to a {duration} second delay!\n\n{await self.bot.error.retrieveError(ctx)}")

    @commands.command(name="listMyServers", description="List all my servers.")
    async def listMyServers(self, ctx: commands.Context):
        i = 0
        c = 0
        serverList = "Your server list:"
        for server in self.bot.guilds:
            serverList = serverList + f"\n{server.name} ({server.member_count} members)"
            i+= 1
            c += server.member_count
            if i % 20 == 0:
                await ctx.send(serverList)
                serverList = ""
        #await ctx.send(serverList)
        await ctx.send(f"count: {i} servers!")
        await ctx.send(f"serving: {c} members!")

    @commands.command(name="listVulnerableServers", description="List all my servers.")
    async def listVulnerableServers(self, ctx: commands.Context, count: int):
        i = 0
        c = 0
        serverList = "Your server list:"
        for server in self.bot.guilds:
            if server.member_count < count:
                serverList = serverList + f"\n{server.name} ({server.member_count} members)"
                i+= 1
                c += server.member_count
                if i % 20 == 0:
                    await ctx.send(serverList)
                    serverList = ""
        await ctx.send(serverList)

    @commands.command(name="pruneServers", description="List all my servers.")
    async def pruneServers(self, ctx: commands.Context, count: int):
        i = 0
        if ctx.author.id != main.ownerID:
            return
        serverList = "Your server list:"
        for server in self.bot.guilds:
            serverList = serverList + f"\n{server.name} ({server.member_count})"
            if server.member_count < count:
                try:
                    await server.owner.send(f"Note: As a result of my current 100-server limitation, I have left **{server.name}** due to insufficient member count.  ")
                except Exception:
                    serverList = serverList + f".  <@{server.owner_id}> apparently had me blocked"
                await server.leave()
                serverList = serverList + " - I have now left this server."
            i+= 1
            if i % 20 == 0:
                await ctx.send(serverList)
                serverList = ""
        await ctx.send(serverList)
        await ctx.send(f"original count: {i} servers.")
        e = 0
        for server in self.bot.guilds:
            e+= 1
        await ctx.send(f"servers left: {i - e} servers.")
        await ctx.send(f"remaining servers: {e} servers.")

    @commands.command(name="sendGlobalUpdate", description="Send a global update to all servers.")
    async def sendGlobalUpdate(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        view = globalSendDropdownView()
        await ctx.send(content="Where are you sending today's update to?", view=view, ephemeral=True)
        await view.wait()
        result = str(view.result).lower()
        await ctx.send("Type your message here!")
        # get the message that is to be sent
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            message_out_text = msg.content
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        if result == "direct":
            for server in self.bot.guilds:
                if server.owner.id != 123105882102824960:
                    serverOwner = self.bot.get_user(server.owner.id)
                    await serverOwner.send(message_out_text)
        else:
            channelList = await self.bot.sql.databaseFetchdict(f'SELECT * FROM serverconfig;')
            for serverDat in channelList:
                serverChn = serverDat[str(result)]
                try:
                    guildIn = self.bot.get_guild(serverDat['serverid'])
                    serverChannel = guildIn.get_channel(serverChn)
                    await serverChannel.send(message_out_text)
                    for attachment in msg.attachments:
                        file = await attachment.to_file()
                        await serverChannel.send(file=file, content="")
                except Exception:
                    try:
                        serverOwner = self.bot.get_user(self.bot.get_guild(serverDat['serverid']).owner.id)
                        await serverOwner.send(message_out_text)
                        for attachment in msg.attachments:
                            file = await attachment.to_file()
                            await serverOwner.send(file=file, content="")
                    except Exception:
                        print(f"Failed to update server of ID {serverDat['serverid']}.  Sprocket Bot is likely not in this server.")

        await ctx.send("## Delivered!")
    @commands.command(name="rebootServer", description="setup the server")
    async def rebootServer(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        os.system("sudo reboot -r now")

    @commands.command(name="restart", description="setup the server")
    async def restart(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        exit()

    @commands.command(name="adminAddColumn", description="add a column to a SQL table")
    async def adminAddColumn(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        tablename = await textTools.getResponse(ctx,"What is the table name?")
        columnname = await textTools.getResponse(ctx, "What will the column be named?  Use all lowercase letters with no spaces.")
        options = ["VARCHAR", "BIGINT", "REAL", "BOOLEAN", "TIMESTAMP"]
        prompt = "What variable type do you want to use?  VARCHAR is for strings, BIGINT is for ints, REALs are for floats, BOOLEANs are true/false, and TIMESTAMPs are for timestamps."
        varType = await ctx.bot.ui.getChoiceFromList(ctx, options, prompt)
        try:
            if varType == "VARCHAR" or varType == "TIMESTAMP":
                await self.bot.sql.databaseExecute(f''' ALTER TABLE {tablename} ADD {columnname} {varType};''')
            else:
                defaultVal = await textTools.getResponse(ctx,"What will the default value be?")
                await self.bot.sql.databaseExecute(f''' ALTER TABLE {tablename} ADD {columnname} {varType} DEFAULT {defaultVal};''')
            await ctx.send("Operation successful!")
        except Exception as e:
            await ctx.send(f"Something was incorrect: {e}")

    @commands.command(name="adminDownloadErrors", description="add a column to a SQL table")
    async def adminDownloadErrors(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        data = await self.bot.sql.databaseFetchdict('''SELECT * FROM errorlist''')
        stringOut = json.dumps(data, indent=4)
        data = io.BytesIO(stringOut.encode())
        await ctx.send(file=discord.File(data, f'errors.json'))

    @commands.command(name="adminExecute", description="register a contest")
    async def adminExecute(self, ctx: commands.Context, *, prompt):
        if ctx.author.id != main.ownerID:
            return
        await ctx.send(await self.bot.sql.databaseExecute(prompt.replace("`", "")))

    @commands.command(name="adminFetch", description="register a contest")
    async def adminFetch(self, ctx: commands.Context, *, prompt):
        if ctx.author.id != main.ownerID:
            return
        result = await self.bot.sql.databaseFetch(prompt)
        print(result)
        await ctx.send(result)

    @commands.command(name="adminGetTable", description="add a column to a SQL table")
    async def adminGetTable(self, ctx: commands.Context):
        if ctx.author.id == main.ownerID:
            await self.bot.error.sendError(ctx)
            return
        tablename = await self.bot.error.getResponse(ctx, "What is the table name?")
        await ctx.send(await self.bot.sql.databaseFetchdict(f"SELECT * FROM {tablename};"))

    @commands.command(name="adminDropColumn", description="add a column to a SQL table")
    async def adminDropColumn(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        tablename = await self.bot.error.getResponse(ctx,"Whatis the table name?")
        columnname = await self.bot.error.getResponse(ctx, "What are the column names?  Use all lowercase letters with no spaces, and split with spacebars.")
        names = columnname.split(" ")
        for name in names:
            try:
                await self.bot.sql.databaseExecute(f''' ALTER TABLE {tablename} DROP COLUMN {name};''')
                await ctx.send(f"Dropped {name}")
            except Exception as e:
                await ctx.send(f"Something was incorrect: {e}")

    @commands.command(name="setBotStatus", description="setup the server")
    async def setBotStatus(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        activityType = await ctx.bot.ui.getButtonChoice(ctx, ["Playing", "Watching", "Listening", "Streaming"])
        if activityType == "Playing":
            name = await textTools.getResponse(ctx, "What game are you playing?")
            await self.bot.change_presence(activity=discord.Game(name=name))
        if activityType == "Watching":
            name = await textTools.getResponse(ctx, "What is your video name?")
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=name))
        if activityType == "Listening":
            url = await textTools.getResponse(ctx, "What song name are you listening to?")
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=url))
        if activityType == "Streaming":
            name = await textTools.getResponse(ctx, "What is your stream name?")
            url = await textTools.getResponse(ctx, "What URL are you streaming?")
            await self.bot.change_presence(activity=discord.Streaming(name=name, url=url))

    @commands.command(name="setBotAvatar", description="setup the server")
    async def setBotAvatar(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        url = await textTools.getResponse(ctx, "Reply with the image link")
        #waitTime = await textTools.getIntResponse(ctx, "How many seconds should it last?")
        response = requests.get(url).content
        await self.bot.user.edit(avatar=response)
        await ctx.send("Hi there!")
        #await asyncio.sleep(waitTime)
        # response = requests.get(defaultURL).content
        # await self.bot.user.edit(avatar=response)
        # await ctx.send("Restored logo to default.")

    @commands.command(name="setBotName", description="setup the server")
    async def setBotName(self, ctx: commands.Context):
        defaultName = main.defaultName
        if ctx.author.guild_permissions.administrator == False:
            return
        url = await textTools.getResponse(ctx, "Reply with my new name!")
        waitTime = await textTools.getIntResponse(ctx, "How many seconds should it last?")

        await ctx.send("Hi there!")
        await asyncio.sleep(waitTime)
        await self.bot.user.edit(username=defaultName)
        await ctx.send("Restored name to default.")

    @commands.command(name="setMusicRole", description="setup the server")
    async def setMusicRole(self, ctx: commands.Context):
        intO = await textTools.getRoleResponse(ctx, "What role do you want to allow to play music?  Reply to this message with a ping of that role.")
        await self.bot.sql.databaseExecuteDynamic(f'''UPDATE serverconfig SET musicroleid = $1 WHERE serverid = $2;''', [intO, ctx.guild.id])
        await adminFunctions.updateServerConfig(self)
        await ctx.send("## Done! \nYour server is now configured.")

    @commands.command(name="setup", description="setup the server")
    async def setup(self, ctx: commands.Context):
        if ctx.author.guild_permissions.administrator == True:
            pass
        else:
            return
        responses = {}
        responses["serverid"] = ctx.guild.id
        responses["ownerid"] = ctx.guild.owner.id
        await ctx.send("This is the setup command, which will configure Sprocket Bot to work with your server.  You will be asked to ping a role or channel in reply to messages; make sure you are running this in an admin channel.  If your server only has one channel and one role, just repeatedly ping them instead")
        await ctx.send("Reply with 'continue' if this is an appropriate channel.")
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

        await ctx.send("Awesome!  Let's get started. \n\nWhat is your server's general chat?  A.K.A. the channel that your community uses as the primary discussion chat.  Reply to this message with a mention of that channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["generalchannelID"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What channel do you want Sprocket Bot update notes to appear in?  This should be set to any publicly-visible channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["updateschannelID"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What is your bot commands channel?  This channel will be the only location that utility commands can be ran, as a result it should be a publicly-visible channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["commandschannelID"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What channel do you want administrative Sprocket Bot information to appear in?  This channel should only be visible to trusted server managers.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["managerchannelID"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What is your server booster role?  Reply to this message with a ping of that role.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["serverboosterroleID"] = msg.role_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What role do you want to designate as your server contest managers?  Reply to this message with a ping of that role.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["contestmanagerroleID"] = msg.role_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What role do you want to designate as your server campaign managers?  Reply to this message with a ping of that role.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["campaignmanagerroleID"] = msg.role_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What role do you want to allow to play music?  Reply to this message with a ping of that role.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["musicroleid"] = msg.role_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("## Next up: scam protection.\n\nHow many consecutive scam messages do you want an account to send before Sprocket Bot considers it as hacked?\nRecommended values are between 3 and 6.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["flagthreshold"] = int(msg.content)
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        scamActionPrompt = "What action do you want Sprocket Bot to take, if any?"
        scamActionList = ["nothing", "timeout for 12 hours", "kick"]
        scamAction = await ctx.bot.ui.getChoiceFromList(ctx, scamActionList, scamActionPrompt)
        responses["flagaction"] = scamAction

        scamPingPrompt = "What do you want Sprocket Bot to ping when it detects a hacked account?  \n\nThese pings will be sent into the management channel you defined previously, with some information about the hacked account."
        scamPingList = ["nobody", "everyone", "here", "custom"]
        scamPing = await ctx.bot.ui.getChoiceFromList(ctx, scamPingList, scamPingPrompt)
        responses["flagping"] = scamPing
        if scamPing == "custom":
            await ctx.send("What role do you want to designate to be pinged when a hacked account is detected?  Reply to this message with a ping of that role.")
            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
                pingRoleID = msg.role_mentions[0].id
            except asyncio.TimeoutError:
                await ctx.send("Operation cancelled.")
                return
            responses["flagpingid"] = pingRoleID
        else:
            responses["flagpingid"] = 0

        await ctx.send("What role do you want to grant permissions to edit (some of) Sprocket Bot's settings?  Reply to this message with a ping of that role.")

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["botmanagerroleID"] = msg.role_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("In the future, Sprocket Bot may be able to interact with users in your general chat.  Do you wish to enable the fun module for exclusively your general chat?  Reply with 'yes' or 'no'.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            if msg.content.lower() == "true" or msg.content.lower() == "yes":
                responses["allowfunny"] = True
            else:
                responses["allowfunny"] = False
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("## All data successfully collected!\nBeginning processing now...")
        keystr, valuestr = await textTools.getSQLprompt(responses)
        await self.bot.sql.databaseExecute(f'''DELETE FROM serverconfig WHERE serverid = {ctx.guild.id};''')
        await self.bot.sql.databaseExecute(f'''INSERT INTO serverconfig ({keystr}) VALUES ({valuestr});''')
        await adminFunctions.updateServerConfig(self)
        await ctx.send("## Done! \nYour server is now configured and can fully utilize its commands.")

    @commands.command(name="hey_alexa_kill_the_lights", description="send a message wherever you want")
    async def exit(self, ctx: commands.Context):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        await exit(1)

    @commands.command(name="troll", description="send a message wherever you want")
    async def troll(self, ctx: commands.Context, channelin: str, *, message):
        print("a")
        if ctx.author.id in [712509599135301673, 686640777505669141]:
            print("b")
            tts = False
            import re
            await ctx.send("Message is en route.  \nReminder that adding `-tts-` anywhere will enable TTS readout.")
            if "-tts-" in message:
                tts = True
            # webhook
            if "api" in channelin:
                async with aiohttp.ClientSession() as session:
                    print("e")
                    webhook = Webhook.from_url(channelin, session=session)
                    await webhook.send(message)
                    for attachment in ctx.message.attachments:
                        file = await attachment.to_file()
                        await webhook.send(file=file, content="")
            else:
                channelin = int(re.sub(r'[^0-9]', '', channelin))
                print(channelin)
                channel = self.bot.get_channel(channelin)
                if ctx.author.id == 686640777505669141 and channel.guild.id in [788349365466038283, 1002673504002519121]:
                    return
                await channel.send(message.replace("-tts-", ""), tts=tts)
                for attachment in ctx.message.attachments:
                    file = await attachment.to_file()
                    await channel.send(file=file, content="")

    @commands.command(name="trollReply", description="send a message wherever you want")
    async def trollReply(self, ctx: commands.Context, msglink: str, *, message):
        if ctx.author.id == 712509599135301673:
            import re
            srvrid = int(msglink.split("/")[-3])
            chnlid = int(msglink.split("/")[-2])
            msgid = int(msglink.split("/")[-1])
            serverIn = await self.bot.fetch_guild(srvrid)
            channelIn = await self.bot.fetch_channel(chnlid)
            messageIn = await channelIn.fetch_message(msgid)
            await ctx.send("Message is en route.")
            await messageIn.reply(message)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channelIn.send(file=file, content="")

    @commands.command(name="complain", description="Get a response back from Google")
    async def complain(self, ctx: commands.Context, msglink: str, *, style = None):
        if ctx.author.id in [712509599135301673, 686640777505669141]:
            import re
            if "https" in msglink:
                srvrid = int(msglink.split("/")[-3])
                chnlid = int(msglink.split("/")[-2])
                msgid = int(msglink.split("/")[-1])

                serverIn = await self.bot.fetch_guild(srvrid)
                channelIn = await self.bot.fetch_channel(chnlid)
                messageIn = await channelIn.fetch_message(msgid)
            else:
                messageIn = None
                mention_list = await self.bot.fetch_channel(int(re.sub('[^0-9\-]', '', msglink)))
                print(mention_list)
                async for message_l in mention_list.history(limit=1):
                    messageIn = message_l
                channelIn = messageIn.channel
            init_prompt = messageIn.content
            gemini = genai.Client(api_key=ctx.bot.geminikey)
            if not style:
                style = "drunk"
            message = gemini.models.generate_content(model='gemini-2.0-flash-001', contents=f"Make a complaint in less than 250 words about this sentence: '{init_prompt}'.  Apply a {style} accent to your complaint.")
            print(message.text)
            await ctx.send("Message is en route.")

            await messageIn.reply(message.text)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channelIn.send(file=file, content="")
    @commands.command(name="trollreplyai", description="Get a response back from Google")
    async def trollreplyai(self, ctx: commands.Context, msglink: str, *, prompt):
        if ctx.author.id in [712509599135301673, 686640777505669141]:
            import re
            srvrid = int(msglink.split("/")[-3])
            chnlid = int(msglink.split("/")[-2])
            msgid = int(msglink.split("/")[-1])
            serverIn = await self.bot.fetch_guild(srvrid)
            channelIn = await self.bot.fetch_channel(chnlid)
            messageIn = await channelIn.fetch_message(msgid)
            gemini = genai.Client(api_key=ctx.bot.geminikey)
            message = gemini.models.generate_content(model='gemini-2.0-flash-001', contents=prompt)
            print(message.text)
            await ctx.send("Message is en route.")

            await messageIn.reply(message.text)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channelIn.send(file=file, content="")

    @commands.command(name="trollcai", description="Troll a channel")
    async def trollcai(self, ctx: commands.Context, channelin: str, *, prompt):
        if ctx.author.id in [712509599135301673, 686640777505669141]:
            import re
            channelin = int(re.sub(r'[^0-9]', '', channelin))
            print(channelin)
            channel = self.bot.get_channel(channelin)
            await ctx.send("Collecting message history")
            messages = []
            message_raw = channel.history(limit=1000)
            async for messagee in message_raw:
                messages.append({'author': messagee.author, 'content': messagee.content})
            print(messages)
            await ctx.send("Getting AI response")
            message_out = await ctx.bot.AI.get_response(prompt=f"You are a Discord bot that needs to respond to a conversation.  Here are the most recent messages from that Discord channel, provided in a json format: \n\n {str(messages)}\n\n Unless otherwise instructed, your reply cannot exceed 250 words in length. {prompt}", temperature=1.5)
            whereSend = await ctx.bot.ui.getButtonChoice(ctx, ["here", "there", "webhook"])
            dest = None
            if whereSend == "here":
                dest = ctx.channel
            if whereSend == "there":
                dest = channel
            if whereSend == "webhook":
                async with aiohttp.ClientSession() as session:
                    dest = Webhook.from_url(
                        'https://discord.com/api/webhooks/1351525808484651008/C7EO5uUViQ5ZTPQcV06I88Vs0MTBMrbCofopyNd5aaDulqM_h0J-kgcS2U11pjDbhs83',session=session)
            await dest.send(message_out)
            await ctx.send("Message is en route.")
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await dest.send(file=file, content="")

    @commands.command(name="trollai", description="Get a response back from Google")
    async def trollai(self, ctx: commands.Context, channelin: str, *, prompt):
        if ctx.author.id in [712509599135301673, 686640777505669141]:
            import re
            channelin = int(re.sub(r'[^0-9]', '', channelin))
            print(channelin)
            channel = self.bot.get_channel(channelin)
            gemini = genai.Client(api_key=ctx.bot.geminikey)
            message = gemini.models.generate_content(model='gemini-2.0-flash-001', contents=prompt)
            print(message.text)
            await ctx.send("Message is en route.")

            await channel.send(message.text)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channel.send(file=file, content="")

    @commands.command(name="trollai", description="Get a response back from Google")
    async def trollai(self, ctx: commands.Context, channelin: str, *, prompt):
        if ctx.author.id in [712509599135301673, 686640777505669141]:
            import re
            channelin = int(re.sub(r'[^0-9]', '', channelin))
            print(channelin)
            channel = self.bot.get_channel(channelin)
            gemini = genai.Client(api_key=ctx.bot.geminikey)
            message = gemini.models.generate_content(model='gemini-2.0-flash-001', contents=prompt)
            print(message.text)
            await ctx.send("Message is en route.")

            await channel.send(message.text)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channel.send(file=file, content="")

    @commands.command(name="trollReact", description="send a message wherever you want")
    async def trollReact(self, ctx: commands.Context, msglink: str, *, message):
        if ctx.author.id == 712509599135301673:
            import re
            srvrid = int(msglink.split("/")[-3])
            chnlid = int(msglink.split("/")[-2])
            msgid = int(msglink.split("/")[-1])
            serverIn = await self.bot.fetch_guild(srvrid)
            channelIn = await self.bot.fetch_channel(chnlid)
            messageIn = await channelIn.fetch_message(msgid)
            await ctx.send("Message is en route.")
            message = message.replace("><", "> <")
            emojis_out = message.split(" ")

            for emoji_raw in emojis_out:
                try:
                    print(emoji_raw)
                    emoji_id = emoji_raw.replace(">", "").split(":")[2]
                    #print(emoji_id)
                    await messageIn.add_reaction(ctx.bot.get_emoji(int(emoji_id)))
                except Exception:
                    print(emoji_raw)
                    #emoji_id = emoji_raw.replace(">", "").split(":")[2]
                    # print(emoji_id)
                    await messageIn.add_reaction(emoji_raw)
                await asyncio.sleep(1)

            # for attachment in ctx.message.attachments:
            #     file = await attachment.to_file()
            #     await channelIn.send(file=file, content="")

    @commands.command(name="edit", description="send a message wherever you want")
    async def edit(self, ctx: commands.Context, msglink: str):
        if ctx.author.id == 712509599135301673:
            print(msglink.split("/"))
            srvrid = int(msglink.split("/")[-3])
            chnlid = int(msglink.split("/")[-2])
            msgid = int(msglink.split("/")[-1])
            serverIn = await self.bot.fetch_guild(srvrid)
            channelIn = await self.bot.fetch_channel(chnlid)
            messageIn = await channelIn.fetch_message(msgid)
            await ctx.send(messageIn.content)
            newText = await textTools.getResponse(ctx, "What do you want the result to be?", action="raw")
            await messageIn.edit(content=newText)
            await ctx.send("## Done!")

    @commands.command(name="sendError", description="send a message wherever you want")
    async def sendError(self, ctx: commands.Context, channelin: str):
        if ctx.author.id == 712509599135301673:
            import re
            channelin = int(re.sub(r'[^0-9]', '', channelin))
            print(channelin)
            channel = self.bot.get_channel(channelin)
            await ctx.send("Message is en route.")
            await channel.send(await self.bot.error.retrieveError(ctx))
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channel.send(file=file, content="")

    async def getServerConfig(self, ctx: commands.Context):
        return await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM serverconfig WHERE serverid = $1;''', [ctx.guild.id])

    @commands.command(name="DM", description="send a message to anyone's DM")
    async def DM(self, ctx: commands.Context, userID: str, *, message):
        if ctx.author.id == 712509599135301673:
            import re
            await ctx.send("Message is en route.")
            recipient = self.bot.get_user(int(userID))
            await recipient.send(message)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await recipient.send(file=file, content="")

    @commands.command(name="trollWebhookTest", description="send a message wherever you want")
    async def trollweb(self, ctx: commands.Context, *, message):
        from discord import Webhook
        import aiohttp
        if ctx.author.id in [712509599135301673, 686640777505669141]:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url('https://discord.com/api/webhooks/1351525808484651008/C7EO5uUViQ5ZTPQcV06I88Vs0MTBMrbCofopyNd5aaDulqM_h0J-kgcS2U11pjDbhs83', session=session)
                await webhook.send(message, username=ctx.author.nick, avatar_url=ctx.author.avatar.url)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(adminFunctions(bot))

class globalSendDropdown(discord.ui.Select):
    def __init__(self):
        options = []
        options.append(discord.SelectOption(label="Server Owners' DMs", emoji='🏆', value="direct"))
        options.append(discord.SelectOption(label="General Chats", emoji='🏆', value="generalchannelID"))
        options.append(discord.SelectOption(label="Bot Updates", emoji='🏆', value="updateschannelID"))
        options.append(discord.SelectOption(label="Server Managers", emoji='🏆', value="managerchannelID"))
        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # promptResponses[self.authorID] = self.values[0]
        self.view.result = self.values[0]
        await interaction.response.defer()
        self.view.stop()

class globalSendDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(globalSendDropdown())