import os
import json
import asyncio
import datetime
import aiohttp
import discord
from discord.ext import commands
import type_hints
from cogs.adminFunctions import adminFunctions


class AIAssistants(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.configs_dir = "ai_configs"
        self.ai_personas = {}  # Holds loaded JSON configs
        self.active_sessions = {}  # Maps channel_id -> session data

        # Cooldown Tracking: (user_id, persona_name) -> data
        self.user_cooldowns = {}
        self.user_bursts = {}

        # Blacklist for NSFW/Racist terms
        self.blacklist = ["penis", "nigge", "cock", "jerk", "jork", "mig-15", "mig 15", "fagot"]

    async def cog_load(self):
        """Native discord.py method that runs asynchronously when the cog loads."""
        await self.load_configs()

    async def load_configs(self):
        """Loads all JSON files from the ai_configs directory and fetches knowledge URLs."""
        if not os.path.exists(self.configs_dir):
            os.makedirs(self.configs_dir)
            print(f"[AI Engine] Created {self.configs_dir} directory. Add JSONs and restart.")
            return

        async with aiohttp.ClientSession() as session:
            for filename in os.listdir(self.configs_dir):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join(self.configs_dir, filename), "r", encoding="utf-8") as f:
                            config = json.load(f)

                            # We use a clean base name for flexible triggering
                            key = config.get("activation_name", "").lower().strip()
                            if key.endswith(","): key = key[:-1].strip()

                            # --- FETCH KNOWLEDGE BASE URL ---
                            knowledge_url = config.get("knowledge_url", "")
                            if knowledge_url.startswith("http"):
                                try:
                                    print(f"[AI Engine] Fetching knowledge base for '{key}'...")
                                    async with session.get(knowledge_url) as r:
                                        if r.status == 200:
                                            config["_cached_knowledge"] = await r.text()
                                            print(
                                                f"[AI Engine] Successfully loaded {len(config['_cached_knowledge'])} characters of knowledge.")
                                        else:
                                            print(f"[AI Engine] Failed to fetch knowledge: HTTP {r.status}")
                                except Exception as e:
                                    print(f"[AI Engine] Failed to fetch knowledge URL: {e}")

                            if key:
                                self.ai_personas[key] = config
                    except Exception as e:
                        print(f"[AI Engine] Failed to load config {filename}: {e}")

        print(f"[AI Engine] Loaded {len(self.ai_personas)} AI Personas successfully.")

    async def get_or_create_webhook(self, channel: discord.TextChannel):
        """Retrieves an existing webhook or creates a new one for impersonation."""
        try:
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                if webhook.name == "SprocketAITool":
                    return webhook
            return await channel.create_webhook(name="SprocketAITool")
        except discord.Forbidden:
            print(f"[AI Engine] ERROR: Missing 'Manage Webhooks' permission in #{channel.name}")
            return None
        except Exception as e:
            print(f"[AI Engine] Webhook fetch error: {e}")
            return None

    def contains_blacklisted_words(self, text: str) -> bool:
        content_lower = text.lower()
        return any(word in content_lower for word in self.blacklist)

    def is_trigger_match(self, content_lower: str, base_name: str) -> bool:
        """Checks if the message starts with the AI's name (handles commas/spaces)."""
        if content_lower == base_name: return True
        if content_lower.startswith(f"{base_name} "): return True
        if content_lower.startswith(f"{base_name},"): return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if not self.bot.operational and (message.author.id != self.bot.owner_id):
            return

        # 1. Skip if message violates blacklist
        if self.contains_blacklisted_words(message.content):
            return

        channel_id = message.channel.id
        content_lower = message.content.lower().strip()

        # 2. Check if there is an ACTIVE session in this channel
        if channel_id in self.active_sessions:
            session = self.active_sessions[channel_id]
            # Feed message into the AI's queue
            await session["queue"].put(message)
            return

        # 3. If no active session, check if the user is attempting to SUMMON an AI
        for base_name, config in self.ai_personas.items():
            if self.is_trigger_match(content_lower, base_name):

                # Check Server Whitelist
                server_id = config.get("server_id", 0)
                if server_id != 0 and message.guild.id != server_id:
                    continue

                # Check Channel Whitelist
                allowed_channel_id = config.get("channel_id", 0)
                if allowed_channel_id != 0 and message.channel.id != allowed_channel_id:
                    continue

                # --- FETCH SERVER CONFIG ---
                ctx = await self.bot.get_context(message)
                try:
                    serverconfig = await adminFunctions.getServerConfig(ctx)
                except Exception as e:
                    print(f"[AI Engine] Failed to fetch server config: {e}")
                    serverconfig = {}

                # --- COOLDOWN & BURST LOGIC ---
                base_cooldown = serverconfig.get("jarviscooldown", config.get("cooldown_seconds", 60))
                burst_limit = serverconfig.get("jarvisburst", config.get("burst_limit", 5))
                active_cooldown = base_cooldown

                # Fetch top error users for cooldown reduction
                try:
                    userSetList = await self.bot.sql.databaseFetchdict(
                        f'''SELECT userid, COUNT(userid) AS value_occurrence FROM errorlist GROUP BY userid ORDER BY value_occurrence DESC LIMIT 10;''')
                    top_error_users = [int(row['userid']) for row in userSetList if 'userid' in row]
                except Exception as e:
                    top_error_users = []

                # Apply Reductions
                if message.author.id in top_error_users or message.author.id == 1005108173360869507:  # Nitro Gifter
                    active_cooldown = round(active_cooldown / 8)

                special_users = [220134579736936448, 437324319102730263, 806938248060469280, 198602742317580288,
                                 870337116381515816, 298548176778952704, 874912257128136734]
                if message.author.id in special_users or message.author.guild_permissions.ban_members:
                    active_cooldown = round(active_cooldown / 2)

                exec_users = [199887270323552256, 299330776162631680, 502814400562987008, 686640777505669141,
                              712509599135301673]
                if message.author.id in exec_users:
                    active_cooldown = 1

                if message.author.premium_since is not None:
                    active_cooldown = round(active_cooldown / 24)

                # Floor cooldown at 1 second
                if active_cooldown < 1:
                    active_cooldown = 1

                # Evaluate limits
                cooldown_key = (message.author.id, base_name)
                now = datetime.datetime.now()

                if cooldown_key not in self.user_cooldowns:
                    self.user_bursts[cooldown_key] = 0
                else:
                    self.user_bursts[cooldown_key] += 1
                    last_triggered = self.user_cooldowns[cooldown_key]
                    time_since = (now - last_triggered).total_seconds()

                    if time_since <= active_cooldown:
                        if self.user_bursts[cooldown_key] > burst_limit:
                            await message.add_reaction("⏰")
                            print(
                                f"[AI Engine] Blocked '{base_name}' summon from {message.author.name} - burst limit hit.")
                            return
                    else:
                        # Time window passed, reset burst tracker
                        self.user_bursts[cooldown_key] = 0

                # Log the valid trigger
                self.user_cooldowns[cooldown_key] = now

                # Lock the channel and start the conversation loop
                print(f"[AI Engine] Summoning '{config.get('webhook_name')}' in #{message.channel.name}")
                await self.start_conversation(message.channel, config, message)
                return

    async def start_conversation(self, channel: discord.TextChannel, config: dict, initial_message: discord.Message):
        """Initializes the session state and spawns the background worker loop."""
        queue = asyncio.Queue()
        await queue.put(initial_message)

        history = []
        context_limit = config.get("context_limit", 0)

        # --- FETCH PREVIOUS CONTEXT MESSAGES ---
        if context_limit > 0:
            try:
                past_messages = []
                # Retrieve 'context_limit' messages prior to the summon command
                async for msg in channel.history(limit=context_limit, before=initial_message):
                    # Flag messages from bots as 'AI' and real users as 'User'
                    role = "AI" if msg.author.bot else "User"
                    past_messages.append({
                        "role": role,
                        "author": msg.author.display_name,
                        "content": msg.clean_content
                    })

                # Reverse them so they are in chronological order
                past_messages.reverse()
                history.extend(past_messages)
                print(f"[AI Engine] Fetched {len(past_messages)} previous context messages.")
            except discord.Forbidden:
                print(f"[AI Engine] WARNING: Missing 'Read Message History' permission in #{channel.name}")
            except Exception as e:
                print(f"[AI Engine] Error fetching context history: {e}")

        self.active_sessions[channel.id] = {
            "config": config,
            "queue": queue,
            "history": history,
            "message_count": 0
        }

        # Fire and forget the background processing loop with an error wrapper
        asyncio.create_task(self._safe_conversation_loop(channel.id))

    async def _safe_conversation_loop(self, channel_id: int):
        """Wrapper to prevent the background task from failing silently."""
        try:
            await self._conversation_loop(channel_id)
        except Exception as e:
            print(f"[AI Engine] CRITICAL TASK CRASH in #{channel_id}: {e}")
            import traceback
            traceback.print_exc()
            await self.end_session(channel_id)

    async def _conversation_loop(self, channel_id: int):
        """The core rate-limited AI processing loop."""
        session = self.active_sessions[channel_id]
        config = session["config"]
        queue = session["queue"]
        history = session["history"]
        message_cap = config.get("message_cap", 10)
        use_webhook = config.get("use_webhook", True)

        channel = self.bot.get_channel(channel_id)
        if not channel:
            await self.end_session(channel_id)
            return

        # Safely fetch Webhook ONLY if use_webhook is True
        webhook = None
        if use_webhook:
            webhook = await self.get_or_create_webhook(channel)
            if not webhook:
                await channel.send(
                    "❌ **System Error:** I cannot run this AI Persona here because I am missing the `Manage Webhooks` permission. (You can set `\"use_webhook\": false` in the config to bypass this).")
                await self.end_session(channel_id)
                return

        while session["message_count"] < message_cap:
            try:
                print(f"[AI Engine] Waiting for messages in #{channel.name}...")
                message: discord.Message = await asyncio.wait_for(queue.get(), timeout=120.0)
            except asyncio.TimeoutError:
                print(f"[AI Engine] Session timed out (idle) in #{channel.name}.")
                break

            # --- PROCESS ATTACHMENTS (Images + Text Files) ---
            ai_model = config.get("ai_model", "normal")
            attachments = []
            message_content = message.clean_content

            for att in message.attachments:
                # Handle Images
                if att.content_type and att.content_type.startswith("image/"):
                    attachments.append(att)
                    ai_model = "gemma"
                    # Handle Text Files
                elif att.filename.endswith(".txt") or (att.content_type and att.content_type.startswith("text/")):
                    try:
                        file_bytes = await att.read()
                        file_text = file_bytes.decode('utf-8')
                        message_content += f"\n\n[USER ATTACHED TEXT FILE: {att.filename}]\n{file_text}"
                        print(f"[AI Engine] Appended text file {att.filename} to user prompt.")
                    except Exception as e:
                        print(f"[AI Engine] Failed to read text attachment: {e}")

            # Add user message to history
            history.append({"role": "User", "author": message.author.display_name, "content": message_content})

            # --- DYNAMIC HISTORY TRIMMER ---
            # Automatically preserve the configured context_limit + the active message cap + a small buffer
            max_memory = config.get("context_limit", 0) + message_cap + 5

            # Prevent context from exceeding 30 interactions total to avoid extreme token bloat
            max_memory = min(max_memory, 30)

            while len(history) > max_memory:
                history.pop(0)

            # --- PREPARE SYSTEM INSTRUCTIONS (Developer Context) ---
            is_last_message = (session["message_count"] >= message_cap - 1)
            exit_instructions = config.get("exit_instructions", "").strip()

            system_instruction = (
                f"You are {config.get('webhook_name')}. {config.get('character_details')}\n"
                f"Personality: {config.get('personality')}\n"
                f"Format rules: Min length {config.get('min_length', 10)} chars, Max length {config.get('max_length', 2000)} chars.\n\n"
            )

            # Inject the cached knowledge base directly into the strict system instructions
            cached_knowledge = config.get("_cached_knowledge", "")
            if cached_knowledge:
                system_instruction += (
                    f"=== INTERNAL KNOWLEDGE BASE ===\n"
                    f"You MUST use the information below to answer user questions accurately. Do not invent answers if the topic is covered here:\n\n"
                    f"{cached_knowledge}\n"
                    f"===============================\n\n"
                )

            system_instruction += (
                f"INSTRUCTIONS:\n"
                f"Read the user's chat history. You must decide whether to reply to the latest message.\n"
                f"- If you choose NOT to reply (e.g., the message wasn't directed at you), output EXACTLY `******` and nothing else.\n"
            )

            # Exit logic instructions (Strictly Constrained)
            if exit_instructions:
                system_instruction += f"- DO NOT end the conversation unless the user explicitly dismisses you, says goodbye, or the conversation has reached a definitive conclusion.\n"
                system_instruction += f"- If and ONLY if those conditions are met, include the tag `[end]` in your response and follow these exit instructions: {exit_instructions}\n"
            else:
                system_instruction += f"- DO NOT end the conversation unless the user explicitly dismisses you, says goodbye, or the conversation has reached a definitive conclusion.\n"
                system_instruction += f"- If and ONLY if those conditions are met, include the tag `[end]` anywhere in your response.\n"

            # Hard cap warning injection
            if is_last_message:
                system_instruction += "\n⚠️ SYSTEM ALERT: This is your final message before the conversation hard-cap is reached. You MUST wrap up the conversation now and include the `[end]` tag in your response."
                if exit_instructions:
                    system_instruction += f" Follow your exit instructions: {exit_instructions}"
                system_instruction += "\n"

            system_instruction += f"- Generate your in-character response. Do not include your own name at the start.\n\n"

            # --- PREPARE USER PROMPT (Chat History) ---
            user_prompt = "CHAT HISTORY:\n"
            for entry in history:
                user_prompt += f"{entry['role']} ({entry.get('author', 'AI')}): {entry['content']}\n"
            user_prompt += "Your Response:"

            # Get temperature (Default 0.4 for strong factual recall)
            ai_temp = config.get("temperature", 0.4)

            # --- CALL AI API ---
            try:
                print(f"[AI Engine] Generating response using model '{ai_model}' with temp {ai_temp}...")

                # If webhook is false, show typing indicator. If true, hide it.
                if use_webhook:
                    ai_response = await self.bot.AI.get_response(
                        prompt=user_prompt,
                        temperature=ai_temp,
                        instructions=system_instruction,
                        mode=ai_model,
                        attachments=attachments
                    )
                else:
                    async with channel.typing():
                        ai_response = await self.bot.AI.get_response(
                            prompt=user_prompt,
                            temperature=ai_temp,
                            instructions=system_instruction,
                            mode=ai_model,
                            attachments=attachments
                        )
            except Exception as e:
                print(f"[AI Engine] API Error: {e}")
                ai_response = "******"  # Skip on error

            # Clean response
            ai_response = (ai_response or "******").strip()

            # --- HANDLE AI DECISIONS ---
            if ai_response == "******" or ai_response == "":
                print(f"[AI Engine] AI chose to stay silent.")
                continue

            # Check for [end] tag
            end_conversation = False
            if "[end]" in ai_response.lower():
                end_conversation = True
                ai_response = ai_response.replace("[end]", "").replace("[END]", "").strip()

            # Apply blacklist filter to AI output
            for item in self.blacklist:
                ai_response = ai_response.replace(item, "").replace(item.capitalize(), "")

            # --- SEND RESPONSE ---
            if ai_response:
                try:
                    if use_webhook and webhook:
                        await webhook.send(
                            content=ai_response,
                            username=config.get("webhook_name"),
                            avatar_url=config.get("webhook_avatar")
                        )
                    else:
                        # Send directly from the bot as a reply
                        try:
                            await message.reply(content=ai_response)
                        except discord.HTTPException:
                            # Fallback if the user deleted their message while the AI was thinking
                            await channel.send(content=ai_response)

                    session["message_count"] += 1
                    history.append({"role": "AI", "content": ai_response})
                    print(f"[AI Engine] Sent message {session['message_count']}/{message_cap}")
                except Exception as e:
                    print(f"[AI Engine] Message sending failed: {e}")

            if end_conversation:
                print(f"[AI Engine] AI signaled [end] tag.")
                break

        # --- EXIT CONVERSATION ---
        await self.end_session(channel_id)

    async def end_session(self, channel_id: int):
        """Cleans up the active session."""
        if channel_id in self.active_sessions:
            print(f"[AI Engine] Ending session in channel {channel_id}")
            # We removed the session_cooldowns line here since cooldowns are now per-user!
            del self.active_sessions[channel_id]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AIAssistants(bot))