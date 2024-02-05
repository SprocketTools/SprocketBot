import discord, asyncio, requests, io, base64
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageChops
class imageTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @commands.command(name="weather", description="Weather a picture.  Must be a .png")
    async def weather(self, ctx: commands.Context):
        imageLink = "https://sprockettools.github.io/textures/Scratched_Metal_2.png"
        attachments = ctx.message.attachments

        await ctx.send("Send the url to your modifier image (either from sprockettools.github.io or Imgur), or say 'default' to use the standard modifier.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=90.0)
            imageInput = str(msg.content)
            if imageInput.lower() == "default":
                pass
            else:
                if "https://i.imgur.com/9SAQYUm.png" in imageInput or "https://sprockettools.github.io/" in imageInput:
                    imageLink = imageInput
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return
        await ctx.send("Beginning processing now.  This will take some time.")
        for item in attachments:
            # Brave AI actually works fairly decent
            if int(item.size) > 3000000:
                await ctx.send(f"Error: {item.filename} is too big!")

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