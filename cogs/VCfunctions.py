import asyncio
import configparser
import locale
import os
import re
import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp

import type_hints
import main
from cogs.adminFunctions import adminFunctions
from cogs.textTools import textTools

locale.setlocale(locale.LC_ALL, '')

# --- Spotify Configuration (Ported from celestial_navigator.py) ---
sp = None
try:
    baseConfig = configparser.ConfigParser()
    if os.name == 'nt':
        config_path = "C:\\\\SprocketBot\\\\configuration.ini"
    else:
        config_path = os.path.join(os.path.expanduser("~"), "configuration.ini")

    baseConfig.read(config_path)
    client_id = baseConfig['settings']['spotify_client_id']
    client_secret = baseConfig['settings']['spotify_client_secret']
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
except Exception as e:
    print(f"[VCfunctions] Warning: Could not initialize Spotify client: {e}")

FFMPEG_OPTIONS_CURSED = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 128k -filter:a "volume=0.115, asetrate=44100*1.9, atempo=0.55, bass=g=4" -c:a libopus'
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 128k -filter:a "volume=0.15, bass=g=4" -c:a libopus'
}
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch1',
    'source_address': '0.0.0.0',  # prevents IPv6 routing issues on some servers
    'quiet': True,
    'noprogress': True,
    'cookiefile': 'cookies.txt',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


class VCfunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id: int) -> list:
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def _resolve_spotify_queries(self, search: str) -> list[tuple[str, str | None]]:
        """
        Resolves a search string or URL into a list of (query_or_url, spotify_display_title) tuples.
        - Direct Spotify URLs (track, playlist, album) are fetched directly via Spotipy.
        - Direct non-Spotify URLs are passed through untouched.
        - Text queries search Spotify first for track metadata, falling back to raw text if Spotify fails.
        """
        is_url = "https://" in search or "http://" in search
        is_spotify_url = ("open.spotify.com" in search or "spotify.link" in search or search.startswith("spotify:"))

        if is_spotify_url and sp:
            try:
                if "track" in search:
                    track = sp.track(search)
                    designation = f"{track['artists'][0]['name']} - {track['name']}"
                    return [(designation, designation)]
                elif "playlist" in search:
                    tracks = []
                    results = sp.playlist_items(search)
                    while results:
                        for item in results.get('items', []):
                            track = item.get('track')
                            if track and track.get('artists') and track.get('name'):
                                designation = f"{track['artists'][0]['name']} - {track['name']}"
                                tracks.append((designation, designation))
                        results = sp.next(results) if results.get('next') else None
                    if tracks:
                        return tracks
                elif "album" in search:
                    tracks = []
                    results = sp.album_tracks(search)
                    while results:
                        for track in results.get('items', []):
                            if track and track.get('artists') and track.get('name'):
                                designation = f"{track['artists'][0]['name']} - {track['name']}"
                                tracks.append((designation, designation))
                        results = sp.next(results) if results.get('next') else None
                    if tracks:
                        return tracks
            except Exception as e:
                print(f"[VCfunctions] Spotify link extraction failed, falling back to raw query: {e}")

        if is_url:
            return [(search, None)]

        # Default to searching through Spotify for text queries
        if sp:
            try:
                results = sp.search(q=search, type='track', limit=1)
                items = results.get('tracks', {}).get('items', [])
                if items:
                    track = items[0]
                    designation = f"{track['artists'][0]['name']} - {track['name']}"
                    return [(designation, designation)]
            except Exception as e:
                print(f"[VCfunctions] Spotify search failed, falling back to YouTube search: {e}")

        return [(search, None)]

    def _query_youtube_with_retries(self, query: str, preferred_title: str = None) -> tuple[str, str]:
        """
        Queries YouTube via yt-dlp with multiple fallback attempts (ported from celestial_navigator.py).
        """
        is_url = "https://" in query or "http://" in query

        if is_url:
            attempts = [query]
        else:
            clean_query = re.sub(r'[^a-zA-Z0-9 \\-]', '', query).strip()
            attempts = [
                f"ytsearch1:{query} lyrics",
                f"ytsearch1:{clean_query if clean_query else query}",
                f"ytsearch1:{query}"
            ]
            # Deduplicate while preserving order
            seen = set()
            attempts = [a for a in attempts if not (a in seen or seen.add(a))]

        last_error = None
        for attempt_idx, attempt_query in enumerate(attempts, start=1):
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(attempt_query, download=False)
                    if 'entries' in info:
                        entries = [e for e in info['entries'] if e]
                        if not entries:
                            raise ValueError("No results returned from YouTube.")
                        info = entries[0]

                    url = info.get('url') or info.get('webpage_url')
                    if not url:
                        raise ValueError("Could not extract playable stream URL.")

                    title = preferred_title or info.get('title', 'Unknown Track')
                    return url, title
            except Exception as e:
                print(f"[VCfunctions] YouTube attempt {attempt_idx}/{len(attempts)} failed for '{attempt_query}': {e}")
                last_error = e

        raise RuntimeError(f"All YouTube search attempts failed. Last error: {last_error}")

    def _extract_media_info(self, search: str) -> tuple[str, str]:
        """Single-track synchronous wrapper for compatibility."""
        resolved = self._resolve_spotify_queries(search)
        query, preferred_title = resolved[0]
        return self._query_youtube_with_retries(query, preferred_title)

    def _extract_media_list(self, search: str) -> list[tuple[str, str]]:
        """Resolves one or more tracks (supporting Spotify track/playlist/album links) into playable (url, title) pairs."""
        resolved = self._resolve_spotify_queries(search)
        tracks = []
        for query, preferred_title in resolved:
            try:
                url, title = self._query_youtube_with_retries(query, preferred_title)
                tracks.append((url, title))
            except Exception as e:
                print(f"[VCfunctions] Skipping failed track '{query}': {e}")
                if len(resolved) == 1:
                    raise
        if not tracks:
            raise RuntimeError("Could not resolve any playable tracks.")
        return tracks

    @commands.command(name="play", description="Play music or uploaded audio files with the bot",
                      extras={'category': 'utility'})
    async def play(self, ctx: commands.Context, *, searchIn: str = None):
        serverConfig = await adminFunctions.getServerConfig(ctx)
        if str(serverConfig["musicroleid"]) not in str(ctx.author.roles):
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("You are not authorized to run this command.")
                return

        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("You need to be in a voice channel to play music!")

        # Ensure active voice connection
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            try:
                await voice_channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                await ctx.send(f"Failed to connect to voice channel: `{e}`")
                return

        guild_queue = self.get_queue(ctx.guild.id)

        # 1. Attachment handling
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if any(attachment.filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
                guild_queue.append((attachment.url, f"Uploaded File: {attachment.filename}", FFMPEG_OPTIONS))
                await ctx.send(f'Added attachment to queue: **{attachment.filename}**')
            else:
                return await ctx.send("Unsupported audio file format.")
        elif searchIn:
            # Preserve URLs directly (avoid stripping URL characters in mild_sanitize), sanitize normal search queries
            if "https://" in searchIn or "http://" in searchIn or searchIn.startswith("spotify:"):
                search = searchIn.strip()
            else:
                search = await textTools.mild_sanitize(searchIn)

            async with ctx.typing():
                try:
                    tracks = await asyncio.to_thread(self._extract_media_list, search)
                    for url, title in tracks:
                        guild_queue.append((url, title, FFMPEG_OPTIONS))

                    if len(tracks) == 1:
                        await ctx.send(f'Added to queue: **{tracks[0][1]}**')
                    else:
                        await ctx.send(f'Added **{len(tracks)}** tracks from Spotify to the queue!')
                except Exception as e:
                    return await ctx.send(f"Could not retrieve audio: `{e}`")

        if ctx.voice_client and not ctx.voice_client.is_playing():
            await self.play_next_guild(ctx, ctx.guild)

    async def play_next_guild(self, ctx, guild: discord.Guild):
        guild_vc = guild.voice_client
        guild_queue = self.get_queue(guild.id)

        if guild_queue:
            if not guild_vc or not guild_vc.is_connected():
                await ctx.send(f"Lost voice connection in **{guild.name}**.")
                return

            url, title, ffoptions = guild_queue.pop(0)

            try:
                source = await discord.FFmpegOpusAudio.from_probe(url, **ffoptions)
                guild_vc.play(
                    source,
                    after=lambda e: self.bot.loop.create_task(self.play_next_guild(ctx, guild))
                )
                await ctx.send(f'Now playing in **{guild.name}**: **{title}**')
            except Exception as e:
                await ctx.send(f"Error starting track **{title}**: `{e}`")
                await self.play_next_guild(ctx, guild)

        elif guild_vc and not guild_vc.is_playing():
            await ctx.send(f"Queue empty for **{guild.name}**!")
            await asyncio.sleep(5)
            if guild_vc and guild_vc.is_connected() and not guild_vc.is_playing() and not guild_queue:
                await guild_vc.disconnect()

    @commands.command(name="search", description="Search for music with the bot")
    async def search(self, ctx: commands.Context, *, searchIn):
        if "https://" in searchIn or "http://" in searchIn or searchIn.startswith("spotify:"):
            search = searchIn.strip()
        else:
            search = await textTools.mild_sanitize(searchIn)

        async with ctx.typing():
            try:
                url, title = await asyncio.to_thread(self._extract_media_info, search)
                await ctx.send(f'Result:\\n**{title}**\\n<{url}>')
            except Exception as e:
                await ctx.send(f"Search failed: `{e}`")

    @commands.command(name="trollVC", description="Play audio in a specified channel across servers")
    async def trollVC(self, ctx: commands.Context, channelID: int, *, action: str = None):
        if ctx.author.id != main.ownerID:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return await ctx.send("You are not authorized to run this command.")

        target_channel = self.bot.get_channel(channelID)
        if not target_channel or not isinstance(target_channel, discord.VoiceChannel):
            return await ctx.send("Target voice channel not found or invalid.")

        target_guild = target_channel.guild
        guild_vc = target_guild.voice_client

        if guild_vc:
            if guild_vc.channel != target_channel:
                await guild_vc.move_to(target_channel)
            elif not guild_vc.is_connected():
                await guild_vc.disconnect(force=True)
                guild_vc = await target_channel.connect(timeout=20.0, reconnect=True)
        else:
            guild_vc = await target_channel.connect(timeout=20.0, reconnect=True)

        options = FFMPEG_OPTIONS_CURSED if action == "cursed" else FFMPEG_OPTIONS
        tracks_to_queue = []

        # Extract track details from attachments or prompts
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if any(attachment.filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
                tracks_to_queue.append((attachment.url, f"Uploaded File: {attachment.filename}"))
            else:
                return await ctx.send("Unsupported audio file format attached.")
        else:
            await ctx.send("What is the song's search query or attached audio file?")
            try:
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                prompt_msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out waiting for a response.")

            if prompt_msg.attachments:
                attachment = prompt_msg.attachments[0]
                if any(attachment.filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
                    tracks_to_queue.append((attachment.url, f"Uploaded File: {attachment.filename}"))
                else:
                    return await ctx.send("Unsupported audio file format attached.")
            elif prompt_msg.content:
                raw_content = prompt_msg.content.strip()
                if "https://" in raw_content or "http://" in raw_content or raw_content.startswith("spotify:"):
                    search = raw_content
                else:
                    search = await textTools.mild_sanitize(raw_content)

                async with ctx.typing():
                    try:
                        tracks_to_queue = await asyncio.to_thread(self._extract_media_list, search)
                    except Exception as e:
                        return await ctx.send(f"Could not retrieve audio: `{e}`")

        # Append to target guild's isolated queue
        target_queue = self.get_queue(target_guild.id)
        for url, title in tracks_to_queue:
            target_queue.append((url, title, options))

        if len(tracks_to_queue) == 1:
            await ctx.send(f'Added to queue for **{target_guild.name}** (<#{channelID}>): **{tracks_to_queue[0][1]}**')
        else:
            await ctx.send(f'Added **{len(tracks_to_queue)}** tracks to queue for **{target_guild.name}** (<#{channelID}>)!')

        if guild_vc and not guild_vc.is_playing():
            await self.play_next_guild(ctx, target_guild)

    @commands.command(name="skip", description="Skip the current track")
    async def skip(self, ctx: commands.Context):
        serverConfig = await adminFunctions.getServerConfig(ctx)
        if str(serverConfig["musicroleid"]) not in str(ctx.author.roles):
            if not ctx.author.guild_permissions.administrator:
                await ctx.send(await self.bot.error.retrieveError(ctx))
                await ctx.send("You are not authorized to run this command.")
                return

        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped!")

    @commands.command(name="playSong", description="Play local sample file")
    async def playSong(self, ctx: commands.Context, filepath: str = "sample.mp3"):
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel.")

        vc = ctx.voice_client or await ctx.author.voice.channel.connect()
        try:
            source = discord.FFmpegPCMAudio(source=filepath)
            vc.play(source, after=lambda e: print(f"Finished playing local file: {e}") if e else None)
            await ctx.send(f"Playing local file: `{filepath}`")
        except Exception as e:
            await ctx.send(f"Failed to play file: `{e}`")

    @commands.command(name="playTest", description="Test local audio playback")
    async def playTest(self, ctx: commands.Context, filepath: str = "sample.mp3"):
        if not ctx.author.voice:
            return await ctx.send("You are not in a voice channel.")

        vc = ctx.voice_client or await ctx.author.voice.channel.connect()

        def after_playing(error):
            if error:
                print(f"Error in playTest: {error}")
            self.bot.loop.create_task(vc.disconnect())

        try:
            source = discord.FFmpegPCMAudio(source=filepath)
            vc.play(source, after=after_playing)
        except Exception as e:
            await ctx.send(f"Playback error: `{e}`")
            await vc.disconnect()

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VCfunctions(bot))