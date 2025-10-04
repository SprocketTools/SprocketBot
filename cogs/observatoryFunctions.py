# /cogs/observatoryFunctions.py

import discord
from discord.ext import commands
import os
import uuid
import difflib
import asyncio

# ADDED
import json
import tempfile

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp


class observatoryFunctions(commands.Cog):
    # ... (init, send_command_to_navigator, setup, catalog, and plot commands are unchanged) ...
    def __init__(self, bot: commands.Bot):
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
            print("Warning: Spotify API credentials not found in configuration.ini. Bulk synchronize will be disabled.")

    async def send_command_to_navigator(self, command: str, payload: str = None):
        command_id = str(uuid.uuid4())
        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO celestial_directives (id, directive, payload, processed) VALUES ($1, $2, $3, FALSE);''',
            [command_id, command, payload]
        )

    @commands.command(name="setup_observatory_log", description="[Owner] Prepares the celestial database tables.")
    @commands.is_owner()
    async def setup_observatory_log(self, ctx: commands.Context):
        await ctx.send("Initializing Ephemeris and Directives Log...")
        try:
            await self.bot.sql.databaseExecute('''
                CREATE TABLE IF NOT EXISTS astral_bodies (
                    id SERIAL PRIMARY KEY,
                    unique_id VARCHAR(255) UNIQUE NOT NULL,
                    designation VARCHAR(255),
                    cataloger_id BIGINT,
                    classification VARCHAR(50),
                    mon_arc BOOLEAN, tue_arc BOOLEAN, wed_arc BOOLEAN,
                    thu_arc BOOLEAN, fri_arc BOOLEAN, sat_arc BOOLEAN, sun_arc BOOLEAN,
                    filepath VARCHAR(1024)
                );
            ''')
            await self.bot.sql.databaseExecute('''
                CREATE TABLE IF NOT EXISTS celestial_directives (
                    id VARCHAR(255) PRIMARY KEY,
                    directive VARCHAR(50), payload TEXT, processed BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            await ctx.send("✅ Observatory logs initialized successfully.")
        except Exception as e:
            await ctx.send(f"❌ Log initialization failed: `{e}`")

    @commands.command(name="catalog_celestial_body", description="Upload a new audio file to the station.")
    async def catalog_celestial_body(self, ctx: commands.Context, *, name: str):
        if not ctx.message.attachments:
            await ctx.send("Error: You must attach an audio file to catalog.")
            return
        attachment = ctx.message.attachments[0]
        sanitized_name = await self.bot.get_cog("textTools").sanitize(name)
        existing_body = await self.bot.sql.databaseFetchrowDynamic(
            "SELECT 1 FROM astral_bodies WHERE LOWER(designation) = LOWER($1);",
            [sanitized_name]
        )
        if existing_body:
            await ctx.send(
                f"❌ A celestial body with the designation **'{sanitized_name}'** already exists in the catalog. Upload cancelled.")
            return
        unique_filename = f"{uuid.uuid4()}{os.path.splitext(attachment.filename)[1]}"
        file_path = os.path.join(self.constellation_path, unique_filename)
        await attachment.save(file_path)
        class_prompt = "Classify this celestial body:"
        classification = await self.bot.ui.getButtonChoice(ctx, ["Star Cluster", "Nova Event", "Pulsar Burst"])
        if not classification:
            await ctx.send("Cataloging cancelled.")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        class_map = {"Star Cluster": "STAR_CLUSTER", "Nova Event": "NOVA_EVENT", "Pulsar Burst": "PULSAR_BURST"}
        internal_class = class_map.get(classification)
        await ctx.send("Select the days this body is cleared for broadcast:")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        selected_days = []
        while True:
            remaining_days = [d for d in days if d not in selected_days]
            if not remaining_days: break
            options = remaining_days + ["All Remaining", "Done"]
            choice = await self.bot.ui.getButtonChoice(ctx, options)
            if choice == "Done": break
            if choice == "All Remaining":
                selected_days.extend(remaining_days)
                break
            selected_days.append(choice)
        day_bools = {f"{day[:3].lower()}_arc": (day in selected_days) for day in days}
        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO astral_bodies (unique_id, designation, cataloger_id, classification, 
               mon_arc, tue_arc, wed_arc, thu_arc, fri_arc, sat_arc, sun_arc, filepath) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);''',
            [
                unique_filename, sanitized_name, ctx.author.id, internal_class,
                day_bools['mon_arc'], day_bools['tue_arc'], day_bools['wed_arc'],
                day_bools['thu_arc'], day_bools['fri_arc'], day_bools['sat_arc'],
                day_bools['sun_arc'], file_path
            ]
        )
        await self.send_command_to_navigator("REFRESH_EPHEMERIS")
        await ctx.send(
            f"✅ **{sanitized_name}** has been cataloged as a **{classification}** and added to the broadcast schedule.")

    @commands.command(name="plot_priority_trajectory", description="Sets the next song to play.")
    async def plot_priority_trajectory(self, ctx: commands.Context, *, search_query: str):
        all_bodies = await self.bot.sql.databaseFetchdict(
            "SELECT designation, unique_id FROM astral_bodies WHERE classification = 'STAR_CLUSTER';"
        )
        if not all_bodies:
            await ctx.send("There are no Star Clusters (songs) in the observatory log to choose from.")
            return
        designations = [body['designation'] for body in all_bodies]
        matches = difflib.get_close_matches(search_query, designations, n=1, cutoff=0.6)
        if not matches:
            await ctx.send(f"I couldn't find a close match for '{search_query}'. Please try again.")
            return
        best_match_name = matches[0]
        matched_body = next((body for body in all_bodies if body['designation'] == best_match_name), None)
        if matched_body:
            unique_id_to_queue = matched_body['unique_id']
            await self.send_command_to_navigator("PRIORITY_TRAJECTORY", payload=unique_id_to_queue)
            await ctx.send(f"Trajectory confirmed. **'{best_match_name}'** will be the next transmission.")
        else:
            await ctx.send("An unexpected error occurred while matching the celestial body.")

    @commands.command(name="bulk_synchronize_trajectory",
                      description="Download a Spotify playlist and add it to the catalog.")
    @commands.is_owner()
    async def bulk_synchronize_trajectory(self, ctx: commands.Context, playlist_url: str):
        if not self.sp:
            return await ctx.send("Error: Spotify API credentials are not configured. This command is disabled.")
        await ctx.send("Select the broadcast days for all songs in this playlist:")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        selected_days = []
        while True:
            remaining_days = [d for d in days if d not in selected_days]
            if not remaining_days: break
            options = remaining_days + ["All Remaining", "Done"]
            choice = await self.bot.ui.getButtonChoice(ctx, options)
            if choice == "Done": break
            if choice == "All Remaining":
                selected_days.extend(remaining_days)
                break
            selected_days.append(choice)
        if not selected_days:
            return await ctx.send("No days selected. Bulk synchronization cancelled.")
        day_bools = {f"{day[:3].lower()}_arc": (day in selected_days) for day in days}
        await ctx.send(
            "✅ Trajectory synchronization initiated. I will report progress here. This may take a long time.")
        asyncio.create_task(self._perform_bulk_synchronization(ctx, playlist_url, day_bools))

    async def _perform_bulk_synchronization(self, ctx, playlist_url, day_bools):
        try:
            existing_bodies_records = await self.bot.sql.databaseFetch(
                "SELECT LOWER(designation) as designation FROM astral_bodies");
            existing_designations = {record['designation'] for record in existing_bodies_records}
            results = self.sp.playlist_items(playlist_url)
            tracks = results['items']
            total = len(tracks)
            success_count = 0
            skipped_count = 0
            for i, item in enumerate(tracks):
                track = item['track']
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                designation = f"{artist_name} - {track_name}"
                search_query = f"{designation} lyrics"
                if designation.lower() in existing_designations:
                    skipped_count += 1
                    await ctx.send(f"⏭️ **({i + 1}/{total})** Skipping duplicate: `{designation}`")
                    await asyncio.sleep(1)
                    continue
                await ctx.send(f"🛰️ **({i + 1}/{total})** Searching for `{designation}`...")
                try:
                    unique_id = str(uuid.uuid4())
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'postprocessors': [
                            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                        'outtmpl': os.path.join(self.constellation_path, f'{unique_id}.%(ext)s'),
                        'default_search': 'ytsearch1', 'quiet': True, 'noprogress': True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([search_query])
                    filepath = os.path.join(self.constellation_path, f'{unique_id}.mp3')
                    await self.bot.sql.databaseExecuteDynamic(
                        '''INSERT INTO astral_bodies (unique_id, designation, cataloger_id, classification, 
                        mon_arc, tue_arc, wed_arc, thu_arc, fri_arc, sat_arc, sun_arc, filepath) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);''',
                        [
                            unique_id, designation, ctx.author.id, "STAR_CLUSTER",
                            day_bools['mon_arc'], day_bools['tue_arc'], day_bools['wed_arc'],
                            day_bools['thu_arc'], day_bools['fri_arc'], day_bools['sat_arc'],
                            day_bools['sun_arc'], filepath
                        ]
                    )
                    existing_designations.add(designation.lower())
                    await ctx.send(f"✅ **({i + 1}/{total})** Cataloged `{designation}`.")
                    success_count += 1
                except Exception as e:
                    await ctx.send(f"❌ **({i + 1}/{total})** Failed to process `{designation}`. Error: `{e}`")
                await asyncio.sleep(2)
            await ctx.send(
                f"✨ **Synchronization Complete!** Successfully cataloged **{success_count}/{total}** bodies. Skipped **{skipped_count}** duplicates.")
            await self.send_command_to_navigator("REFRESH_EPHEMERIS")
        except Exception as e:
            await ctx.send(f"A critical error occurred during bulk synchronization: `{e}`")

    # ADDED THIS NEW COMMAND
    @commands.command(name="view_trajectory", description="Views the upcoming broadcast queue.")
    async def view_trajectory(self, ctx: commands.Context):
        """Reads the trajectory snapshot file and displays the queue."""
        snapshot_path = os.path.join(tempfile.gettempdir(), "celestial_trajectory.json")

        if not os.path.exists(snapshot_path):
            return await ctx.send(
                "The trajectory snapshot is not available. The player might be offline or the queue is empty.")

        with open(snapshot_path, 'r') as f:
            trajectory_data = json.load(f)

        if not trajectory_data:
            return await ctx.send("The broadcast trajectory is currently empty.")

        embed = discord.Embed(title="Upcoming Broadcast Trajectory", color=discord.Color.blue())

        description = ""
        # Emojis for each classification
        class_map = {"STAR_CLUSTER": "🌠", "NOVA_EVENT": "✨", "PULSAR_BURST": "💥"}

        for i, item in enumerate(trajectory_data):
            emoji = class_map.get(item['classification'], "❔")
            description += f"`{i + 1}.` {emoji} {item['designation']}\n"

        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name="interrupt_transmission", description="Skips the current track.")
    async def interrupt_transmission(self, ctx: commands.Context):
        await self.send_command_to_navigator("INTERRUPT")
        await ctx.send("Directive sent to interrupt the current transmission and proceed to the next object.")

    @commands.command(name="realign_navigator", description="Restarts the music player process.")
    @commands.is_owner()
    async def realign_navigator(self, ctx: commands.Context):
        await self.send_command_to_navigator("REALIGN")
        await ctx.send("Shutdown directive sent. The Celestial Navigator will realign its systems.")


async def setup(bot: commands.Bot):
    await bot.add_cog(observatoryFunctions(bot))