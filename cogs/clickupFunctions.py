import asyncio
import datetime
import requests
import json
import discord
from discord.ext import commands, tasks
from cogs.textTools import textTools
import main  # To access main.ownerID and other main settings
from cogs.adminFunctions import adminFunctions  # For getServerConfig


# from difflib import SequenceMatcher # No longer needed

# ClickUp API Endpoints
# Note: ClickUp API requires a Personal API Token.
# The base URL for V2 is 'https://api.clickup.com/api/v2/'

class clickupFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Updated AI instructions for: Task Title (bolded) \n Assigned to: [User]
        self.ai_instructions = "You are a professional project manager tasked with summarizing the most pressing tasks for the day and the upcoming week from a list of ClickUp tasks. You have also been given a separate JSON list of Discord users and their roles for a server. Your summary must be extremely concise and should be presented as a bulleted or numbered list. **For each task, use the format: Task Title (bolded) followed by a newline, then Assigned to: [BEST DISCORD @PING, OR ClickUp Name], and finally a period followed by the Summary of work required from Description**. The 'Assigned to' field must contain ONLY the Discord ping if a match is found, or ONLY the ClickUp Name if no match is found. Avoid using phrases like 'This involves' or 'The task is to'. **Ensure all task titles are bolded in the final summary.** Group tasks by their urgency (Overdue, Due Today, Due This Week). The summary must be under 500 words. Do not use any introductory phrases."
        # Start the scheduled task loop
        self.daily_report.start()

    def cog_unload(self):
        # Cancel the loop when the cog is unloaded
        self.daily_report.cancel()

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
        if now_utc.weekday() in [0, 2, 4, 6]:  # Monday (0), Wednesday (2), Friday (4)
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
                'SELECT serverid, clickupkey, updateschannelid FROM serverconfig WHERE clickupkey IS NOT NULL AND clickupkey != \'0\';')
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
            config = await self.bot.sql.databaseFetchrowDynamic(
                'SELECT clickupkey, updateschannelid FROM serverconfig WHERE serverid = $1;', [server_id])
            api_key = config.get('clickupkey')
            manager_channel_id = config.get('updateschannelid')

            if not api_key or api_key == '0':
                return  # No key set

            if not guild:
                return  # Bot is no longer in this guild

            # Determine the destination channel
            if is_manual and manual_channel:
                dest_channel = manual_channel
            elif manager_channel_id:
                dest_channel = guild.get_channel(manager_channel_id)
                if not dest_channel:
                    dest_channel = guild.system_channel or guild.text_channels[0]
            else:
                dest_channel = guild.system_channel or guild.text_channels[0]

            if not dest_channel:
                return  # Cannot find a channel to send to

            # 1. Download all tasks for all accessible spaces/teams (ClickUp 'Teams' are 'Workspaces')
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

            # 3. Use AI to summarize
            # Pass the guild to the formatter for Discord name list
            ai_prompt = self._format_tasks_for_ai(pressing_tasks, guild)

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

            # --- MODIFIED LINE 152 LOGIC ---
            if ctx_in:
                # If a Context object is provided (manual command), use it for the error footer
                footer_text = await self.bot.error.retrieveError(ctx_in)
            else:
                # If no Context object is available (scheduled task), use a fallback or try
                # calling the error retriever with minimal context, defaulting to a string.
                try:
                    # Attempt to call retrieveError with None, which some implementations
                    # use as a signal to return a generic error message string.
                    footer_text = await self.bot.error.retrieveError(ctx=None)
                except:
                    footer_text = "Summary generated by AI based on overdue, due-today, and due-this-week tasks."

            embed.set_footer(text=footer_text)
            await dest_channel.send(embed=embed)

        except Exception as e:
            print(f"Error processing ClickUp report for server {server_id}: {e}")
            if is_manual and manual_channel:
                await manual_channel.send(f"Critical error during report generation: ```{e}```")
            # Log to the owner/log channel in case of a critical failure
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

        # 2. For each Team, fetch all filtered tasks (simplest way to get all tasks)
        # We filter for open tasks with a due date.
        for team_id in team_ids:
            tasks_url = f"{base_url}/team/{team_id}/task"
            params = {
                'include_closed': 'false',  # Only open tasks
                'due_date_gt': 0,  # Tasks with a due date
                'date_updated_gt': 0,
                'subtasks': 'true',  # Include subtasks
                'include_markdown_description': 'true',  # Get rich description for AI context
            }
            try:
                tasks_response = requests.get(tasks_url, headers=headers, params=params)
                tasks_response.raise_for_status()
                tasks_data = tasks_response.json()
                all_tasks.extend(tasks_data.get('tasks', []))
            except Exception as e:
                print(f"Error fetching tasks for team {team_id}: {e}")
                continue  # Move to the next team

        return all_tasks

    def _identify_pressing_tasks(self, tasks: list) -> list:
        """
        Filters tasks to find those that are due today, overdue, or due in the next week.
        """
        pressing = []
        now = datetime.datetime.now().date()
        one_week_from_now = now + datetime.timedelta(days=7)

        # Mapping for sorting: Overdue (0) > Due Today (1) > Due This Week (2) > Later (3)
        urgency_map = {'Overdue': 0, 'Due Today': 1, 'Due This Week': 2}

        for task in tasks:
            # Due date is in milliseconds since epoch
            due_date_ms = task.get('due_date')
            if not due_date_ms:
                continue

            # Convert to seconds, then to a datetime.date object
            due_date = datetime.datetime.fromtimestamp(int(due_date_ms) / 1000).date()

            task_urgency = None

            # 1. Check if Overdue (before today)
            if due_date < now:
                task_urgency = 'Overdue'
            # 2. Check if Due Today
            elif due_date == now:
                task_urgency = 'Due Today'
            # 3. Check if Due This Week (tomorrow up to 7 days from now)
            elif now < due_date <= one_week_from_now:
                task_urgency = 'Due This Week'

            if task_urgency:
                task['urgency'] = task_urgency
                task['sort_key'] = urgency_map[task_urgency]
                pressing.append(task)

        # Sort by: Urgency (Overdue first) -> Due Date (Oldest first)
        pressing.sort(key=lambda t: (
            t['sort_key'],
            datetime.datetime.fromtimestamp(int(t.get('due_date', 0)) / 1000).date()
        ))

        return pressing

    def _get_assignee_info(self, task: dict) -> str:
        """
        Extracts the ClickUp display name of the first assignee.
        """
        assignees = task.get('assignees')
        if assignees and len(assignees) > 0:
            return assignees[0].get('display_name') or assignees[0].get('username') or 'Assigned'
        return 'Unassigned'

    def _get_server_members_for_ai(self, guild: discord.Guild) -> str:
        """
        Generates a JSON string of all server members, their display name, username, and roles for the AI to use.
        """
        member_list = []
        for member in guild.members:
            # Skip bots to reduce noise
            if member.bot:
                continue

            member_roles = [role.name for role in member.roles if role.name != '@everyone']

            member_list.append({
                "discord_ping": member.mention,
                "display_name": member.display_name,
                "username": member.name,
                "roles": member_roles
            })

        return json.dumps(member_list, indent=2)

    def _format_tasks_for_ai(self, tasks: list, guild: discord.Guild) -> str:
        """Formats the list of pressing tasks into a string for the AI prompt, including descriptions and Discord pings."""

        # 1. Get the list of server members for the AI to use for matching
        member_json = self._get_server_members_for_ai(guild)

        # 2. Format the ClickUp tasks
        formatted_tasks = "ClickUp Tasks to Summarize:\n\n"

        for task in tasks:
            name = task.get('name', 'N/A')
            url = task.get('url', 'N/A')
            urgency = task.get('urgency', 'N/A')

            # Get the ClickUp Assignee Name
            clickup_name = self._get_assignee_info(task)

            description = task.get('text_content') or task.get('description') or 'No detailed description available.'

            # Safely handle 'None' values for status
            status_raw = task.get('status', {}).get('status')
            status = str(status_raw).upper() if status_raw is not None else 'N/A'.upper()

            formatted_tasks += (
                f"--- TASK START ---\n"
                f"**Task Name**: {name}\n"
                f"**Urgency**: {urgency}\n"
                f"**ClickUp Assignee**: {clickup_name}\n"  # <-- AI will use this name to match
                f"**Status**: {status}\n"
                f"**Description**: {description}\n"
                f"**Link**: {url}\n"
                f"--- TASK END ---\n"
            )

        # 3. Assemble the final prompt
        return (
            f"The current date is {datetime.date.today().strftime('%B %d, %Y')}. "
            f"Here is a JSON list of all Discord members and their roles for the server: \n\n"
            f"{member_json}\n\n"
            f"Now, summarize the following ClickUp tasks. For each task, use the **ClickUp Assignee** name to find the best match in the Discord member list and include their **@ping** in the summary. **The resulting summary must strictly adhere to a concise bulleted or numbered list format, using this structure: Task Title (bolded) followed by a newline, then Assigned to: [BEST DISCORD @PING, OR ClickUp Name], and finally a period followed by the Summary of work required from Description**. Do not use any introductory, transitional, or descriptive phrases (like 'The task involves'). Omit any 'No detailed description available.' if they appear."
            f"Focus on the 'Overdue', 'Due Today', and 'Due This Week' tasks. "
            f"The final summary must be under 500 words. \n\n"
            f"{formatted_tasks}"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(clickupFunctions(bot))