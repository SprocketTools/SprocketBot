import asyncio
import datetime
import requests
import json
import discord
from discord.ext import commands, tasks
from cogs.textTools import textTools
import main  # To access main.ownerID and other main settings
from cogs.adminFunctions import adminFunctions  # For getServerConfig


# ClickUp API Endpoints
# Note: ClickUp API requires a Personal API Token.
# The base URL for V2 is 'https://api.clickup.com/api/v2/'

class clickupFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Updated AI instructions: removed 'priority' and increased word allowance to 500
        self.ai_instructions = "You are a professional project manager tasked with summarizing the most pressing tasks for the day and the upcoming week from a list of ClickUp tasks. Your summary should be clear, concise, and professional. Group tasks by their urgency (Overdue, Due Today, Due This Week) and include the assignee for each task. Clearly state what needs to be done. The summary must be under 500 words. Do not use any introductory phrases."
        # Start the scheduled task loop
        self.daily_report.start()

    def cog_unload(self):
        # Cancel the loop when the cog is unloaded
        self.daily_report.cancel()

    @tasks.loop(time=[
        datetime.time(hour=9, minute=0, tzinfo=datetime.timezone.utc),  # Monday, Wednesday, Friday at 9:00 AM UTC
        datetime.time(hour=9, minute=0, tzinfo=datetime.timezone.utc),
        datetime.time(hour=9, minute=0, tzinfo=datetime.timezone.utc)
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
            await self._process_server_report(ctx.guild.id, is_manual=True, manual_channel=ctx.channel)
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
                # Process each server in a separate non-blocking task
                asyncio.create_task(self._process_server_report(config['serverid']))
        except Exception as e:
            # Log this error to the owner/log channel
            log_channel = self.bot.get_channel(
                1152377925916688484)  # Assuming this is the log channel ID from adminFunctions.py
            if log_channel:
                await log_channel.send(f"Error fetching server configs for ClickUp report: {e}")
            else:
                print(f"Error fetching server configs for ClickUp report: {e}")

    async def _process_server_report(self, server_id: int, is_manual=False, manual_channel=None):
        """Generates and sends the ClickUp report for a single server."""
        try:
            config = await self.bot.sql.databaseFetchrowDynamic(
                'SELECT clickupkey, managerchannelid FROM serverconfig WHERE serverid = $1;', [server_id])
            api_key = config.get('clickupkey')
            manager_channel_id = config.get('managerchannelid')

            if not api_key or api_key == '0':
                return  # No key set

            # Determine the destination channel
            guild = self.bot.get_guild(server_id)
            if not guild:
                return  # Bot is no longer in this guild

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
            # Note: The 'include_description' parameter is crucial here for feeding to the AI
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
            ai_prompt = self._format_tasks_for_ai(pressing_tasks)

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
            embed.set_footer(text="Summary generated by AI based on overdue, due-today, and due-this-week tasks.")
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

    def _get_assignee_name(self, task: dict) -> str:
        """Extracts the display name of the first assignee, or 'Unassigned'."""
        assignees = task.get('assignees')
        if assignees and len(assignees) > 0:
            # ClickUp task objects list assignees as a list of user objects
            return assignees[0].get('display_name') or assignees[0].get('username') or 'Assigned'
        return 'Unassigned'

    def _format_tasks_for_ai(self, tasks: list) -> str:
        """Formats the list of pressing tasks into a string for the AI prompt, including descriptions."""
        formatted_list = "List of Pressing ClickUp Tasks:\n\n"

        for task in tasks:
            name = task.get('name', 'N/A')
            url = task.get('url', 'N/A')
            urgency = task.get('urgency', 'N/A')
            assignee = self._get_assignee_name(task)
            description = task.get('text_content') or task.get(
                'description') or 'No detailed description available.'  # Prioritize text_content if markdown was included

            # Safely handle 'None' values for status
            status_raw = task.get('status', {}).get('status')
            status = str(status_raw).upper() if status_raw is not None else 'N/A'.upper()

            formatted_list += (
                f"--- TASK START ---\n"
                f"**Task Name**: {name}\n"
                f"**Urgency**: {urgency}\n"
                f"**Assignee**: {assignee}\n"
                f"**Status**: {status}\n"
                f"**Description**: {description}\n"  # <-- Description included here
                f"**Link**: {url}\n"
                f"--- TASK END ---\n"
            )

        return (
            f"The current date is {datetime.date.today().strftime('%B %d, %Y')}. "
            f"Summarize the following list of tasks. The **Description** field contains key context for what the task requires. "
            f"Focus on the 'Overdue', 'Due Today', and 'Due This Week' tasks. "
            f"Ensure to mention the task name and assignee in your summary. "
            f"The final summary must be under 500 words. \n\n"
            f"{formatted_list}"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(clickupFunctions(bot))