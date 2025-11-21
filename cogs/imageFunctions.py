import random

import discord, asyncio, requests, io
from discord.ext import commands
import platform

from PIL import Image, ImageChops
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
        baseImages = []
        serverID = (ctx.guild.id)

        try:
            channel = int([dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT commandschannelid FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
                await ctx.send(f"Utility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
                return
        for item in attachments:
            # Brave AI actually works fairly decent
            if int(item.size) > 20000000:
                errorText = await self.bot.error.retrieveError(ctx)
                await ctx.send(
                    f"{errorText}\n\n{item.filename} is bigger than 20MB.  Please optimize this image a bit more to avoid issues when trying to use the decal.")
                return

            if int(item.size) > 8000000:
                errorText = await self.bot.error.retrieveError(ctx)
                await ctx.send(
                    f"{errorText}\n\n{item.filename} is bigger than 8MB.  I may be unable to reply with the image due to Discord filesize limitations.")
                return

            response = requests.get(item.url)
            imageBase = Image.open(io.BytesIO(response.content)).convert('RGBA')
            baseImages.append(imageBase)
        while True:
            await ctx.send("How do you want to weather your decal?")
            imageInput = await self.bot.ui.getButtonChoice(ctx, ["light scratches", "heavy scratches", "centerline wear", "water runoff", "dirt splotches", "mud stains", "custom", "done"])
            if imageInput == 'light scratches':
                imageLink = 'https://sprockettools.github.io/img/black_scratches_1.png'
            elif imageInput == 'heavy scratches':
                imageLink = 'https://sprockettools.github.io/img/white_scratches_2.png'
            elif imageInput == 'centerline wear':
                imageLink = 'https://sprockettools.github.io/textures/Rusty_Metal.png'
            elif imageInput == 'water runoff':
                imageLink = 'https://sprockettools.github.io/img/stain02.png'
            elif imageInput == 'mud stains':
                imageLink = 'https://sprockettools.github.io/img/grey_scratches_2.png'
            elif imageInput == 'dirt splotches':
                imageLink = 'https://sprockettools.github.io/img/weathering_overlay_alternative.png'
            elif imageInput == 'custom':
                urlgram = await ctx.send(
                    "Send the url to your modifier image (either from https://sprockettools.github.io or Imgur)")
                if "https://i.imgur.com" in imageInput or "https://sprockettools.github.io/" in imageInput:
                    imageLink = imageInput
                else:
                    await ctx.send("Invalid URL.  Reverting to default pattern...")
                    imageLink = 'https://sprockettools.github.io/img/white_scratches_2.png'
            else:
                return

            await ctx.send("Beginning processing now.  This may take some time.")
            newImages = []
            for imageBase in baseImages:

                response2 = requests.get(imageLink)
                imageModIn = Image.open(io.BytesIO(response2.content)).convert('RGBA')
                imageBaseWidth, imageBaseHeight = imageBase.size
                imageMod = imageModIn.resize((imageBaseWidth, imageBaseHeight), resample=Image.LANCZOS)
                imageMod = imageMod.convert("RGBA")
                imageBaseR, imageBaseG,imageBaseB,imageBaseA = imageBase.split()
                imageModA = imageMod.split()[3]

                original_size = imageModA.size
                width, height = original_size
                left = int(width * 0.05)
                top = int(height * 0.05)
                right = int(width * 0.95)
                bottom = int(height * 0.95)
                crop_box = (left, top, right, bottom)
                center_part = imageModA.crop(crop_box)
                stretched_alpha_mask = center_part.resize(original_size, resample=Image.LANCZOS)

                newAlpha = ImageChops.subtract(imageBaseA, stretched_alpha_mask)
                imageOut = Image.merge("RGBA", (imageBaseR, imageBaseG, imageBaseB, newAlpha))

                byte_io = io.BytesIO()
                imageOut.save(byte_io, format='PNG')
                byte_io.seek(0)
                file = discord.File(byte_io, filename=f'edited_image.png')
                await ctx.send(file=file)
                newImages.append(imageOut)
            baseImages = newImages







async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(imageTools(bot))