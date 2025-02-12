import shutil

import discord, os, platform, time, asyncio, requests, io, datetime
from pathlib import Path
from cogs.errorFunctions import errorFunctions
from discord.ext import commands
from discord import app_commands
from git import Repo

# Github config
from PIL import Image, ImageChops

from cogs.textTools import textTools
from cogs.SQLfunctions import SQLfunctions
from cogs.discordUIfunctions import discordUIfunctions
imageCategoryList = ["Featured", "Chalk", "Fictional Insignia", "Historical Insignia", "Inscriptions", "Labels", "Letters", "Miscellaneous", "Memes", "Numbers", "Optics", "Seams", "Symbols", "Textures", "Weathering", "Welding"]
GithubURL = "git@github.com:SprocketTools/SprocketTools.github.io.git"
username = 'SprocketTools'

if platform.system() == "Windows":

    GithubDirectory = "C:\\Users\\colson\\Documents\\GitHub\\SprocketTools.github.io"
    OSslashLine = "\\"

else:
    # default settings (running on Rasbian)
    GithubDirectory = "/home/mumblepi/Github/SprocketTools.github.io"
    OSslashLine = "/"
imgCatalogFolder = "img"
imgDisplayFolder = "imgbin"
Path(GithubDirectory).mkdir(parents=True, exist_ok=True)
try:
    Repo.clone_from(GithubURL, GithubDirectory)
except Exception:
    pass
operatingRepo = Repo(GithubDirectory)
origin = operatingRepo.remote('origin')
origin.fetch()
origin.pull(origin.refs[0].remote_head)

class githubTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="pullRepository", description="Reload the repository onto the Pi")
    async def pullRepository(self, ctx: commands.Context):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        operatingRepo = Repo(GithubDirectory)
        origin = operatingRepo.remote('origin')
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
        await ctx.reply("# Done!")

    @commands.command(name="resetImageCatalog", description="Reset the image catalog")
    async def resetImageCatalog(self, ctx: commands.Context):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        prompt = "DROP TABLE IF EXISTS imagecatalog"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS imagecatalog (
                                      name VARCHAR,
                                      tags VARCHAR,
                                      strippedname VARCHAR,
                                      approved VARCHAR,
                                      ownername VARCHAR,
                                      ownerid BIGINT,
                                      category VARCHAR);''')
        await SQLfunctions.databaseExecute(prompt)
        imageCatalogFilepath = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}"
        imageDisplayFilepath = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}"

        shutil.rmtree(imageCatalogFilepath)
        shutil.rmtree(imageDisplayFilepath)

        Path(imageCatalogFilepath).mkdir(parents=True, exist_ok=True)
        Path(imageDisplayFilepath).mkdir(parents=True, exist_ok=True)
        operatingRepo.index.add(f'{GithubDirectory}{OSslashLine}{"imgbin"}')
        operatingRepo.index.add(f'{GithubDirectory}{OSslashLine}{"img"}')
        await ctx.send("Done!")

    @commands.command(name="changeDecalAuthor", description="Submit a decal to the SprocketTools website")
    async def changeDecalAuthor(self, ctx):
        name = await textTools.getResponse(ctx, f"What is the title of the decal?")
        newAuthorID = await textTools.getIntResponse(ctx, f"What is the new author's ID?")
        author = self.bot.get_user(newAuthorID)
        authorName = await textTools.mild_sanitize(author.name)
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE imagecatalog SET ownerid = $1 WHERE name = $2''', [newAuthorID, name])
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE imagecatalog SET ownername = $1 WHERE name = $2''',[authorName, name])
        await ctx.send(f"### The image has been updated.")

    @commands.command(name="submitDecal", description="Submit a decal to the SprocketTools website")
    async def submitDecal(self, ctx):
        imageCategoryListTemp = imageCategoryList.copy()
        if ctx.author.id != 712509599135301673:
            imageCategoryListTemp.remove("Featured")
        if len(ctx.message.attachments) != 0:
            await ctx.send("Note: this command no longer looks for images attached to the command initiation itself.  You will need to upload the images again.")
        allAttachments = await textTools.getManyFilesResponse(ctx, "Process started.\nUpload up to 10 images that you wish to add to the SprocketTools decal catalog.")
        if len(allAttachments) == 0:
            await errorFunctions.sendError(ctx)
            return
        userPrompt = "What category should the image(s) go into?"
        category = await discordUIfunctions.getChoiceFromList(ctx, imageCategoryList, userPrompt)
        tags = await textTools.getCappedResponse(ctx, "Reply with a list of comma-separated tags to help with searching for these images.  Ex: `british, tonnage, tons`", 32)
        await ctx.send(f"Alright, let's get the names down for your images.")
        print(category)
        for attachment in allAttachments:
            if "image" in attachment.content_type:
                type = ".png"
                name = await textTools.getCappedResponse(ctx, f"What is the title of {attachment.filename}?  Limit the name to no more than 32 characters.", 32)
                name = name.lower()
                strippedname = name.replace(" ", "_")
                strippedname = f"{strippedname}{type}"
                strippedname = strippedname.lower()
                imageCatalogFilepath = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{strippedname}"
                if os.path.isfile(imageCatalogFilepath):
                    response = await errorFunctions.retrieveError(ctx)
                    await ctx.send(f"{response}\n\n{strippedname} already exists!  Submit this again, but with a different name.")
                else:
                    # Optimized image https://www.askpython.com/python-modules/compress-png-image-using-pillow
                    maxwidth = 400
                    response = requests.get(attachment.url)
                    imageBase = Image.open(io.BytesIO(response.content)).convert('RGBA')
                    width, height = imageBase.size
                    aspectratio = width / height
                    newheight = maxwidth / aspectratio
                    imageOut = imageBase.resize((maxwidth, round(newheight)))

                    # Saving the image
                    imageDisplayFilepath = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}{OSslashLine}{strippedname}"
                    imageOut.save(imageDisplayFilepath, optimize=True, quality=80)
                    imageBase.save(imageCatalogFilepath, optimize=True, quality=95)
                    operatingRepo.index.add(imageDisplayFilepath)
                    operatingRepo.index.add(imageCatalogFilepath)
                    # byte_io = io.BytesIO()
                    # imageOut.save(byte_io, format='PNG')
                    # byte_io.seek(0)
                    # file = discord.File(byte_io, filename=f'edited_image.png')
                    # await ctx.send(file=file)

                    values = [name, tags, strippedname, 'Pending', str(self.bot.get_user(ctx.author.id)), ctx.author.id, category]
                    await SQLfunctions.databaseExecuteDynamic(f'''INSERT INTO imagecatalog (name, tags, strippedname, approved, ownername, ownerid, category) VALUES ($1, $2, $3, $4, $5, $6, $7);''', values)
                    await ctx.send(f"### The image {strippedname} has been sent off for approval!")
                    channel = self.bot.get_channel(1152377925916688484)
                    await channel.send(f"<@{self.bot.owner_id}>\n**{name}** has been submitted by <@{ctx.author.id}> and is waiting for approval!")

    @commands.command(name="removeDecal", description="Remove a decal from the SprocketTools website")
    async def removeDecal(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await ctx.send(f"Reply with the stripped name of the decal you wish to remove.  Ex: `6_side_circle.png`")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=3000.0)
            delete = await textTools.sanitize(msg.content.lower())
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        try:
            values = [delete]
            imageCatalogFilepath = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{delete}"
            imageDisplayFilepath = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}{OSslashLine}{delete}"
            await SQLfunctions.databaseExecuteDynamic(f'''DELETE FROM imagecatalog WHERE strippedname = $1''', values)
            os.remove(imageCatalogFilepath)
            os.remove(imageDisplayFilepath)
            await ctx.send("Removed!")
            await githubTools.updateHTML(self, ctx)
        except Exception as out:
            await ctx.send(f"There appears to have been an error: \n{out}")

    @commands.command(name="processDecals", description="Submit a decal to the SprocketTools website")
    async def processDecals(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        try:
            while True:
                decalInfo = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM imagecatalog WHERE approved = 'Pending';''')][0]
                imageCatalogFilepath = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{decalInfo['strippedname']}"
                imageDisplayFilepath = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}{OSslashLine}{decalInfo['strippedname']}"
                await ctx.send(file=discord.File(imageCatalogFilepath))
                userPrompt = f"Do you want to approve this decal? \nName: {decalInfo['name']}\nFilename: {decalInfo['strippedname']}\nOwner: {decalInfo['ownername']} (<@{decalInfo['ownerid']}>)\nCategory: {decalInfo['category']}"
                responseList = ["Too inappropriate", "Invalid category", "Inadequate image quality", "Image descriptions are not consistent", "Rejection was requested by submitter", "Other", "No", "Override Name", "Override Category", "Yes"]
                answer = await discordUIfunctions.getChoiceFromList(ctx, responseList, userPrompt)
                if answer == "Yes":
                    values = [decalInfo['strippedname']]
                    await SQLfunctions.databaseExecuteDynamic(f'''UPDATE imagecatalog SET approved = 'True' WHERE strippedname = $1''', values)
                    recipient = self.bot.get_user(int(decalInfo['ownerid']))
                    await recipient.send(f'Your decal "{decalInfo["strippedname"]}" was approved!')
                    await ctx.send("## Approved!")
                    operatingRepo.index.add(imageCatalogFilepath)
                    operatingRepo.index.add(imageDisplayFilepath)
                elif answer == "Override Category":
                    userPrompt = f"Alright then, pick a new category to use with this decal."
                    values = [decalInfo['strippedname']]
                    newCategory = await discordUIfunctions.getChoiceFromList(ctx, imageCategoryList, userPrompt)
                    await SQLfunctions.databaseExecuteDynamic(f'''UPDATE imagecatalog SET approved = 'True' WHERE strippedname = $1''', values)
                    values = [newCategory, decalInfo['strippedname']]
                    await SQLfunctions.databaseExecuteDynamic(f'''UPDATE imagecatalog SET category = $1 WHERE strippedname = $2''', values)
                    recipient = self.bot.get_user(int(decalInfo['ownerid']))
                    await recipient.send(f'Your decal "{decalInfo["strippedname"]}" was approved!  \nNote: the category was changed to "{newCategory}."')
                    await ctx.send("## Approved! \n(with a category change)")
                    operatingRepo.index.add(imageCatalogFilepath)
                    operatingRepo.index.add(imageDisplayFilepath)
                elif answer == "Override Name":
                    await ctx.send(f"Alright then, pick a new name to use with this decal.")
                    values = [decalInfo['strippedname']]
                    def check(m: discord.Message):
                        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=3000.0)
                        newName = await textTools.sanitize(msg.content.lower())
                    except asyncio.TimeoutError:
                        await ctx.send("Operation cancelled.")
                        return
                    await SQLfunctions.databaseExecuteDynamic(f'''UPDATE imagecatalog SET approved = 'True' WHERE strippedname = $1''', values)
                    values = [newName, decalInfo['strippedname']]
                    await SQLfunctions.databaseExecuteDynamic(f'''UPDATE imagecatalog SET name = $1 WHERE strippedname = $2''', values)
                    recipient = self.bot.get_user(int(decalInfo['ownerid']))
                    await recipient.send(f'Your decal "{decalInfo["strippedname"]}" was approved!  \nNote: the image name was changed to "{newName}."')
                    await ctx.send("## Approved! \n(with a name change)")
                    operatingRepo.index.add(imageCatalogFilepath)
                    operatingRepo.index.add(imageDisplayFilepath)
                else:
                    values = [decalInfo['strippedname']]
                    await SQLfunctions.databaseExecuteDynamic(f'''DELETE FROM imagecatalog WHERE strippedname = $1''', values)
                    recipient = self.bot.get_user(int(decalInfo['ownerid']))
                    os.remove(imageCatalogFilepath)
                    os.remove(imageDisplayFilepath)
                    await recipient.send(f'Your decal "{decalInfo["strippedname"]}" was not approved.  Reason: {answer}')
                    await ctx.send(f"## Done!\nRejection letter was sent to <@{decalInfo['ownerid']}>")
        except Exception:
            await ctx.send("Looks like there are no more decals to approve!")
            result = await githubTools.updateHTML(self, ctx)
    async def updateHTML(self, ctx):
        HTMLending = '''	</ul></center></body><script>
		function copyText(inputText) {
			// Copy the text inside the text field
			navigator.clipboard.writeText(inputText);
		}	
        </script>
        </html>'''

        # Update all the main pages first
        for category in imageCategoryList:
            inText = category
            if category == "Featured":
                inText = "SprocketTools Decal Catalog"
            HTMLdoc = f'''<html>
                <head>
                    <title>{inText}</title>
                    <link rel="stylesheet" href="https://use.typekit.net/oov2wcw.css">
                    <link rel="icon" type="image/x-icon" href="SprocketToolsLogo.png">
                    <link rel="stylesheet" href="stylesV3.css">
                </head>
            <body>
            <div class="navbar">
            	<img src="SprocketToolsLogo.png"/>
                <a href="index.html">Home</a>
                <a href="TopGearCalculator.html">Gear Calculator</a>
                <a href="resources.html">Sprocket Guides</a>
                <a href="credits.html">Credits</a>
                <a href="https://www.youtube.com/watch?v=p7YXXieghto">Get Trolled</a>
                <a class="active" href="DecalsFeatured.html">Decal Catalog</a>
                <a href="DecalsRGBmaker.html">RGB Decal Maker</a>
            </div>
            <div class="container">
                <h1 class="text-center">{inText}</h1>
            </div>
            <div>
                <ul class="navbar">'''
            for subcategory in imageCategoryList:
                if subcategory == category:
                    appendation = f'''<li class="active" onclick="document.location='Decals{subcategory}.html'">{subcategory}</li>'''
                else:
                    appendation = f'''<li onclick="document.location='Decals{subcategory}.html'">{subcategory}</li>'''
                HTMLdoc = f'{HTMLdoc}{appendation}'
            if category == "Featured":
                HTMLdocmid = f'''<li onclick="document.location='DecalsContribute.html'">Contribute your own!</li>
                    </div>
                </div>
                <div class="wrap">
                    <div class="box">
                        <h2>Welcome to the biggest community collection of URL-embeddable decals!</h2> 
                        <h4>Click on a picture to copy its embeddable URL.</h4>
                        <h4>Then, select a decal in Sprocket Tank Design, and then paste the link into the URL field.</h4>
                        <h4>Your decals will now automatically download and apply wherever you share your tank!</h4>
                    </div>
                </div>
                <ul class="catalog">'''
            else:
                HTMLdocmid = f'''
                            <li onclick="document.location='DecalsContribute.html'">Contribute your own!</li>
                        </div>
                    </div>
                </div>
                <div class="wrap">
                    <div class="box">
                        <h4>Click on a picture to copy its embeddable URL.</h4>
                        <h4>Then, select a decal in Sprocket Tank Design, and then paste the link into the URL field.</h4>
                        <h4>Your decals will now automatically download and apply wherever you share your tank!</h4>
                    </div>
                </div>
                <ul class="catalog">'''
            HTMLdoc = f'{HTMLdoc}{HTMLdocmid}'
            decalList = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM imagecatalog WHERE approved = 'True' AND category = '{category}' ORDER BY name;''')]
            for decalInfo in decalList:
                print("Hi!")
                decalLI = f'''<li><img src="imgbin/{decalInfo['strippedname']}" onclick="copyText('https://sprockettools.github.io/img/{decalInfo['strippedname']}')"/>
                <h3>{decalInfo['name']}</h3>
                <h5>Uploaded by: {decalInfo['ownername']}</h5>'''
                HTMLdoc = f'{HTMLdoc}{decalLI}'
            HTMLdoc = HTMLdoc + HTMLending
            saveDirectory = f'{GithubDirectory}{OSslashLine}Decals{category}.html'
            print(saveDirectory)
            with open(saveDirectory, "w") as outfile:
                outfile.write(HTMLdoc)
            operatingRepo.index.add(saveDirectory)

        # specialized entry for the contribution directory
        HTMLdoccontribute = f'''<html>
                        <head>
                            <title>Contribute Decals</title>
                            <link rel="stylesheet" href="https://use.typekit.net/oov2wcw.css">
                            <link rel="icon" type="image/x-icon" href="SprocketToolsLogo.png">
                            <link rel="stylesheet" href="stylesV3.css">
                        </head>
                    <body>
                    <div class="navbar">
                        <a href="index.html">Home</a>
                        <a href="TopGearCalculator.html">Gear Calculator</a>
                        <a href="resources.html">Sprocket Guides</a>
                        <a href="credits.html">Credits</a>
                        <a href="https://www.youtube.com/watch?v=p7YXXieghto">Get Trolled</a>
                        <a class="active" href="DecalsFeatured.html">Decal Catalog</a>
                        <a href="DecalsRGBmaker.html">RGB Decal Maker</a>
                    </div>

                    <div>
                        <ul class="navbar">'''
        for subcategory in imageCategoryList:
            appendation = f'''<li onclick="document.location='Decals{subcategory}.html'">{subcategory}</li>'''
            HTMLdoccontribute = f'{HTMLdoccontribute}{appendation}'

        HTMLdoccontributemid = '''<li class="active" onclick="document.location='DecalsContribute.html'">Contribute your own!</li>
                            </div>
                        </div>
                        <div class="wrap">
                            <h1 class="text-center">Contributing Decals</h1>
                            <div class="box">
                                <h4>To contribute your own decals to the catalog, use the -submitDecal command in any discord server with Sprocket Bot.</h4> 
                                <h4>This includes the <a href="https://discord.gg/sprocket">Sprocket Official Discord</a>.</h4>
                                <h3>Decals need to meet the following criteria:</h3>   
                                <h5>- Files must be a .png</h5>
                                <h5>- Files should not exceed 1MB in size</h5>
                                <h5>- Decals need to be compliant with Discord TOS (no hateful symbols, NSFW, etc.)</h5>
                            </div>
                        </div>
                        </center></body></html>'''
        HTMLdoccontribute = f'{HTMLdoccontribute}{HTMLdoccontributemid}'
        saveDirectory = f'{GithubDirectory}{OSslashLine}DecalsContribute.html'
        print(saveDirectory)
        with open(saveDirectory, "w") as outfile:
            outfile.write(HTMLdoccontribute)
        operatingRepo.index.add(saveDirectory)
        await githubTools.updateActiveContests(self)
        await ctx.send("Done!")
        try:
            operatingRepo.git.add(update=True)
            operatingRepo.index.commit("Automated decal updating sequence")
            origin = operatingRepo.remote(name='origin')
            origin.push().raise_if_error()
            await ctx.send("Decals are now pushed to GitHub!")
        except:
            await ctx.send("Some error occurred pushing the decals to GitHub.")

    @commands.command(name="changeDecalCategory", description="change a decal category from the SprocketTools website")
    async def changeDecalCategory(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await ctx.send(f"Reply with the stripped name of the decal you wish to change.  Ex: `6_side_circle.png`")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=3000.0)
            decalName = await textTools.sanitize(msg.content.lower())
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return
        userPrompt = f"Alright then, pick a new category to use with this decal."
        newCategory = await discordUIfunctions.getChoiceFromList(ctx, imageCategoryList, userPrompt)
        values = [newCategory, decalName]
        await SQLfunctions.databaseExecuteDynamic(
            f'''UPDATE imagecatalog SET category = $1 WHERE strippedname = $2''', values)
        await ctx.send("## Config updated!")

    @commands.command(name="changeDecalName", description="change a decal name from the SprocketTools website")
    async def changeDecalName(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await ctx.send(f"Reply with the stripped name of the decal you wish to change.  Ex: `6_side_circle.png`")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=3000.0)
            decalName = await textTools.sanitize(msg.content.lower())
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return
        await ctx.send(f"Alright then, pick a new name to use with this decal.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=3000.0)
            newName = await textTools.sanitize(msg.content.lower())
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return
        values = [newName, decalName]
        await SQLfunctions.databaseExecuteDynamic(
            f'''UPDATE imagecatalog SET name = $1 WHERE strippedname = $2''', values)
        await ctx.send("## Config updated!")
    async def updateActiveContests(self):
        currentTime = int(time.time())
        contests = [dict(row) for row in await SQLfunctions.databaseFetch(f'''SELECT * FROM contests WHERE starttimestamp < '{currentTime}' AND endtimestamp > '{currentTime}' AND crossServer = 'True';''')]
        startHTML = '''
        <html>
        <head>
            <title>Code of Conduct</title>
            <link rel="stylesheet" href="https://use.typekit.net/oov2wcw.css">
            <link rel="icon" type="image/x-icon" href="SprocketToolsLogo.png">
            <link rel="stylesheet" href="styles_testing.css">
            <style>
            </style> 
        </head>
        <body>
            <div class="navbar">
            <a href="index.html">Home</a>
            <a href="TopGearCalculator.html">Gear Calculator</a>
            <a  class="active" href="ContestsList.html">Contests</a>
            <a href="VehicleGenerator.html">Random Tank Picker</a>
            <a href="resources.html">Guides</a>
            <a href="credits.html">Credits</a>
            <a href="https://www.youtube.com/watch?v=p7YXXieghto">Get Trolled</a>
            <a href="DecalsFeatured.html">Decal Catalog</a>
            <a href="DecalsRGBmaker.html">RGB Decal Maker</a>
        </div>
        <div class="container">
            <center>
            <div>
                <ul class="decal-menu">
                    <li class="active" onclick="document.location='ContestsList.html'">Active Contests</li>
                    <li onclick="document.location='CodeOfConduct.html'">Code of Conduct</li>
                    <li onclick="document.location='ContestTankPicker.html'">Contest Tank Picker</li>
                </ul>
            </div>
            </center>
            
            <br />
            <h1 class="text-center">
                Community Contests
            </h1 class="text-center"> 
            <ul class="contest-list">
        '''

        for contestInfo in contests:
            serverID = self.bot.get_guild(int(contestInfo["serverid"]))
            channel = serverID.text_channels[0]
            print(channel)
            link = await channel.create_invite(max_age=90)
            date_time = datetime.datetime.fromtimestamp(int(contestInfo["endtimestamp"]))
            appendices = f'''
			<li>
				<h2>{contestInfo["name"]}</h2>
				<h4 style="color: red">Until: {date_time.strftime("%D at %H:%M (UTC)")}</h4>
				<h4>{contestInfo["description"]}</h4>
				<h5 onclick="document.location='{contestInfo["ruleslink"]}'">Contest Rules</h5>
				<h5 onclick="document.location='{link}'">Discord Server</h5>
			</li>
            '''
            startHTML = f'{startHTML}{appendices}'
        endHTML = '''</ul>
                </div>
            </body>
        </html>'''
        startHTML = f'{startHTML}{endHTML}'
        saveDirectory = f'{GithubDirectory}{OSslashLine}ContestsList.html'
        print(saveDirectory)
        with open(saveDirectory, "w") as outfile:
            outfile.write(startHTML)
        operatingRepo.index.add(saveDirectory)



async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(githubTools(bot))
