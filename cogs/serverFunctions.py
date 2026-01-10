import asyncio
import datetime as datetime
import random
import io
from discord.ext import tasks
import discord
import type_hints
import pandas as pd
from discord.ext import commands
import main
from typing import Union

updateFrequency = 60
promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions


class serverFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        now = datetime.datetime.now()
        current_minute = now.minute
        current_second = now.second
        seconds_count = int(3600 - (current_minute * 60 + current_second))
        seconds_count = seconds_count % updateFrequency
        status_log_channel = self.bot.get_channel(1152377925916688484)
        if status_log_channel:
            await status_log_channel.send(
                f"Auto unban cycle: **{int(seconds_count / 60)} minutes,** **{int(seconds_count % 60)} seconds** from now.")
        await asyncio.sleep(seconds_count)
        await self.loopUpdate.start()

    @tasks.loop(seconds=updateFrequency)
    async def loopUpdate(self):
        try:
            setdata = await self.bot.sql.databaseFetchdict(
                '''SELECT * FROM modlogs WHERE name = 'Ban' AND endtime < now() AND timestamp < endtime;''')
            for data in setdata:
                try:
                    server = self.bot.get_guild(data['serverid'])
                    if server:
                        try:
                            user = await self.bot.fetch_user(data['userid'])
                            await server.unban(user)
                        except discord.NotFound:
                            pass

                        await self.bot.sql.databaseExecuteDynamic(
                            '''UPDATE modlogs SET name = 'Expired Ban' WHERE name = 'Ban' AND endtime < now() AND serverid = $1 AND userid = $2 AND timestamp < endtime;''',
                            [server.id, data['userid']])
                except Exception as e:
                    print(f"Error in unban loop for {data['userid']}: {e}")
        except Exception as e:
            print(f"Database error in loopUpdate: {e}")

    @commands.command(name="setupmoderationdatabase", description="Setup the moderation database")
    async def setupmoderationdatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS modlogs;''')
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS modrules;''')
        await self.bot.sql.databaseExecute(
            '''CREATE TABLE IF NOT EXISTS modrules (serverid BIGINT, name VARCHAR, description VARCHAR, points INT);''')
        await self.bot.sql.databaseExecute(
            '''CREATE TABLE IF NOT EXISTS modlogs (logid BIGINT, serverid BIGINT, userid BIGINT, moderatorid BIGINT, name VARCHAR, description VARCHAR, points INT, timestamp TIMESTAMP, endtime TIMESTAMP, type VARCHAR);''')
        await ctx.send("## Done!")

    @commands.has_permissions(ban_members=True)
    @app_commands.default_permissions(administrator=True)
    @commands.hybrid_command(name="addrule", description="Add a moderation rule or subrule")
    async def addRule(self, ctx: commands.Context, name: str, points: int, description: str):
        serverid = ctx.guild.id
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO modrules VALUES ($1, $2, $3, $4);''',
                                                  [serverid, name, description, points])
        await ctx.send("## Done!")

    @commands.hybrid_command(name="rules", description="List the server rules")
    async def rules(self, ctx: commands.Context):
        data = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM modrules WHERE serverid = $1;''',
                                                           [ctx.guild.id])
        embed = discord.Embed(title=f"{ctx.guild.name}'s server rules", color=discord.Color.random())
        for rule in data:
            embed.add_field(name=f"{rule['name']} ({rule['points']} points)", value=f"{rule['description']}",
                            inline=False)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Add rules using the /addrule slash command!")
        await ctx.send(embed=embed)

    # --- WARNINGS COMMAND (UPDATED) ---
    @commands.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    @commands.hybrid_command(name="warnings", description="View a member's warnings")
    async def warnings(self, ctx: commands.Context, user: Union[discord.Member, discord.User]):
        data = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM modlogs WHERE userid = $1 AND serverid = $2;''', [user.id, ctx.guild.id])

        points_total = 0
        points_365 = 0
        last_ban_timestamp = None

        now = datetime.datetime.now()
        cutoff_365 = now - datetime.timedelta(days=365)

        embed = discord.Embed(title=f"{user.name}'s warnings", color=discord.Color.random())

        for rule in data:
            dt = await textTools.getUnixTimestamp(rule['timestamp'])
            embed.add_field(name=rule['name'],
                            value=f"{rule['description']}\nModerator: <@{rule['moderatorid']}>\nTime: <t:{dt}:f>",
                            inline=False)

            p = int(rule["points"])
            points_total += p

            if rule['timestamp'] > cutoff_365:
                points_365 += p

            # Check for last ban
            if rule['type'] == 'ban':
                if last_ban_timestamp is None or rule['timestamp'] > last_ban_timestamp:
                    last_ban_timestamp = rule['timestamp']

        # Determine string for last ban
        if last_ban_timestamp:
            delta = now - last_ban_timestamp
            ban_str = f"{delta.days} days ago"
        else:
            ban_str = "Never"

        embed.add_field(
            name="Recent Activity",
            value=f"Time since last ban: **{ban_str}**\nPoints (365 days): **{points_365}**",
            inline=False
        )
        embed.set_footer(text=f"Total Lifetime Points: {points_total}")
        embed.set_thumbnail(url=user.display_avatar.url)

        await ctx.send(embed=embed)

        if len(data) > 0:
            delWarnTrigger = await ctx.bot.ui.getButtonChoice(ctx, ["Delete warn"])
            if delWarnTrigger == "Delete warn":
                warnList = []
                warnData = {}
                for rule in data:
                    desc_short = (rule['description'][:95] + '..') if len(rule['description']) > 95 else rule[
                        'description']
                    warnList.append(desc_short)
                    warnData[desc_short] = rule

                warnChoice = await ctx.bot.ui.getChoiceFromList(ctx, warnList, "Which warn do you want to delete?")
                if warnChoice:
                    full_rule = warnData[warnChoice]
                    await self.bot.sql.databaseExecuteDynamic(
                        '''DELETE FROM modlogs WHERE userid = $1 AND serverid = $2 AND description = $3 AND timestamp = $4;''',
                        [user.id, ctx.guild.id, full_rule['description'], full_rule['timestamp']]
                    )
                    await ctx.send("Done!")

    @warnings.error
    async def warnings_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Could not find that user. Try using their User ID.", ephemeral=True)
        else:
            await ctx.send(f"Error: {error}", ephemeral=True)

    # --- NOTE COMMAND (UPDATED) ---
    @commands.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    @commands.hybrid_command(name="note", description="Leave a mod-visible note about a user")
    async def note(self, ctx: commands.Context, user: Union[discord.Member, discord.User], reason: str, points: int):
        ruleName = "Staff note"
        logValues = [random.randint(1, 123456789), ctx.guild.id, user.id, ctx.author.id, ruleName, reason, points,
                     datetime.datetime.now(), datetime.datetime.now(), "warning"]
        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT into modlogs VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);''', logValues)

        # Calculate Stats
        data = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM modlogs WHERE userid = $1 AND serverid = $2;''', [user.id, ctx.guild.id])
        points_total = 0
        points_365 = 0
        last_ban_timestamp = None
        now = datetime.datetime.now()
        cutoff_365 = now - datetime.timedelta(days=365)

        for rule in data:
            p = int(rule["points"])
            points_total += p
            if rule['timestamp'] > cutoff_365:
                points_365 += p
            if rule['type'] == 'ban':
                if last_ban_timestamp is None or rule['timestamp'] > last_ban_timestamp:
                    last_ban_timestamp = rule['timestamp']

        if last_ban_timestamp:
            ban_str = f"{(now - last_ban_timestamp).days} days ago"
        else:
            ban_str = "Never"

        await ctx.send(
            f'Note logged for **{user.name}**.\n\nTotal points: {points_total}\nLast Ban: {ban_str}\nPoints (365d): {points_365}')

    @note.error
    async def note_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Could not find that user. Try using their User ID.", ephemeral=True)
        else:
            await ctx.send(f"Error: {error}", ephemeral=True)

    # --- WARN COMMAND (UPDATED) ---
    @commands.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    @commands.hybrid_command(name="warn", description="Issue a warning")
    async def warn(self, ctx: commands.Context, user: Union[discord.Member, discord.User], reason: str):
        data = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT name, description, points FROM modrules WHERE serverid = $1;''', [ctx.guild.id])
        dataOut = []
        for rule in data:
            dataOut.append(f'{rule["name"]} - {rule["description"]}')

        await ctx.send("Select the applicable rule violation")
        ruleName = await ctx.bot.ui.getButtonChoice(ctx, dataOut)

        if not ruleName:
            return await ctx.send("Operation cancelled or timed out.")

        data = (await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT points FROM modrules WHERE serverid = $1 AND name = $2;''',
            [ctx.guild.id, ruleName.split(' - ')[0]]))
        points = data['points']

        logValues = [random.randint(1, 123456789), ctx.guild.id, user.id, ctx.author.id, ruleName, reason, points,
                     datetime.datetime.now(), datetime.datetime.now(), "warning"]
        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT into modlogs VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);''', logValues)

        try:
            messageDM = f"You have been warned in **{ctx.guild.name}**\nReason: {reason}\nRule broken: {ruleName}"
            await user.send(messageDM)
        except Exception:
            await ctx.send("User is not in the server or has DMs blocked. Warning has been logged to database.")

        # Calculate Stats
        data = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM modlogs WHERE userid = $1 AND serverid = $2;''', [user.id, ctx.guild.id])
        points_total = 0
        points_365 = 0
        last_ban_timestamp = None
        now = datetime.datetime.now()
        cutoff_365 = now - datetime.timedelta(days=365)

        for rule in data:
            p = int(rule["points"])
            points_total += p
            if rule['timestamp'] > cutoff_365:
                points_365 += p
            if rule['type'] == 'ban':
                if last_ban_timestamp is None or rule['timestamp'] > last_ban_timestamp:
                    last_ban_timestamp = rule['timestamp']

        if last_ban_timestamp:
            ban_str = f"{(now - last_ban_timestamp).days} days ago"
        else:
            ban_str = "Never"

        await ctx.send(
            f"Warning issued to **{user.name}**.\n\nTotal points: {points_total}\nLast Ban: {ban_str}\nPoints (365d): {points_365}")

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Could not find that user. Try using their User ID.", ephemeral=True)
        else:
            await ctx.send(f"Error: {error}", ephemeral=True)

    @commands.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    @commands.hybrid_command(name="ban", description="Ban a user")
    @app_commands.describe(
        user="The user to ban (ID or Mention)",
        reason="Reason for the ban",
        days="Duration of the ban in days (for database logging)",
        delete_days="Clean up messages from the last X days (0-7)"
    )
    async def ban(self, ctx: commands.Context, user: Union[discord.Member, discord.User],
                  reason: str = "No reason provided", days: int = 0, delete_days: int = 0):
        print(f"DEBUG: Ban command triggered by {ctx.author.name} targeting {user}")
        await ctx.defer()

        user_to_ban = user

        # 1. Log to Database
        try:
            serverData = await adminFunctions.getServerConfig(ctx)
            ruleName = "Ban"
            points = 0
            timeIn = datetime.datetime.now()
            endTime = timeIn + datetime.timedelta(days=days) if days > 0 else timeIn + datetime.timedelta(days=3650)

            logValues = [random.randint(1, 123456789), ctx.guild.id, user.id, ctx.author.id, ruleName, reason, points,
                         timeIn, endTime, "ban"]
            await self.bot.sql.databaseExecuteDynamic(
                '''INSERT into modlogs VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);''', logValues)
        except Exception as e:
            print(f"Database logging failed: {e}")

        # 2. Notify User
        try:
            ban_msg_content = serverData.get('banmessage', 'You have been banned.')
            messageDM = f"You have been banned from **{ctx.guild.name}**\nReason: {reason}\nDuration: {days} days\n{ban_msg_content}"
            await user_to_ban.send(messageDM)
        except Exception:
            await ctx.send("Failed to notify the user (DMs closed or bot blocked).")

        # 3. Execute Ban
        target_username = user_to_ban.display_name if hasattr(user_to_ban, "display_name") else user_to_ban.name
        try:
            await ctx.guild.ban(user_to_ban, reason=f"Banned by {ctx.author.name} - {reason}",
                                delete_message_seconds=delete_days * 86400)
            await ctx.send(f'**{target_username}** has been banned.')
        except Exception as e:
            await ctx.send(f'Failed to ban user on Discord: {e}')

    @ban.error
    async def ban_error(self, ctx, error):
        print(f"DEBUG: Ban Error: {error}")
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban members.", ephemeral=True)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I do not have permission to ban members.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Could not find that user. Try using their User ID.", ephemeral=True)
        else:
            await ctx.send(f"Error: {error}", ephemeral=True)

    @app_commands.command(name="roll", description="🎲 roll a dice")
    async def roll(self, interaction):
        result = random.randint(1, 6)
        embed = discord.Embed(
            title=f"🎲 Dice Roll",
            description=f"**Result:** You rolled a `{result}`!",
            color=discord.Color.random()
        )
        await interaction.response.send_message(embed=embed)

    @commands.has_permissions(ban_members=True)
    @commands.command(name="manageAllRules", description="Edit a faction un bulk")
    async def manageAllRules(self, ctx: commands.Context):

        await ctx.send("Do you have a .csv sheet of your rules ready yet?")
        isReady = await ctx.bot.ui.getYesNoChoice(ctx)
        if isReady:

            attachment = await textTools.getFileResponse(ctx,
                                                         "Upload your .csv file containing all your faction's data.")
            df = pd.read_csv(io.StringIO((await attachment.read()).decode('utf-8')))
            data = df.to_dict(orient='records')
            print(data)
            await self.bot.sql.databaseExecuteDynamic('''DELETE FROM modrules WHERE serverid = $1;''', [ctx.guild.id])
            for row in data:
                await self.bot.sql.databaseExecuteDynamic('''INSERT INTO modrules VALUES ($1, $2, $3, $4);''',
                                                          [ctx.guild.id, row['name'], row['description'],
                                                           row['points']])
            await ctx.send(f"## Done!\n{ctx.guild.name} now has {len(data)} rules in its catalog.")
        else:
            await ctx.send(
                "Download this file and edit it in a spreadsheet editor.  When you're done, save it as a .csv and run the command again.")
            data = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM modrules where serverid = $1;''', [ctx.guild.id])
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
            serverData = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM serverconfig WHERE serverid = $1;''', [ctx.guild.id])
        except Exception:
            await ctx.send("No server configuration detected!  Adding a default config...")
            data = await self._generate_best_guess_config(ctx.guild)
            await self.bot.sql.databaseExecuteDynamic(
                '''INSERT INTO serverconfig VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18);''',
                list(data.values()))
            await ctx.send("Done!")
        serverData = await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM serverconfig WHERE serverid = $1;''',
                                                                [ctx.guild.id])
        for key, value in serverData.items():
            if value == None:
                serverData[key] = "`UPDATE THIS VALUE`"
        embed = discord.Embed(title=f"Server Config: {ctx.guild.name}", color=discord.Color.random())

        embed.add_field(name="Channels",
                        value=f"General: <#{serverData['generalchannelid']}>\nAnnouncements: <#{serverData['updateschannelid']}>\nBot commands: <#{serverData['commandschannelid']}>\nServer managers: <#{serverData['managerchannelid']}>",
                        inline=False)
        embed.add_field(name="Roles", value=(
            f"Server booster: <@&{serverData['serverboosterroleid']}>\nContest manager: <@&{serverData['contestmanagerroleid']}>\nBot manager: <@&{serverData['botmanagerroleid']}>\nCampaign manager: <@&{serverData['campaignmanagerroleid']}>\nMusic commands role: <@&{serverData['musicroleid']}>"),
                        inline=False)
        embed.add_field(name="Fun",
                        value=f"Allow random error replies: {serverData['allowfunny']}\nAllow AI conversations: {serverData['allowconversations']}\nJarvis cooldown: {round(serverData['jarviscooldown'] / 60)} minutes\nJarvis burst count: {serverData['jarvisburst']}",
                        inline=False)
        embed.add_field(name="Threshold of scam messages", value=serverData['flagthreshold'], inline=False)
        embed.add_field(name="Action taken on scammer", value=serverData['flagaction'], inline=False)
        embed.add_field(name="What to ping on scam action", value=f"@{serverData['flagping']}", inline=False)
        if serverData['flagping'] == "custom":
            embed.add_field(name="Role pinged on scam action", value=(f"<@&{serverData['flagpingid']}>"), inline=False)
        embed.add_field(name="Ban message", value=serverData['banmessage'], inline=False)
        if serverData['clickupkey'] != "0":
            embed.add_field(name="ClickUp integration", value=f"True", inline=False)
        else:
            embed.add_field(name="ClickUp integration", value=f"False", inline=False)

        embed.set_thumbnail(url=ctx.guild.icon)
        await ctx.send(embed=embed)

    async def _generate_best_guess_config(self, guild: discord.Guild) -> dict:
        """Generates a best-guess configuration for a server."""

        def find_channel_by_names(names_to_check):
            for channel in guild.text_channels:
                for name in names_to_check:
                    if name in channel.name.lower().replace('-', '').replace('_', ''):
                        return channel
            return guild.system_channel or (guild.text_channels[0] if guild.text_channels else None)

        def find_role_by_names(names_to_check):
            matching_roles = []
            for role in guild.roles:
                for name in names_to_check:
                    if name in role.name.lower():
                        matching_roles.append(role)

            if matching_roles:
                return max(matching_roles, key=lambda r: r.position)

            return guild.roles[-1] if guild.roles else guild.default_role

        manager_role = find_role_by_names(["admin", "moderator", "staff", "manager"])
        booster_role = find_role_by_names(["booster"])

        general_channel = find_channel_by_names(["general", "chat", "lounge"])
        updates_channel = find_channel_by_names(["updates", "announcements", "news"])
        commands_channel = find_channel_by_names(["botcommands", "commands", "botspam"])
        manager_channel = find_channel_by_names(["staff", "admin", "moderator"])

        config = {
            "serverid": guild.id,
            "ownerid": guild.owner_id,
            "generalchannelid": general_channel.id if general_channel else 0,
            "allowfunny": True,
            "updateschannelid": updates_channel.id if updates_channel else 0,
            "commandschannelid": commands_channel.id if commands_channel else 0,
            "managerchannelid": manager_channel.id if manager_channel else 0,
            "serverboosterroleid": booster_role.id if booster_role else 0,
            "contestmanagerroleid": manager_role.id if manager_role else 0,
            "campaignmanagerroleid": manager_role.id if manager_role else 0,
            "botmanagerroleid": manager_role.id if manager_role else 0,
            "flagthreshold": 3,
            "flagaction": "timeout for 12 hours",
            "flagping": "nobody",
            "flagpingid": 0,
            "musicroleid": 0,
            "banmessage": f"You have been banned from {guild.name}.",
            "clickupkey": "0",
            "jarviscooldown": 3600,
            "jarvisburst": 4,
            "allowconversations": True,
        }
        return config

    @commands.command(name="settings", description="Configure Sprocket Bot")
    async def settings(self, ctx: commands.Context):
        cooldown_min = 30
        if not ctx.message.author.guild_permissions.administrator:
            if ctx.author.id == main.ownerID:
                await ctx.send("You are the bot owner.  Override the restriction against your server permissions?")
                answer = await ctx.bot.ui.getYesNoChoice(ctx)
                if not answer:
                    return
            else:
                return
        continue_val = True
        if ctx.author.id == main.ownerID:
            cooldown_min = 0
        while continue_val:
            data = await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM serverconfig WHERE serverid = $1''',
                                                              [ctx.guild.id])
            await serverFunctions.showSettings(self, ctx)
            await ctx.send("What setting do you wish to modify?")
            inList = ["General channel", "Announcements channel", "Bot commands channel", "Server managers channel",
                      "Server booster role", "Contest manager role", "Bot manager role", "Campaign manager role",
                      "Music player role", "Toggle the fun module", "Scam message threshold", "Action taken on scammer",
                      "Who to ping post-action", "Ban message", "Clickup Integration", "Jarvis Cooldown",
                      "Jarvis Burst", "Toggle AI Conversations", "Exit"]
            answer = str.lower(await ctx.bot.ui.getButtonChoice(ctx, inList))
            if answer == "exit":
                await ctx.send("Alright, have fun.")
                return
            elif answer == "general channel":
                new_value = await textTools.getChannelResponse(ctx, "Reply with a mention of your general channel.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET generalchannelid = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            elif answer == "announcements channel":
                new_value = await textTools.getChannelResponse(ctx,
                                                               "Reply with a mention of your announcements channel.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET updateschannelid = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            elif answer == "bot commands channel":
                new_value = await textTools.getChannelResponse(ctx,
                                                               "Reply with a mention of your bot commands channel.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET commandschannelid = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            elif answer == "server managers channel":
                new_value = await textTools.getChannelResponse(ctx,
                                                               "Reply with a mention of your server managers channel.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET managerchannelid = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            elif answer == "server booster role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET serverboosterroleid = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            elif answer == "contest manager role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET contestmanagerroleid = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            elif answer == "bot manager role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET botmanagerroleid = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            elif answer == "campaign manager role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET campaignmanagerroleid = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            elif answer == "music player role":
                new_value = await textTools.getRoleResponse(ctx, "Reply with the ID of your role.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET musicroleid = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "toggle the fun module":
                new_value = not data['allowfunny']
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET allowfunny = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "scam message threshold":
                new_value = await textTools.getFlooredIntResponse(ctx,
                                                                  "How many scam messages do you want a user to send before triggering the detector?  A minimum of 3 is required.",
                                                                  3)
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET flagthreshold = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "action taken on scammer":
                await ctx.send(
                    "How many scam messages do you want a user to send before triggering the detector?  A minimum of 3 is required.")
                new_value = await ctx.bot.ui.getButtonChoice(ctx, ["nothing", "timeout for 12 hours", "kick"])
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET flagaction = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "who to ping post-action":
                new_value = await ctx.bot.ui.getButtonChoice(ctx, ["nobody", "everyone", "here", "custom"])
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET flagping = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
                if new_value == "custom":
                    new_value = await textTools.getRoleResponse(ctx,
                                                                "Reply with the ID of your role that you wish to have pinged.")
                    await self.bot.sql.databaseExecuteDynamic(
                        f'''UPDATE serverconfig SET flagpingid = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "ban message":
                new_value = await textTools.getResponse(ctx,
                                                        "What do you want your ban message to include?  Include ban appeals forms or other links in your reply if desired.")
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET banmessage = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "clickup integration":
                new_value = await textTools.getResponse(ctx,
                                                        "What is the API key to your CLickUp setup?  Reply with a 0 to clear your key.",
                                                        0)
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET clickupkey = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "jarvis cooldown":
                new_value = await textTools.getFlooredIntResponse(ctx,
                                                                  f"What should the Jarvis cooldown be?  Reply with a number in minutes (min. {cooldown_min}).",
                                                                  cooldown_min) * 60
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET jarviscooldown = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "jarvis burst":
                new_value = await textTools.getCappedIntResponse(ctx,
                                                                 f"How many times can someone interact with Jarvis before triggering a cooldown?  Reply with a number (up to {42 - cooldown_min})",
                                                                 (42 - cooldown_min))
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET jarvisburst = $1 WHERE serverid = $2;''', [new_value, ctx.guild.id])
            elif answer == "toggle ai conversations":
                new_value = not data['allowconversations']
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE serverconfig SET allowconversations = $1 WHERE serverid = $2;''',
                    [new_value, ctx.guild.id])
            else:
                await ctx.send("Looks like you clicked on an unsupported button, or this window timed out.")
                return
            await ctx.send("## Done!")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(serverFunctions(bot))