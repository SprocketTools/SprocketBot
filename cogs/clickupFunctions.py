import asyncio
import datetime
import requests
import json
import discord
from discord.ext import commands, tasks
from cogs.textTools import textTools
import main  # To access main.ownerID and other main settings
from cogs.adminFunctions import adminFunctions  # For getServerConfig


# Removed: from difflib import SequenceMatcher # This synchronous module is removed to prevent blocking.

# ClickUp API Endpoints
# Note: ClickUp API requires a Personal API Token.
# The base URL for V2 is 'https://api.clickup.com/api/v2/'

class clickupFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Final, rigid AI instructions for SUMMARY: Word limit kept low for stability.
        self.ai_instructions = "You are a professional project manager tasked with summarizing the most pressing tasks for the day and the upcoming week from a list of ClickUp tasks. Your summary should be clear, concise, and professional. Group tasks by urgency (Overdue, Due Today, Due This Week), using a new section heading for each. **For every task, start a new bullet point.** The **STRICT** format for each bullet must be: **Task Title (bolded)\nAssigned to: [User @PING or ClickUp Name]. Summary of work required from Description**. The summary must be under 100 words. Do not use any introductory phrases."
        # Start the scheduled task loop
        self.daily_report.start()

    def cog_unload(self):
        # Cancel the loop when the cog is unloaded
        self.daily_report.cancel()

    @commands.command(name="setupclickup", description="Sets up the required SQL table for ClickUp user mapping.")
    async def setup_clickup_database(self, ctx: commands.Context):
        """Creates the clickup_mappings table if it doesn't exist."""
        if ctx.author.id != main.ownerID:
            await ctx.send("Permission denied. Only the bot owner can run database setup commands.")
            return

        prompt = ('''CREATE TABLE IF NOT EXISTS clickup_mappings (
                        serverid BIGINT,
                        clickup_name VARCHAR,
                        discord_id BIGINT,
                        PRIMARY KEY (serverid, clickup_name)
                    );''')

        try:
            await self.bot.sql.databaseExecute(prompt)
            await ctx.send(
                "✅ **ClickUp mapping table (`clickup_mappings`) created successfully!** You can now use the `/setclickupuser` command.")
        except Exception as e:
            await ctx.send(f"❌ Failed to create table. Error: ```{e}```")

    @commands.command(name="setclickupuser",
                      description="Map a ClickUp user name to a Discord member for accurate pings.")
    async def set_clickup_user(self, ctx: commands.Context, clickup_name: str, member: discord.Member):
        """Maps a ClickUp assignee name to a Discord member's ID using SQL."""

        # Check permissions (assuming Bot Managers can run this)
        server_config = await adminFunctions.getServerConfig(self, ctx)
        bot_manager_role_id = server_config.get('botmanagerroleid')

        is_bot_manager = False
        if bot_manager_role_id and isinstance(ctx.author, discord.Member):
            for role in ctx.author.roles:
                if role.id == bot_manager_role_id:
                    is_bot_manager = True
                    break

        if not ctx.author.guild_permissions.administrator and ctx.author.id != main.ownerID and not is_bot_manager:
            await ctx.send("You do not have permission to run this command. Must be an administrator or Bot Manager.")
            return

        # Clean the ClickUp name to ensure consistency (remove multi-assignee indicator, make lowercase)
        clean_clickup_name = clickup_name.split(' (+')[0].strip().lower()

        # --- CRITICAL FIX START ---
        # Change fetch method to one that returns a list (which is iterable and handles the 'None' case safely)
        check_query = '''SELECT discord_id FROM clickup_mappings WHERE serverid = $1 AND clickup_name = $2;'''
        existing_mapping = await self.bot.sql.databaseFetchdictDynamic(check_query, [ctx.guild.id, clean_clickup_name])

        try:
            # Check if the list is NOT empty
            if existing_mapping:
                update_query = '''UPDATE clickup_mappings SET discord_id = $3 WHERE serverid = $1 AND clickup_name = $2;'''
                await self.bot.sql.databaseExecuteDynamic(update_query, [ctx.guild.id, clean_clickup_name, member.id])
                await ctx.send(
                    f"✅ Updated ClickUp user '{clickup_name}' (stored as '{clean_clickup_name}') to ping {member.mention}.")
            else:
                insert_query = '''INSERT INTO clickup_mappings (serverid, clickup_name, discord_id) VALUES ($1, $2, $3);'''
                await self.bot.sql.databaseExecuteDynamic(insert_query, [ctx.guild.id, clean_clickup_name, member.id])
                await ctx.send(
                    f"✅ Created ClickUp user mapping: '{clickup_name}' (stored as '{clean_clickup_name}') now pings {member.mention}.")

        except Exception as e:
            # Inform the user that the setup command needs to be run.
            await ctx.send(
                f"❌ Failed to set ClickUp mapping. Ensure the `clickup_mappings` table exists. Try running `/setupclickup` if you are the bot owner. Error: ```{e}```")
        # --- CRITICAL FIX END ---

    @tasks.loop(time=[
        # UPDATED TIME TO 16:00 UTC
        datetime.time(hour=16, minute=0, tzinfo=datetime.timezone.utc),  # Monday, Wednesday, Friday at 16:00 PM UTC
        datetime.time(hour=16, minute=0, tzinfo=datetime.timezone.utc),
        datetime.time(hour=16, minute=0, tzinfo=datetime.timezone.utc)
    ])
    async def daily_report(self):
        """Runs on a schedule to send daily ClickUp reports."""
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
        if now_utc.weekday() in [0, 2, 4]:  # Monday (0), Wednesday (2), Friday (4)
            await self._send_global_clickup_report()

    @commands.command(name="clickupreport", description="Manually generate and send the daily ClickUp report.")
    async def manual_report_command(self, ctx: commands.Context):
        """Allows authorized users to manually trigger a report for their server."""

        # Check for admin or owner permission
        server_config = await adminFunctions.getServerConfig(self, ctx)
        bot_manager_role_id = server_config.get('botmanagerroleid')

        is_bot_manager = False
        if bot_manager_role_id and isinstance(ctx.author, discord.Member):
            for role in ctx.author.roles:
                if role.id == bot_manager_role_id:
                    is_bot_manager = True
                    break

        if not ctx.author.guild_permissions.administrator and ctx.author.id != main.ownerID and not is_bot_manager:
            await ctx.send(
                "You do not have permission to run this command. You need to be a server administrator, the bot owner, or have the configured Bot Manager role.")
            return

        await ctx.send("Generating ClickUp task report...")
        try:
            # Pass ctx to ctx_in
            await self._process_server_report(ctx.guild.id, guild=ctx.guild, is_manual=True, manual_channel=ctx.channel,
                                              ctx_in=ctx)
            await ctx.send("Report generated and sent to the manager channel (or this channel if configured).")
        except Exception as e:
            await ctx.send(f"An error occurred while generating the report: ```{e}```")

    async def _send_global_clickup_report(self):
        """Fetches all server configs and triggers report generation."""
        # This will fetch all server configurations with a clickupkey
        try:
            all_configs = await self.bot.sql.databaseFetchdict(
                'SELECT serverid, clickupkey, managerchannelid FROM serverconfig WHERE clickupkey IS NOT NULL AND clickupkey != \'0\';')
            for config in all_configs:
                # Get guild object for member access
                guild = self.bot.get_guild(config['serverid'])
                if guild:
                    # Do not pass ctx (it's None by default for ctx_in)
                    asyncio.create_task(self._process_server_report(config['serverid'], guild=guild))
        except Exception as e:
            # Log this error to the owner/log channel
            log_channel = self.bot.get_channel(
                1152377925916688484)  # Assuming this is the log channel ID from adminFunctions.py
            if log_channel:
                await log_channel.send(f"Error fetching server configs for ClickUp report: {e}")
            else:
                print(f"Error fetching server configs for ClickUp report: {e}")

    async def _process_server_report(self, server_id: int, guild: discord.Guild, is_manual=False, manual_channel=None,
                                     ctx_in: commands.Context = None):
        """Generates and sends the ClickUp report for a single server."""
        try:
            # Fetch config including updateschannelid for destination
            config = await self.bot.sql.databaseFetchrowDynamic(
                'SELECT clickupkey, managerchannelid, updateschannelid FROM serverconfig WHERE serverid = $1;',
                [server_id])
            api_key = config.get('clickupkey')
            manager_channel_id = config.get('managerchannelid')
            updates_channel_id = config.get('updateschannelid')

            if not api_key or api_key == '0':
                return  # No key set

            if not guild:
                return  # Bot is no longer in this guild

            # Determine the destination channel (Announcements Channel is first priority)
            if is_manual and manual_channel:
                dest_channel = manual_channel
            elif updates_channel_id:
                dest_channel = guild.get_channel(updates_channel_id)
                if not dest_channel:
                    dest_channel = guild.get_channel(manager_channel_id) or guild.system_channel or guild.text_channels[
                        0]
            elif manager_channel_id:
                dest_channel = guild.get_channel(manager_channel_id)
            else:
                dest_channel = guild.system_channel or guild.text_channels[0]

            if not dest_channel:
                return  # Cannot find a channel to send to

            # 1. Download all tasks
            tasks_data = await self._fetch_all_tasks(api_key)

            if not tasks_data:
                await dest_channel.send(
                    "ClickUp Report: No active tasks found or failed to connect to ClickUp. Please check your API key and permissions.")
                return

            # 2. Parse and filter tasks
            pressing_tasks = self._identify_pressing_tasks(tasks_data)

            if not pressing_tasks:
                await dest_channel.send(
                    "ClickUp Report: No pressing tasks (due today, overdue, or due this week) found.")
                return

            # 3. Format prompt (using SQL lookup for PING)
            ai_prompt = await self._format_tasks_for_ai(pressing_tasks, guild)

            # Using the bot's configured AI wrapper (GeminiAITools from main.py)
            summary = await self.bot.AI.get_response(
                prompt=ai_prompt,
                temperature=0.3,  # Lower temperature for a professional summary
                instructions=self.ai_instructions
            )

            # 4. Send the report
            embed = discord.Embed(
                title=f"ClickUp Task Report ({datetime.date.today().strftime('%A, %B %d')})",
                description=summary,
                color=discord.Color.blue()
            )

            # --- FOOTER LOGIC: Using Mock Context for Scheduled Tasks ---
            if ctx_in:
                # Use the real context if it exists (manual command)
                footer_text = await self.bot.error.retrieveError(ctx_in)
            else:
                # Create a simple mock context object for the scheduled task
                class MockContext:
                    def __init__(self, bot, guild, channel):
                        self.bot = bot
                        self.guild = guild
                        self.author = bot.get_user(self.bot.ownerid) or bot.user
                        self.channel = channel
                        self.message = MockMessage(self.author, channel)

                class MockMessage:
                    def __init__(self, author, channel):
                        self.author = author
                        self.channel = channel
                        self.content = "scheduled_task_report"

                try:
                    mock_ctx = MockContext(self.bot, guild, dest_channel)
                    footer_text = await self.bot.error.retrieveError(mock_ctx)
                except Exception as e:
                    print(f"Error calling retrieveError with mock context: {e}")
                    footer_text = "Task summary complete."

            embed.set_footer(text=footer_text)
            await dest_channel.send(embed=embed)

        except Exception as e:
            # Catch and report the error
            print(f"Error processing ClickUp report for server {server_id}: {e}")
            if is_manual and manual_channel:
                await manual_channel.send(f"An error occurred while generating the report: ```{e}```")

            log_channel = self.bot.get_channel(1152377925916688484)
            if log_channel:
                await log_channel.send(f"Critical ClickUp report failure for server {server_id}: {e}")

    def _get_headers(self, api_key: str):
        """Returns the headers for ClickUp API requests."""
        return {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

    async def _fetch_all_tasks(self, api_key: str) -> list:
        """
        Fetches all tasks the API key can access.
        We fetch tasks that are open and have a due date.
        """
        base_url = "https://api.clickup.com/api/v2"
        headers = self._get_headers(api_key)
        all_tasks = []

        # 1. Get Authorized Teams (Workspaces)
        teams_url = f"{base_url}/team"
        try:
            teams_response = requests.get(teams_url, headers=headers)
            teams_response.raise_for_status()
            teams_data = teams_response.json()
            team_ids = [team['id'] for team in teams_data.get('teams', [])]
        except Exception as e:
            print(f"Error fetching ClickUp teams: {e}")
            return []

        # 2. For each Team, fetch all filtered tasks
        for team_id in team_ids:
            tasks_url = f"{base_url}/team/{team_id}/task"
            params = {
                'include_closed': 'false',  # Only open tasks
                'due_date_gt': 0,  # Tasks with a due date
                'date_updated_gt': 0,
                'subtasks': 'true',
                'include_markdown_description': 'true',  # Get rich description
            }
            try:
                tasks_response = requests.get(tasks_url, headers=headers, params=params)
                tasks_response.raise_for_status()
                tasks_data = tasks_response.json()
                all_tasks.extend(tasks_data.get('tasks', []))
            except Exception as e:
                print(f"Error fetching tasks for team {team_id}: {e}")
                continue

        return all_tasks

    def _identify_pressing_tasks(self, tasks: list) -> list:
        """
        Filters tasks to find those that are due today, overdue, or due in the next week.
        """
        pressing = []
        now = datetime.datetime.now().date()
        one_week_from_now = now + datetime.timedelta(days=7)

        urgency_map = {'Overdue': 0, 'Due Today': 1, 'Due This Week': 2}

        for task in tasks:
            due_date_ms = task.get('due_date')
            if not due_date_ms:
                continue

            due_date = datetime.datetime.fromtimestamp(int(due_date_ms) / 1000).date()
            task_urgency = None

            if due_date < now:
                task_urgency = 'Overdue'
            elif due_date == now:
                task_urgency = 'Due Today'
            elif now < due_date <= one_week_from_now:
                task_urgency = 'Due This Week'

            if task_urgency:
                task['urgency'] = task_urgency
                task['sort_key'] = urgency_map[task_urgency]
                pressing.append(task)

        pressing.sort(key=lambda t: (
            t['sort_key'],
            datetime.datetime.fromtimestamp(int(t.get('due_date', 0)) / 1000).date()
        ))

        return pressing

    # --- JOKE RETRIEVAL ---
    async def _get_dad_joke(self) -> str:
        """Generates a dad joke using the AI tool."""
        joke_prompt = "Generate a single, short, funny dad joke. Do not include a conversational introduction."
        try:
            return await self.bot.AI.get_response(
                prompt=joke_prompt,
                temperature=0.9,  # Higher temperature for creativity
                instructions="You are a stand-up comedian. Respond with only a single, short dad joke."
            )
        except Exception:
            return "Why don't scientists trust atoms? Because they make up everything."

    # --- END JOKE RETRIEVAL ---

    def _get_assignee_info(self, task: dict) -> str:
        """
        Extracts the name of the first assignee, and indicates if there are more.
        """
        assignees = task.get('assignees')
        if not assignees:
            return 'Unassigned'

        first_assignee_name = assignees[0].get('display_name') or assignees[0].get('username') or 'Assigned'

        # Indicate if there are multiple assignees
        if len(assignees) > 1:
            return f"{first_assignee_name} (+{len(assignees) - 1} more)"

        return first_assignee_name

    async def _get_ping_from_sql(self, clickup_name: str, guild: discord.Guild) -> str:
        """
        Retrieves the Discord ID from the SQL database and returns a ping.
        """
        # Clean the name: remove multi-assignee indicator and make lowercase for lookup
        clean_clickup_name = clickup_name.split(' (+')[0].lower()

        try:
            # Query the database for the mapped Discord ID
            query = '''SELECT discord_id FROM clickup_mappings WHERE serverid = $1 AND clickup_name = $2;'''
            mapping = await self.bot.sql.databaseFetchrowDynamic(query, [guild.id, clean_clickup_name])

            if mapping:
                # FIX: databaseFetchrowDynamic returns a dict, access value by key
                discord_id = mapping.get('discord_id')
                if discord_id:
                    # Return the Discord mention (ping)
                    return f"<@{discord_id}>"

        except Exception:
            # If the table doesn't exist or query fails, quietly fall back
            pass

        # If no mapping or database fails, return the original ClickUp name
        return clickup_name

    async def _format_tasks_for_ai(self, tasks: list, guild: discord.Guild) -> str:
        """
        Formats the list of pressing tasks for the single-pass AI summary.
        Uses the non-blocking SQL lookup for accurate pinging.
        """
        formatted_tasks = "ClickUp Tasks to Summarize:\n\n"

        for task in tasks:
            name = task.get('name', 'N/A')
            url = task.get('url', 'N/A')
            urgency = task.get('urgency', 'N/A')

            clickup_name = self._get_assignee_info(task)

            # --- CRITICAL FIX: Use SQL Lookup for Ping ---
            assignee_ping_or_name = await self._get_ping_from_sql(clickup_name, guild)

            raw_description = task.get('text_content') or task.get(
                'description') or 'No detailed description available.'

            # --- JOKE SUBSTITUTION LOGIC ---
            if "dad joke" in raw_description.lower() or "joke" in raw_description.lower():
                joke = await self._get_dad_joke()
                joke_placeholder = f"[JOKE REQUEST FULFILLED: {joke}]"
                description_for_ai = raw_description.replace("dad joke", joke_placeholder).replace("joke",
                                                                                                   joke_placeholder)
            else:
                description_for_ai = raw_description

            # Truncate description to 500 characters
            description = description_for_ai[:500] + ('...' if len(description_for_ai) > 500 else '')

            status_raw = task.get('status', {}).get('status')
            status = str(status_raw).upper() if status_raw is not None else 'N/A'.upper()

            # Use the most specific name/ping available
            final_assignee_string = assignee_ping_or_name

            formatted_tasks += (
                f"--- TASK START ---\n"
                f"**Task Name**: {name}\n"
                f"**Urgency**: {urgency}\n"
                f"**FINAL ASSIGNEE STRING**: {final_assignee_string}\n"  # PING OR CLICKUP NAME
                f"**Status**: {status}\n"
                f"**Description**: {description}\n"  # Truncated description (may contain joke)
                f"**Link**: {url}\n"
                f"--- TASK END ---\n"
            )

        return (
            f"The current date is {datetime.date.today().strftime('%B %d, %Y')}. "
            f"Summarize the following ClickUp tasks. The **Description** field contains key context for what the task requires. "
            f"The **FINAL ASSIGNEE STRING** field contains the exact ping or name that MUST be used in the summary. "
            f"STRICTLY adhere to the format: **Task Title (bolded)\nAssigned to: [FINAL ASSIGNEE STRING]**. Summary of work required from Description."
            f"The final summary must be under 100 words. \n\n"
            f"{formatted_tasks}"
        )


async def setup(bot: commands.Cog) -> None:
    await bot.add_cog(clickupFunctions(bot))