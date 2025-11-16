import asyncio
import datetime
import random
import discord
import requests
import json
from discord.ext import commands
from discord import app_commands
import main
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions  # To fetch server config for ClickUp key and channel

# --- Configuration ---
DEFAULT_TASK_DAYS = 7
# Placeholder for List ID—must be updated by the user with the correct value
DEFAULT_CLICKUP_LIST_ID = "901317097085"
CLICKUP_API_BASE = "https://api.clickup.com/api/v2/list/"
CLICKUP_ENDPOINT_SUFFIX = "/task"


class jarvisFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.on_message_cooldowns = {}
        self.on_message_cooldowns_burst = {}
        self.on_message_cooldowns_notify = {}
        self.cooldown = 11880  # Retained original cooldown value
        self.geminikey = self.bot.geminikey

    async def _handle_task_addition(self, message: discord.Message, task_details: str):
        """
        Handles the actual, non-blocking ClickUp API interaction and AI guessing.
        """
        ctx = await self.bot.get_context(message)

        server_config = await adminFunctions.getServerConfig(self, ctx)
        api_key = server_config.get('clickupkey')

        if not api_key or api_key == '0':
            await message.channel.send("❌ Access denied. The ClickUp API key for this server is not set.")
            return

        # --- 1. Fetch Conversation History ---
        messages = []
        message_raw = message.channel.history(limit=15, before=message)
        async for messagee in message_raw:
            messages.append({'author nickname': messagee.author.display_name, 'author username': messagee.author.name,
                             "user_id": messagee.author.id, 'content': messagee.content})

        messages.append({'author nickname': message.author.display_name, 'author username': message.author.name,
                         "user_id": message.author.id, 'content': message.content})

        # --- 2. Determine Base Due Date (Default is 7 days from now) ---
        default_due_date = datetime.datetime.now() + datetime.timedelta(days=DEFAULT_TASK_DAYS)
        default_due_date_ms = int(default_due_date.timestamp() * 1000)

        # 3. Determine Task Title and Description using AI

        # Default fallbacks before AI runs
        task_title = "Task Requested Without Clear Title"
        task_due_ms = default_due_date_ms
        task_description = f"Original Request: {message.content}"

        # --- AI PROMPT ---
        ai_task_prompt = (
            f"You are J.A.R.V.I.S., analyzing a user's task request in the context of a conversation.\n"
            f"Conversation History (backwards, includes the request): \n{json.dumps(messages)}\n\n"
            f"Current date is {datetime.datetime.now().strftime('%Y-%m-%d')}. If the user mentions a specific date or timeframe (e.g., 'tomorrow', 'next week', 'in 3 days'), calculate the Unix timestamp in milliseconds for that due date. If no date is specified, use {DEFAULT_TASK_DAYS} days from now (timestamp: {default_due_date_ms}).\n"
            f"Extract the main task title and place all remaining relevant information (e.g., technical details, links, notes) into the description field.\n"
            f"**RULE:** The task title and description MUST NOT contain the user's trigger phrase: 'Jarvis, add this task' or 'add this task'.\n"
            f"Respond ONLY with a single, raw JSON object in the format: "
            f'{{"title": "Extracted Task Title", "description": "Remaining details or notes.", "due_date_ms": calculated_timestamp_in_milliseconds}}'
        )

        # CRITICAL DEBUGGING: Running AI call and parsing

        try:
            ai_response = await self.bot.AI.get_response(
                prompt=ai_task_prompt,
                temperature=0.1,
                instructions="Return ONLY a single, raw JSON object. Do not include any formatting or conversational text. Your highest priority is excluding the trigger phrase."
            )

            # Aggressive cleanup of AI output to remove markdown/preamble
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.startswith('```'):
                clean_response = clean_response[3:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]

            task_info = json.loads(clean_response.strip())

            # Attempt to use AI-guessed data
            task_title = task_info.get('title', task_title)
            task_description = task_info.get('description', task_description)

            # CRITICAL FIX: Ensure due_date_ms is an integer
            ai_due_ms = task_info.get('due_date_ms')
            if isinstance(ai_due_ms, (int, str)) and str(ai_due_ms).isdigit():
                task_due_ms = int(ai_due_ms)
            else:
                task_due_ms = default_due_date_ms

        except Exception as e:
            # Report failure, but exit cleanly.
            await message.channel.send(f"❌ Jarvis failed JSON extraction/processing. Error: ```{e}```")
            return

        # 3. Finalize Task Content and Clean Title (Code Cleanup)

        # Define phrases to aggressively remove
        trigger_phrases = ["jarvis, add this task", "add this task", "to clickup for me", "to clickup"]

        # Aggressive cleaning of the task title just in case the AI failed to exclude the phrase
        task_title_lower = task_title.lower()
        for phrase in trigger_phrases:
            if task_title_lower.startswith(phrase):
                task_title = task_title[len(phrase):].strip()
                task_title_lower = task_title.lower()  # Re-evaluate for cascade removal

        if not task_title:
            task_title = "Task Requested Without Clear Title"

        final_description = f"Requested by {ctx.author.display_name} ({ctx.author.id}, {ctx.author.mention}).\n"
        final_description += f"Task Notes: {task_description}"

        # 4. Use Target List ID
        list_id = DEFAULT_CLICKUP_LIST_ID

        # --- URL Construction ---
        # 4a. Sanitize List ID to only include digits/alphanumeric characters
        clean_list_id = "".join(filter(str.isalnum, list_id.strip()))

        # 4b. Use explicit concatenation with the globally defined constants
        url = CLICKUP_API_BASE + clean_list_id + CLICKUP_ENDPOINT_SUFFIX
        # --- END URL Construction ---

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "name": task_title,
            "description": final_description,
            "due_date": task_due_ms,
            "priority": 3,  # Normal priority
        }

        # 6. Send Request (Non-blocking HTTP request)
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raises HTTPError for 400/500 errors
            task_data = response.json()

            # 7. Send Confirmation
            due_date_obj = datetime.datetime.fromtimestamp(task_due_ms / 1000).strftime('%Y-%m-%d')
            await message.channel.send(
                f'''Right away, sir. I have added task **"{task_data.get('name')}"** to your ClickUp board as requested.\n'''
                f"Due: **{due_date_obj}**\n"
                f"View Task: {task_data.get('url')}")

        except requests.exceptions.HTTPError as err:
            # Include the response text for detailed debugging of the 400 error
            try:
                error_details = response.json()
            except:
                error_details = {"message": "No detailed JSON error provided by ClickUp."}

            error_message = f"ClickUp API Error ({response.status_code}): Could not create task."
            await message.channel.send(f"❌ Jarvis failed: {error_message}\nDetails: `{error_details.get('message')}`")
        except Exception as e:
            await message.channel.send(f"❌ Jarvis encountered an unknown error during API call: ```{e}```")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Combined message listener for task creation and conversation.
        FIXED: Checks now accommodate 'Jarvis, ' OR 'Jarvis '.
        """
        if message.author.bot:
            return

        content_lower = message.content.lower().strip()
        user_id = message.author.id
        now = datetime.datetime.now()

        # --- FIX: Standardized Prefix Checking ---

        # Helper function to check for "jarvis" followed by optional comma and space
        def check_jarvis_prefix(text: str, command: str) -> str:
            # Looks for: "jarvis, command" or "jarvis command"
            base = "jarvis"
            prefix_with_comma = f"{base}, {command}"
            prefix_no_comma = f"{base} {command}"

            if text.startswith(prefix_with_comma):
                return text[len(prefix_with_comma):].strip()
            elif text.startswith(prefix_no_comma):
                return text[len(prefix_no_comma):].strip()
            return None

        # Check for TASK command first
        task_command_phrase = "add this task"
        task_details = check_jarvis_prefix(content_lower, task_command_phrase)

        if task_details is not None:
            # --- TASK ADDITION MODE ---
            # task_details now holds the remainder of the message or an empty string if only the prefix was used.

            # Run the task handler in a non-blocking fashion
            await message.add_reaction('✅')  # Indicate task processing started
            asyncio.create_task(self._handle_task_addition(message, message.content))  # Pass original message.content

            # Prevent standard conversation flow from running
            return

        # Check for standard conversation prefix
        standard_conversation_trigger = check_jarvis_prefix(content_lower, "")  # Check for "jarvis," or "jarvis"

        if standard_conversation_trigger is not None:
            # --- STANDARD CONVERSATION MODE (with cooldown logic) ---
            # Cooldown logic (copied from testingFunctions.py)
            special_users = [220134579736936448, 437324319102730263, 806938248060469280, 198602742317580288,
                             870337116381515816, 298548176778952704, 874912257128136734]
            exec_users = [712509599135301673, 199887270323552256, 299330776162631680, 502814400562987008,
                          686640777505669141]

            active_cooldown = self.cooldown
            if message.author.id in special_users or message.author.guild_permissions.ban_members:
                active_cooldown = round(active_cooldown / 2)
            if message.author.id in exec_users:
                active_cooldown = 1
            if message.author.premium_since is not None:
                active_cooldown = round(active_cooldown / 24)

            # Check cooldown
            if user_id not in self.on_message_cooldowns:
                self.on_message_cooldowns_burst[user_id] = 0
            else:
                self.on_message_cooldowns_burst[user_id] = self.on_message_cooldowns_burst[user_id] + 1
                last_triggered = self.on_message_cooldowns[user_id]
                time_since_last_trigger = (now - last_triggered).total_seconds()
                if time_since_last_trigger < active_cooldown:
                    if self.on_message_cooldowns_burst[user_id] > 2: # burst length
                        if self.on_message_cooldowns_notify.get(user_id) == False:
                            remaining_time = active_cooldown - time_since_last_trigger
                            await message.author.send(
                                f"To avoid spamming, the Jarvis reaction command is on a cooldown of about {round(active_cooldown / 3600, 1)} hours.")
                            self.on_message_cooldowns_notify[user_id] = True
                        return
                else:
                    self.on_message_cooldowns_burst[user_id] = 0
            self.on_message_cooldowns[user_id] = now
            self.on_message_cooldowns_notify[user_id] = False

            print("got this far")

            # --- AI Response Generation ---
            channel = message.channel
            messages = []
            message_raw = channel.history(limit=65)
            async for messagee in message_raw:
                messages.append(
                    {'author nickname': messagee.author.display_name, 'author username': messagee.author.name,
                     "user_id": messagee.author.id, 'content': messagee.content})
            async with channel.typing():
                ai_prompt = f"Generate a reply to the user's message in less than 100 words.  If the author makes a request that's at least slightly sexual or racist in nature, or your response contains anything at least slightly sexual or racist, your response must be exactly 'Apologies Tony, I cannot comply.'"
                messageOut = await self.bot.AI.get_response(prompt=ai_prompt, temperature=1.75, instructions=f"You are pretending to be J.A.R.V.I.S. from the Marvel Cinematic Universe, except that you are assisting a Discord user named {message.author} (you must still refer to them as Tony Stark). Their request was made in this conversation, which is provided backwards in a json format: \n\n{messages}\n\n  The reply that you generate needs to be in-character for J.A.R.V.I.S. from the Iron Man movies and comics.")
                await message.reply(
                    messageOut.replace('@everyone', '[Redacted]').replace('@here', '[Redacted]').replace('@&',
                                                                                                         '@').replace(
                        '123105882102824960', str(message.author.id)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(jarvisFunctions(bot))