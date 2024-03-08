import discord, asyncio, requests, io, base64
from discord.ext import commands
from main import SQLsettings
import asyncpg, platform

from discord import app_commands
from cogs.discordUIfunctions import discordUIfunctions
from pathlib import Path
from PIL import Image, ImageChops
from cogs.textTools import textTools
from cogs.SQLfunctions import SQLfunctions
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
    @commands.command(name="weather", description="Weather a picture.  Must be a .png")
    async def weather(self, ctx: commands.Context):
        imageLink = "https://sprockettools.github.io/textures/Scratch.png"
        attachments = ctx.message.attachments
        serverID = (ctx.guild.id)
        try:
            channel = int([dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
                await ctx.send(f"Utility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
                return

        await ctx.send("Send the url to your modifier image (either from sprockettools.github.io or Imgur), or say 'default' to use the standard modifier.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=90.0)
            imageInput = str(msg.content)
            if imageInput.lower() == "default":
                pass
            else:
                if "https://i.imgur.com" in imageInput or "https://sprockettools.github.io/" in imageInput:
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

    @commands.command(name="resetImageCatalog", description="Reset the image catalog")
    async def resetImageCatalog(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = "DROP TABLE IF EXISTS imagecatalog"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS imagecatalog (
                                  name VARCHAR, 
                                  strippedname VARCHAR,
                                  approved BOOL,
                                  ownername VARCHAR,
                                  category VARCHAR);''')
        await SQLfunctions.databaseExecute(prompt)
        imageCandidateFilepath = f"{GithubDirectory}{OSslashLine}{imgCandidateFolder}"
        Path(imageCandidateFilepath).mkdir(parents=True, exist_ok=True)
        imageCatalogFilepath = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}"
        Path(imageCatalogFilepath).mkdir(parents=True, exist_ok=True)
        await ctx.send("Done!")
    @commands.command(name="submitDecal", description="Submit a decal to the SprocketTools website")
    async def submitDecal(self, ctx):
        for attachment in ctx.message.attachments:
            if "image" in attachment.content_type:
                type = ".png"
                await ctx.send(f"What is the title of {attachment.filename}?  Limit the name to no more than 32 characters.")
                def check(m: discord.Message):
                    return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=3000.0)
                    name = await textTools.sanitize(msg.content.lower())
                except asyncio.TimeoutError:
                    await ctx.send("Operation cancelled.")
                    return

                userPrompt = "What category should the image go into?"
                category = await discordUIfunctions.getChoiceFromList(ctx, imageCategoryList, userPrompt)
                print(category)
                name = ('%.32s' % name)


                strippedname = name.replace(" ", "_")
                strippedname = f"{strippedname}{type}"
                imageCandidateFilepath = f"{GithubDirectory}{OSslashLine}{imgCandidateFolder}{OSslashLine}{strippedname}"
                print(name)
                print(strippedname)

                pic = Image.open(await attachment.read())
                pic = pic.save(imageCandidateFilepath)

                await SQLfunctions.databaseExecute(f'''INSERT INTO imagecatalog (name, strippedname, approved, ownername, category) VALUES ('{name}','{strippedname}','False', '{self.bot.get_user(ctx.author.id)}','{category}'); ''')
                await ctx.send(f"The {name} has been sent off for approval!")







async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(imageTools(bot))