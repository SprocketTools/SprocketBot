import asyncio
import locale
import type_hints
import discord
from discord.ext import commands
import yt_dlp

import main
from cogs.adminFunctions import adminFunctions
from cogs.textTools import textTools

locale.setlocale(locale.LC_ALL, '')

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
    'default_search': 'auto',
    'source_address': '0.0.0.0', # prevents IPv6 routing issues on some servers
}


class VCfunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.queue = []

    def _extract_media_info(self, ydl, search: str):
        """Helper function to cleanly extract single track details from yt-dlp queries."""
        if "https://" in search or "http://" in search:
            info = ydl.extract_info(search, download=False)
        else:
            info = ydl.extract_info(f"scsearch:{search}", download=False)

        if 'entries' in info and info['entries']:
            info = info['entries'][0]

        url = info.get('url') or info.get('webpage_url')
        title = info.get('title', 'Unknown Track')
        return url, title

    def _extract_media_info(self, search: str):
        """Synchronous wrapper for yt-dlp to run inside an executor thread."""
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            if "https://" in search or "http://" in search:
                info = ydl.extract_info(search, download=False)
            else:
                info = ydl.extract_info(f"scsearch:{search}", download=False)

            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            url = info.get('url') or info.get('webpage_url')
            title = info.get('title', 'Unknown Track')
            return url, title

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

        if not ctx.voice_client:
            try:
                await voice_channel.connect()
            except Exception as e:
                await ctx.send(f"Failed to connect to the voice channel.\nError: `{e}`")
                return

        # 1. Process local/uploaded file attachments
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if any(attachment.filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
                url = attachment.url
                title = f"Uploaded File: {attachment.filename}"
                self.queue.append((url, title, FFMPEG_OPTIONS))
                await ctx.send(f'Added attachment to queue: **{attachment.filename}**')
            else:
                return await ctx.send("Unsupported audio file format.")

        # 2. Process search queries asynchronously without blocking the loop
        elif searchIn:
            search = await textTools.mild_sanitize(searchIn)
            async with ctx.typing():
                try:
                    # Offloads blocking network call to a separate worker thread
                    url, title = await asyncio.to_thread(self._extract_media_info, search)
                    self.queue.append((url, title, FFMPEG_OPTIONS))
                    await ctx.send(f'Added to queue: **{title}**')
                except Exception as e:
                    await ctx.send(f"Could not retrieve audio: `{e}`")
                    return
        else:
            return await ctx.send("Please provide a search term/link or upload an audio file attachment.")

        # 3. Trigger playback loop if idle
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queue:
            url, title, ffoptions = self.queue.pop(0)

            try:
                # Offload stream probing to a background thread to keep loop responsive
                source = await asyncio.to_thread(
                    discord.FFmpegOpusAudio.from_probe, url, **ffoptions
                )
                ctx.voice_client.play(
                    source,
                    after=lambda e: self.bot.loop.create_task(self.play_next(ctx))
                )
                await ctx.send(f'Now playing: **{title}**')
            except Exception as e:
                await ctx.send(f"Error starting track **{title}**: `{e}`")
                await self.play_next(ctx)

        elif ctx.voice_client and not ctx.voice_client.is_playing():
            await ctx.send("Queue is empty!")
            await asyncio.sleep(5)
            if ctx.voice_client and not ctx.voice_client.is_playing() and not self.queue:
                await ctx.voice_client.disconnect()

    @commands.command(name="search", description="Search for music with the bot")
    async def search(self, ctx: commands.Context, *, searchIn):
        search = await textTools.mild_sanitize(searchIn)

        async with ctx.typing():
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    url, title = await self.bot.loop.run_in_executor(
                        None, lambda: self._extract_media_info(ydl, search)
                    )
                await ctx.send(f'Result:\n**{title}**\n<{url}>')
            except Exception as e:
                await ctx.send(f"Search failed: `{e}`")

    @commands.command(name="trollVC", description="Play audio in a specified channel with optional filters")
    async def trollVC(self, ctx: commands.Context, channelID: int, *, action=None):
        if ctx.author.id != main.ownerID:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            await ctx.send("You are not authorized to run this command.")
            return

        channel = self.bot.get_channel(channelID)
        if not channel:
            return await ctx.send("Target voice channel not found.")

        search = await textTools.mild_sanitize(await textTools.getResponse(ctx, "What is the song's search query?"))

        if not ctx.voice_client:
            await channel.connect()

        async with ctx.typing():
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    url, title = await self.bot.loop.run_in_executor(
                        None, lambda: self._extract_media_info(ydl, search)
                    )

                options = FFMPEG_OPTIONS_CURSED if action == "cursed" else FFMPEG_OPTIONS
                self.queue.append((url, title, options))
                await ctx.send(f'Added to queue: **{title}**')
            except Exception as e:
                await ctx.send(f"Failed to extract target audio: `{e}`")
                return

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

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