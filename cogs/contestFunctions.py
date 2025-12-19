import io
import zipfile
import io
import pandas as pd
import os
import discord
from discord.ext import commands
import json
import datetime
import aiohttp
import asyncio
import os
import random
from cogs.textTools import textTools


class contestFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # NOTE: self.bot.analyzer is expected to be loaded in main.py

    # ----------------------------------------------------------------------------------
    # SETUP: Database Tables
    # ----------------------------------------------------------------------------------
    @commands.command(name="setupContestTables", description="[Owner] Create SQL tables for contests.")
    async def setupContestTables(self, ctx: commands.Context):
        if ctx.author.id != self.bot.ownerid:
            return await self.bot.error.sendError(ctx)

        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS contests;''')
        # 1. Ensure the shared Blueprint Stats table exists
        await self.bot.sql.databaseExecute('''
            CREATE TABLE IF NOT EXISTS blueprint_stats (
                vehicle_id BIGINT PRIMARY KEY,
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

        # 2. Modify blueprint_stats to cleanup columns
        try:
            # We DROP contest_name because we are switching to host_id
            await self.bot.sql.databaseExecute('''ALTER TABLE blueprint_stats DROP COLUMN IF EXISTS contest_name;''')
            await self.bot.sql.databaseExecute(
                '''ALTER TABLE blueprint_stats ADD COLUMN IF NOT EXISTS file_url VARCHAR;''')
            await self.bot.sql.databaseExecute(
                '''ALTER TABLE blueprint_stats ADD COLUMN IF NOT EXISTS submission_date TIMESTAMP;''')
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
                log_channel_id BIGINT
            );
        ''')

        # --- DATABASE MIGRATION PATCH ---
        # 1. Add ID column if missing
        try:
            await self.bot.sql.databaseExecute('''ALTER TABLE contests ADD COLUMN IF NOT EXISTS contest_id BIGINT;''')
        except:
            pass

        # 2. Backfill IDs for old contests (Generate a deterministic-ish ID based on time + random if NULL)
        await self.bot.sql.databaseExecute('''
            UPDATE contests 
            SET contest_id = CAST(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) + (RANDOM() * 100000) AS BIGINT) 
            WHERE contest_id IS NULL;
        ''')

        # 3. Add other columns
        columns_to_add = [
            ("status", "BOOLEAN"), ("deadline", "TIMESTAMP"), ("rulesLink", "VARCHAR"),
            ("description", "VARCHAR"), ("costlimit", "BIGINT"), ("weightLimit", "REAL"),
            ("era", "VARCHAR"), ("crewMin", "INT"), ("crewMax", "INT"),
            ("hullHeightMin", "REAL"), ("hullWidthMax", "REAL"), ("torsionBarLengthMin", "REAL"),
            ("allowHVSS", "BOOLEAN"), ("beltWidthMin", "REAL"), ("groundPressureMax", "REAL"),
            ("minHPT", "REAL"), ("caliberLimit", "REAL"), ("armorMax", "REAL"),
            ("submission_channel_id", "BIGINT"), ("log_channel_id", "BIGINT")
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

        await ctx.send("## Done!\nContest system migrated. `contest_name` dropped; using `host_id` linkage.")

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

        # Generate Unique ID
        contest_id = random.randint(10000000, 99999999)

        desc = await textTools.getResponse(ctx, "Provide a brief description.")
        rules = await textTools.getResponse(ctx, "Link to rules (or type 'None').")

        # 2. Limits
        weight_lim = await textTools.getFloatResponse(ctx, "Max Weight (tons) (0 for none):")
        cost_lim = await textTools.getIntResponse(ctx, "Max Cost (0 for none):")

        # 3. Channels
        submission_channel_id = 0
        while True:
            raw_channel = await textTools.getResponse(ctx,
                                                      "Mention the **Submission Channel** (where users upload files):")
            try:
                sub_id_str = ''.join(filter(str.isdigit, raw_channel))
                if not sub_id_str: raise ValueError
                submission_channel_id = int(sub_id_str)

                if not ctx.guild.get_channel(submission_channel_id):
                    await ctx.send("❌ Channel not found.")
                    continue

                overlap = await self.bot.sql.databaseFetchrowDynamic(
                    '''SELECT name FROM contests WHERE submission_channel_id = $1 AND status = TRUE;''',
                    [submission_channel_id]
                )
                if overlap:
                    await ctx.send(f"❌ Channel occupied by **'{overlap['name']}'**. Choose another.")
                    continue
                break
            except ValueError:
                await ctx.send("❌ Invalid channel.")

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
        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO contests (contest_id, name, serverID, ownerID, description, rulesLink, status, deadline, weightLimit, costlimit, submission_channel_id, log_channel_id) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);''',
            [contest_id, name, ctx.guild.id, ctx.author.id, desc, rules, True, deadline, weight_lim, cost_lim,
             submission_channel_id, log_channel_id]
        )

        formatted_date = deadline.strftime("%B %d, %Y")
        await ctx.send(
            f"## Contest Created!\n**ID:** `{contest_id}`\n**Name:** {name}\n**Deadline:** {formatted_date}\n**Submit Here:** <#{submission_channel_id}>")

    @commands.command(name="renameContest", description="Rename a contest without breaking entries")
    async def renameContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        contest_name = await self._pick_contest(ctx, only_active=False)
        if not contest_name: return

        new_name = await textTools.getCappedResponse(ctx, "Enter the new name:", 64)

        # Update Database
        await self.bot.sql.databaseExecuteDynamic(
            '''UPDATE contests SET name = $1 WHERE name = $2 AND serverID = $3;''',
            [new_name, contest_name, ctx.guild.id]
        )
        # Note: We don't need to update blueprint_stats because it links via ID (host_id), not name!
        await ctx.send(f"✅ Renamed **'{contest_name}'** to **'{new_name}'**.")

    @commands.command(name="deleteContest", description="Delete a contest")
    async def deleteContest(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        contest_name = await self._pick_contest(ctx, only_active=False)
        if not contest_name: return

        confirm = await ctx.bot.ui.getYesNoChoice(ctx)
        if not confirm: return await ctx.send("Cancelled.")

        # Get ID before deletion to clean up stats
        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT contest_id FROM contests WHERE name = $1 AND serverID = $2;''',
            [contest_name, ctx.guild.id]
        )

        if contest_data:
            c_id = contest_data['contest_id']
            # Delete Definition
            await self.bot.sql.databaseExecuteDynamic(
                '''DELETE FROM contests WHERE contest_id = $1;''', [c_id]
            )
            # Unlink Entries (Set host_id to 0 or NULL)
            await self.bot.sql.databaseExecuteDynamic(
                '''UPDATE blueprint_stats SET host_id = 0 WHERE host_id = $1;''', [c_id]
            )
            await ctx.send(f"Contest deleted and entries unlinked.")

    @commands.command(name="setContestRule", description="Configure advanced contest limits")
    async def setContestRule(self, ctx: commands.Context):
        if not await self._check_manager(ctx): return

        contest_name = await self._pick_contest(ctx)
        if not contest_name: return

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
            "Allow HVSS?": "allowhvss"
        }

        selection = await ctx.bot.ui.getChoiceFromList(ctx, list(rules_map.keys()), "Select rule to modify:")
        if not selection: return
        db_column = rules_map[selection]

        if db_column == "allowhvss":
            val = await ctx.bot.ui.getYesNoChoice(ctx)
        elif db_column == "era":
            val = await ctx.bot.ui.getChoiceFromList(ctx, ["WWI", "Interwar", "Earlywar", "Midwar", "Latewar"],
                                                     "Select Era:")
        else:
            val = await textTools.getFloatResponse(ctx, f"Enter value for {selection} (0 to disable/reset):")

        await self.bot.sql.databaseExecuteDynamic(
            f"UPDATE contests SET {db_column} = $1 WHERE name = $2 AND serverID = $3;",
            [val, contest_name, ctx.guild.id]
        )
        await ctx.send(f"✅ Updated **{selection}** to `{val}`.")

    # ----------------------------------------------------------------------------------
    # SCANNING & SUBMISSIONS
    # ----------------------------------------------------------------------------------

    @commands.command(name="scanChannel", description="Scan channel for blueprint entries")
    async def scanChannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
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
            contest_name = await self._pick_contest(ctx)
            if not contest_name: return
            contest_data = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM contests WHERE name = $1 AND serverID = $2;''',
                [contest_name, ctx.guild.id]
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
                        print(f"Scan Error on {message.id}: {e}")
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
            contest_name = await self._pick_contest(ctx)
            if not contest_name: return
            contest_data = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM contests WHERE name = $1 AND serverID = $2;''',
                [contest_name, ctx.guild.id]
            )

        # 2. Process
        await self._process_entry(ctx, ctx.message, attachment, contest_data, silent=False)

    # --- INTERNAL ENTRY PROCESSOR ---
    async def _process_entry(self, ctx, message, attachment, contest_data, silent=False):
        try:
            contest_id = contest_data['contest_id']
            contest_name = contest_data['name']  # For file path/logging only

            # A. Download & Save Locally
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        if not silent: await ctx.send("❌ Failed to download file.")
                        return False
                    file_bytes = await resp.read()

            # Sanitize name
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

            # C. Validation & Overrides
            stats['owner_id'] = message.author.id
            # *** CRITICAL CHANGE: Use host_id for contest link ***
            stats['host_id'] = contest_id

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

            # D. Final Decision
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

            # E. Database Insertion (Use host_id)
            # 1. Clean previous entry for this user in this contest ID
            await self.bot.sql.databaseExecuteDynamic(
                '''UPDATE blueprint_stats SET host_id = 0 WHERE owner_id = $1 AND host_id = $2;''',
                [stats['owner_id'], contest_id]
            )

            stats['file_url'] = attachment.url
            stats['submission_date'] = datetime.datetime.now()

            valid_cols = [
                "vehicle_id", "vehicle_class", "vehicle_era", "host_id", "faction_id", "owner_id", "base_cost",
                "tank_weight", "tank_length", "tank_width", "tank_height", "tank_total_height",
                "fuel_tank_capacity", "ground_pressure", "horsepower", "hpt", "top_speed", "travel_range",
                "crew_count", "cannon_stats", "armor_mass", "upper_frontal_angle", "lower_frontal_angle",
                "health", "attack", "defense", "breakthrough", "piercing", "armor", "cohesion",
                "file_url", "submission_date"  # Removed contest_name
            ]

            insert_data = {k: v for k, v in stats.items() if k in valid_cols}
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join([f"${i + 1}" for i in range(len(insert_data))])
            values = list(insert_data.values())

            await self.bot.sql.databaseExecuteDynamic(
                f"INSERT INTO blueprint_stats ({columns}) VALUES ({placeholders}) ON CONFLICT (vehicle_id) DO UPDATE SET host_id = EXCLUDED.host_id;",
                values
            )

            if not silent:
                await ctx.send(f"✅ **Submitted!** Entry recorded.")

            # F. Log
            if contest_data.get('log_channel_id') and contest_data['log_channel_id'] != 0:
                log_chan = ctx.guild.get_channel(contest_data['log_channel_id'])
                if log_chan:
                    embed = discord.Embed(title="📋 New Contest Entry", color=discord.Color.blue())
                    embed.add_field(name="Contest", value=contest_name)
                    embed.add_field(name="Author", value=f"<@{stats['owner_id']}>")
                    embed.add_field(name="Vehicle", value=attachment.filename)
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
    # VIEWING & HELPERS
    # ----------------------------------------------------------------------------------
    @commands.command(name="viewSubmissions", description="List entries for a contest")
    async def viewSubmissions(self, ctx: commands.Context):
        contest_name = await self._pick_contest(ctx, only_active=False)
        if not contest_name: return

        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT * FROM contests WHERE name = $1 AND serverID = $2;''',
            [contest_name, ctx.guild.id]
        )
        c_id = contest_data['contest_id']

        # Select using host_id
        subs = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT owner_id, tank_weight, base_cost, file_url 
               FROM blueprint_stats 
               WHERE host_id = $1;''',
            [c_id]
        )

        desc = f"{contest_data['description']}\n\n**Rules:**"
        if contest_data['weightlimit']: desc += f"\nWeight < {contest_data['weightlimit']}t"
        if contest_data['costlimit']: desc += f"\nCost < {contest_data['costlimit']}"
        if contest_data['era']: desc += f"\nEra: {contest_data['era']}"

        embed = discord.Embed(title=f"🏆 {contest_name}", description=desc, color=discord.Color.gold())

        if not subs:
            embed.add_field(name="Entries", value="*No submissions yet.*", inline=False)
        else:
            entry_list = []
            for sub in subs:
                user = ctx.guild.get_member(sub['owner_id'])
                username = user.display_name if user else "Unknown User"
                weight_tons = sub['tank_weight'] / 1000.0 if sub['tank_weight'] else 0
                entry_list.append(
                    f"• **{username}** ({weight_tons:.1f}t, ${sub['base_cost']}) [Link]({sub['file_url']})")

            chunk_size = 10
            for i in range(0, len(entry_list), chunk_size):
                chunk = entry_list[i:i + chunk_size]
                embed.add_field(name=f"Submissions ({i + 1}-{i + len(chunk)})", value="\n".join(chunk), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="downloadSubmissions", description="add a column to a SQL table")
    async def downloadSubmissions(self, ctx: commands.Context):
        contest_name = await self._pick_contest(ctx, only_active=False)
        data = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM blueprint_stats WHERE host_id = $1;''',
            [contest_name, ctx.guild.id])
        stringOut = json.dumps(data, indent=4)
        data = io.BytesIO(stringOut.encode())
        await ctx.send(file=discord.File(data, f'submissions-{contest_name}.json'))

    async def _pick_contest(self, ctx: commands.Context, only_active=True):
        query = '''SELECT name FROM contests WHERE serverID = $1'''
        if only_active:
            query += ''' AND status = true'''

        contests = await self.bot.sql.databaseFetchdictDynamic(query, [ctx.guild.id])

        if not contests:
            await ctx.send("No contests found in this server.")
            return None

        contest_names = [c['name'] for c in contests]
        if len(contest_names) == 1:
            return contest_names[0]

        return await ctx.bot.ui.getChoiceFromList(ctx, contest_names, "Select a contest:")

    async def _check_manager(self, ctx: commands.Context):
        if ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.manage_guild or ctx.author.id == self.bot.ownerid:
            return True
        await ctx.send("❌ You need **Manage Server** permissions to manage contests.")
        return False

    @commands.command(name="downloadContest", description="Download CSV stats and ZIP of blueprints")
    async def downloadContest(self, ctx: commands.Context):
        # 1. Permissions Check
        if not await self._check_manager(ctx): return

        # 2. Select Contest
        contest_name = await self._pick_contest(ctx, only_active=False)
        if not contest_name: return

        # 3. Get Contest ID (needed to find database entries)
        contest_data = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT contest_id FROM contests WHERE name = $1 AND serverID = $2;''',
            [contest_name, ctx.guild.id]
        )
        if not contest_data:
            return await ctx.send("❌ Error: Could not find contest ID.")

        c_id = contest_data['contest_id']

        await ctx.send("📦 Compiling data... please wait.")

        # --- PART A: GENERATE CSV ---
        try:
            # Fetch all stats for this contest ID
            data = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM blueprint_stats WHERE host_id = $1''',
                [c_id]
            )

            if not data:
                await ctx.send("⚠️ No database entries found for this contest.")
            else:
                # Use Pandas to create CSV easily
                df = pd.DataFrame(data)

                # Create in-memory buffer
                csv_buffer = io.BytesIO()
                df.to_csv(csv_buffer, index=False, encoding='utf-8')
                csv_buffer.seek(0)

                await ctx.send(
                    content=f"📊 **Database Stats for '{contest_name}'**",
                    file=discord.File(csv_buffer, filename=f"{contest_name}_stats.csv")
                )
        except Exception as e:
            await ctx.send(f"❌ Error generating CSV: `{e}`")

        # --- PART B: GENERATE ZIP ---
        try:
            # Reconstruct the folder path used in _process_entry
            safe_name = "".join([c for c in contest_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            folder_path = os.path.join("blueprints", str(ctx.guild.id), safe_name)

            if not os.path.exists(folder_path):
                return await ctx.send("⚠️ No local blueprint folder found for this contest.")

            # Create in-memory ZIP buffer
            zip_buffer = io.BytesIO()

            has_files = False
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Walk through the directory
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.endswith(".blueprint"):
                            file_path = os.path.join(root, file)
                            # Add file to zip (arcname ensures it doesn't store the full C:/ path)
                            zip_file.write(file_path, arcname=file)
                            has_files = True

            if not has_files:
                return await ctx.send("⚠️ Folder exists, but no .blueprint files were found.")

            zip_buffer.seek(0)

            # Check size (Discord 8MB limit for non-boosted)
            size_mb = zip_buffer.getbuffer().nbytes / (1024 * 1024)
            if size_mb > 8 and ctx.guild.filesize_limit < zip_buffer.getbuffer().nbytes:
                await ctx.send(f"❌ The ZIP file is too large ({size_mb:.2f}MB) for Discord upload.")
            else:
                await ctx.send(
                    content=f"🗂️ **Blueprint Archive for '{contest_name}'**",
                    file=discord.File(zip_buffer, filename=f"{safe_name}_files.zip")
                )

        except Exception as e:
            await ctx.send(f"❌ Error generating ZIP: `{e}`")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(contestFunctions(bot))