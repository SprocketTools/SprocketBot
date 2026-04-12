import random
import aiohttp
import discord, asyncio, requests, io
from discord.ext import commands
import platform
import type_hints
from PIL import Image, ImageChops, ImageDraw, ImageOps

import os
import asyncio
import io
import math
import subprocess
import discord
from PIL import Image
from discord.ext import commands
from typing import Literal, Union
import re
#import demjson3
import type_hints

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
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.WELCOME_GIF_PATH = os.path.join("assets", "jumpscare_background.gif")

    @commands.hybrid_command(name="weather", description="Weather a picture.  Must be a .png", extras={'category': 'utility'})
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

    # --- NEW COMMAND: Avatar Welcome ---
    @commands.command(name="jumpscare", description="Replies with a welcome GIF, fading in your avatar.")
    async def avatar_fade_command(self, ctx: commands.Context, memberin: discord.Member, channelout: discord.TextChannel):
        author_id = memberin.id
        avatar_url = memberin.display_avatar.url

        # --- FIX: Use Absolute Paths to prevent Windows confusion ---
        cwd = os.getcwd()
        temp_avatar_name = os.path.abspath(os.path.join(cwd, f"temp_avatar_{author_id}.png"))
        temp_output_name = os.path.abspath(os.path.join(cwd, f"final_output_{author_id}.gif"))
        background_path = os.path.abspath(self.WELCOME_GIF_PATH)
        shadow_path = os.path.abspath(os.path.join(cwd, "assets", "black_circle.png"))

        try:
            await ctx.send("Generating your customized welcome...")

            # Download Avatar
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    if resp.status != 200: return await ctx.send("Failed to download avatar.")
                    avatar_bytes = await resp.read()

            avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

            # 1. Force the image into a perfect square (512x512 is a good base)
            size = (280, 280)
            avatar_img = ImageOps.fit(avatar_img, size, Image.LANCZOS)

            # 2. Create a circular mask
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)

            # 3. Apply the mask as the Alpha channel
            avatar_img.putalpha(mask)

            # 4. Save the "Circle Version" to the temp file
            avatar_img.save(temp_avatar_name)

            if not os.path.exists(shadow_path):
                return await ctx.send("Error: 'assets/shadow.png' is missing!")

            # Build the filter
            ffmpeg_filter = self._build_fade_overlay_filter()

            # --- FIX: Removed -loop to prevent 'Option not found' errors ---
            # We now handle the loop inside the filter_complex instead
            cmd = [
                'ffmpeg',
                '-threads', '0',
                '-i', background_path,
                '-i', temp_avatar_name,
                '-i', shadow_path,
                '-filter_complex', ffmpeg_filter,
                '-fps_mode', 'passthrough',  # Keeps the original background FPS
                '-y', temp_output_name
            ]

            process = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)

            if process.returncode != 0:
                print(f"FFmpeg Error: {process.stderr}")
                return await ctx.send("FFmpeg failed to process the GIF.")

            await channelout.send(file=discord.File(temp_output_name, filename=f'jumpscare_{memberin.name}.gif'))

        finally:
            # Cleanup
            for f in [temp_avatar_name, temp_output_name]:
                if os.path.exists(f): os.remove(f)

    @staticmethod
    def _build_fade_overlay_filter() -> str:
        """
        High-Quality / Low-Resource Hybrid:
        - Internal loops for PNGs.
        - High-quality scaling (Lanczos).
        - Targeted PaletteGen (only scans the first 3s for perfect colors).
        - Smooth dithering (sierra2_4a) for the fade.
        """
        av_x, av_y = "55", "60"
        sh_x, sh_y = "35", "400"

        filter_str = (
            # Step A: Loop and Prep Avatar
            f"[1:v]loop=loop=-1:size=1:start=0,format=rgba,scale=280:280:flags=lanczos,fade=t=in:st=1.0:d=1.0:alpha=1[av_f];"

            # Step B: Loop and Prep Shadow
            f"[2:v]loop=loop=-1:size=1:start=0,format=rgba,scale=320:60:flags=lanczos,colorchannelmixer=aa=0.2,"
            f"fade=t=in:st=1.0:d=1.0:alpha=1[sh_f];"

            # Step C: Overlays
            f"[0:v][sh_f]overlay=x={sh_x}:y={sh_y}:shortest=1[bg_s];"
            f"[bg_s][av_f]overlay=x={av_x}:y={av_y}:shortest=1[v_c];"

            # Step D: Smart Palette (The Quality Fix)
            # trim=end=3 ensures it only spends CPU analyzing the intro fade
            f"[v_c]split[p_i][p_a];"
            f"[p_i]trim=end=3,palettegen=stats_mode=full:max_colors=256[pal];"
            f"[p_a][pal]paletteuse=dither=sierra2_4a:diff_mode=rectangle"
        )
        return filter_str




async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(imageTools(bot))