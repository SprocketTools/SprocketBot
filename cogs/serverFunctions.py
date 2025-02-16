import asyncio
import datetime as datetime
import random
import io
from discord.ext import tasks
import discord

import pandas as pd
from discord.ext import commands

from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions
updateFrequency = 60
promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions
from main import SQLfunctions
class serverFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        now = datetime.datetime.now()
        current_minute = now.minute
        current_second = now.second
        seconds_count = int(3600 - (current_minute*60 + current_second))
        seconds_count = seconds_count % updateFrequency
        status_log_channel = self.bot.get_channel(1152377925916688484)
        await status_log_channel.send(f"Auto unban cycle: **{int(seconds_count/60)} minutes,** **{int(seconds_count % 60)} seconds** from now.")
        await asyncio.sleep(seconds_count)
        await self.loopUpdate.start()
    @tasks.loop(seconds=updateFrequency)
    async def loopUpdate(self):
        current_time = int(datetime.datetime.now().timestamp())
        setdata = await SQLfunctions.databaseFetchdict('''SELECT * FROM modlogs WHERE name = 'Ban' AND endtime < now() AND timestamp < endtime;''')
        for data in setdata:
            try:
                server = self.bot.get_guild(data['serverid'])
                user = await self.bot.fetch_user(data['userid'])
                await server.unban(user)
                await SQLfunctions.databaseExecuteDynamic('''UPDATE modlogs SET name = 'Expired Ban' WHERE name = 'Ban' AND endtime < now() AND serverid = $1 AND userid = $2 AND timestamp < endtime;''', [server.id, user.id])
            except Exception:
                serverData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM serverconfig WHERE serverid = $1;''', [data['serverid']])
                try:
                    server = self.bot.get_guild(data['serverid'])
                    user = await self.bot.fetch_user(data['userid'])
                    channel = self.bot.get_channel(serverData['managerchannelid'])
                    await channel.send(f'I am unable to lift the ban for <@{data["userid"]}> (userID: {data["userid"]})')
                    await SQLfunctions.databaseExecuteDynamic('''UPDATE modlogs SET name = 'Expired Ban' WHERE name = 'Ban' AND endtime < now() AND serverid = $1 AND userid = $2 AND timestamp < endtime;''',[server.id, user.id])
                except Exception:
                    pass






    @commands.command(name="setupmoderationdatabase", description="Setup the moderation database")
    async def setupmoderationdatabase(self, ctx: commands.Context):
        if ctx.author.id != self.bot.owner_id:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS modlogs;''')
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS modrules;''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS modrules (serverid BIGINT, name VARCHAR, description VARCHAR, points INT);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS modlogs (logid BIGINT, serverid BIGINT, userid BIGINT, moderatorid BIGINT, name VARCHAR, description VARCHAR, points INT, timestamp TIMESTAMP, endtime TIMESTAMP, type VARCHAR);''')
        await ctx.send("## Done!")

    @commands.has_permissions(ban_members=True)
    @app_commands.default_permissions(administrator=True)
    @commands.hybrid_command(name="addrule", description="Add a moderation rule or subrule")
    async def addRule(self, ctx: commands.Context, name: str, points: int, description: str):
        serverid = ctx.guild.id
        # ruleName = await textTools.getCappedResponse(ctx, '''What do you want the name of the rule to be?''', 32)
        # ruleDesc = await textTools.getCappedResponse(ctx,'''Reply with a short description of the rule.''',128)
        # pointCount = await textTools.getFlooredIntResponse(ctx,'''How many points do you want this rule to be worth?''',0)
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO modrules VALUES ($1, $2, $3, $4);''', [serverid, name, description, points])
        await ctx.send("## Done!")

    @commands.hybrid_command(name="rules", description="List the server rules")
    async def rules(self, ctx: commands.Context):
        data = await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM modrules WHERE serverid = $1;''', [ctx.guild.id])
        embed = discord.Embed(title=f"{ctx.guild.name}'s server rules", color=discord.Color.random())
        for rule in data:
            embed.add_field(name=f"{rule['name']} ({rule['points']} points)", value=f"{rule['description']}", inline=False)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Add rules using the /addrule slash command!")
        await ctx.send(embed=embed)

    @commands.has_permissions(ban_members=True)
    @commands.hybrid_command(name="warnings", description="View a member's warnings")
    async def warnings(self, ctx: commands.Context, user: discord.Member):
        data = await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM modlogs WHERE userid = $1 AND serverid = $2;''', [user.id, ctx.guild.id])
        points_total = 0
        embed = discord.Embed(title=f"{user.name}'s warnings", color=discord.Color.random())
        for rule in data:
            dt = await textTools.getUnixTimestamp(rule['timestamp'])
            # date_string = str().split('.')[0]
            # format_string = "%Y-%m-%d %H:%M:%S"
            # dt = int(datetime.datetime.strptime(date_string, format_string).timestamp())
            embed.add_field(name=rule['name'], value=f"{rule['description']}\nModerator: <@{rule['moderatorid']}>\nTime: <t:{dt}:f>", inline=False)
            points_total += int(rule["points"])
        embed.set_footer(text=f"Total points: {points_total}")
        embed.set_thumbnail(url=user.avatar.url)
        await ctx.send(embed=embed)
        delWarnTrigger = await discordUIfunctions.getButtonChoice(ctx, ["Delete warn"])
        if delWarnTrigger == "Delete warn" and len(data) > 0:
            warnList = []
            warnData = {}
            for rule in data:
                warnList.append(rule['description'])
                warnData[rule['description']] = rule['timestamp']
            warnChoice = await discordUIfunctions.getChoiceFromList(ctx, warnList, "Which warn do you want to delete?")
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM modlogs WHERE userid = $1 AND serverid = $2 AND description = $3 AND timestamp = $4;''', [user.id, ctx.guild.id, warnChoice, warnData[warnChoice]])
            await ctx.send("Done!")

    @commands.has_permissions(ban_members=True)
    @commands.hybrid_command(name="note", description="Leave a mod-visible note about a user")
    async def note(self, ctx: commands.Context, user: discord.Member, reason: str):
        data = await SQLfunctions.databaseFetchdictDynamic('''SELECT name, description, points FROM modrules WHERE serverid = $1;''', [ctx.guild.id])
        dataOut = []
        for rule in data:
            dataOut.append(f'{rule["name"]} - {rule["description"]}')
        await ctx.send("Select the applicable rule violation")
        ruleName = "Staff note"
        points = 0
        # serverid BIGINT, userid BIGINT, moderatorid BIGINT, name VARCHAR, description VARCHAR, points INT, timestamp TIMESTAMP, endtime TIMESTAMP, type VARCHAR
        logValues = [random.randint(1, 123456789), ctx.guild.id, user.id, ctx.author.id, ruleName, reason, points, datetime.datetime.now(), datetime.datetime.now(), "warning"]
        await SQLfunctions.databaseExecuteDynamic('''INSERT into modlogs VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);''', logValues)
        await ctx.send(f'Note logged for **{user.name}**.')

    @commands.has_permissions(ban_members=True)
    @commands.hybrid_command(name="warn", description="Issue a warning")
    async def warn(self, ctx: commands.Context, user: discord.Member, reason: str):
        data = await SQLfunctions.databaseFetchdictDynamic('''SELECT name, description, points FROM modrules WHERE serverid = $1;''', [ctx.guild.id])
        dataOut = []
        for rule in data:
            dataOut.append(f'{rule["name"]} - {rule["description"]}')
        await ctx.send("Select the applicable rule violation")
        ruleName = await discordUIfunctions.getButtonChoice(ctx, dataOut)
        data = (await SQLfunctions.databaseFetchrowDynamic('''SELECT points FROM modrules WHERE serverid = $1 AND name = $2;''',[ctx.guild.id, ruleName.split(' - ')[0]]))
        points = data['points']
        # serverid BIGINT, userid BIGINT, moderatorid BIGINT, name VARCHAR, description VARCHAR, points INT, timestamp TIMESTAMP, endtime TIMESTAMP, type VARCHAR
        logValues = [random.randint(1, 123456789), ctx.guild.id, user.id, ctx.author.id, ruleName, reason, points, datetime.datetime.now(), datetime.datetime.now(), "warning"]
        await SQLfunctions.databaseExecuteDynamic('''INSERT into modlogs VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);''', logValues)
        try:
            messageDM = f"You have been warned in **{ctx.guild.name}**\nReason: {reason}\nRule broken: {ruleName}"
            await user.send(messageDM)
        except Exception:
            await ctx.send("Failed to notify the user; they likely have Sprocket Bot blocked.")
        await ctx.send(f'Warning issued to **{user.name}**.\n')
        points_total = points
        for rule in data:
            points_total += int(rule["points"])
        await ctx.send(f"Total points: {points_total}")

    @commands.has_permissions(ban_members=True)
    @commands.hybrid_command(name="ban", type="ban", description="Ban a user")
    async def ban(self, ctx: commands.Context, user: discord.Member, reason: str, days: int):
        try:
            print(user.name)
        except Exception as e:
            await ctx.send(f'Sprocket Bot could not ban this user: \n{e}')
        serverData = await adminFunctions.getServerConfig(ctx)
        ruleName = "Ban"
        points = 0
        # serverid BIGINT, userid BIGINT, moderatorid BIGINT, name VARCHAR, description VARCHAR, points INT, timestamp TIMESTAMP, endtime TIMESTAMP, type VARCHAR
        timeIn = datetime.datetime.now()
        logValues = [random.randint(1, 123456789), ctx.guild.id, user.id, ctx.author.id, ruleName, reason, points, timeIn, timeIn + datetime.timedelta(days=days), "ban"]
        await SQLfunctions.databaseExecuteDynamic('''INSERT into modlogs VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);''', logValues)
        try:
            messageDM = f"You have been banned from **{ctx.guild.name}**\nReason: {reason}\nDuration: {days}\n{serverData['banmessage']}"
            await user.send(messageDM)
        except Exception:
            await ctx.send("Failed to notify the user; they likely have Sprocket Bot blocked.")
        try:
            await user.ban(reason=f"Banned by {ctx.author.name} - {reason}")
            await ctx.send(f'Ban issued to **{user.name}**.')
        except Exception as e:
            await ctx.send(f'Sprocket Bot could not ban this user: \n{e}')

    @app_commands.command(name="roll", description="🎲 roll a dice")
    async def roll(self, interaction):
        result = random.randint(1, 6)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"**Result:** You rolled a `{result}`!",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

    @commands.has_permissions(ban_members=True)
    @commands.command(name="manageAllRules", description="Edit a faction un bulk")
    async def manageAllRules(self, ctx: commands.Context):

        await ctx.send("Do you have a .csv sheet of your rules ready yet?")
        isReady = await discordUIfunctions.getYesNoChoice(ctx)
        if isReady:

            attachment = await textTools.getFileResponse(ctx, "Upload your .csv file containing all your faction's data.")
            df = pd.read_csv(io.StringIO((await attachment.read()).decode('utf-8')))
            data = df.to_dict(orient='records')
            print(data)
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM modrules WHERE serverid = $1;''', [ctx.guild.id])
            for row in data:
                await SQLfunctions.databaseExecuteDynamic('''INSERT INTO modrules VALUES ($1, $2, $3, $4);''', [ctx.guild.id, row['name'], row['description'], row['points']])
            await ctx.send(f"## Done!\n{ctx.guild.name} now has {len(data)} rules in its catalog.")
        else:
            await ctx.send("Download this file and edit it in a spreadsheet editor.  When you're done, save it as a .csv and run the command again.")
            data = await SQLfunctions.databaseFetchdictDynamic(
                '''SELECT * FROM modrules where serverid = $1;''',[ctx.guild.id])
            # credits: brave AI
            df = pd.DataFrame(data)
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            # Send CSV file
            buffer.seek(0)
            await ctx.channel.send(file=discord.File(buffer, "data.csv"))
            await ctx.send("## Warning\nKeep the rule names and descriptions as short as possible.")

    @commands.command(name="viewSettings", description="Edit a faction un bulk")
    async def viewSettings(self, ctx: commands.Context):
        await serverFunctions.showSettings(self, ctx)

    async def showSettings(self, ctx: commands.Context):
        try:
            serverData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM serverconfig WHERE serverid = $1;''', [ctx.guild.id])
        except Exception:
            await ctx.send("No server configuration detected!  Adding a default config...")
            data = {}
            data['serverid'] = ctx.guild.id
            data['ownerid'] = ctx.guild.owner.id
            data['generalchannelid'] = ctx.guild.channels[0].id
            data['allowfunny'] = True
            data['updateschannelid'] = ctx.guild.channels[0].id
            data['commandschannelid'] = ctx.guild.channels[0].id
            data['managerchannelid'] = ctx.guild.channels[0].id
            data['serverboosterroleid'] = ctx.guild.roles[len(ctx.guild.roles)-1].id
            data['contestmanagerroleid'] = ctx.guild.roles[0].id
            data['botmanagerroleid'] = ctx.guild.roles[0].id
            data['campaignmanagerroleid'] = ctx.guild.roles[0].id
            data['flagthreshold'] = 3
            data['flagaction'] = 'nothing'
            data['flagping'] = 'nobody'
            data['flagpingid'] = ctx.guild.roles[0].id
            data['musicroleid'] = ctx.guild.roles[len(ctx.guild.roles)-1].id
            data['banmessage'] = "`VALUE MISSING`"
            await SQLfunctions.databaseExecuteDynamic('''INSERT INTO serverconfig VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17);''', data)
            await ctx.send("Done!")
            serverData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM serverconfig WHERE serverid = $1;''', [ctx.guild.id])
        for key, value in serverData.items():
            if value == None:
                serverData[key] = "`UPDATE THIS VALUE`"
        embed = discord.Embed(title=f"Server Config: {ctx.guild.name}",color=discord.Color.random())
        print(serverData)
        embed.add_field(name="General chat", value=f"<#{serverData['generalchannelid']}>", inline=False)
        embed.add_field(name="Announcements chat",value=f"<#{serverData['updateschannelid']}>",inline=False)
        embed.add_field(name="Bot commands chat", value=f"<#{serverData['commandschannelid']}>", inline=False)
        embed.add_field(name="Server managers chat", value=f"<#{serverData['managerchannelid']}>", inline=False)
        embed.add_field(name="Server booster role", value=(f"<@&{serverData['serverboosterroleid']}>"), inline=False)
        embed.add_field(name="Contest manager role",value=(f"<@&{serverData['contestmanagerroleid']}>"),inline=False)
        embed.add_field(name="Bot manager role",value=(f"<@&{serverData['botmanagerroleid']}>"),inline=False)
        embed.add_field(name="Campaign manager role",value=(f"<@&{serverData['campaignmanagerroleid']}>"),inline=False)
        embed.add_field(name="Music player role",value=(f"<@&{serverData['musicroleid']}>"),inline=False)
        embed.add_field(name="Fun module",value=serverData['allowfunny'],inline=False)
        embed.add_field(name="Threshold of scam messages", value=serverData['flagthreshold'], inline=False)
        embed.add_field(name="Action taken on scammer", value=serverData['flagaction'], inline=False)
        embed.add_field(name="What to ping on scam action", value=f"@{serverData['flagping']}", inline=False)
        if serverData['flagping'] == "custom":
            embed.add_field(name="Role pinged on scam action", value=(f"<@&{serverData['flagpingid']}>"), inline=False)
        embed.add_field(name="Ban message", value=serverData['banmessage'], inline=False)
        embed.set_thumbnail(url=ctx.guild.icon)
        await ctx.send(embed=embed)
        # except Exception:
        #     await ctx.send(await errorFunctions.retrieveError(ctx))
        #     await ctx.send(
        #         "It appears that your configuration is out of date and needs to be updated.  Use `-setup` to update your server settings.")

    @commands.command(name="settings", description="Configure Sprocket Bot")
    async def settings(self, ctx: commands.Context):
        if not ctx.message.author.guild_permissions.administrator:
            if ctx.author.id == self.bot.owner_id:
                await ctx.send("You are the bot owner.  Override the restriction against your server permissions?")
                answer = await discordUIfunctions.getYesNoChoice(ctx)
                if not answer:
                    return
            else:
                return
        continue_val = True
        while continue_val:
            data = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM serverconfig WHERE serverid = $1''', [ctx.guild.id])
            print(data)
            print(data)
            await serverFunctions.showSettings(self, ctx)
            await ctx.send("What statistic do you wish to modify?")
            inList = ["General channel", "Announcements channel", "Bot commands channel", "Server managers channel", "Server booster role", "Contest manager role", "Bot manager role", "Campaign manager role", "Music player role", "Toggle the fun module", "Scam message threshold", "Action taken on scammer", "Who to ping post-action", "Ban message", "Exit"]
            answer = str.lower(await discordUIfunctions.getButtonChoice(ctx, inList))
            if answer == "exit":
                await ctx.send("Alright, have fun.")
                return
            elif answer == "general channel":
                new_value = await textTools.getChannelResponse(ctx, "Reply with a mention of your general channel.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET generalchannelid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "announcements channel":
                new_value = await textTools.getChannelResponse(ctx, "Reply with a mention of your announcements channel.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET updateschannelid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "bot commands channel":
                new_value = await textTools.getChannelResponse(ctx, "Reply with a mention of your bot commands channel.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET commandschannelid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "server managers channel":
                new_value = await textTools.getChannelResponse(ctx, "Reply with a mention of your server managers channel.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET managerchannelid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "server booster role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET serverboosterroleid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "contest manager role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET contestmanagerroleid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "bot manager role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET botmanagerroleid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "campaign manager role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET campaignmanagerroleid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "music player role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET musicroleid = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "toggle the fun module":
                new_value = not data['allowfunny']
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET allowfunny = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "scam message threshold":
                new_value = await textTools.getFlooredIntResponse(ctx, "How many scam messages do you want a user to send before triggering the detector?  A minimum of 3 is required.", 3)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET flagthreshold = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "action taken on scammer":
                await ctx.send("How many scam messages do you want a user to send before triggering the detector?  A minimum of 3 is required.")
                new_value = await discordUIfunctions.getButtonChoice(ctx, ["nothing", "timeout for 12 hours", "kick"])
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET flagaction = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            elif answer == "who to ping post-action":
                new_value = await discordUIfunctions.getButtonChoice(ctx, ["nobody", "everyone", "here", "custom"])
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET flagping = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
                if new_value == "custom":
                    new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role that you wish to have pinged.")
                    await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET flagpingid = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "ban message":
                new_value = await textTools.getResponse(ctx, "What do you want your ban message to include?  Include ban appeals forms or other links in your reply if desired.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE serverconfig SET banmessage = $1 WHERE serverid = $2;''',[new_value, ctx.guild.id])
            else:
                await ctx.send("Looks like you clicked on an unsupported button, or this window timed out.")
                return
            await ctx.send("## Done!")



async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(serverFunctions(bot))