import random

import discord, asyncio, requests, io, base64
from discord.ext import commands
from cogs.errorFunctions import errorFunctions
import asyncpg, platform

from discord import app_commands
from cogs.discordUIfunctions import discordUIfunctions
from pathlib import Path
from PIL import Image, ImageChops
from cogs.textTools import textTools
from main import SQLfunctions
imageCategoryList = ["chalk inscriptions", "inscriptions", "labels", "letters", "memes", "numbers", "optics", "welding", "textures", "weathering"]

if platform.system() == "Windows":
    GithubURL = "https://github.com/SprocketTools/SprocketTools.github.io"
    GithubDirectory = "C:\\Users\\colson\\Documents\\GitHub\\Testing\\SprocketTools.github.io"
    OSslashLine = "\\"

else:
    # default settings (running on Rasbian)
    GithubURL = "https://github.com/SprocketTools/SprocketTools.github.io"
    GithubDirectory = "/home/mumblepi/SprocketTools.github.io"
    OSslashLine = "/"
imgCatalogFolder = "img"
imgCandidateFolder = "imgbin"

class imageTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @commands.hybrid_command(name="weather", description="Weather a picture.  Must be a .png")
    async def weather(self, ctx: commands.Context):
        if random.random() < 0.001:
            imageLink = "https://sprockettools.github.io/inscriptions/SprocketBotLogoOutlineTransparent.png"
        else:
            imageLink = "https://sprockettools.github.io/textures/Scratch.png"
        attachments = ctx.message.attachments
        serverID = (ctx.guild.id)

        try:
            channel = int([dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT commandschannelid FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
                await ctx.send(f"Utility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
                return

        await ctx.send("Send the url to your modifier image (either from sprockettools.github.io or Imgur), or reply with one of the following: `default preset`, `decal preset`, `dirt preset`, `vertical preset`, `seam preset`.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=200.0)
            imageInput = str(msg.content).lower()
            if imageInput == 'decal preset':
                imageLink = 'https://sprockettools.github.io/textures/Scratch.png'
            if imageInput == 'vertical preset':
                imageLink = 'https://sprockettools.github.io/textures/Rusty_Metal.png'
            if imageInput == 'seam preset':
                imageLink = 'https://sprockettools.github.io/textures/Rusty_Metal_2.png'
            if imageInput == 'dirt preset':
                imageLink = 'https://sprockettools.github.io/img/weathering_overlay_alternative.png'
            else:
                if "https://i.imgur.com" in imageInput or "https://sprockettools.github.io/" in imageInput:
                    imageLink = imageInput


        except asyncio.TimeoutError:
            await ctx.reply("Weather command timed out.")
            return
        await ctx.send("Beginning processing now.  This may take some time.")

        for item in attachments:
            # Brave AI actually works fairly decent
            if int(item.size) > 25000000:
                errorText = await errorFunctions.retrieveError(ctx)
                await ctx.send(f"{errorText}\n\n{item.filename} is bigger than 25MB.  Please optimize this image a bit more to avoid issues when trying to use the decal.")
                return

            response = requests.get(item.url)
            imageBase = Image.open(io.BytesIO(response.content)).convert('RGBA')
            response2 = requests.get(imageLink)
            imageModIn = Image.open(io.BytesIO(response2.content)).convert('RGBA')
            imageBaseWidth, imageBaseHeight = imageBase.size
            imageMod = imageModIn.resize((imageBaseWidth, imageBaseHeight), resample=Image.LANCZOS)
            imageMod = imageMod.convert("RGBA")
            imageBaseR, imageBaseG,imageBaseB,imageBaseA = imageBase.split()
            imageModA = imageMod.split()[3]

            newAlpha = ImageChops.subtract(imageBaseA, imageModA)
            imageOut = Image.merge("RGBA", (imageBaseR, imageBaseG, imageBaseB, newAlpha))

            byte_io = io.BytesIO()
            imageOut.save(byte_io, format='PNG')
            byte_io.seek(0)
            file = discord.File(byte_io, filename=f'edited_image.png')
            await ctx.send(file=file)







async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(imageTools(bot))