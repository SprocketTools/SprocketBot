import asyncio
import datetime
import random
import discord
import type_hints
import aiohttp  # CHANGED: Swapped requests for aiohttp (non-blocking)
import json
from discord.ext import commands
from discord import app_commands
import main
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions

# --- Configuration ---
DEFAULT_TASK_DAYS = 7
DEFAULT_CLICKUP_LIST_ID = "901317097085"
CLICKUP_API_BASE = "https://api.clickup.com/api/v2/list/"
CLICKUP_ENDPOINT_SUFFIX = "/task"


class jarvisFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.on_message_cooldowns = {}
        self.on_message_cooldowns_burst = {}
        self.on_message_cooldowns_notify = {}
        self.cooldown = 14990 #retired
        self.geminikey = self.bot.geminikey
        self.prior_instructions = {}

    # --- NEW: Separate handler for conversation to run in background ---
    async def _handle_conversation(self, message: discord.Message):
        """
        Handles the AI conversation response in the background.
        """
        server_config = await adminFunctions.getServerConfig(await self.bot.get_context(message))
        channel = message.channel
        messages = []
        message_raw = channel.history(limit=45)
        async for messagee in message_raw:
            messages.append(
                {'author nickname': messagee.author.display_name, 'author username': messagee.author.name,
                 "user_id": messagee.author.id, 'content': messagee.content})

        try:
            current_instructions = self.prior_instructions[message.author.id]
        except Exception:
            current_instructions = ""
        async with channel.typing():
            ai_prompt = f"Generate a reply (or replies) to the user's message in less than {120 + 15*int(server_config['jarvisburst'])} words, and try to make the message smaller if possible. If the author makes a request that's noticeably sexual or racist in nature, or your response contains anything noticeably sexual or racist, your response must be exactly 'Apologies Tony, I cannot comply.'"

            messageOut = await self.bot.AI.get_response(
                prompt=ai_prompt,
                temperature=1.9,
                mode='gemma',
                instructions=f"You are pretending to be J.A.R.V.I.S. from the Marvel Cinematic Universe, except that you are assisting a Discord user named {message.author} (you must still refer to them as Tony Stark). "
                             f"Their request was made in this conversation, which is provided in backwards order in a json format: \n\n{messages}\n\n  "
                             f"The specific message you are replying to is this one:\n\n{message.content}\n\n"
                             f"The reply (or replies) that you generate needs to be in-character for J.A.R.V.I.S. from the Iron Man movies and comics.  Start with just 'Sir, ' if you use an intro."
                             f"Use funny happy sarcasm wherever possible, akin to this example response: 'As you wish, sir. I've also prepared a safety briefing for you to entirely ignore.'"
                             f"If the user is asking something that you don't have enough information to work with, imagine scenarios based on the Marvel Cinematic Universe and play off that in your reply."
                             f"Don't tell the user that you can't satisfy their request based on in-character ethical, moral, or technological concerns; play into in-universe ways to bypass those."
                             f"Just don't break the racism and sexism rules outlined in the prompt."
                             f"Additional instructions were provided from the prior interaction with this person: \n{current_instructions}\nUse these instructions to modify your response."
                             f"Provide instructions for your next reply to this user (not anyone else) in triple brackets at the end of your response, [[[like this]]]."

            )
            print(messageOut)
            # --- START OF CHANGE ---
            if messageOut == "Apologies Tony, I cannot comply.":
                # 1. Get the context from the message so we can use error tools
                ctx = await self.bot.get_context(message)

                # 2. Retrieve your random database error
                error_response = await self.bot.error.retrieveError(ctx)

                # 3. Send that instead

                await message.reply(error_response)

                return
            # --- END OF CHANGE ---

            messageOut = messageOut.replace("[[", "[[[").replace("]]", "]]]")
            print(messageOut)
            if "[[[" in messageOut:
                self.prior_instructions[message.author.id] = messageOut.split("[[[")[1].replace("]]]", "")
                messageOut = messageOut.split("[[[")[0]

            await message.reply(
                messageOut.split("<NEWLINE>")[0].replace('@everyone', '[Redacted]')
                .replace('@here', '[Redacted]')
                .replace('@&', '@')
                .replace('123105882102824960', str(message.author.id))
            )
            
            try:
                for subMessageOut in messageOut.split("<NEWLINE>")[1:]:
                    await message.channel.send(
                        subMessageOut.replace('@everyone', '[Redacted]')
                        .replace('@here', '[Redacted]')
                        .replace('@&', '@')
                        .replace('123105882102824960', str(message.author.id))
                    )
            except Exception:
                pass

    async def _handle_task_addition(self, message: discord.Message, task_details: str):
        ctx = await self.bot.get_context(message)
        server_config = await adminFunctions.getServerConfig(ctx)
        api_key = server_config.get('clickupkey')

        if not api_key or api_key == '0':
            await message.channel.send("❌ Access denied. The ClickUp API key for this server is not set.")
            return

        # Fetch History
        messages = []
        message_raw = message.channel.history(limit=15, before=message)
        async for messagee in message_raw:
            messages.append({'author nickname': messagee.author.display_name, 'author username': messagee.author.name,
                             "user_id": messagee.author.id, 'content': messagee.content})

        messages.append({'author nickname': message.author.display_name, 'author username': message.author.name,
                         "user_id": message.author.id, 'content': message.content})

        # Calculate Dates
        default_due_date = datetime.datetime.now() + datetime.timedelta(days=DEFAULT_TASK_DAYS)
        default_due_date_ms = int(default_due_date.timestamp() * 1000)

        # Defaults
        task_title = "Task Requested Without Clear Title"
        task_due_ms = default_due_date_ms
        task_description = f"Original Request: {message.content}"

        # AI Prompt
        ai_task_prompt = (
            f"You are J.A.R.V.I.S., analyzing a user's task request in the context of a conversation.\n"
            f"Conversation History (backwards, includes the request): \n{json.dumps(messages)}\n\n"
            f"Current date is {datetime.datetime.now().strftime('%Y-%m-%d')}. If the user mentions a specific date or timeframe (e.g., 'tomorrow', 'next week', 'in 3 days'), calculate the Unix timestamp in milliseconds for that due date. If no date is specified, use {DEFAULT_TASK_DAYS} days from now (timestamp: {default_due_date_ms}).\n"
            f"Extract the main task title and place all remaining relevant information (e.g., technical details, links, notes) into the description field.\n"
            f"**RULE:** The task title and description MUST NOT contain the user's trigger phrase: 'Jarvis, add this task' or 'add this task'.\n"
            f"Respond ONLY with a single, raw JSON object in the format: "
            f'{{"title": "Extracted Task Title", "description": "Remaining details or notes.", "due_date_ms": calculated_timestamp_in_milliseconds}}'
        )

        try:
            ai_response = await self.bot.AI.get_response(
                prompt=ai_task_prompt,
                temperature=0.1,
                instructions="Return ONLY a single, raw JSON object. Do not include any formatting or conversational text. Your highest priority is excluding the trigger phrase."
            )

            clean_response = ai_response.strip()
            if clean_response.startswith('```json'): clean_response = clean_response[7:]
            if clean_response.startswith('```'): clean_response = clean_response[3:]
            if clean_response.endswith('```'): clean_response = clean_response[:-3]

            task_info = json.loads(clean_response.strip())
            task_title = task_info.get('title', task_title)
            task_description = task_info.get('description', task_description)

            ai_due_ms = task_info.get('due_date_ms')
            if isinstance(ai_due_ms, (int, str)) and str(ai_due_ms).isdigit():
                task_due_ms = int(ai_due_ms)
            else:
                task_due_ms = default_due_date_ms

        except Exception as e:
            await message.channel.send(f"❌ Jarvis failed JSON extraction/processing. Error: ```{e}```")
            return

        # Trigger cleanup
        trigger_phrases = ["jarvis, add this task", "add this task", "to clickup for me", "to clickup"]
        task_title_lower = task_title.lower()
        for phrase in trigger_phrases:
            if task_title_lower.startswith(phrase):
                task_title = task_title[len(phrase):].strip()
                task_title_lower = task_title.lower()

        if not task_title:
            task_title = "Task Requested Without Clear Title"

        final_description = f"Requested by {ctx.author.display_name} ({ctx.author.id}, {ctx.author.mention}).\n"
        final_description += f"Task Notes: {task_description}"

        # API Setup
        list_id = DEFAULT_CLICKUP_LIST_ID
        clean_list_id = "".join(filter(str.isalnum, list_id.strip()))
        url = CLICKUP_API_BASE + clean_list_id + CLICKUP_ENDPOINT_SUFFIX
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "name": task_title,
            "description": final_description,
            "due_date": task_due_ms,
            "priority": 3,
        }

        # --- NON-BLOCKING API CALL ---
        try:
            # CHANGED: Use aiohttp ClientSession instead of requests
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    # Check for HTTP errors manually since raise_for_status isn't automatic in aiohttp
                    if response.status >= 400:
                        try:
                            error_details = await response.json()
                        except:
                            error_details = {"message": "No detailed JSON error provided by ClickUp."}

                        error_message = f"ClickUp API Error ({response.status}): Could not create task."
                        await message.channel.send(
                            f"❌ Jarvis failed: {error_message}\nDetails: `{error_details.get('message')}`")
                        return

                    # Parse success
                    task_data = await response.json()

                    due_date_obj = datetime.datetime.fromtimestamp(task_due_ms / 1000).strftime('%Y-%m-%d')
                    await message.channel.send(
                        f'''Right away, sir. I have added task **"{task_data.get('name')}"** to your ClickUp board as requested.\n'''
                        f"Due: **{due_date_obj}**\n"
                        f"View Task: {task_data.get('url')}")

        except Exception as e:
            await message.channel.send(f"❌ Jarvis encountered an unknown error during API call: ```{e}```")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot and message.author.id != self.bot.user.id:
            return

        if not self.bot.operational and (message.author.id != self.bot.owner_id):
            return

        serverconfig = await adminFunctions.getServerConfig(await self.bot.get_context(message))

        content_lower = message.content.lower().strip()
        user_id = message.author.id
        now = datetime.datetime.now()

        def check_jarvis_prefix(text: str, command: str) -> str:
            base = "jarvis"
            prefix_with_comma = f"{base}, {command}"
            prefix_no_comma = f"{base} {command}"
            if text.startswith(prefix_with_comma):
                return text[len(prefix_with_comma):].strip()
            elif text.startswith(prefix_no_comma):
                return text[len(prefix_no_comma):].strip()
            return None

        # --- 1. Check for TASK command ---
        task_command_phrase = "add this task"
        task_details = check_jarvis_prefix(content_lower, task_command_phrase)

        if task_details is not None:
            await message.add_reaction('✅')
            # FIRE AND FORGET: Create task and return immediately
            asyncio.create_task(self._handle_task_addition(message, message.content))
            return

        # --- 2. Check for CONVERSATION command ---
        standard_conversation_trigger = check_jarvis_prefix(content_lower, "")

        if standard_conversation_trigger is not None:
            # Cooldown Logic
            special_users = [220134579736936448, 437324319102730263, 806938248060469280, 198602742317580288,
                             870337116381515816, 298548176778952704, 874912257128136734]
            exec_users = [199887270323552256, 299330776162631680, 502814400562987008, 686640777505669141, 712509599135301673]

            active_cooldown = serverconfig["jarviscooldown"]

            userSetList = await self.bot.sql.databaseFetchdict(f'''SELECT userid, COUNT(userid) AS value_occurrence FROM errorlist GROUP BY userid ORDER BY value_occurrence DESC LIMIT 10;''')
            if str(message.author.id) in str(userSetList) or message.author.id == 1005108173360869507: ## Nitro gifter is this ID
                active_cooldown = round(active_cooldown / 8)
            if message.author.id in special_users or message.author.guild_permissions.ban_members:
                active_cooldown = round(active_cooldown / 2)
            if message.author.id in exec_users:
                active_cooldown = 1
            if message.author.premium_since is not None:
                active_cooldown = round(active_cooldown / 24)
            if user_id not in self.on_message_cooldowns:
                self.on_message_cooldowns_burst[user_id] = 0
            else:
                self.on_message_cooldowns_burst[user_id] = self.on_message_cooldowns_burst[user_id] + 1
                last_triggered = self.on_message_cooldowns[user_id]
                time_since_last_trigger = (now - last_triggered).total_seconds()
                if time_since_last_trigger <= active_cooldown:
                    if self.on_message_cooldowns_burst[user_id] > serverconfig["jarvisburst"]:
                        await message.add_reaction("⏰")
                        return
                else:
                    self.on_message_cooldowns_burst[user_id] = 0

            self.on_message_cooldowns[user_id] = now
            self.on_message_cooldowns_notify[user_id] = False

            # FIRE AND FORGET: Move conversation logic to background task
            asyncio.create_task(self._handle_conversation(message))
            # Return immediately so other commands (like -settings) can process
            return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(jarvisFunctions(bot))