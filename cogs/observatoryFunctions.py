# /cogs/observatoryFunctions.py

import discord
from discord.ext import commands
import os
import uuid
import difflib
import json
import tempfile
import asyncio
import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class observatoryFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        # ... (init function is unchanged) ...
        self.bot = bot
        self.constellation_path = "./celestial_audio/"
        os.makedirs(self.constellation_path, exist_ok=True)
        try:
            client_id = self.bot.baseConfig['settings']['spotify_client_id']
            client_secret = self.bot.baseConfig['settings']['spotify_client_secret']
            auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
        except KeyError:
            self.sp = None
            print("Warning: Spotify API credentials not found. Bulk synchronize will be disabled.")

    async def send_command_to_navigator(self, command: str, payload: str = None):
        # ... (This function is unchanged) ...
        command_id = str(uuid.uuid4())
        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO celestial_directives (id, directive, payload, processed) VALUES ($1, $2, $3, FALSE);''',
            [command_id, command, payload]
        )

    @commands.command(name="setup_observatory_log", description="[Owner] Prepares the celestial database tables.")
    @commands.is_owner()
    async def setup_observatory_log(self, ctx: commands.Context):
        # ... (This function is unchanged) ...
        await ctx.send("Initializing Observatory Logs...")
        try:
            await self.bot.sql.databaseExecute(
                '''CREATE TABLE IF NOT EXISTS astral_bodies ( id SERIAL PRIMARY KEY, unique_id VARCHAR(255) UNIQUE NOT NULL, designation VARCHAR(255), cataloger_id BIGINT, classification VARCHAR(50), mon_arc BOOLEAN, tue_arc BOOLEAN, wed_arc BOOLEAN, thu_arc BOOLEAN, fri_arc BOOLEAN, sat_arc BOOLEAN, sun_arc BOOLEAN, filepath VARCHAR(1024) );''')
            await self.bot.sql.databaseExecute(
                '''CREATE TABLE IF NOT EXISTS celestial_directives ( id VARCHAR(255) PRIMARY KEY, directive VARCHAR(50), payload TEXT, processed BOOLEAN DEFAULT FALSE, timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );''')
            await self.bot.sql.databaseExecute(
                '''CREATE TABLE IF NOT EXISTS download_queue ( id SERIAL PRIMARY KEY, playlist_url TEXT NOT NULL, requester_id BIGINT NOT NULL, day_bools_json TEXT NOT NULL, status VARCHAR(20) DEFAULT 'pending', created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );''')
            await ctx.send("✅ All Observatory logs initialized successfully.")
        except Exception as e:
            await ctx.send(f"❌ Log initialization failed: `{e}`")

    @commands.command(name="catalog_celestial_body", description="Upload multiple audio files to the station.")
    async def catalog_celestial_body(self, ctx: commands.Context):
        if not ctx.message.attachments:
            return await ctx.send("Error: You must attach at least one audio file to use this command.")

        class_prompt = "Classify this batch of celestial bodies:"
        classification = await self.bot.ui.getButtonChoice(ctx, ["Static Noise", "Major Event", "Solar Cycle"])
        if not classification:
            return await ctx.send("Batch cataloging cancelled.")

        class_map = {
            "Static Noise": "STAR_CLUSTER",
            "Major Event": "NOVA_EVENT",
            "Solar Cycle": "PULSAR_BURST"
        }
        internal_class = class_map.get(classification)

        days_message = await ctx.send("Select the days for this entire batch:")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        selected_days = []
        while True:
            remaining_days = [d for d in days if d not in selected_days]
            if not remaining_days: break
            choice = await self.bot.ui.getButtonChoice(ctx, remaining_days + ["All Remaining", "Done"])
            if choice == "Done": break
            if choice == "All Remaining": selected_days.extend(remaining_days); break
            selected_days.append(choice)

        # MODIFIED: The check for an empty selected_days list has been removed.
        # if not selected_days:
        #     await days_message.delete()
        #     return await ctx.send("No days selected. Batch cataloging cancelled.")

        day_bools = {f"{day[:3].lower()}_arc": (day in selected_days) for day in days}
        await days_message.edit(content="Settings confirmed. Starting batch processing...", view=None)

        success_count = 0
        skipped_count = 0
        for attachment in ctx.message.attachments:
            name = os.path.splitext(attachment.filename)[0].replace('_', ' ').replace('-', ' ')
            sanitized_name = await self.bot.get_cog("textTools").sanitize(name)

            async with self.bot.pool.acquire() as connection:
                result = await connection.fetchrow("SELECT 1 FROM astral_bodies WHERE LOWER(designation) = LOWER($1);",
                                                   sanitized_name)
                if result:
                    skipped_count += 1
                    await ctx.send(f"⏭️ Skipping duplicate: **{sanitized_name}**")
                    continue

            unique_filename = f"{uuid.uuid4()}{os.path.splitext(attachment.filename)[1]}"
            file_path = os.path.join(self.constellation_path, unique_filename)

            await attachment.save(file_path)

            await self.bot.sql.databaseExecuteDynamic(
                '''INSERT INTO astral_bodies (unique_id, designation, cataloger_id, classification, mon_arc, tue_arc, wed_arc, thu_arc, fri_arc, sat_arc, sun_arc, filepath) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);''',
                [unique_filename, sanitized_name, ctx.author.id, internal_class, day_bools['mon_arc'],
                 day_bools['tue_arc'], day_bools['wed_arc'], day_bools['thu_arc'], day_bools['fri_arc'],
                 day_bools['sat_arc'], day_bools['sun_arc'], file_path]
            )
            await ctx.send(f"✅ Cataloged: **{sanitized_name}**")
            success_count += 1

        await self.send_command_to_navigator("REFRESH_EPHEMERIS")
        await ctx.send(
            f"\n✨ **Batch complete!**\n- Cataloged: **{success_count}** new bodies.\n- Skipped: **{skipped_count}** duplicates.")

    @commands.command(name="scan_sky", description="Lists all songs available for the current day.")
    async def scan_sky(self, ctx: commands.Context):
        # ... (This function is unchanged) ...
        today = datetime.datetime.now()
        day_name = today.strftime('%A')
        day_column = f"{today.strftime('%a').lower()}_arc"
        query = f"SELECT designation FROM astral_bodies WHERE classification = 'STAR_CLUSTER' AND {day_column} = TRUE ORDER BY designation ASC;"
        try:
            records = await self.bot.sql.databaseFetch(query)
            if not records:
                return await ctx.send(f"There are no songs scheduled for today ({day_name}).")
            song_list = [rec['designation'] for rec in records]
            page_size = 20
            pages = [song_list[i:i + page_size] for i in range(0, len(song_list), page_size)]
            await ctx.send(f"Found **{len(song_list)}** songs scheduled for {day_name}:")
            for i, page in enumerate(pages):
                embed = discord.Embed(title=f"Available Songs for {day_name} (Page {i + 1}/{len(pages)})",
                                      color=discord.Color.dark_purple())
                description = "\n".join(page)
                embed.description = f"```\n{description}\n```"
                await ctx.send(embed=embed)
                await asyncio.sleep(1)
        except Exception as e:
            await ctx.send(f"An error occurred while scanning the sky: `{e}`")

    # ... (The rest of the file is unchanged) ...
    @commands.command(name="plot_priority_trajectory", description="Sets the next song to play.")
    async def plot_priority_trajectory(self, ctx: commands.Context, *, search_query: str):
        all_bodies = await self.bot.sql.databaseFetchdict(
            "SELECT designation, unique_id FROM astral_bodies WHERE classification = 'STAR_CLUSTER';")
        if not all_bodies: return await ctx.send("No Star Clusters to choose from.")
        designations = [body['designation'] for body in all_bodies]
        matches = difflib.get_close_matches(search_query, designations, n=1, cutoff=0.6)
        if not matches: return await ctx.send(f"I couldn't find a close match for '{search_query}'.")
        best_match_name = matches[0]
        matched_body = next((body for body in all_bodies if body['designation'] == best_match_name), None)
        if matched_body:
            await self.send_command_to_navigator("PRIORITY_TRAJECTORY", payload=matched_body['unique_id'])
            await ctx.send(f"Trajectory confirmed. **'{best_match_name}'** will be the next transmission.")
        else:
            await ctx.send("An unexpected error occurred.")

    @commands.command(name="bulk_synchronize_trajectory",
                      description="Download a Spotify playlist and add it to the catalog.")
    @commands.is_owner()
    async def bulk_synchronize_trajectory(self, ctx: commands.Context, playlist_url: str):
        if not self.sp: return await ctx.send("Error: Spotify API credentials are not configured.")
        await ctx.send("Select the broadcast days for all songs in this playlist:")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        selected_days = []
        while True:
            remaining_days = [d for d in days if d not in selected_days]
            if not remaining_days: break
            choice = await self.bot.ui.getButtonChoice(ctx, remaining_days + ["All Remaining", "Done"])
            if choice == "Done": break
            if choice == "All Remaining": selected_days.extend(remaining_days); break
            selected_days.append(choice)
        day_bools = {f"{day[:3].lower()}_arc": (day in selected_days) for day in days}
        day_bools_json = json.dumps(day_bools)
        await self.bot.sql.databaseExecuteDynamic(
            "INSERT INTO download_queue (playlist_url, requester_id, day_bools_json) VALUES ($1, $2, $3)",
            [playlist_url, ctx.author.id, day_bools_json])
        await ctx.send(
            "✅ Playlist has been added to the download queue. The Celestial Downloader will begin processing it shortly. Watch the configured webhook channel for progress.")

    @commands.command(name="view_trajectory", description="Views the upcoming broadcast queue.")
    async def view_trajectory(self, ctx: commands.Context):
        snapshot_path = os.path.join(tempfile.gettempdir(), "celestial_trajectory.json")
        if not os.path.exists(snapshot_path): return await ctx.send("Trajectory snapshot not available.")
        with open(snapshot_path, 'r') as f:
            trajectory_data = json.load(f)
        if not trajectory_data: return await ctx.send("The broadcast trajectory is currently empty.")
        embed = discord.Embed(title="Upcoming Broadcast Trajectory", color=discord.Color.blue())
        description = ""
        class_map = {"STAR_CLUSTER": "🌠", "NOVA_EVENT": "✨", "PULSAR_BURST": "💥"}
        for i, item in enumerate(trajectory_data):
            emoji = class_map.get(item['classification'], "❔")
            description += f"`{i + 1}.` {emoji} {item['designation']}\n"
        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name="purge_observatory_log", description="[Owner] Deletes all songs and audio files.")
    @commands.is_owner()
    async def purge_observatory_log(self, ctx: commands.Context):
        count_record = await self.bot.sql.databaseFetchrow("SELECT COUNT(*) FROM astral_bodies;")
        song_count = count_record['count']
        if song_count == 0: return await ctx.send("The observatory log is already empty.")
        confirm_msg = await ctx.send(
            f"⚠️ **WARNING** ⚠️\n\nYou are about to permanently delete **{song_count}** cataloged audio files and their database records. This action cannot be undone.\n\nType `CONFIRM` to proceed.")

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            if msg.content != "CONFIRM":
                await confirm_msg.delete();
                await msg.delete()
                return await ctx.send("Purge cancelled.")
        except asyncio.TimeoutError:
            await confirm_msg.delete()
            return await ctx.send("Purge cancelled due to timeout.")
        await ctx.send(f"Confirmation received. Purging all **{song_count}** celestial bodies...")
        records = await self.bot.sql.databaseFetch("SELECT filepath FROM astral_bodies;")
        filepaths = [record['filepath'] for record in records]
        await self.bot.sql.databaseExecute("TRUNCATE TABLE astral_bodies RESTART IDENTITY;")
        deleted_files = 0
        for path in filepaths:
            try:
                if os.path.exists(path): os.remove(path); deleted_files += 1
            except Exception as e:
                print(f"Could not delete file {path}: {e}")
        await self.send_command_to_navigator("REFRESH_EPHEMERIS")
        await ctx.send(
            f"✅ Purge complete. Deleted **{deleted_files}** audio files and all associated database records.")

    @commands.command(name="interrupt_transmission", description="Skips the current track.")
    async def interrupt_transmission(self, ctx: commands.Context):
        await self.send_command_to_navigator("INTERRUPT")
        await ctx.send("Directive sent to interrupt the current transmission.")

    @commands.command(name="realign_navigator", description="Restarts the music player process.")
    @commands.is_owner()
    async def realign_navigator(self, ctx: commands.Context):
        await self.send_command_to_navigator("REALIGN")
        await ctx.send("Shutdown directive sent to the Celestial Navigator.")


async def setup(bot: commands.Bot):
    await bot.add_cog(observatoryFunctions(bot))