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
        self.queues = {}

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

    def get_queue(self, guild_id: int) -> list:
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

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
            search = await textTools.mild_sanitize(searchIn)
            async with ctx.typing():
                try:
                    url, title = await asyncio.to_thread(self._extract_media_info, search)
                    guild_queue.append((url, title, FFMPEG_OPTIONS))
                    await ctx.send(f'Added to queue: **{title}**')
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
        url, title = None, None

        # Extract track details from attachments or prompts
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if any(attachment.filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
                url, title = attachment.url, f"Uploaded File: {attachment.filename}"
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
                    url, title = attachment.url, f"Uploaded File: {attachment.filename}"
                else:
                    return await ctx.send("Unsupported audio file format attached.")
            elif prompt_msg.content:
                search = await textTools.mild_sanitize(prompt_msg.content)
                async with ctx.typing():
                    try:
                        url, title = await asyncio.to_thread(self._extract_media_info, search)
                    except Exception as e:
                        return await ctx.send(f"Could not retrieve audio: `{e}`")

        # Append to target guild's isolated queue
        target_queue = self.get_queue(target_guild.id)
        target_queue.append((url, title, options))
        await ctx.send(f'Added to queue for **{target_guild.name}** (<#{channelID}>): **{title}**')

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