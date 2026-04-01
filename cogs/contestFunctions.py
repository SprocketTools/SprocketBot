import discord
import type_hints
from discord.ext import commands
import json
import datetime
import aiohttp
import asyncio
import os
import random
import zipfile
import random
import io
import pandas as pd
from typing import Union
from cogs.textTools import textTools

CHAOS_VEHICLE_TYPES = {
    "Tankette": {"weight": (2.0, 5.0), "caliber": (20, 37)},
    "Light Tank": {"weight": (5.0, 15.0), "caliber": (20, 50)},
    "Medium Tank": {"weight": (15.0, 35.0), "caliber": (50, 88)},
    "Heavy Tank": {"weight": (35.0, 65.0), "caliber": (85, 122)},
    "Super Heavy Tank": {"weight": (65.0, 150.0), "caliber": (105, 183)},
    "Armored Car": {"weight": (2.0, 15.0), "caliber": (20, 47)},
    "Tank Destroyer": {"weight": (10.0, 50.0), "caliber": (75, 152)},
    "SPG": {"weight": (10.0, 40.0), "caliber": (105, 183)}
}

class contestFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------
    # SETUP: Database Tables (Contests Only)
    # ----------------------------------------------------------------------------------
    @commands.command()
    async def setupContestTables(self, ctx: commands.Context):
        """[Owner] Initializes or updates the Contest database tables."""
        if ctx.author.id != self.bot.ownerid:
            return await self.bot.error.sendError(ctx)

        # 1. Ensure Blueprint Stats table exists
        try:
            bp_cog = self.bot.get_cog("blueprintFunctions2")
            if bp_cog:
                await bp_cog.setup_stats_tables(ctx)
            else:
                await ctx.send("Warning: `blueprintFunctions2` not loaded. Skipping stats table check.")
        except Exception as e:
            print(f"Stats table sync error: {e}")

        # 2. Main Contests Table
        # (Commented out DROP TABLE so you don't accidentally wipe active contests! Re-enable only if you want a total nuke.)
        # await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS contests;''')

        await self.bot.sql.databaseExecute('''
                CREATE TABLE IF NOT EXISTS contests (
                    contest_id BIGINT PRIMARY KEY,
                    name VARCHAR,
                    serverID BIGINT,
                    ownerID BIGINT,
                    description VARCHAR,
                    rulesLink VARCHAR,
                    status BOOLEAN,
                    deadline TIMESTAMP,
                    costlimit BIGINT,
                    weightLimit REAL,
                    era VARCHAR,
                    crewMin INT,
                    crewMax INT,
                    hullHeightMin REAL,
                    hullWidthMax REAL,
                    torsionBarLengthMin REAL,
                    allowHVSS BOOLEAN,
                    beltWidthMin REAL,
                    groundPressureMax REAL,
                    minHPT REAL,
                    caliberLimit REAL,
                    armorMax REAL,
                    submission_channel_id BIGINT,
                    log_channel_id BIGINT,
                    entryLimit INT DEFAULT 0,
                    violationLimit INT DEFAULT 0,
                    caliber_min FLOAT DEFAULT 0,
                    caliber_max FLOAT DEFAULT 0,
                    prop_min FLOAT DEFAULT 0,
                    prop_max FLOAT DEFAULT 0,
                    barrel_limit_m FLOAT DEFAULT 0,
                    chaos_level INT DEFAULT 0,
                    chaos_vehicle_types VARCHAR,
                    ai_companion BOOLEAN DEFAULT FALSE,
                    ai_prompt VARCHAR
                );
            ''')

        # 3. User Chaos Rolls Table (WITH NEW TIMESTAMP COLUMN)
        # We drop this one to cleanly wipe the old formats and apply the timestamp upgrade
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS user_chaos_rolls;''')
        await self.bot.sql.databaseExecute('''
                CREATE TABLE IF NOT EXISTS user_chaos_rolls (
                    user_id BIGINT,
                    contest_id BIGINT,
                    target_weight REAL,
                    gun_count INT,
                    vehicle_type VARCHAR,
                    target_caliber REAL,
                    min_fuel REAL,
                    roll_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, contest_id)
                );
            ''')

        # 4. Cleanup old deprecated tables
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS contestcategories;''')
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS contest_entries;''')
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS contestsubmissions;''')

        await ctx.send(
            "✅ **Done!** Contest database tables are configured and running the latest schema (including AI Build Time tracking).")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot: return

        # Ignore explicit bot commands so we don't double-trigger
        if message.content.startswith('-'): return

        # --- DEBUG 1 ---
        # print(f"DEBUG: Message sent in {message.channel.name}")

        contest_records = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
            [message.channel.id]
        )
        if not contest_records: return

        contest_data = {k.lower(): v for k, v in contest_records[0].items()}

        # --- DEBUG 2 ---
        print(f"DEBUG: Contest found ({contest_data.get('name')}). AI Enabled? {contest_data.get('ai_companion')}")

        if not contest_data.get('ai_companion'): return

        # ==========================================
        # SCENARIO A: AUTO-SUBMIT BLUEPRINT
        # ==========================================
        bp_attachment = next((a for a in message.attachments if a.filename.endswith(".blueprint")), None)

        if bp_attachment:
            ctx = await self.bot.get_context(message)
            img_attachment = next(
                (a for a in message.attachments if a.filename.lower().endswith(('.png', '.jpg', '.jpeg'))), None)

            # 1. Fetch persona data early to get the processing phrase
            ai_prompt = contest_data.get('ai_prompt')
            persona_data = {}
            if ai_prompt:
                try:
                    persona_data = json.loads(ai_prompt)
                except Exception:
                    pass

            processing_phrase = persona_data.get("processing_phrase", "Taking a look at this...")

            # Send the initial confirmation message instantly
            processing_msg = await message.reply(f"{processing_phrase}", allowed_mentions=discord.AllowedMentions.none())

            async with message.channel.typing():
                try:
                    success, stats, warnings, clean_name = await self._process_entry(ctx, message, bp_attachment,
                                                                                     img_attachment, contest_data,
                                                                                     silent=True)
                except Exception as e:
                    print(f"DEBUG: Validator crashed! {e}")
                    await processing_msg.edit(content="❌ *(An error occurred while inspecting this blueprint.)*")
                    return

                # --- VISUAL CONFIRMATION ---
                await message.add_reaction('✅' if success else '❌')
                #status_header = "✅ **[OFFICIAL SUBMISSION ACCEPTED]**\n" if success else "❌ **[OFFICIAL SUBMISSION REJECTED]**\n"

                tank_data = {
                    "name": clean_name,
                    "weight": stats.get('tank_weight', 0) / 1000.0 if stats else 0,
                    "cost": stats.get('base_cost', 0) if stats else 0,
                    "warnings": warnings or [],
                    "rejected": not success,
                    "build_time": stats.get('build_time') if stats else None
                }

                ai_text = await self._ask_gemma_judge(contest_data.get('ai_prompt'), message.author.display_name,
                                                      contest_data, tank_data=tank_data)

                import re
                if not success:
                    # REJECTED: Inject the list of broken rules
                    formatted_warnings = "\n".join([f"❌ **{w}**" for w in
                                                    warnings]) if warnings else "❌ **(Vehicle failed global rule validation)**"
                    injection_string = f"\n\n{formatted_warnings}\n\n"

                    if "[warnings]" in ai_text.lower():
                        ai_text = re.sub(r'\[warnings\]', injection_string, ai_text, flags=re.IGNORECASE)
                    else:
                        ai_text += f"\n\n*(Automated Violation Report):*{injection_string}"
                else:
                    # ACCEPTED: If the AI hallucinates the tag, silently erase it!
                    ai_text = re.sub(r'\[warnings\]', "", ai_text, flags=re.IGNORECASE).strip()

                # Edit the processing message with the final response
                final_reply = f"{ai_text}"
                await processing_msg.edit(content=final_reply, allowed_mentions=discord.AllowedMentions.none())
            return

        # ==========================================
        # SCENARIO B: CONVERSATIONAL CHAT
        # ==========================================
        if message.content:
            try:
                print("DEBUG CHAT: Starting Scenario B analysis...")
                is_pinged = self.bot.user in message.mentions
                force_reply = is_pinged
                secret_context = ""

                chat_lower = message.content.lower()
                keywords = ['rule', 'requirement', 'roll', 'stat', 'build', 'assignment', 'what do i', 'give me']
                asking_for_stats = any(k in chat_lower for k in keywords)
                if asking_for_stats:
                    force_reply = True

                print(f"DEBUG CHAT: Is Pinged? {is_pinged} | Asking for Stats? {asking_for_stats}")

                if contest_data.get('chaos_level') and contest_data['chaos_level'] > 0:
                    print("DEBUG CHAT: Chaos level > 0 detected. Checking DB for existing rolls...")
                    user_records = await self.bot.sql.databaseFetchdictDynamic(
                        '''SELECT * FROM user_chaos_rolls WHERE user_id = $1 AND contest_id = $2;''',
                        [message.author.id, contest_data['contest_id']]
                    )
                    if user_records and len(user_records) > 0:
                        print("DEBUG CHAT: User already has a roll.")
                        roll = user_records[0]
                        if asking_for_stats:
                            print("DEBUG CHAT: User asked for existing stats. Reminding them to check DMs...")
                            # --- BUG FIX: Do NOT resend the DM! Just tell the AI to remind them! ---
                            secret_context = f"\n\n[System Note: The user is asking for their vehicle requirements, but you ALREADY sent them to their private direct messages (mailbox) previously. Their OFFICIAL assignment is: {roll['vehicle_type']}, {round(roll['target_weight'], 1)}t, {roll['target_caliber']}mm. Tell them aggressively/in-character to go check their mailbox history! Do NOT invent different numbers and do NOT state the numbers in this channel!]"
                        else:
                            secret_context = f"\n\n[System Note: The user is just chatting. Reply in-character. Their assigned vehicle is a {roll['vehicle_type']}. Do NOT mention any of their specific numbers or invent new ones.]"
                    else:
                        print("DEBUG CHAT: No roll found. Generating new stats...")
                        force_reply = True
                        new_stats = self._generate_chaos_roll(
                            contest_data['chaos_level'],
                            contest_data.get('chaos_vehicle_types', '')
                        )

                        print("DEBUG CHAT: New stats generated. Saving to DB...")
                        await self.bot.sql.databaseExecuteDynamic(
                            '''INSERT INTO user_chaos_rolls (user_id, contest_id, target_weight, gun_count, vehicle_type, target_caliber, min_fuel)
                               VALUES ($1, $2, $3, $4, $5, $6, $7);''',
                            [message.author.id, contest_data['contest_id'], new_stats['target_weight'],
                             new_stats['gun_count'],
                             new_stats['vehicle_type'], new_stats['target_caliber'], new_stats['min_fuel']]
                        )

                        print("DEBUG CHAT: Sending new roll DM...")
                        dm_success = await self._send_roll_dm(message.author, contest_data, new_stats)
                        if dm_success:
                            secret_context = "\n\n[System Note: This user did not have a vehicle assignment, so you just generated one and sent it to their private DMs. Welcome them to the contest and excitedly (or aggressively) tell them to check their mailbox for their assignment! DO NOT reveal the numbers in this channel.]"
                        else:
                            secret_context = "\n\n[System Note: You tried to assign this new user a vehicle, but their Discord DMs are closed! Tell them they must open their mailbox/DMs to receive their assignment.]"

                print(f"DEBUG CHAT: Proceeding to chatter filter. Force Reply = {force_reply}")
                if not force_reply:
                    rng = random.random()
                    print(f"DEBUG CHAT: Casual chat RNG roll: {rng} (Needs <= 0.015 to proceed)")
                    if rng > 0.015:
                        print("DEBUG CHAT: RNG failed. Silently ignoring casual message.")
                        return

                print("DEBUG CHAT: Handing off to AI Engine for final channel reply...")
                async with message.channel.typing():
                    ai_text = await self._ask_gemma_judge(
                        ai_prompt=contest_data.get('ai_prompt'),
                        user_name=message.author.display_name,
                        contest_data=contest_data,
                        user_message=message.content + secret_context
                    )
                    # --- SECURITY PATCH: Break highlight and block pings ---
                    if ai_text:
                        ai_text = ai_text.replace("@everyone", "an everyone ping").replace("@here", "a here ping")
                    await message.reply(ai_text, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=True))
                    print("DEBUG CHAT: Success! Message replied to.")

            except Exception as e:
                print(f"CRITICAL ERROR IN SCENARIO B: {e}")
                import traceback
                traceback.print_exc()

    @commands.command(name="createContest", description="Start a new building contest")
    async def createContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        # 1. Basic Info
        name = await textTools.getCappedResponse(ctx, "What is the name of this contest?", 64)

        exists = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT name FROM contests WHERE name = $1 AND serverID = $2;''',
            [name, ctx.guild.id]
        )
        print(exists)
        if len(exists) > 1:
            return await ctx.send("A contest with that name already exists in this server.")

        contest_id = random.randint(10000000, 99999999)
        desc = await textTools.getResponse(ctx, "Provide a brief description.")
        rules = await textTools.getResponse(ctx, "Link to rules (or type 'None').")

        # 2. Limits
        weight_lim = await textTools.getFloatResponse(ctx, "Max Weight (tons) (0 for none):")
        cost_lim = await textTools.getIntResponse(ctx, "Max Cost (0 for none):")

        # New: Violation Limit
        vio_lim = await textTools.getIntResponse(ctx, "Max Rule Violations allowed (0 for strict):")

        # --- CHAOS MODE SETTINGS ---
        chaos_level = await textTools.getIntResponse(ctx,"Enable Randomized Vehicle Stats? Enter a randomization level from 1 to 10 (Enter `0` to disable randomization):")

        # Clamp the value between 0 and 10 for math safety
        chaos_level = max(0, min(10, chaos_level))

        chaos_vehicle_types = ""

        # Only ask the follow-up questions if they actually enabled Chaos Mode!
        if chaos_level > 0:
            type_list = ", ".join(list(CHAOS_VEHICLE_TYPES.keys()))
            chaos_vehicle_types = await textTools.getResponse(ctx,f"Enter the **allowed Vehicle Types** for randomization, separated by semicolons (or type 'All').\n*(Available types: {type_list})*")

        # 3. Channels
        submission_channel_id = 0
        await ctx.send("Mention the Submission Channel or Thread (where users upload files):")

        while True:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out.")

            if msg.content.lower() == "cancel": return await ctx.send("Cancelled.")

            target_obj = None
            if msg.channel_mentions:
                target_obj = msg.channel_mentions[0]
            if not target_obj:
                clean_content = "".join([c for c in msg.content if c.isdigit()])
                if clean_content:
                    try:
                        target_obj = ctx.guild.get_channel_or_thread(int(clean_content))
                        if not target_obj: target_obj = await ctx.guild.fetch_channel(int(clean_content))
                    except:
                        target_obj = None

            if target_obj and isinstance(target_obj, (discord.TextChannel, discord.Thread)):
                submission_channel_id = target_obj.id
                overlap = await self.bot.sql.databaseFetchdictDynamic(
                    '''SELECT name FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
                    [submission_channel_id]
                )
                if len(overlap) < 0:
                    await ctx.send(f"Channel occupied by '{overlap[0]['name']}'. Choose another.")
                    continue
                break
            else:
                await ctx.send("Invalid Channel/Thread. Try again.")

        log_channel_id = 0
        raw_log = await textTools.getResponse(ctx, "Mention the Log Channel (or 'here'):")
        if "here" in raw_log.lower():
            log_channel_id = ctx.channel.id
        else:
            try:
                log_id_str = ''.join(filter(str.isdigit, raw_log))
                log_channel_id = int(log_id_str) if log_id_str else ctx.channel.id
            except:
                log_channel_id = ctx.channel.id

        # 4. Date Picker
        deadline = await ctx.bot.ui.getDate(ctx, "Select the deadline:")
        if not deadline:
            return await ctx.send("Cancelled.")

        # 5. Insert
        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO contests (contest_id, name, serverID, ownerID, description, rulesLink, status, deadline, weightLimit, costlimit, submission_channel_id, log_channel_id, entryLimit, violationLimit, prop_max, barrel_limit_m, chaos_level, chaos_vehicle_types) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 0, $13, $14, $15, $16, $17);''',
            [contest_id, name, ctx.guild.id, ctx.author.id, desc, rules, True, deadline, weight_lim, cost_lim,
             submission_channel_id, log_channel_id, vio_lim, 0.0, 0.0, chaos_level, chaos_vehicle_types]
        )

        formatted_date = deadline.strftime("%B %d, %Y")
        await ctx.send(
            f"**Contest Created!**\nID: `{contest_id}`\nName: {name}\nDeadline: {formatted_date}\nSubmit Here: <#{submission_channel_id}>")

    @commands.command(name="manageContest", description="Dashboard to edit all contest settings")
    async def manageContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        # 1. Select Contest
        contest_id = await self._pick_contest(ctx, only_active=False)
        if not contest_id: return

        # Main Loop
        while True:
            data = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM contests WHERE contest_id = $1 AND serverID = $2;''',
                [contest_id, ctx.guild.id]
            )
            if not data:
                await ctx.send("Contest not found.")
                break

            # Build Dashboard Embed
            status_txt = "Open" if data['status'] else "Closed"
            dl_str = data['deadline'].strftime("%Y-%m-%d") if data['deadline'] else "None"
            entry_limit_str = str(data['entrylimit']) if data.get('entrylimit', 0) > 0 else "Unlimited"
            vio_limit = data.get('violationlimit', 0)

            embed = discord.Embed(title=f"Managing: {data['name']}", color=discord.Color.blue())

            gen_info = f"**Desc:** {data['description'][:50]}...\n**Rules:** {data['ruleslink']}\n**Status:** {status_txt}\n**Deadline:** {dl_str}"
            embed.add_field(name="General Info", value=gen_info, inline=False)

            limits = f"**Weight:** {data['weightlimit']}t | **Cost:** {data['costlimit']}\n**Era:** {data['era']}\n**Crew:** {data['crewmin']}-{data['crewmax']}\n**Entries:** {entry_limit_str} | **Max Violations:** {vio_limit}"
            embed.add_field(name="Core Limits", value=limits, inline=False)

            dims = f'''**Hull height min:** {(str(data['hullheightmin']) + 'm') if data['hullheightmin'] else 'None'}\n**Hull width max:** {(str(data['hullwidthmax']) + 'm') if data['hullwidthmax'] else 'None'}\n**Torsion bar length min:** > {(str(round(data['torsionbarlengthmin'] * 1000)) + 'mm') if data['torsionbarlengthmin'] else 'None'}\n**Other suspension allowed:** {'Yes' if data['allowhvss'] else 'No'}'''

            embed.add_field(name="Dimensions/Suspension", value=dims, inline=False)

            mob = f"**HP/T:** > {data['minhpt']}\n**Gnd Press:** < {data['groundpressuremax']}\n**Belt:** > {data['beltwidthmin']}"
            embed.add_field(name="Mobility", value=mob, inline=True)

            fire = f"**Caliber:** < {data['caliberlimit']}mm\n**Armor:** < {data['armormax']}mm"
            embed.add_field(name="Firepower", value=fire, inline=True)

            chans = f"**Submit:** <#{data['submission_channel_id']}>\n**Logs:** <#{data['log_channel_id']}>"
            embed.add_field(name="Channels", value=chans, inline=False)

            # Buttons
            options = [
                "General Info", "Status/Deadline", "Channels",
                "Weight/Cost/Limit", "Era/Crew", "Dimensions",
                "Mobility", "Firepower", "Exit"
            ]
            msgOut = await ctx.send(embed=embed)
            selection = await ctx.bot.ui.getButtonChoice(ctx, options)

            if selection == "Exit":
                await msgOut.delete()
                break

            # --- Logic Handlers ---
            elif selection == "General Info":
                sub = await ctx.bot.ui.getButtonChoice(ctx, ["Name", "Description", "Rules Link", "Back"])
                if sub == "Name":
                    val = await textTools.getCappedResponse(ctx, "Enter new name:", 64)
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET name=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
                elif sub == "Description":
                    val = await textTools.getResponse(ctx, "Enter description:")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET description=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
                elif sub == "Rules Link":
                    val = await textTools.getResponse(ctx, "Enter rules link:")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET ruleslink=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])

            elif selection == "Status/Deadline":
                sub = await ctx.bot.ui.getButtonChoice(ctx, ["Toggle Status", "Set Deadline", "Back"])
                if sub == "Toggle Status":
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET status=$1 WHERE contest_id=$2",
                                                              [not data['status'], data['contest_id']])
                elif sub == "Set Deadline":
                    val = await ctx.bot.ui.getDate(ctx, "Select new deadline:")
                    if val: await self.bot.sql.databaseExecuteDynamic(
                        "UPDATE contests SET deadline=$1 WHERE contest_id=$2", [val, data['contest_id']])

            elif selection == "Channels":
                sub = await ctx.bot.ui.getButtonChoice(ctx, ["Submission Channel", "Log Channel", "Back"])
                if sub == "Submission Channel":
                    chan = await textTools.getChannelResponse(ctx, "Mention new submission channel:")
                    if chan:
                        overlap = await self.bot.sql.databaseFetchdictDynamic(
                            "SELECT name FROM contests WHERE submission_channel_id=$1 AND status=TRUE AND contest_id!=$2",
                            [chan, data['contest_id']])
                        if overlap:
                            await ctx.send(f"Occupied by {overlap['name']}")
                        else:
                            await self.bot.sql.databaseExecuteDynamic(
                                "UPDATE contests SET submission_channel_id=$1 WHERE contest_id=$2",
                                [chan, data['contest_id']])
                elif sub == "Log Channel":
                    chan = await textTools.getChannelResponse(ctx, "Mention new log channel:")
                    if chan: await self.bot.sql.databaseExecuteDynamic(
                        "UPDATE contests SET log_channel_id=$1 WHERE contest_id=$2", [chan, data['contest_id']])

            elif selection == "Weight/Cost/Limit":
                sub = await ctx.bot.ui.getButtonChoice(ctx, ["Max Weight", "Max Cost", "Entry Limit", "Max Violations",
                                                             "Back"])
                if sub == "Max Weight":
                    val = await textTools.getFloatResponse(ctx, "Enter Max Weight (0 for none):")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET weightlimit=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
                elif sub == "Max Cost":
                    val = await textTools.getIntResponse(ctx, "Enter Max Cost (0 for none):")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET costlimit=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
                elif sub == "Entry Limit":
                    val = await textTools.getIntResponse(ctx, "Enter Max Entries per User (0 for Unlimited):")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET entrylimit=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
                elif sub == "Max Violations":
                    val = await textTools.getIntResponse(ctx, "Enter Max Allowed Violations (0 for Strict):")
                    await self.bot.sql.databaseExecuteDynamic(
                        "UPDATE contests SET violationlimit=$1 WHERE contest_id=$2",
                        [val, data['contest_id']])

            elif selection == "Era/Crew":
                sub = await ctx.bot.ui.getButtonChoice(ctx, ["Era", "Min Crew", "Max Crew", "Back"])
                if sub == "Era":
                    val = await ctx.bot.ui.getChoiceFromList(ctx, ["WWI", "Interwar", "Earlywar", "Midwar", "Latewar",
                                                                   "None"], "Select Era:")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET era=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
                elif sub == "Min Crew":
                    val = await textTools.getIntResponse(ctx, "Enter Min Crew:")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET crewmin=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
                elif sub == "Max Crew":
                    val = await textTools.getIntResponse(ctx, "Enter Max Crew (0 for none):")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET crewmax=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])

            elif selection == "Dimensions":
                sub = await ctx.bot.ui.getButtonChoice(ctx,
                                                       ["Min Height", "Max Width", "Min Torsion", "Allow HVSS", "Back"])
                cmap = {"Min Height": "hullheightmin", "Max Width": "hullwidthmax",
                        "Min Torsion": "torsionbarlengthmin"}
                try:
                    if sub == "Allow HVSS":
                        val = await ctx.bot.ui.getYesNoChoice(ctx)
                        await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET allowhvss=$1 WHERE contest_id=$2",
                                                                  [val, data['contest_id']])
                    elif sub in cmap:
                        val = await textTools.getFloatResponse(ctx, f"Enter {sub}:")
                        await self.bot.sql.databaseExecuteDynamic(f"UPDATE contests SET {cmap[sub]}=$1 WHERE contest_id=$2",
                                                                  [val, data['contest_id']])
                except Exception as e:
                    await ctx.send(f"Error: {e}")

            elif selection == "Mobility":
                sub = await ctx.bot.ui.getButtonChoice(ctx, ["Min HP/T", "Max Gnd Press", "Min Belt Width", "Back"])
                cmap = {"Min HP/T": "minhpt", "Max Gnd Press": "groundpressuremax", "Min Belt Width": "beltwidthmin"}
                if sub in cmap:
                    val = await textTools.getFloatResponse(ctx, f"Enter {sub}:")
                    await self.bot.sql.databaseExecuteDynamic(f"UPDATE contests SET {cmap[sub]}=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])

            elif selection == "Firepower":
                sub = await ctx.bot.ui.getButtonChoice(ctx, ["Max Caliber", "Max Armor", "Back"])
                cmap = {"Max Caliber": "caliberlimit", "Max Armor": "armormax"}
                if sub in cmap:
                    val = await textTools.getFloatResponse(ctx, f"Enter {sub}:")
                    await self.bot.sql.databaseExecuteDynamic(f"UPDATE contests SET {cmap[sub]}=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
            await msgOut.delete()
        await ctx.send("Exited Dashboard.")

    @commands.command(name="renameContest", description="Rename a contest")
    async def renameContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        # Now returns ID
        contest_id = await self._pick_contest(ctx, only_active=False)
        if not contest_id: return

        new_name = await textTools.getCappedResponse(ctx, "Enter the new name:", 64)

        await self.bot.sql.databaseExecuteDynamic(
            '''UPDATE contests SET name = $1 WHERE contest_id = $2;''',
            [new_name, contest_id]
        )
        await ctx.send(f"Renamed contest ID `{contest_id}` to **'{new_name}'**.")

    @commands.command(name="deleteContest", description="Delete a contest")
    async def deleteContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        # Now returns ID
        contest_id = await self._pick_contest(ctx, only_active=False)
        if not contest_id: return

        confirm = await ctx.bot.ui.getYesNoChoice(ctx)
        if not confirm: return await ctx.send("Cancelled.")

        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM contests WHERE contest_id = $1;''', [contest_id])
        await self.bot.sql.databaseExecuteDynamic('''UPDATE blueprint_stats SET host_id = 0 WHERE host_id = $1;''',
                                                  [contest_id])
        await ctx.send(f"Contest deleted and entries unlinked.")

    @commands.command(name="setContestRule", description="Configure advanced contest limits")
    async def setContestRule(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        # Now returns ID
        contest_id = await self._pick_contest(ctx)
        if not contest_id: return

        rules_map = {
            "Era (WWI/Inter/Early/Mid/Late)": "era",
            "Min Crew Count": "crewmin",
            "Max Crew Count": "crewmax",
            "Min Hull Height (m)": "hullheightmin",
            "Max Hull Width (m)": "hullwidthmax",
            "Min Torsion Bar Length": "torsionbarlengthmin",
            "Max Armor Thickness (mm)": "armormax",
            "Max Gun Caliber (mm)": "caliberlimit",
            "Min HP/Ton": "minhpt",
            "Max Ground Pressure": "groundpressuremax",
            "Min Belt Width": "beltwidthmin",
            "Allow HVSS?": "allowhvss",
            "Max Entries Per User": "entrylimit",
            "Max Rule Violations": "violationlimit",
            "Enable AI Judge?": "ai_companion",
            "Set AI Persona Prompt": "ai_prompt"
        }

        selection = await ctx.bot.ui.getChoiceFromList(ctx, list(rules_map.keys()), "Select rule to modify:")
        if not selection: return
        db_column = rules_map[selection]

        if db_column == "allowhvss":
            val = await ctx.bot.ui.getYesNoChoice(ctx)

            # --- NEW AI INPUT LOGIC ---
        elif db_column == "ai_companion":
            val = await ctx.bot.ui.getYesNoChoice(ctx)

        elif db_column == "ai_prompt":
            import os
            import json

            # 1. Scan the personas folder and load all valid JSONs
            personas = {}
            if not os.path.exists("personas"):
                os.makedirs("personas")

            for filename in os.listdir("personas"):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join("personas", filename), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if "name" in data:
                                personas[data["name"]] = data
                    except Exception as e:
                        print(f"Failed to load {filename}: {e}")

            # 2. Build the dropdown options
            options = list(personas.keys()) + ["✏️ Custom Prompt"]

            # 3. Ask the host to pick one
            choice = await ctx.bot.ui.getChoiceFromList(ctx, options, "Select an AI Persona for this contest:")
            if not choice: return

            # 4. Process and Serialize
            if choice == "✏️ Custom Prompt":
                val = await textTools.getResponse(ctx, "Enter the custom instructions for the AI Judge:")
            else:
                # Serialize the entire dictionary into a string so the DB can hold it!
                val = json.dumps(personas[choice])
                await ctx.send(f"✅ Persona successfully set to **{choice}**!")
            # --------------------------

        elif db_column == "era":
            val = await ctx.bot.ui.getChoiceFromList(ctx, ["WWI", "Interwar", "Earlywar", "Midwar", "Latewar"],
                                                     "Select Era:")
        elif db_column == "entrylimit" or db_column == "violationlimit":
            val = await textTools.getIntResponse(ctx, f"Enter value for {selection} (0 to disable/reset):")
        else:
            val = await textTools.getFloatResponse(ctx, f"Enter value for {selection} (0 to disable/reset):")

        await self.bot.sql.databaseExecuteDynamic(
            f"UPDATE contests SET {db_column} = $1 WHERE contest_id = $2;",
            [val, contest_id]
        )
        await ctx.send(f"Updated **{selection}** to `{val}`.")

    # ----------------------------------------------------------------------------------
    # SCANNING & SUBMISSIONS
    # ----------------------------------------------------------------------------------

    @commands.command(name="scanChannel", description="Scan channel for blueprint entries")
    async def scanChannel(self, ctx: commands.Context, channel: Union[discord.TextChannel, discord.Thread] = None):
        """Scans history for entries. Supports Threads."""
        if not await self._check_manager(ctx): return

        target_channel = channel or ctx.channel

        # 1. AUTO-DETECT
        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT * FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
            [target_channel.id]
        )

        if contest_data:
            await ctx.send(f"Channel matches contest **'{contest_data['name']}'**. Auto-selecting.")
        else:
            # Fallback to manual ID selection
            contest_id = await self._pick_contest(ctx)
            if not contest_id: return
            contest_data = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM contests WHERE contest_id = $1 AND serverID = $2;''',
                [contest_id, ctx.guild.id]
            )

        status_msg = await ctx.send(f"Scanning **{target_channel.name}** for entries to '{contest_data['name']}'...")

        count_processed = 0
        count_errors = 0
        users_processed = set()

        async for message in target_channel.history(limit=1000):
            if not message.attachments: continue
            for attachment in message.attachments:
                if attachment.filename.endswith(".blueprint"):
                    try:
                        success = await self._process_entry(ctx, message, attachment, None, contest_data, silent=True)
                        if success:
                            count_processed += 1
                            users_processed.add(message.author.display_name)
                        else:
                            count_errors += 1
                    except Exception as e:
                        print(f"Scan Error on {message.jump_url}: {e}")
                        count_errors += 1

        await status_msg.edit(
            content=f"**Scan Complete!**\nEntries Processed: {count_processed}\nErrors/Invalid: {count_errors}\nUnique Users: {len(users_processed)}")

    #@commands.command(name="submitEntry", description="Submit a blueprint to a contest")
    async def submitEntry(self, ctx: commands.Context):
        if not ctx.message.attachments:
            return await ctx.send("You must upload a `.blueprint` file with this command.")

        # --- SEPARATE ATTACHMENTS ---
        blueprint_attachment = None
        image_attachment = None

        for att in ctx.message.attachments:
            if att.filename.endswith(".blueprint"):
                blueprint_attachment = att
            elif att.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                image_attachment = att

        if not blueprint_attachment:
            return await ctx.send("Invalid file type. Please upload a `.blueprint` file.")

        # 1. AUTO-DETECT CONTEST (Using the safe dictionary fetcher)
        contest_records = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
            [ctx.channel.id]
        )

        # Safely extract the first record. If it's an error object or empty list, it safely becomes None.
        contest_data = contest_records[0] if (isinstance(contest_records, list) and len(contest_records) > 0) else None

        # 2. IF NOT IN A CONTEST CHANNEL, OFFER THE DROPDOWN
        if not contest_data:
            await ctx.send("⚠️ This channel isn't directly linked to an active contest. Let's pick one manually:")

            # This triggers the interactive dropdown menu!
            contest_id = await self._pick_contest(ctx)
            if not contest_id:
                return  # User cancelled or no contests exist

            # Fetch the specifically selected contest safely
            contest_records = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM contests WHERE contest_id = $1 AND serverID = $2;''',
                [contest_id, ctx.guild.id]
            )
            contest_data = contest_records[0] if (
                        isinstance(contest_records, list) and len(contest_records) > 0) else None

            if not contest_data:
                return await ctx.send("❌ Error: Could not load the selected contest data.")

        # 3. Process
        await self._process_entry(ctx, ctx.message, blueprint_attachment, image_attachment, contest_data, silent=False)

    # --- INTERNAL ENTRY PROCESSOR ---
    async def _process_entry(self, ctx, message, bp_attachment, img_attachment, contest_data, silent=False):
        try:
            # 1. Protect against invalid channels (contest_data is None)
            if not contest_data:
                if not silent: await ctx.send(
                    "❌ No active contest found here. Make sure you are in the correct submission channel!")
                return False, {}, [], "Unknown"

            contest_id = contest_data.get('contest_id')
            contest_name = contest_data.get('name', 'Unknown')
            entry_limit = contest_data.get('entrylimit', 0)
            violation_limit = contest_data.get('violationlimit', 0)

            # A. Download Blueprint
            async with aiohttp.ClientSession() as session:
                async with session.get(bp_attachment.url) as resp:
                    if resp.status != 200:
                        if not silent: await ctx.send("Failed to download blueprint.")
                        return False, {}, [], "Unknown"
                    file_bytes = await resp.read()

            # Save Locally
            safe_name = "".join([c for c in contest_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            save_dir = os.path.join("blueprints", str(ctx.guild.id), safe_name)
            os.makedirs(save_dir, exist_ok=True)

            local_path = os.path.join(save_dir, bp_attachment.filename)
            with open(local_path, "wb") as f:
                f.write(file_bytes)

            bp_json = json.loads(file_bytes.decode('utf-8'))

            # 2. Protect against missing headers
            game_version = str(bp_json.get("header", {}).get("gameVersion", ""))

            # B. Analyze
            if not silent:
                msg = await ctx.send("Analyzing blueprint...")

            stats = await self.bot.analyzer._parse_blueprint_stats(ctx, bp_json)

            # 3. Protect against analyzer returning None
            if not stats:
                if not silent: await msg.edit(content="**Analysis Failed:** Could not read vehicle data.")
                return False, {}, [], "Unknown"

            if 'error' in stats and stats['error']:
                if not silent: await msg.edit(content=f"**Analysis Failed:** {stats.get('error')}")
                return False, {}, [], "Unknown"

            stats['owner_id'] = message.author.id
            stats['host_id'] = contest_id

            # Use CLEANED name for comparison and storage
            clean_name = bp_attachment.filename.replace('.blueprint', '').replace('_', ' ').strip()
            clean_name = clean_name.replace("@", " ")  # Replaces with a safe, full-width character
            stats['vehicle_name'] = clean_name

            # C. Rules Check & Chaos Enforcement
            warnings = []

            # --- 1. FETCH CHAOS ROLL ---
            user_roll = None
            if contest_data.get('chaos_level') and contest_data['chaos_level'] > 0:
                user_records = await self.bot.sql.databaseFetchdictDynamic(
                    '''SELECT * FROM user_chaos_rolls WHERE user_id = $1 AND contest_id = $2;''',
                    [stats['owner_id'], contest_id]
                )
                # --- CALCULATE BUILD TIME IN MEMORY ---
                if user_records and 'roll_timestamp' in user_records[0] and user_records[0]['roll_timestamp']:
                    import datetime
                    roll_time = user_records[0]['roll_timestamp']
                    delta = datetime.datetime.utcnow() - roll_time.replace(tzinfo=None)

                    days = delta.days
                    hours, remainder = divmod(delta.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)

                    if days > 0:
                        stats['build_time'] = f"{days} days, {hours} hours"
                    elif hours > 0:
                        stats['build_time'] = f"{hours} hours, {minutes} minutes"
                    else:
                        stats['build_time'] = f"{minutes} minutes"

                if not user_records:
                    if not silent:
                        await msg.delete()
                        await ctx.send(
                            "❌ **Wait!** This contest uses Randomized Stats. You must roll your unique requirements first by typing `-rules` in this channel before submitting.")
                    warnings.append(
                        "NO ASSIGNMENT FOUND: User must ask for their vehicle assignment before submitting a blueprint!")
                    return False, stats, warnings, clean_name
                user_roll = user_records[0]

            # --- 2. GATHER ACTUAL STATS ---
            declared_weight = stats.get('tank_weight', 0) / 1000.0
            actual_cal = stats.get('caliber', 0)
            actual_fuel = stats.get('fuel_tank_capacity', 0)

            # Safely count the number of cannons directly from the blueprint structure
            actual_guns = 0
            for bp in bp_json.get("blueprints", []):
                bp_type = str(bp.get("type", "")).lower()
                # THE FIX: Only count the literal barrel ("cannon"), ignore "cannonbreech" or "cannonmount"
                if bp_type == "cannon":
                    actual_guns += 1

            if actual_guns == 0:
                actual_guns = 1  # Failsafe assumption for custom mantlets

            # ==========================================================
            # 3. CHAOS MODE ENFORCEMENT (Overrides Global Limits)
            # ==========================================================
            if user_roll:
                # Weight (+/- 0.5t allowance)
                target_w = user_roll['target_weight']
                if declared_weight < (target_w - 0.5) or declared_weight > (target_w + 0.5):
                    warnings.append(f"Weight: {declared_weight:.2f}t is too far outside the target {(target_w + 0.5):.1f} - {(target_w - 0.5):.1f} ton weight")

                # Gun Count
                if actual_guns != user_roll['gun_count']:
                    warnings.append(
                        f"Guns: {actual_guns} guns were equipped, but {user_roll['gun_count']} are required")

                # Caliber (Allowing a 1.5mm float tolerance for game rounding)
                target_c = user_roll['target_caliber']
                if abs(actual_cal - target_c) > 1.5:
                    warnings.append(f"Caliber: {actual_cal}mm does not match the required {int(target_c)}mm caliber")

                # Fuel
                if actual_fuel < user_roll['min_fuel']:
                    warnings.append(f"Fuel: {int(actual_fuel)}L does not meet the minimum {int(user_roll['min_fuel'])}L capacity")

            # ==========================================================
            # 4. STANDARD GLOBAL ENFORCEMENT
            # ==========================================================

            # Only enforce global weight/caliber if Chaos Mode is NOT active for this user
            if not user_roll:
                if contest_data.get('weightlimit') and contest_data['weightlimit'] > 0:
                    if declared_weight > contest_data['weightlimit']:
                        warnings.append(f"Weight: {declared_weight:.2f}t > Limit {contest_data['weightlimit']}t")

                if contest_data.get('caliber_min') and contest_data['caliber_min'] > 0:
                    if actual_cal < contest_data['caliber_min']:
                        warnings.append(f"Caliber: {actual_cal}mm < Minimum {contest_data['caliber_min']}mm")

                if contest_data.get('caliber_max') and contest_data['caliber_max'] > 0:
                    if actual_cal > contest_data['caliber_max']:
                        warnings.append(f"Caliber: {actual_cal}mm > Limit {contest_data['caliber_max']}mm")

            # Cost and remaining global stats apply to EVERYONE
            if contest_data.get('costlimit') and contest_data['costlimit'] > 0:
                if not silent:
                    user_cost = await textTools.getIntResponse(ctx, "Enter the in-game **Cost** of your vehicle:")
                    stats['base_cost'] = user_cost
                if stats.get('base_cost', 0) > contest_data['costlimit']:
                    warnings.append(f"Cost: ${stats.get('base_cost', 0):,} > Limit ${contest_data['costlimit']:,}")

            prop = stats.get('prop_len', 0)
            if contest_data.get('prop_min') and contest_data['prop_min'] > 0:
                if prop < contest_data['prop_min']: warnings.append(
                    f"Propellant: {prop}mm < Minimum {contest_data['prop_min']}mm")
            if contest_data.get('prop_max') and contest_data['prop_max'] > 0:
                if prop > contest_data['prop_max']: warnings.append(
                    f"Propellant: {prop}mm > Limit {contest_data['prop_max']}mm")

            barrel = stats.get('gun_len', 0)
            if contest_data.get('barrel_limit_m') and contest_data['barrel_limit_m'] > 0:
                if barrel > contest_data['barrel_limit_m']: warnings.append(
                    f"Barrel Length: {barrel:.2f}m > Limit {contest_data['barrel_limit_m']}m")

            # --- Mobility & Dimensions ---
            crew = stats.get('crew_count', 0)
            if contest_data.get('crewmin') and contest_data['crewmin'] > 0:
                if crew < contest_data['crewmin']: warnings.append(f"Crew: {crew} < Minimum {contest_data['crewmin']}")
            if contest_data.get('crewmax') and contest_data['crewmax'] > 0:
                if crew > contest_data['crewmax']: warnings.append(f"Crew: {crew} > Limit {contest_data['crewmax']}")

            hpt = stats.get('hpt', 0)
            if contest_data.get('minhpt') and contest_data['minhpt'] > 0:
                if hpt < contest_data['minhpt']: warnings.append(
                    f"Power-to-Weight: {hpt:.1f} < Minimum {contest_data['minhpt']} hp/t")

            gp = stats.get('ground_pressure', 0)
            if contest_data.get('groundpressuremax') and contest_data['groundpressuremax'] > 0:
                if gp > contest_data['groundpressuremax']: warnings.append(
                    f"Ground Pressure: {gp:.2f} > Limit {contest_data['groundpressuremax']}")

            w_width = stats.get('tank_width', 0)
            if contest_data.get('hullwidthmax') and contest_data['hullwidthmax'] > 0:
                if w_width > contest_data['hullwidthmax']: warnings.append(
                    f"Width: {w_width:.2f}m > Limit {contest_data['hullwidthmax']}m")

            # D. Violation Check
            if not silent: await msg.delete()

            if warnings:
                if len(warnings) > violation_limit:
                    if not silent:
                        fail_embed = discord.Embed(title=f"Submission Rejected: {clean_name}",
                                                   color=discord.Color.red())
                        fail_embed.description = f"Found {len(warnings)} rule violations (Limit: {violation_limit})."
                        fail_embed.add_field(name="Issues", value="\n".join(warnings))
                        await ctx.send(embed=fail_embed)
                    return False, stats, warnings, clean_name
                else:
                    pass

            # E. ENTRY LIMIT & BUMP LOGIC
            user_entries = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT vehicle_id, file_url, vehicle_name FROM blueprint_stats 
                   WHERE owner_id = $1 AND host_id = $2 
                   ORDER BY submission_date ASC;''',
                [stats['owner_id'], contest_id]
            )

            # 4. Safeguard in case DB returns None instead of empty list
            if user_entries is None:
                user_entries = []

            overwrite_target_id = None
            for entry in user_entries:
                db_name = entry.get('vehicle_name', '')
                if db_name == clean_name:
                    overwrite_target_id = entry['vehicle_id']
                    break

            removed_msg = ""
            if overwrite_target_id:
                if overwrite_target_id != stats['vehicle_id']:
                    await self.bot.sql.databaseExecuteDynamic(
                        '''UPDATE blueprint_stats SET host_id = 0 WHERE vehicle_id = $1;''',
                        [overwrite_target_id]
                    )
            else:
                if entry_limit > 0 and len(user_entries) >= entry_limit:
                    oldest_entry = user_entries[0]
                    await self.bot.sql.databaseExecuteDynamic(
                        '''UPDATE blueprint_stats SET host_id = 0 WHERE vehicle_id = $1;''',
                        [oldest_entry['vehicle_id']]
                    )
                    removed_msg = f"\n(Oldest entry '{oldest_entry['vehicle_name']}' was removed to make room)"

            # F. Database Insertion
            stats['file_url'] = bp_attachment.url
            stats['image_url'] = img_attachment.url if img_attachment else None
            stats['submission_date'] = datetime.datetime.now()

            valid_cols = [
                "vehicle_id", "vehicle_name", "vehicle_class", "vehicle_era", "host_id", "faction_id", "owner_id",
                "base_cost", "tank_weight", "tank_length", "tank_width", "tank_height", "tank_total_height",
                "fuel_tank_capacity", "ground_pressure", "horsepower", "hpt", "top_speed", "travel_range",
                "crew_count", "armor_mass",
                "hit_points", "damage_rating", "penetration_rating", "accuracy_rating", "mobility_rating",
                "armor_rating",
                "muzzle_velocity", "gun_len"
            ]

            insert_data = {k: v for k, v in stats.items() if k in valid_cols}
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join([f"${i + 1}" for i in range(len(insert_data))])

            await self.bot.sql.databaseExecuteDynamic(
                f"INSERT INTO blueprint_stats ({columns}) VALUES ({placeholders}) ON CONFLICT (vehicle_id) DO UPDATE SET host_id = EXCLUDED.host_id, vehicle_name = EXCLUDED.vehicle_name, image_url = EXCLUDED.image_url;",
                list(insert_data.values())
            )

            # --- G. Generate GIF & Update DB ---
            gif_file = None
            sent_msg = None
            try:
                if "0.2" in game_version:
                    # 5. Removed the broken await bp_attachment.seek(0)
                    baked_data = await self.bot.analyzer.bakeGeometryV3(ctx, bp_attachment)
                    if baked_data and "meshes" in baked_data and len(baked_data["meshes"]) > 0:
                        mesh = baked_data["meshes"][0]["meshData"]["mesh"]
                    else:
                        mesh = bp_json["meshes"][0]["meshData"]["mesh"]
                else:
                    mesh = bp_json["meshes"][0]["meshData"]["mesh"]

                gif_file = await self.bot.analyzer.generate_blueprint_gif(mesh, stats['vehicle_name'])
            except Exception as e:
                print(f"Contest GIF fail: {e}")

            if not silent:
                txt = f"Accepted!{removed_msg}"
                if overwrite_target_id:
                    txt = f"Accepted! (Overwrote existing entry '{clean_name}')"

                if warnings:
                    txt += f"\n⚠️ **Warnings:** {len(warnings)} (Allowed)"

                # --- SECURITY PATCH: Block Pings ---
                if gif_file:
                    sent_msg = await ctx.send(content=txt, file=gif_file, allowed_mentions=discord.AllowedMentions.none())
                else:
                    sent_msg = await ctx.send(content=txt, allowed_mentions=discord.AllowedMentions.none())

            # UPDATE DB WITH GIF URL
            if sent_msg and gif_file:
                final_gif_url = sent_msg.attachments[0].url
                await self.bot.sql.databaseExecuteDynamic(
                    '''UPDATE blueprint_stats SET gif_url = $1 WHERE vehicle_id = $2;''',
                    [final_gif_url, stats['vehicle_id']]
                )

            # H. Log Channel
            if contest_data.get('log_channel_id') and contest_data['log_channel_id'] != 0:
                log_chan = ctx.guild.get_channel(contest_data['log_channel_id'])
                if log_chan:
                    embed = discord.Embed(title="New Contest Entry", color=discord.Color.blue())
                    embed.add_field(name="Contest", value=contest_name)
                    embed.add_field(name="Author", value=f"<@{stats['owner_id']}>")
                    embed.add_field(name="Vehicle", value=stats['vehicle_name'])
                    embed.add_field(name="Stats",
                                    value=f"{stats.get('tank_weight', 0) / 1000:.1f}t | ${stats.get('base_cost', 0)}")
                    if stats.get('image_url'):
                        embed.add_field(name="Screenshot", value=f"[Link]({stats['image_url']})")
                    if stats and stats.get('build_time'):
                        embed.add_field(name="Build Time", value=stats['build_time'], inline=True)
                    if warnings:
                        embed.color = discord.Color.orange()
                        embed.add_field(name="Permitted Warnings", value="\n".join(warnings), inline=False)

                    if sent_msg and gif_file:
                        embed.set_image(url=sent_msg.attachments[0].url)

                    await log_chan.send(embed=embed)

            return True, stats, warnings, clean_name

        except Exception as e:
            if not silent: await ctx.send(f"Error processing file: {e}")
            print(f"Entry Processing Error: {e}")
            import traceback
            traceback.print_exc()
            return False, stats, warnings, clean_name

    @commands.command(name="resetRoll", description="[Host] Clear a user's randomized stats so they can roll again.")
    async def resetRoll(self, ctx: commands.Context, target: discord.Member = None):
        if not await self._check_manager(ctx): return

        # 1. Ask which contest we are managing
        contest_id = await self._pick_contest(ctx)
        if not contest_id: return

        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT name, chaos_level FROM contests WHERE contest_id = $1 AND serverID = $2;''',
            [contest_id, ctx.guild.id]
        )

        if not contest_data.get('chaos_level') or contest_data['chaos_level'] == 0:
            return await ctx.send("❌ This contest does not have Randomized Stats (Chaos Mode) enabled.")

        # 2. Default to the command author if no one is pinged
        user_to_reset = target or ctx.author

        # 3. Delete their record from the database
        await self.bot.sql.databaseExecuteDynamic(
            '''DELETE FROM user_chaos_rolls WHERE contest_id = $1 AND user_id = $2;''',
            [contest_id, user_to_reset.id]
        )

        await ctx.send(
            f"✅ Successfully cleared the Chaos Roll for **{user_to_reset.display_name}** in '{contest_data['name']}'!\n*(They can now type in the submission channel to trigger the AI to generate a brand new set of requirements).*")

    # ----------------------------------------------------------------------------------
    # VIEWING & DOWNLOAD
    # ----------------------------------------------------------------------------------

    #@commands.command(name="contestRules", description="View the rules and requirements for an active contest.")
    async def contestRules(self, ctx: commands.Context):
        # 1. AUTO-DETECT CONTEST
        contest_records = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
            [ctx.channel.id]
        )

        contest_data = contest_records[0] if (isinstance(contest_records, list) and len(contest_records) > 0) else None

        # 2. IF NOT IN A CONTEST CHANNEL, OFFER THE DROPDOWN
        if not contest_data:
            await ctx.send("Let's pull up the rules for a specific contest:")
            contest_id = await self._pick_contest(ctx, False)
            if not contest_id: return

            contest_records = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM contests WHERE contest_id = $1 AND serverID = $2;''',
                [contest_id, ctx.guild.id]
            )
            if not contest_records:
                return await ctx.send("❌ Error: Could not load the selected contest data.")
            contest_data = contest_records[0]

        # =====================================================================
        # 3. RANDOMIZED STATS INTERCEPT
        # =====================================================================
        if contest_data.get('chaos_level') and contest_data['chaos_level'] > 0:
            contest_id = contest_data['contest_id']

            # Check if this user already has assigned stats
            user_records = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM user_chaos_rolls WHERE user_id = $1 AND contest_id = $2;''',
                [ctx.author.id, contest_id]
            )

            user_roll = user_records[0] if (isinstance(user_records, list) and len(user_records) > 0) else None

            # If they don't have stats yet, generate and save them!
            if not user_roll:
                status_msg = await ctx.send("🎲 **Generating your unique randomized vehicle requirements...**")

                new_stats = self._generate_chaos_roll(contest_data['chaos_level'],
                                                      contest_data.get('chaos_vehicle_types', ''))

                await self.bot.sql.databaseExecuteDynamic(
                    '''INSERT INTO user_chaos_rolls (user_id, contest_id, target_weight, gun_count, vehicle_type, target_caliber, min_fuel)
                       VALUES ($1, $2, $3, $4, $5, $6, $7);''',
                    [ctx.author.id, contest_id, new_stats['target_weight'], new_stats['gun_count'],
                     new_stats['vehicle_type'], new_stats['target_caliber'], new_stats['min_fuel']]
                )

                # Fetch it back to guarantee we have the exact database record
                user_records = await self.bot.sql.databaseFetchdictDynamic(
                    '''SELECT * FROM user_chaos_rolls WHERE user_id = $1 AND contest_id = $2;''',
                    [ctx.author.id, contest_id]
                )
                user_roll = user_records[0]
                await status_msg.delete()

            # --- BUILD THE PERSONALIZED EMBED ---
            embed = discord.Embed(title=f"🎲 Your Official Requirements: {contest_data.get('name')}",
                                  color=discord.Color.purple())
            embed.description = f"This contest uses **Randomized Vehicle Stats** (Level {contest_data['chaos_level']}). These are your permanent, unique design constraints!\n\n*(You must also adhere to any global rules set by the host).*\""

            embed.add_field(name="Classification", value=f"**Vehicle Type:** {user_roll['vehicle_type']}", inline=False)

            primary = f"**Target Weight:** {round(user_roll['target_weight'], 2)}t (±0.5t)\n**Min Fuel Capacity:** {user_roll['min_fuel']} L"
            embed.add_field(name="Chassis Specs", value=primary, inline=True)

            armament = f"**Required Guns:** {user_roll['gun_count']}\n**Required Caliber:** {user_roll['target_caliber']}mm"
            embed.add_field(name="Armament", value=armament, inline=True)

            if contest_data.get('deadline'):
                dl = contest_data['deadline']
                embed.add_field(name="Deadline", value=f"<t:{int(dl.timestamp())}:F>\n(<t:{int(dl.timestamp())}:R>)",
                                inline=False)

            await ctx.send(content=f"<@{ctx.author.id}>", embed=embed)
            # We RETURN here so the standard global embed below doesn't print!

        # =====================================================================
        # 4. STANDARD GLOBAL RULES EMBED (Fallback)
        # =====================================================================
        # THE FIX: Normalize keys to lowercase to bypass database case-sensitivity!
        c_data = {k.lower(): v for k, v in contest_data.items()}

        embed = discord.Embed(title=f"📜 Rules: {c_data.get('name') or 'Unknown'}", color=discord.Color.blue())

        desc_text = c_data.get('description')
        if desc_text and len(str(desc_text)) > 6:
            embed.description = str(desc_text)

        rules_text = c_data.get('ruleslink')
        if rules_text and len(str(rules_text)) > 6:
            embed.description = f"{embed.description or ''}\n\n[📖 Extended Rules Document]({rules_text})"

        general = []
        if c_data.get('era'): general.append(f"**Era:** {c_data['era']}")
        if c_data.get('weightlimit'): general.append(f"**Max Weight:** {c_data['weightlimit']}t")
        if c_data.get('costlimit'): general.append(f"**Max Cost:** {c_data['costlimit']}")

        entry_limit = c_data.get('entrylimit') or 0
        general.append(f"**Max Entries:** {entry_limit if entry_limit > 0 else 'Unlimited'}")
        general.append(f"**Allowed Violations:** {c_data.get('violationlimit') or 0}")
        print(len("\n".join(general)))
        if general: embed.add_field(name="General Constraints", value="\n".join(general), inline=False)

        mobility = []
        c_min = c_data.get('crewmin') or 0
        c_max = c_data.get('crewmax') or 0

        if c_max > 0 or c_min > 0:
            if c_max > 0:
                mobility.append(f"**Crew:** {c_min} to {c_max} members")
            else:
                mobility.append(f"**Crew:** Min {c_min} members")

        if c_data.get('minhpt'): mobility.append(f"**Min Power-to-Weight:** {c_data['minhpt']} hp/t")
        if c_data.get('groundpressuremax'): mobility.append(
            f"**Max Ground Pressure:** {c_data['groundpressuremax']}")
        if c_data.get('hullheightmin'): mobility.append(f"**Min Hull Height:** {c_data['hullheightmin']}m")
        if c_data.get('hullwidthmax'): mobility.append(f"**Max Hull Width:** {c_data['hullwidthmax']}m")
        if c_data.get('torsionbarlengthmin'): mobility.append(
            f"**Min Torsion Bar Length:** {c_data['torsionbarlengthmin']}m")
        if c_data.get('beltwidthmin'): mobility.append(f"**Min Track Belt Width:** {c_data['beltwidthmin']}m")
        if c_data.get('allowhvss') is not None: mobility.append(
            f"**HVSS Allowed:** {'Yes' if c_data['allowhvss'] else 'No'}")

        if mobility: embed.add_field(name="Mobility & Dimensions", value="\n".join(mobility), inline=True)

        combat = []
        if c_data.get('caliberlimit'): combat.append(f"**Max Gun Caliber (Legacy):** {c_data['caliberlimit']}mm")

        cal_min = c_data.get('caliber_min') or 0
        cal_max = c_data.get('caliber_max') or 0

        if cal_max > 0 or cal_min > 0:
            if cal_max > 0 and cal_min > 0:
                combat.append(f"**Caliber:** {cal_min}mm - {cal_max}mm")
            elif cal_min > 0:
                combat.append(f"**Min Caliber:** {cal_min}mm")
            elif cal_max > 0:
                combat.append(f"**Max Caliber:** {cal_max}mm")

        prop_min = c_data.get('prop_min') or 0
        prop_max = c_data.get('prop_max') or 0

        if prop_max > 0 or prop_min > 0:
            if prop_max > 0 and prop_min > 0:
                combat.append(f"**Propellant Length:** {prop_min}mm - {prop_max}mm")
            elif prop_min > 0:
                combat.append(f"**Min Propellant:** {prop_min}mm")
            elif prop_max > 0:
                combat.append(f"**Max Propellant:** {prop_max}mm")

        if c_data.get('barrel_limit_m'): combat.append(f"**Max Barrel Length:** {c_data['barrel_limit_m']}m")
        if c_data.get('armormax'): combat.append(f"**Max Effective Armor:** {c_data['armormax']}mm")

        if combat: embed.add_field(name="Firepower & Armor", value="\n".join(combat), inline=True)

        if c_data.get('deadline'):
            dl = c_data['deadline']
            embed.add_field(name="Deadline", value=f"<t:{int(dl.timestamp())}:F>\n(<t:{int(dl.timestamp())}:R>)",
                            inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="viewAllEntries", description="List ALL entries for a contest")
    async def viewAllEntries(self, ctx: commands.Context):
        # Now returns ID
        contest_id = await self._pick_contest(ctx, only_active=False)
        if not contest_id: return

        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT * FROM contests WHERE contest_id = $1 AND serverID = $2;''',
            [contest_id, ctx.guild.id]
        )

        subs = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT owner_id, tank_weight, base_cost, file_url 
               FROM blueprint_stats 
               WHERE host_id = $1;''',
            [contest_id]
        )

        desc = f"{contest_data['description']}\n\n**Rules:**"
        if contest_data['weightlimit']: desc += f"\nWeight < {contest_data['weightlimit']}t"
        if contest_data['costlimit']: desc += f"\nCost < {contest_data['costlimit']}"
        if contest_data['era']: desc += f"\nEra: {contest_data['era']}"

        embed = discord.Embed(title=f"🏆 {contest_data['name']}", description=desc, color=discord.Color.gold())

        if not subs:
            embed.add_field(name="Entries", value="*No submissions yet.*", inline=False)
        else:
            entry_list = []
            for sub in subs:
                user = ctx.guild.get_member(sub['owner_id'])
                username = user.display_name if user else "Unknown User"
                weight_tons = sub['tank_weight'] / 1000.0 if sub['tank_weight'] else 0
                file_name = sub['file_url'].split('/')[-1] if sub['file_url'] else "File"
                entry_list.append(
                    f"• **{file_name}** by {username} ({weight_tons:.1f}t) [Link]({sub['file_url']})")

            chunk_size = 10
            for i in range(0, len(entry_list), chunk_size):
                chunk = entry_list[i:i + chunk_size]
                embed.add_field(name=f"Submissions ({i + 1}-{i + len(chunk)})", value="\n".join(chunk), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="viewSubmissions", description="List user submissions for a contest")
    async def viewSubmissions(self, ctx: commands.Context, user: discord.Member = None):
        target = user or ctx.author

        # 1. Auto-detect from channel
        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT contest_id, name, entrylimit FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
            [ctx.channel.id]
        )

        if contest_data:
            contest_id = contest_data['contest_id']
        else:
            contest_id = await self._pick_contest(ctx, only_active=False)
            if not contest_id: return
            contest_data = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT contest_id, name, entrylimit FROM contests WHERE contest_id = $1;''',
                [contest_id]
            )

        # 2. Get Entries
        entries = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM blueprint_stats WHERE host_id = $1 AND owner_id = $2 ORDER BY submission_date DESC;''',
            [contest_id, target.id]
        )

        # 3. Build Embed
        embed = discord.Embed(
            title=f"Entries: {contest_data['name']}",
            description=f"User: {target.display_name}\nLimit: {len(entries)}/{contest_data['entrylimit'] if contest_data['entrylimit'] > 0 else 'Unlimited'}",
            color=discord.Color.blue()
        )

        if not entries:
            embed.description += "\n\nNo active entries found."
        else:
            description_lines = []
            for i, entry in enumerate(entries, 1):
                name = entry.get('vehicle_name', 'Unknown')
                weight = f"{entry.get('tank_weight', 0) / 1000:.1f}t"
                cost = f"${entry.get('base_cost', 0):,}"
                links = []
                if entry.get('file_url'): links.append(f"[BP]({entry['file_url']})")
                if entry.get('gif_url'): links.append(f"[3D]({entry['gif_url']})")
                link_str = " | ".join(links)

                description_lines.append(f"**{i}. {name}**\n{weight} | {cost} | {link_str}")

            embed.add_field(name="Submissions", value="\n\n".join(description_lines), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="adminDownloadContest", description="Download CSV stats and ZIP of blueprints")
    async def adminDownloadContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        # Now returns ID
        contest_id = await self._pick_contest(ctx, only_active=False)
        if not contest_id: return

        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT name FROM contests WHERE contest_id = $1 AND serverID = $2;''',
            [contest_id, ctx.guild.id]
        )
        contest_name = contest_data['name']

        await ctx.send("Compiling data...")

        # A. CSV
        try:
            data = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM blueprint_stats WHERE host_id = $1''',
                                                               [contest_id])
            if not data:
                await ctx.send("No database entries found.")
            else:
                df = pd.DataFrame(data)

                if 'vehicle_name' not in df.columns:
                    df['vehicle_name'] = df['file_url'].apply(
                        lambda x: x.split('/')[-1].replace('.blueprint', '').replace('_', ' ') if x else 'Unknown')
                else:
                    mask = df['vehicle_name'].isna()
                    df.loc[mask, 'vehicle_name'] = df.loc[mask, 'file_url'].apply(
                        lambda x: x.split('/')[-1].replace('.blueprint', '').replace('_', ' ') if x else 'Unknown')

                csv_buffer = io.BytesIO()
                df.to_csv(csv_buffer, index=False, encoding='utf-8')
                csv_buffer.seek(0)
                await ctx.send(file=discord.File(csv_buffer, filename=f"{contest_name}_stats.csv"))
        except Exception as e:
            await ctx.send(f"Error generating CSV: `{e}`")

        # B. ZIP (UNFILTERED - All files in folder)
        try:
            safe_name = "".join([c for c in contest_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            folder_path = os.path.join("blueprints", str(ctx.guild.id), safe_name)

            if not os.path.exists(folder_path):
                return await ctx.send("No local blueprint folder found.")

            zip_buffer = io.BytesIO()
            has_files = False

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.endswith(".blueprint"):
                            file_path = os.path.join(root, file)
                            zip_file.write(file_path, arcname=file)
                            has_files = True

            if not has_files:
                return await ctx.send("Folder exists, but contains no .blueprint files.")

            zip_buffer.seek(0)
            if zip_buffer.getbuffer().nbytes > 8 * 1024 * 1024 and ctx.guild.filesize_limit < zip_buffer.getbuffer().nbytes:
                await ctx.send(f"ZIP file is too large for Discord.")
            else:
                await ctx.send(file=discord.File(zip_buffer, filename=f"{safe_name}_files.zip"))

        except Exception as e:
            await ctx.send(f"Error generating ZIP: `{e}`")

    # ----------------------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------------------

    async def _send_roll_dm(self, user: discord.Member, contest_data: dict, roll: dict) -> bool:
        """Attempts to DM the user. If AI is enabled, sends a generated briefing. Otherwise, sends an embed."""
        print("DEBUG DM: Starting _send_roll_dm...")
        try:
            # --- 1. Extract Global Rules cleanly ---
            c_data = {k.lower(): v for k, v in contest_data.items()}
            global_rules = []
            if c_data.get('weightlimit'): global_rules.append(f"Max Weight: {c_data['weightlimit']}t")
            if c_data.get('costlimit'): global_rules.append(f"Max Cost: ${c_data['costlimit']:,}")
            if c_data.get('era'): global_rules.append(f"Era: {c_data['era']}")
            vio_limit = c_data.get('violationlimit', 0)
            global_rules.append(f"Allowed Violations: {'Strict' if vio_limit == 0 else vio_limit}")

            # ==========================================
            # 2. AI-GENERATED DM (If Enabled)
            # ==========================================
            if contest_data.get('ai_companion') and contest_data.get('ai_prompt'):
                print("DEBUG DM: AI Enabled! Building custom prompt...")
                persona_data = {}
                try:
                    persona_data = json.loads(contest_data['ai_prompt'])
                except Exception:
                    persona_data = {"base_persona": contest_data['ai_prompt']}

                base_persona = persona_data.get("base_persona", "You are a sassy mechanical engineer.")

                prompt = f"Context: You are managing the '{contest_data.get('name')}' contest.\n"
                prompt += f"Task: Write a direct, private message (DM) to the competitor '{user.display_name}'. "
                prompt += f"You MUST explicitly give them these exact assigned vehicle requirements in your message:\n"
                prompt += f"- Vehicle Type: {roll['vehicle_type']}\n"
                prompt += f"- Target Weight: {round(roll['target_weight'], 2)}t (±0.5t)\n"
                prompt += f"- Min Fuel Capacity: {roll['min_fuel']} L\n"
                prompt += f"- Required Guns: {roll['gun_count']}\n"
                prompt += f"- Required Caliber: {roll['target_caliber']}mm\n\n"
                prompt += f"Also remind them of these global rules:\n" + "\n".join(
                    [f"- {r}" for r in global_rules]) + "\n\n"

                if c_data.get('ruleslink') and str(c_data.get('ruleslink')).lower() != 'none':
                    prompt += f"Tell them to read the full extended rules here: {c_data['ruleslink']}\n\n"

                    # 1. THE PROMPT FIX: Command the AI to respect the limit
                prompt += "Deliver this strictly in-character, as a private briefing or assignment hand-off. Make it entertaining but clearly state the numbers. STRICT RULE: Your response must be under 1300 characters.\nAI Response:"

                print("DEBUG DM: Requesting generation from AITools...")
                ai_text = await self.bot.AI.get_response(
                    prompt=prompt,
                    instructions=base_persona,
                    mode="gemma",
                    temperature=0.8
                )

                if ai_text and ai_text.strip():
                    print("DEBUG DM: AI responded successfully! Sending to user...")

                    # 2. THE FAILSAFE FIX: Hard truncate the string if the AI disobeyed
                    if len(ai_text) > 1700:
                        ai_text = ai_text[:1697] + "..."

                    await user.send(ai_text)
                    return True
                else:
                    print("DEBUG DM: AI returned blank/None. Falling back to embed...")

            # ==========================================
            # 3. FALLBACK: STANDARD EMBED DM
            # ==========================================
            print("DEBUG DM: Sending static Embed fallback...")
            embed = discord.Embed(title=f"Your Official Requirements: {contest_data.get('name')}",
                                  color=discord.Color.purple())
            embed.description = f"This contest uses **Randomized Vehicle Stats** (Level {contest_data.get('chaos_level', 0)}). These are your unique design constraints!\n\n*(You must also adhere to the global rules listed below).*"
            embed.add_field(name="Classification", value=f"**Vehicle Type:** {roll['vehicle_type']}", inline=False)

            primary = f"**Target Weight:** {round(roll['target_weight'], 2)}t (±0.5t)\n**Min Fuel Capacity:** {roll['min_fuel']} L"
            embed.add_field(name="Chassis Specs", value=primary, inline=True)

            armament = f"**Required Guns:** {roll['gun_count']}\n**Required Caliber:** {roll['target_caliber']}mm"
            embed.add_field(name="Armament", value=armament, inline=True)

            formatted_global_rules = [f"**{r.split(': ')[0]}:** {r.split(': ')[1]}" for r in global_rules if ": " in r]
            if formatted_global_rules:
                embed.add_field(name="Global Rules", value="\n".join(formatted_global_rules), inline=False)

            if c_data.get('ruleslink') and str(c_data.get('ruleslink')).lower() != 'none':
                embed.add_field(name="Extended Rules", value=f"[Read Full Rules Here]({c_data['ruleslink']})",
                                inline=False)

            await user.send(embed=embed)
            print("DEBUG DM: Embed sent successfully!")
            return True

        except discord.Forbidden:
            print("DEBUG DM: Failed! User has DMs disabled.")
            return False
        except Exception as e:
            print(f"DEBUG DM: CRITICAL ERROR IN DM HELPER: {e}")
            return False

    async def _pick_contest(self, ctx: commands.Context, only_active=True):
        query = '''SELECT name, contest_id FROM contests WHERE serverID = $1'''
        if only_active:
            query += ''' AND status = true'''

        contests = await self.bot.sql.databaseFetchdictDynamic(query, [ctx.guild.id])

        if not contests or not isinstance(contests, list) or len(contests) == 0:
            await ctx.send("❌ No active contests were found on this server.")
            return None

        try:
            # Force names to strings just in case someone named their contest a pure number
            contest_names = [str(c['name']) for c in contests]
            selected_name = await ctx.bot.ui.getChoiceFromList(ctx, contest_names, "Select a contest:")

            if not selected_name:
                await ctx.send("❌ Menu timed out or was cancelled.")
                return None

            # THE FIX: Extract the string if Discord wrapped it in a list!
            if isinstance(selected_name, list):
                selected_name = selected_name[0]

            for c in contests:
                if str(c['name']).strip() == str(selected_name).strip():
                    return c['contest_id']

            # Anti-Freeze: If it STILL doesn't match, tell us why!
            await ctx.send(f"❌ Error: Could not match the selection '{selected_name}' to the database.")
            return None

        except Exception as e:
            print(f"Dropdown Menu Error: {e}")
            await ctx.send("An error occurred while generating the contest menu.")
            return None

    def _generate_chaos_roll(self, chaos_level: int, vehicle_types_str: str) -> dict:
        """Generates a unique set of requirements based on vehicle class bounds."""
        c_level = max(1, min(10, chaos_level))

        # ==========================================
        # 1. PRIMARY STATS (Independent)
        # ==========================================

        # Parse the allowed vehicle types. If empty or invalid, allow all of them!
        available_types = list(CHAOS_VEHICLE_TYPES.keys())
        if vehicle_types_str:
            parsed_types = [t.strip() for t in str(vehicle_types_str).split(';') if t.strip() in CHAOS_VEHICLE_TYPES]
            if parsed_types:
                available_types = parsed_types

        vehicle_type = random.choice(available_types)
        limits = CHAOS_VEHICLE_TYPES[vehicle_type]

        # WEIGHT ROLL
        w_min, w_max = limits["weight"]
        w_mid = (w_max + w_min) / 2.0
        # Chaos 1 = 10% of range (near the midpoint), Chaos 10 = 100% of range (could be anything)
        w_range = (w_max - w_min) * (c_level / 10.0)
        target_weight = round(random.uniform(w_mid - w_range / 2, w_mid + w_range / 2), 1)

        # GUN COUNT: 79% (1), 19% (2), 1% (3), 1% (4)
        g_roll = random.randint(1, 100)
        if g_roll <= 79:
            gun_count = 1
        elif g_roll <= 98:
            gun_count = 2
        elif g_roll <= 99:
            gun_count = 3
        else:
            gun_count = 4

        # ==========================================
        # 2. SECONDARY STATS (Dependent on Primary)
        # ==========================================

        # BASE CALIBER CALCULATION: Proportional to weight, inversely proportional to gun count.
        base_caliber = (target_weight * 2.5) / gun_count

        # Apply chaos spread to the mathematical caliber
        cal_variance = base_caliber * (c_level * 0.08)
        raw_caliber = random.uniform(base_caliber - cal_variance, base_caliber + cal_variance)

        # BOUNDARY CHECK: Clamp the raw caliber to the vehicle type's absolute limits
        c_min, c_max = limits["caliber"]
        clamped_caliber = max(c_min, min(c_max, raw_caliber))

        # Snap to nearest common real-world caliber
        common_calibers = [12, 15, 20, 25, 30, 37, 40, 47, 50, 57, 75, 76, 85, 88, 90, 100, 105, 120, 122, 128, 130,
                           152, 155, 183]
        target_caliber = min(common_calibers, key=lambda x: abs(x - clamped_caliber))

        # MINIMUM FUEL: Scales up directly with the weight budget as a balancing penalty
        fuel_variance = c_level * 0.03
        fuel_multiplier = random.uniform(1.0 - fuel_variance, 1.0 + fuel_variance)
        min_fuel = int((target_weight * 15) * fuel_multiplier)

        return {
            "target_weight": target_weight,
            "gun_count": gun_count,
            "vehicle_type": vehicle_type,
            "target_caliber": target_caliber,
            "min_fuel": min_fuel
        }

    async def _check_manager(self, ctx: commands.Context):
        if ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.manage_guild or ctx.author.id == self.bot.ownerid:
            return True
        await ctx.send("You need **Manage Server** permissions.")
        return False

    async def _ask_gemma_judge(self, ai_prompt: str, user_name: str, contest_data: dict, user_message: str = None,
                               tank_data: dict = None):
        """Builds the context dossier and passes it to the central AITools handler."""
        try:
            # 1. Safely decode the database string
            persona_data = {}
            try:
                persona_data = json.loads(ai_prompt) if ai_prompt else {}
            except Exception:
                persona_data = {"base_persona": ai_prompt}

            # 2. Extract fields
            base_persona = persona_data.get("base_persona", "You are a sassy mechanical engineer judging tank designs.")
            length_target = persona_data.get("length_target", "Keep it to 1-3 sentences.")

            # 3. Build the core context prompt
            prompt = f"Context: You are collecting tank design blueprints as part of a critical '{contest_data.get('name')}'."
            prompt += f"Max Weight: {contest_data.get('weightlimit')}t. Max Cost: {contest_data.get('costlimit')}.\n\n"

            # Scenario A: Chatting
            if user_message:
                chat_style = persona_data.get("chat_style", "Answer their question briefly and in-character.")
                prompt += f"User ({user_name}) asks: \"{user_message}\"\n"
                prompt += f"Task: {chat_style} {length_target} Do not use markdown formatting.\nAI Response:"

            # Scenario B: Tank Inspection
            elif tank_data:
                is_rejected = tank_data['rejected']
                num_warnings = len(tank_data['warnings']) if tank_data['warnings'] else 0

                reaction_style = persona_data.get("rejection_style") if is_rejected else persona_data.get(
                    "acceptance_style")
                if not reaction_style:
                    reaction_style = "Provide a highly opinionated, in-character response declaring it accepted or rejected."

                prompt += f"You are currently processing their '{tank_data['name']}' submission.\n"

                if is_rejected:
                    prompt += f"Final Status: REJECTED ({num_warnings} rule violations).\n"
                    prompt += f"Task: {reaction_style} {length_target} You MUST include the exact text `[warnings]` somewhere in your response where the list of broken rules should go. Do not explain the rules yourself, just use the tag.\nAI Response:"
                else:
                    prompt += f"Final Status: ACCEPTED\n"
                    # --- BUG FIX: Tell the AI the tag is forbidden on success ---
                    prompt += f"Task: {reaction_style} {length_target} DO NOT use the [warnings] tag because there are no rule violations!\nAI Response:"

            # 4. Hand off to your existing AITools!
            # Using mode="gemma" to trigger your specific gemma-3-27b-it configuration

            response_text = await self.bot.AI.get_response(
                prompt=prompt,
                instructions=base_persona,
                mode="gemma",
                temperature=0.8,
                attachments=None
            )

            return response_text if response_text else "*(The inspector is currently unavailable. Try again later.)*"

        except Exception as e:
            print(f"Contest AI Builder Error: {e}")
            return "*(The inspector is currently on a smoke break. Try again later.)*"

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(contestFunctions(bot))