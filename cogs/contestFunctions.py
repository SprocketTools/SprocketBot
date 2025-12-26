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
import io
import pandas as pd
from typing import Union
from cogs.textTools import textTools


class contestFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        # NOTE: self.bot.analyzer is expected to be loaded in main.py

    # ----------------------------------------------------------------------------------
    # SETUP: Database Tables
    # ----------------------------------------------------------------------------------
    @commands.command(name="setupContestTables", description="[Owner] Create SQL tables for contests.")
    async def setupContestTables(self, ctx: commands.Context):
        if ctx.author.id != self.bot.ownerid:
            return await self.bot.error.sendError(ctx)

        # 1. Ensure the shared Blueprint Stats table exists
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS blueprint_stats;''')
        await self.bot.sql.databaseExecute('''
            CREATE TABLE IF NOT EXISTS blueprint_stats (
                vehicle_id BIGINT PRIMARY KEY,
                vehicle_name VARCHAR,
                vehicle_class VARCHAR(100),
                vehicle_era VARCHAR(20),
                host_id BIGINT,
                faction_id BIGINT,
                owner_id BIGINT,
                base_cost BIGINT,
                tank_weight REAL,
                tank_length REAL,
                tank_width REAL,
                tank_height REAL,
                tank_total_height REAL,
                fuel_tank_capacity REAL,
                ground_pressure REAL,
                horsepower INT,
                hpt REAL,
                top_speed INT,
                travel_range INT,
                crew_count INT,
                cannon_stats TEXT,
                armor_mass REAL,
                upper_frontal_angle REAL,
                lower_frontal_angle REAL,
                health INT, 
                attack INT,
                defense INT,
                breakthrough INT,
                piercing INT,
                armor INT,
                cohesion INT
            );
        ''')

        # 2. Modify blueprint_stats columns (Migrations)
        try:
            await self.bot.sql.databaseExecute('''ALTER TABLE blueprint_stats DROP COLUMN IF EXISTS contest_name;''')
            await self.bot.sql.databaseExecute(
                '''ALTER TABLE blueprint_stats ADD COLUMN IF NOT EXISTS file_url VARCHAR;''')
            await self.bot.sql.databaseExecute(
                '''ALTER TABLE blueprint_stats ADD COLUMN IF NOT EXISTS submission_date TIMESTAMP;''')
            await self.bot.sql.databaseExecute(
                '''ALTER TABLE blueprint_stats ADD COLUMN IF NOT EXISTS vehicle_name VARCHAR;''')
        except Exception as e:
            print(f"Stats Table alteration warning: {e}")

        # 3. Main Contests Table
        await self.bot.sql.databaseExecute('''
            CREATE TABLE IF NOT EXISTS contests (
                contest_id BIGINT,
                name VARCHAR PRIMARY KEY,
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
                entryLimit INT DEFAULT 0
            );
        ''')

        # --- DATABASE MIGRATION PATCH ---
        try:
            await self.bot.sql.databaseExecute('''ALTER TABLE contests ADD COLUMN IF NOT EXISTS contest_id BIGINT;''')
            await self.bot.sql.databaseExecute(
                '''ALTER TABLE contests ADD COLUMN IF NOT EXISTS entryLimit INT DEFAULT 0;''')
        except:
            pass

        await self.bot.sql.databaseExecute('''
            UPDATE contests 
            SET contest_id = CAST(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) + (RANDOM() * 100000) AS BIGINT) 
            WHERE contest_id IS NULL;
        ''')

        columns_to_add = [
            ("status", "BOOLEAN"), ("deadline", "TIMESTAMP"), ("rulesLink", "VARCHAR"),
            ("description", "VARCHAR"), ("costlimit", "BIGINT"), ("weightLimit", "REAL"),
            ("era", "VARCHAR"), ("crewMin", "INT"), ("crewMax", "INT"),
            ("hullHeightMin", "REAL"), ("hullWidthMax", "REAL"), ("torsionBarLengthMin", "REAL"),
            ("allowHVSS", "BOOLEAN"), ("beltWidthMin", "REAL"), ("groundPressureMax", "REAL"),
            ("minHPT", "REAL"), ("caliberLimit", "REAL"), ("armorMax", "REAL"),
            ("submission_channel_id", "BIGINT"), ("log_channel_id", "BIGINT"),
            ("entryLimit", "INT")
        ]

        print("--- Running Contest DB Migrations ---")
        for col_name, col_type in columns_to_add:
            try:
                await self.bot.sql.databaseExecute(
                    f'''ALTER TABLE contests ADD COLUMN IF NOT EXISTS {col_name} {col_type};''')
            except Exception as e:
                pass

        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS contestcategories;''')
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS contest_entries;''')
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS contestsubmissions;''')

        await ctx.send("## Done!\nContest system migrated and ready.")

    # ----------------------------------------------------------------------------------
    # MANAGEMENT: Create and Edit Contests
    # ----------------------------------------------------------------------------------
    @commands.command(name="createContest", description="Start a new building contest")
    async def createContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        # 1. Basic Info
        name = await textTools.getCappedResponse(ctx, "What is the name of this contest?", 64)

        exists = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT name FROM contests WHERE name = $1 AND serverID = $2;''',
            [name, ctx.guild.id]
        )
        if exists:
            return await ctx.send("❌ A contest with that name already exists in this server.")

        contest_id = random.randint(10000000, 99999999)
        desc = await textTools.getResponse(ctx, "Provide a brief description.")
        rules = await textTools.getResponse(ctx, "Link to rules (or type 'None').")

        # 2. Limits
        weight_lim = await textTools.getFloatResponse(ctx, "Max Weight (tons) (0 for none):")
        cost_lim = await textTools.getIntResponse(ctx, "Max Cost (0 for none):")

        # 3. Channels (Manual Handling to support Threads)
        submission_channel_id = 0
        await ctx.send("Mention the **Submission Channel** or **Thread** (where users upload files):")

        while True:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                return await ctx.send("❌ Timed out.")

            if msg.content.lower() == "cancel": return await ctx.send("❌ Cancelled.")

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
                overlap = await self.bot.sql.databaseFetchrowDynamic(
                    '''SELECT name FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
                    [submission_channel_id]
                )
                if overlap:
                    await ctx.send(f"❌ Channel occupied by **'{overlap['name']}'**. Choose another.")
                    continue
                break
            else:
                await ctx.send("❌ Invalid Channel/Thread. Try again.")

        log_channel_id = 0
        raw_log = await textTools.getResponse(ctx, "Mention the **Log Channel** (or 'here'):")
        if "here" in raw_log.lower():
            log_channel_id = ctx.channel.id
        else:
            try:
                log_id_str = ''.join(filter(str.isdigit, raw_log))
                log_channel_id = int(log_id_str) if log_id_str else ctx.channel.id
            except:
                log_channel_id = ctx.channel.id

        # 4. Date Picker
        deadline = await ctx.bot.ui.getDate(ctx, "📅 **Select the deadline:**")
        if not deadline:
            return await ctx.send("❌ Cancelled.")

        # 5. Insert
        # Default entryLimit to 0 (unlimited)
        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO contests (contest_id, name, serverID, ownerID, description, rulesLink, status, deadline, weightLimit, costlimit, submission_channel_id, log_channel_id, entryLimit) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 0);''',
            [contest_id, name, ctx.guild.id, ctx.author.id, desc, rules, True, deadline, weight_lim, cost_lim,
             submission_channel_id, log_channel_id]
        )

        formatted_date = deadline.strftime("%B %d, %Y")
        await ctx.send(
            f"## Contest Created!\n**ID:** `{contest_id}`\n**Name:** {name}\n**Deadline:** {formatted_date}\n**Submit Here:** <#{submission_channel_id}>")

    @commands.command(name="manageContest", description="Dashboard to edit all contest settings")
    async def manageContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        # 1. Select Contest (Get ID)
        contest_id = await self._pick_contest(ctx, only_active=False)
        if not contest_id: return

        # Main Loop
        while True:
            data = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM contests WHERE contest_id = $1 AND serverID = $2;''',
                [contest_id, ctx.guild.id]
            )
            if not data:
                await ctx.send("❌ Contest not found.")
                break

            # Build Dashboard Embed
            status_emoji = "🟢 Open" if data['status'] else "🔴 Closed"
            dl_str = data['deadline'].strftime("%Y-%m-%d") if data['deadline'] else "None"
            entry_limit_str = str(data['entrylimit']) if data.get('entrylimit', 0) > 0 else "Unlimited"

            embed = discord.Embed(title=f"⚙️ Managing: {data['name']}", color=discord.Color.blue())

            gen_info = f"**Desc:** {data['description'][:50]}...\n**Rules:** {data['ruleslink']}\n**Status:** {status_emoji}\n**Deadline:** {dl_str}"
            embed.add_field(name="General Info", value=gen_info, inline=False)

            limits = f"**Weight:** {data['weightlimit']}t | **Cost:** {data['costlimit']}\n**Era:** {data['era']}\n**Crew:** {data['crewmin']}-{data['crewmax']}\n**Max Entries/User:** {entry_limit_str}"
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
                        overlap = await self.bot.sql.databaseFetchrowDynamic(
                            "SELECT name FROM contests WHERE submission_channel_id=$1 AND status=TRUE AND contest_id!=$2",
                            [chan.id, data['contest_id']])
                        if overlap:
                            await ctx.send(f"❌ Occupied by {overlap['name']}")
                        else:
                            await self.bot.sql.databaseExecuteDynamic(
                                "UPDATE contests SET submission_channel_id=$1 WHERE contest_id=$2",
                                [chan.id, data['contest_id']])
                elif sub == "Log Channel":
                    chan = await textTools.getChannelResponse(ctx, "Mention new log channel:")
                    if chan: await self.bot.sql.databaseExecuteDynamic(
                        "UPDATE contests SET log_channel_id=$1 WHERE contest_id=$2", [chan.id, data['contest_id']])

            elif selection == "Weight/Cost/Limit":
                sub = await ctx.bot.ui.getButtonChoice(ctx, ["Max Weight", "Max Cost", "Entry Limit", "Back"])
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
                if sub == "Allow HVSS":
                    val = await ctx.bot.ui.getYesNoChoice(ctx, "Allow HVSS?")
                    await self.bot.sql.databaseExecuteDynamic("UPDATE contests SET allowhvss=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])
                elif sub in cmap:
                    val = await textTools.getFloatResponse(ctx, f"Enter {sub}:")
                    await self.bot.sql.databaseExecuteDynamic(f"UPDATE contests SET {cmap[sub]}=$1 WHERE contest_id=$2",
                                                              [val, data['contest_id']])

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
        await ctx.send("✅ Exited Dashboard.")

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
        await ctx.send(f"✅ Renamed contest ID `{contest_id}` to **'{new_name}'**.")

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
            "Max Entries Per User": "entrylimit"
        }

        selection = await ctx.bot.ui.getChoiceFromList(ctx, list(rules_map.keys()), "Select rule to modify:")
        if not selection: return
        db_column = rules_map[selection]

        if db_column == "allowhvss":
            val = await ctx.bot.ui.getYesNoChoice(ctx)
        elif db_column == "era":
            val = await ctx.bot.ui.getChoiceFromList(ctx, ["WWI", "Interwar", "Earlywar", "Midwar", "Latewar"],
                                                     "Select Era:")
        elif db_column == "entrylimit":
            val = await textTools.getIntResponse(ctx, "Enter Max Entries per User (0 for Unlimited):")
        else:
            val = await textTools.getFloatResponse(ctx, f"Enter value for {selection} (0 to disable/reset):")

        await self.bot.sql.databaseExecuteDynamic(
            f"UPDATE contests SET {db_column} = $1 WHERE contest_id = $2;",
            [val, contest_id]
        )
        await ctx.send(f"✅ Updated **{selection}** to `{val}`.")

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
            await ctx.send(f"📂 Channel matches contest **'{contest_data['name']}'**. Auto-selecting.")
        else:
            # Fallback to manual ID selection
            contest_id = await self._pick_contest(ctx)
            if not contest_id: return
            contest_data = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM contests WHERE contest_id = $1 AND serverID = $2;''',
                [contest_id, ctx.guild.id]
            )

        status_msg = await ctx.send(f"🔎 Scanning **{target_channel.name}** for entries to '{contest_data['name']}'...")

        count_processed = 0
        count_errors = 0
        users_processed = set()

        async for message in target_channel.history(limit=1000):
            if not message.attachments: continue
            for attachment in message.attachments:
                if attachment.filename.endswith(".blueprint"):
                    try:
                        success = await self._process_entry(ctx, message, attachment, contest_data, silent=True)
                        if success:
                            count_processed += 1
                            users_processed.add(message.author.display_name)
                        else:
                            count_errors += 1
                    except Exception as e:
                        print(f"Scan Error on {message.jump_url}: {e}")
                        count_errors += 1

        await status_msg.edit(
            content=f"✅ **Scan Complete!**\nEntries Processed: {count_processed}\nErrors/Invalid: {count_errors}\nUnique Users: {len(users_processed)}")

    @commands.command(name="submitEntry", description="Submit a blueprint to a contest")
    async def submitEntry(self, ctx: commands.Context):
        if not ctx.message.attachments:
            return await ctx.send("❌ You must upload a `.blueprint` file with this command.")

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(".blueprint"):
            return await ctx.send("❌ Invalid file type. Please upload a `.blueprint` file.")

        # 1. AUTO-DETECT
        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT * FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
            [ctx.channel.id]
        )

        if not contest_data:
            contest_id = await self._pick_contest(ctx)
            if not contest_id: return
            contest_data = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM contests WHERE contest_id = $1 AND serverID = $2;''',
                [contest_id, ctx.guild.id]
            )

        # 2. Process
        await self._process_entry(ctx, ctx.message, attachment, contest_data, silent=False)

    # --- INTERNAL ENTRY PROCESSOR ---
    async def _process_entry(self, ctx, message, attachment, contest_data, silent=False):
        try:
            contest_id = contest_data['contest_id']
            contest_name = contest_data['name']
            entry_limit = contest_data.get('entrylimit', 0)

            # A. Download & Save Locally
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        if not silent: await ctx.send("❌ Failed to download file.")
                        return False
                    file_bytes = await resp.read()

            safe_name = "".join([c for c in contest_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            save_dir = os.path.join("blueprints", str(ctx.guild.id), safe_name)
            os.makedirs(save_dir, exist_ok=True)

            local_path = os.path.join(save_dir, attachment.filename)
            with open(local_path, "wb") as f:
                f.write(file_bytes)

            bp_json = json.loads(file_bytes.decode('utf-8'))

            # B. Analyze
            if not silent:
                msg = await ctx.send("⚙️ Analyzing blueprint...")

            stats = await self.bot.analyzer._parse_blueprint_stats(ctx, bp_json)

            if 'error' in stats and stats['error']:
                if not silent: await msg.edit(content=f"❌ **Analysis Failed:** {stats.get('error')}")
                return False

            stats['owner_id'] = message.author.id
            stats['host_id'] = contest_id

            # --- NAME HANDLING ---
            # 1. Try to get name from filename
            raw_name = attachment.filename.replace('.blueprint', '').replace('_', ' ')
            stats['vehicle_name'] = raw_name

            # C. Rules Check
            warnings = []
            declared_weight = stats.get('tank_weight', 0) / 1000.0
            if contest_data['weightlimit'] and contest_data['weightlimit'] > 0:
                if declared_weight > contest_data['weightlimit']:
                    warnings.append(f"⚠️ Weight: {declared_weight:.2f}t > Limit {contest_data['weightlimit']}t")

            crew_count = stats.get('crew_count', 0)
            if contest_data['crewmin'] and crew_count < contest_data['crewmin']:
                warnings.append(f"⚠️ Crew: {crew_count} < Min {contest_data['crewmin']}")
            if contest_data['crewmax'] and contest_data['crewmax'] > 0 and crew_count > contest_data['crewmax']:
                warnings.append(f"⚠️ Crew: {crew_count} > Max {contest_data['crewmax']}")

            if contest_data['era'] and contest_data['era'] != "None":
                vehicle_era = stats.get('vehicle_era', "Latewar")
                if vehicle_era != contest_data['era']:
                    warnings.append(f"⚠️ Era: {vehicle_era} (Req: {contest_data['era']})")

            if contest_data['costlimit'] and contest_data['costlimit'] > 0:
                if not silent:
                    user_cost = await textTools.getIntResponse(ctx, "Enter the in-game **Cost** of your vehicle:")
                    stats['base_cost'] = user_cost
                if stats['base_cost'] > contest_data['costlimit']:
                    warnings.append(f"⚠️ Cost: {stats['base_cost']} > Limit {contest_data['costlimit']}")

            # D. Final Decision (Warnings)
            if warnings and not silent:
                await msg.delete()
                status_embed = discord.Embed(title=f"⚠️ Rules Issue: {attachment.filename}",
                                             color=discord.Color.orange())
                status_embed.add_field(name="Violations", value="\n".join(warnings))
                status_embed.set_footer(text="Submit anyway?")
                await ctx.send(embed=status_embed)
                if not await ctx.bot.ui.getYesNoChoice(ctx):
                    return False
            elif not silent:
                await msg.delete()

            # E. ENTRY LIMIT & OVERWRITE CHECK
            # Fetch user's existing active entries for this contest
            user_entries = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT vehicle_id, file_url FROM blueprint_stats WHERE owner_id = $1 AND host_id = $2;''',
                [stats['owner_id'], contest_id]
            )

            # Check if this filename already exists among them (Overwrite)
            overwrite_target_id = None
            new_filename = attachment.filename

            for entry in user_entries:
                if entry['file_url'] and entry['file_url'].endswith(f"/{new_filename}"):
                    overwrite_target_id = entry['vehicle_id']
                    break

            # If overwrite match found
            if overwrite_target_id:
                if overwrite_target_id != stats['vehicle_id']:
                    # New ID but same name -> Unlink old ID
                    await self.bot.sql.databaseExecuteDynamic(
                        '''UPDATE blueprint_stats SET host_id = 0 WHERE vehicle_id = $1;''',
                        [overwrite_target_id]
                    )
            # If no overwrite match (New Entry)
            else:
                if entry_limit > 0 and len(user_entries) >= entry_limit:
                    if not silent:
                        await ctx.send(
                            f"❌ **Limit Reached:** You already have {len(user_entries)}/{entry_limit} entries.\n*Submit a file with the same name to overwrite an existing entry.*")
                    return False

            # F. Database Insertion
            stats['file_url'] = attachment.url
            stats['submission_date'] = datetime.datetime.now()

            valid_cols = [
                "vehicle_id", "vehicle_name", "vehicle_class", "vehicle_era", "host_id", "faction_id", "owner_id",
                "base_cost",
                "tank_weight", "tank_length", "tank_width", "tank_height", "tank_total_height",
                "fuel_tank_capacity", "ground_pressure", "horsepower", "hpt", "top_speed", "travel_range",
                "crew_count", "cannon_stats", "armor_mass", "upper_frontal_angle", "lower_frontal_angle",
                "health", "attack", "defense", "breakthrough", "piercing", "armor", "cohesion",
                "file_url", "submission_date"
            ]

            insert_data = {k: v for k, v in stats.items() if k in valid_cols}
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join([f"${i + 1}" for i in range(len(insert_data))])
            values = list(insert_data.values())

            await self.bot.sql.databaseExecuteDynamic(
                f"INSERT INTO blueprint_stats ({columns}) VALUES ({placeholders}) ON CONFLICT (vehicle_id) DO UPDATE SET host_id = EXCLUDED.host_id, vehicle_name = EXCLUDED.vehicle_name;",
                values
            )

            if not silent:
                if overwrite_target_id:
                    await ctx.send(f"✅ **Updated!** Existing entry '{new_filename}' has been overwritten.")
                else:
                    await ctx.send(f"✅ **Submitted!** Entry recorded.")

            # G. Log
            if contest_data.get('log_channel_id') and contest_data['log_channel_id'] != 0:
                log_chan = ctx.guild.get_channel(contest_data['log_channel_id'])
                if log_chan:
                    embed = discord.Embed(title="📋 New Contest Entry", color=discord.Color.blue())
                    embed.add_field(name="Contest", value=contest_name)
                    embed.add_field(name="Author", value=f"<@{stats['owner_id']}>")
                    embed.add_field(name="Vehicle", value=stats['vehicle_name'])
                    embed.add_field(name="Stats",
                                    value=f"{stats.get('tank_weight', 0) / 1000:.1f}t | ${stats.get('base_cost', 0)}")
                    if warnings:
                        embed.color = discord.Color.orange()
                        embed.add_field(name="Warnings", value="\n".join(warnings), inline=False)
                    await log_chan.send(embed=embed)

            return True

        except Exception as e:
            if not silent:
                await ctx.send(f"❌ Error processing file: {e}")
            print(f"Entry Processing Error: {e}")
            return False

    # ----------------------------------------------------------------------------------
    # VIEWING & DOWNLOAD
    # ----------------------------------------------------------------------------------
    @commands.command(name="viewSubmissions", description="List entries for a contest")
    async def viewSubmissions(self, ctx: commands.Context):
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

        await ctx.send("📦 Compiling data...")

        # A. CSV
        try:
            data = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM blueprint_stats WHERE host_id = $1''',
                                                               [contest_id])
            if not data:
                await ctx.send("⚠️ No database entries found.")
            else:
                df = pd.DataFrame(data)

                # --- BACKFILL NAMES IF MISSING ---
                # This ensures old entries without the column still have names in the CSV
                if 'vehicle_name' not in df.columns:
                    df['vehicle_name'] = df['file_url'].apply(
                        lambda x: x.split('/')[-1].replace('.blueprint', '').replace('_', ' ') if x else 'Unknown')
                else:
                    # Fill specifically where it might be NaN/None
                    mask = df['vehicle_name'].isna()
                    df.loc[mask, 'vehicle_name'] = df.loc[mask, 'file_url'].apply(
                        lambda x: x.split('/')[-1].replace('.blueprint', '').replace('_', ' ') if x else 'Unknown')

                csv_buffer = io.BytesIO()
                df.to_csv(csv_buffer, index=False, encoding='utf-8')
                csv_buffer.seek(0)
                await ctx.send(file=discord.File(csv_buffer, filename=f"{contest_name}_stats.csv"))
        except Exception as e:
            await ctx.send(f"❌ Error generating CSV: `{e}`")

        # B. ZIP (UNFILTERED - All files in folder)
        try:
            safe_name = "".join([c for c in contest_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            folder_path = os.path.join("blueprints", str(ctx.guild.id), safe_name)

            if not os.path.exists(folder_path):
                return await ctx.send("⚠️ No local blueprint folder found.")

            zip_buffer = io.BytesIO()
            has_files = False

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.endswith(".blueprint"):
                            file_path = os.path.join(root, file)
                            # Add file to zip (arcname ensures it doesn't store the full C:/ path)
                            zip_file.write(file_path, arcname=file)
                            has_files = True

            if not has_files:
                return await ctx.send("⚠️ Folder exists, but contains no .blueprint files.")

            zip_buffer.seek(0)
            if zip_buffer.getbuffer().nbytes > 8 * 1024 * 1024 and ctx.guild.filesize_limit < zip_buffer.getbuffer().nbytes:
                await ctx.send(f"❌ ZIP file is too large for Discord.")
            else:
                await ctx.send(file=discord.File(zip_buffer, filename=f"{safe_name}_files.zip"))

        except Exception as e:
            await ctx.send(f"❌ Error generating ZIP: `{e}`")

    # ----------------------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------------------
    async def _pick_contest(self, ctx: commands.Context, only_active=True):
        query = '''SELECT name, contest_id FROM contests WHERE serverID = $1'''
        if only_active:
            query += ''' AND status = true'''

        contests = await self.bot.sql.databaseFetchdictDynamic(query, [ctx.guild.id])

        if not contests:
            await ctx.send("No contests found.")
            return None

        contest_names = [c['name'] for c in contests]
        selected_name = await ctx.bot.ui.getChoiceFromList(ctx, contest_names, "Select a contest:")

        if not selected_name: return None

        # Find the ID associated with the selected name
        for c in contests:
            if c['name'] == selected_name:
                return c['contest_id']
        return None

    async def _check_manager(self, ctx: commands.Context):
        if ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.manage_guild or ctx.author.id == self.bot.ownerid:
            return True
        await ctx.send("❌ You need **Manage Server** permissions.")
        return False


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(contestFunctions(bot))