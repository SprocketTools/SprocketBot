import asyncio
import locale, yt_dlp

from cogs.adminFunctions import adminFunctions

locale.setlocale(locale.LC_ALL, '')
from discord.ext.music import MusicClient, WAVAudio, Track
import discord
from discord.ext import commands

import main
from cogs.errorFunctions import errorFunctions
from cogs.textTools import textTools
FFMPEG_OPTIONS_CURSED = {
    'options': '-vn -b:a 128k -filter:a "volume=0.115, asetrate=44100*1.9, atempo=0.55, bass=g=4" -c:a libopus'}
FFMPEG_OPTIONS = {
    'options': '-vn -b:a 128k -filter:a "volume=0.15, bass=g=4" -c:a libopus'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}


class VCfunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []

    @commands.command(name="play", description="Play music with the bot")
    async def play(self, ctx: commands.Context, *, searchIn):
        serverConfig = await adminFunctions.getServerConfig(ctx)
        if str(serverConfig["musicroleid"]) not in str(ctx.author.roles):
            if ctx.author.guild_permissions.administrator == False:
                await ctx.send(await errorFunctions.retrieveError(ctx))
                await ctx.send("You are not authorized to run this command.")
                return
        search = await textTools.mild_sanitize(searchIn)
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send(await errorFunctions.retrieveError(ctx))
        if not ctx.voice_client:
            await voice_channel.connect()


        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                if "https" in search:
                    info = ydl.extract_info(f"{search}", download=False)
                else:
                    info = ydl.extract_info(f"scsearch:{search}", download=False)
            print(info)
            try:
                url = info['url']
            except Exception:
                url = info['webpage_url']
            title = info['title']
            self.queue.append((url, title, FFMPEG_OPTIONS))
            await ctx.send(f'Added to queue: **{title}**')
        if not ctx.voice_client.is_playing():

            await self.play_next(ctx)

    @commands.command(name="search", description="Search for music with the bot")
    async def search(self, ctx: commands.Context, *, searchIn):
        search = await textTools.mild_sanitize(searchIn)

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"scsearch:{search}", download=False)
            print('URL:   ' + info['url'])
            # try:
            #     info = info['entries'][0]
            # except Exception:
            #     await ctx.send(await errorFunctions.retrieveError(ctx))
            #     await ctx.send("This link is not valid.  Note that videos cannot link to a playlist, or be a video inside a playlist.")
            url = info['url']
            title = info['title']
            await ctx.send(f'Result:\n**{title}**')

    @commands.command(name="trollVC", description="Play music with the bot")
    async def trollVC(self, ctx: commands.Context, channelID: int, *, action=None):
        if ctx.author.id != main.ownerID:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            await ctx.send("You are not authorized to run this command.")
            return
        channel = self.bot.get_channel(channelID)
        search = await textTools.mild_sanitize(await textTools.getResponse(ctx, "What is the song's search query?"))
        voice_channel = channel
        if not voice_channel:
            return await ctx.send(await errorFunctions.retrieveError(ctx))
        if not ctx.voice_client:
            await voice_channel.connect()

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"{search}", download=False)
            print('URL:   ' + info['url'])
            # try:
            #     info = info['entries'][0]
            # except Exception:
            #     await ctx.send(await errorFunctions.retrieveError(ctx))
            #     await ctx.send("This link is not valid.  Note that videos cannot link to a playlist, or be a video inside a playlist.")
            url = info['url']
            title = info['title']
            if action == "cursed":
                self.queue.append((url, title, FFMPEG_OPTIONS_CURSED))
            else:
                self.queue.append((url, title, FFMPEG_OPTIONS))
            await ctx.send(f'Added to queue: **{title}**')
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queue:
            url, title, ffoptions = self.queue.pop(0)
            source = await discord.FFmpegOpusAudio.from_probe(url, **ffoptions)
            source.read()
            ctx.voice_client.play(source, after=lambda _:self.bot.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'Now playing: **{title}**')
        if not ctx.voice_client.is_playing():
            await ctx.send("Queue is empty!")
            await ctx.voice_client.disconnect()

    @commands.command(name="skip", description="Skip the current track")
    async def skip(self, ctx: commands.Context):
        serverConfig = await adminFunctions.getServerConfig(ctx)
        if str(serverConfig["musicroleid"]) not in str(ctx.author.roles):
            if ctx.author.guild_permissions.administrator == False:
                await ctx.send(await errorFunctions.retrieveError(ctx))
                await ctx.send("You are not authorized to run this command.")
                return
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped!")

    @commands.command(name="playSong", description="Add a server to an ongoing campaign")
    async def playSong(self, ctx: commands.Context):
        voice_user = ctx.message.author.voice
        music_client = await voice_user.channel.connect(cls=MusicClient, reconnect=True, self_deaf=False)
        track = Track(source=WAVAudio('C:\\Users\\colson\\Music\\Never Gonna Give You Up slow.mp3'), name='This is audio')
        await music_client.play(track)



    @commands.command(name="playTest", description="Add a server to an ongoing campaign")
    async def playTest(self, ctx: commands.Context):
        # Gets voice channel of message author
        channel = None
        voice_channel = ctx.channel.id
        if voice_channel != None:
            channel = ctx.author.voice.channel
            vc = await channel.connect()
            vc.play(discord.FFmpegPCMAudio(executable="C:\\Users\\colson\\Downloads\\Faster-Whisper-XXL\\ffmpeg.exe", source="C:\\Users\\colson\\Music\\Never Gonna Give You Up slow.mp3"))
            # audio_source = discord.FFmpegPCMAudio(executable=ffmpeg, source="C:\\Users\\colson\\Music\\Rick Astley - Never Gonna Give You Up (Official Music Video)slow.mp3")
            # vc.play(audio_source)
            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()
        else:
            await ctx.send(str(ctx.author.name) + "is not in a channel.")
        # Delete command after the audio is done playing.
        await ctx.message.delete()
async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(VCfunctions(bot))