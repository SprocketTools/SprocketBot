import shutil
import urllib.parse
import discord, os, platform, time, asyncio, requests, io, datetime
from pathlib import Path
import type_hints
from discord.ext import commands
from git import Repo
# Github config
from PIL import Image
import main
from cogs.textTools import textTools
## dev test
import git

try:
    repo = git.Repo("/home/mumblepi/Github/SprocketTools.github.io")
    origin = repo.remotes.origin
    try:
        origin.fetch('--verbose')
    except Exception:
        pass
    print("Git fetch successful from python!")
except git.exc.GitCommandError as e:
    print(f"Git fetch error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

imageCategoryList = ["Featured", "Anime", "Chalk", "Fictional Insignia", "Flags", "Historical Insignia", "Inscriptions", "Labels",
                     "Letters", "Miscellaneous", "Memes", "Numbers", "Optics", "Seams", "Symbols", "Textures",
                     "Weathering", "Welding"]
paintCategoryList = ["Featured", "WWI", "WWII", "Cold War", "Modern", "Fictional", "Memes", "Other"]
# GithubURL = "git@github.com:SprocketTools/SprocketTools.github.io.git"
username = 'SprocketTools'
password = main.githubPAT
encoded_password = urllib.parse.quote(password)
GithubURL = f"https://{username}:{encoded_password}@github.com/SprocketTools/SprocketTools.github.io.git"
if platform.system() == "Windows":
    GithubDirectory = "C:\\Users\\colson\\Documents\\GitHub\\SprocketTools.github.io"
    OSslashLine = "\\"
else:
    # default settings (running on Rasbian)
    GithubDirectory = "/home/mumblepi/Github/SprocketTools.github.io"
    OSslashLine = "/"
print(GithubDirectory)
imgCatalogFolder = "img"
imgDisplayFolder = "imgbin"
Path(GithubDirectory).mkdir(parents=True, exist_ok=True)
operatingRepo = Repo(GithubDirectory)
try:
    Repo.clone_from(GithubURL, GithubDirectory)
    origin = operatingRepo.remote('origin')
    origin.fetch('--verbose')
except git.exc.GitCommandError as e:
    print(f"Git fetch error: {e}")
except git.exc.InvalidGitRepositoryError as e:
    print(f"Invalid Git Repo error: {e}")
except Exception as e:
    print(f"An unexpected error occured: {e}")


class githubTools(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.command(name="pullRepository", description="Reload the repository onto the Pi")
    async def pullRepository(self, ctx: commands.Context):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        operatingRepo = Repo(GithubDirectory)
        origin = operatingRepo.remote('origin')
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
        await ctx.reply("# Done!")

    @commands.command(name="pullRepository", description="Reload the repository onto the Pi")
    async def pullRepository(self, ctx: commands.Context):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        operatingRepo = Repo(GithubDirectory)
        origin = operatingRepo.remote('origin')
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
        await ctx.reply("# Done!")

    @commands.command(name="resetImageCatalog", description="Reset the image catalog")
    async def resetImageCatalog(self, ctx: commands.Context):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        prompt = "DROP TABLE IF EXISTS imagecatalog"
        await self.bot.sql.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS imagecatalog (
                                      name VARCHAR,
                                      tags VARCHAR,
                                      strippedname VARCHAR,
                                      approved VARCHAR,
                                      ownername VARCHAR,
                                      ownerid BIGINT,
                                      category VARCHAR,
                                      type VARCHAR);''')
        await self.bot.sql.databaseExecute(prompt)
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
        await self.bot.sql.databaseExecuteDynamic(f'''UPDATE imagecatalog SET ownerid = $1 WHERE name = $2''',
                                                  [newAuthorID, name])
        await self.bot.sql.databaseExecuteDynamic(f'''UPDATE imagecatalog SET ownername = $1 WHERE name = $2''',
                                                  [authorName, name])
        await ctx.send(f"### The image has been updated.")

    @commands.command(name="submitDecal", description="Submit a decal to the SprocketTools website", extras={'category': 'utility'})
    async def submitDecal(self, ctx):
        imageCategoryListTemp = imageCategoryList.copy()
        if ctx.author.id != 712509599135301673:
            imageCategoryListTemp.remove("Featured")
        if len(ctx.message.attachments) != 0:
            await ctx.send(
                "Note: this command no longer looks for images attached to the command initiation itself.  You will need to upload the images again.")
        allAttachments = await textTools.getManyFilesResponse(ctx,
                                                              "## Process started!\nUpload up to 10 images that you wish to add to the SprocketTools decal or paint catalog.")
        if len(allAttachments) == 0:
            await self.bot.error.sendError(ctx)
            return
        await ctx.send("Are you submitting decal(s) or paint(s)?")
        itemType = await ctx.bot.ui.getButtonChoice(ctx, ["decal", "paint"])
        if itemType == "paint":
            imageCategoryListIn = paintCategoryList
        else:
            imageCategoryListIn = imageCategoryList

        userPrompt = "What category should the image(s) go into?"
        category = await ctx.bot.ui.getChoiceFromList(ctx, imageCategoryListIn, userPrompt)
        tags = await textTools.getCappedResponse(ctx,
                                                 "Reply with a list of comma-separated tags to help with searching for these images.  Ex: `british, tonnage, tons`",
                                                 32)
        await ctx.send(f'''Got it!\n\n Next, let's get the names down for your images.  These are the titles that users will see when browsing the catalog.\n- Stick to a lower case format with spaces "like this" for the names.\n- Avoid using punctuation.''')

        print(category)
        operatingRepo = Repo(GithubDirectory)
        origin = operatingRepo.remote('origin')
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
        for attachment in allAttachments:
            if "image" in attachment.content_type:
                type = ".png"
                name = await textTools.getCappedResponse(ctx,
                                                         f"What is the title of {attachment.filename}?  Limit the name to no more than 32 characters.\nName your decals in lower case and include spaces, like this: `roca 10th field army`",
                                                         32)
                name = name.lower()
                strippedname = name.replace(" ", "_")
                strippedname = f"{strippedname}{type}"
                strippedname = strippedname.lower()
                imageCatalogFilepath = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{strippedname}"
                if os.path.isfile(imageCatalogFilepath):
                    response = await self.bot.error.retrieveError(ctx)
                    await ctx.send(
                        f"{response}\n\n{strippedname} already exists!  Submit this again, but with a different name.")
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

                    values = [name, tags, strippedname, 'Pending', str(self.bot.get_user(ctx.author.id)), ctx.author.id,
                              category, itemType]
                    await self.bot.sql.databaseExecuteDynamic(
                        f'''INSERT INTO imagecatalog (name, tags, strippedname, approved, ownername, ownerid, category, type) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);''',
                        values)
                    await ctx.send(f"### The image {strippedname} has been sent off for approval!")
                    channel = self.bot.get_channel(1152377925916688484)
                    await channel.send(
                        f"<@{main.ownerID}>\n**{name}** has been submitted by <@{ctx.author.id}> and is waiting for approval!")

    @commands.command(name="fixInvalidDecalFilenames",
                      description="Automatically finds and fixes decal filenames with invalid characters (e.g., colons).")
    async def fixInvalidDecalFilenames(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return

        await ctx.send("Starting bulk-fix process... Searching for decals with invalid filenames (':')...")

        try:
            # Find all decals with a colon in the strippedname
            invalid_decals = [dict(row) for row in await self.bot.sql.databaseFetch(
                f'''SELECT strippedname FROM imagecatalog WHERE strippedname LIKE '%:%';'''
            )]
        except Exception as e:
            await ctx.send(f"An error occurred while querying the database: ```{e}```")
            return

        if not invalid_decals:
            await ctx.send("No decals with invalid names were found. All good!")
            return

        await ctx.send(f"Found {len(invalid_decals)} decals to fix. Beginning operations...")

        fixed_count = 0
        skipped_count = 0
        error_count = 0
        errors = []

        for decal in invalid_decals:
            old_stripped_name = decal['strippedname']
            new_stripped_name = old_stripped_name.replace(":", "_")

            # Define all file paths
            old_catalog_path = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{old_stripped_name}"
            old_display_path = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}{OSslashLine}{old_stripped_name}"
            new_catalog_path = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{new_stripped_name}"
            new_display_path = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}{OSslashLine}{new_stripped_name}"

            try:
                # --- Pre-Checks ---
                if not os.path.isfile(old_catalog_path) or not os.path.isfile(old_display_path):
                    errors.append(f"File missing: `{old_stripped_name}` (DB entry exists but file not found on disk).")
                    error_count += 1
                    continue

                if os.path.isfile(new_catalog_path) or os.path.isfile(new_display_path):
                    errors.append(f"Skipped (Conflict): `{new_stripped_name}` already exists. Manual check required.")
                    skipped_count += 1
                    continue

                # --- Execute ---
                # 1. Rename files on disk
                os.rename(old_catalog_path, new_catalog_path)
                os.rename(old_display_path, new_display_path)

                # 2. Update the SQL database
                await self.bot.sql.databaseExecuteDynamic(
                    f'''UPDATE imagecatalog SET strippedname = $1 WHERE strippedname = $2''',
                    [new_stripped_name, old_stripped_name]
                )

                # 3. Stage the new files in Git (old files will be staged as "deleted" by updateHTML)
                operatingRepo.index.add([new_catalog_path, new_display_path])

                fixed_count += 1

            except Exception as e:
                errors.append(f"Error on `{old_stripped_name}`: {e}")
                error_count += 1

        await ctx.send(f"File operations complete. Processed {len(invalid_decals)} records.\n"
                       f"✅ **Fixed:** {fixed_count}\n"
                       f"⚠️ **Skipped (Conflict):** {skipped_count}\n"
                       f"❌ **Errors:** {error_count}")

        if errors:
            # Send errors in a follow-up message if there are any
            error_message = "Errors and Skipped Logs:\n- " + "\n- ".join(errors)
            if len(error_message) > 2000:
                await ctx.send(error_message[:1990] + "\n... (truncated)")
            else:
                await ctx.send(error_message)

        if fixed_count > 0:
            await ctx.send("Changes were made. Running HTML update and pushing all changes to GitHub...")
            try:
                await githubTools.updateHTML(self, ctx)
                await ctx.send("Bulk fix complete. All changes have been pushed to GitHub.")
            except Exception as e:
                await ctx.send(f"An error occurred during the final `updateHTML` and push: ```{e}```")
        else:
            await ctx.send("No changes were made to the files, so no GitHub push was required.")

    @commands.command(name="decalLeaderboard", description="Leaderboard of decals!", extras={'category': 'utility'})
    async def decalLeaderboard(self, ctx: commands.Context):
        print("ASE")
        totalErrors = len(await self.bot.sql.databaseFetchdict(f'SELECT strippedname FROM imagecatalog;'))
        embed = discord.Embed(title="Decal & Paint Leaderboard", description=f'''There are {totalErrors} decals and paint jobs in the bot's collection!''',color=discord.Color.random())
        userSetList = await self.bot.sql.databaseFetchdict(f'''SELECT ownerid, COUNT(ownerid) AS value_occurrence FROM imagecatalog GROUP BY ownerid ORDER BY value_occurrence DESC LIMIT 10;''')
        for user in userSetList:
            embed.add_field(name=self.bot.get_user(user['ownerid']), value=user['value_occurrence'], inline=False)
        currentUser = (await self.bot.sql.databaseFetchdictDynamic(f'''SELECT ownerid, COUNT(ownerid) AS value_occ FROM imagecatalog WHERE ownerid = $1 GROUP BY ownerid;''', [ctx.author.id]))[0]['value_occ']
        print(currentUser)
        embed.set_footer(text=f"You have {currentUser} images registered with the bot!")
        await ctx.send(embed=embed)

    @commands.command(name="removeDecal", description="Remove a decal from the SprocketTools website")
    async def removeDecal(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
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
            await self.bot.sql.databaseExecuteDynamic(f'''DELETE FROM imagecatalog WHERE strippedname = $1''', values)
            os.remove(imageCatalogFilepath)
            os.remove(imageDisplayFilepath)
            await ctx.send("Removed!")
            await githubTools.updateHTML(self, ctx)
        except Exception as out:
            await ctx.send(f"There appears to have been an error: \n{out}")

    @commands.command(name="processDecals", description="Submit a decal to the SprocketTools website")
    async def processDecals(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        try:
            while True:
                decalInfo = [dict(row) for row in await self.bot.sql.databaseFetch(
                    f'''SELECT * FROM imagecatalog WHERE approved = 'Pending';''')][0]
                imageCatalogFilepath = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{decalInfo['strippedname']}"
                imageDisplayFilepath = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}{OSslashLine}{decalInfo['strippedname']}"
                await ctx.send(file=discord.File(imageCatalogFilepath))
                userPrompt = f"Do you want to approve this {decalInfo['type']}? \nName: {decalInfo['name']}\nFilename: {decalInfo['strippedname']}\nOwner: {decalInfo['ownername']} (<@{decalInfo['ownerid']}>)\nCategory: {decalInfo['category']}"
                responseList = ["Too inappropriate", "Invalid category", "Inadequate image quality",
                                "Image descriptions are not consistent", "Rejection was requested by submitter",
                                "Other", "No", "Override Name", "Override Category", "Yes"]
                answer = await ctx.bot.ui.getChoiceFromList(ctx, responseList, userPrompt)
                if answer == "Yes":
                    values = [decalInfo['strippedname']]
                    await self.bot.sql.databaseExecuteDynamic(
                        f'''UPDATE imagecatalog SET approved = 'True' WHERE strippedname = $1''', values)
                    recipient = self.bot.get_user(int(decalInfo['ownerid']))
                    await recipient.send(f'Your decal "{decalInfo["strippedname"]}" was approved!\nExpect the decal to appear on https://sprockettools.github.io in 3-5 minutes.')
                    await ctx.send("## Approved!")
                    operatingRepo.index.add(imageCatalogFilepath)
                    operatingRepo.index.add(imageDisplayFilepath)
                elif answer == "Override Category":
                    userPrompt = f"Alright then, pick a new category to use with this {decalInfo['type']}."
                    values = [decalInfo['strippedname']]
                    if decalInfo["type"] == "paint":
                        newCategory = await ctx.bot.ui.getChoiceFromList(ctx, paintCategoryList, userPrompt)
                    else:
                        newCategory = await ctx.bot.ui.getChoiceFromList(ctx, imageCategoryList, userPrompt)
                    await self.bot.sql.databaseExecuteDynamic(
                        f'''UPDATE imagecatalog SET approved = 'True' WHERE strippedname = $1''', values)
                    values = [newCategory, decalInfo['strippedname']]
                    await self.bot.sql.databaseExecuteDynamic(
                        f'''UPDATE imagecatalog SET category = $1 WHERE strippedname = $2''', values)
                    recipient = self.bot.get_user(int(decalInfo['ownerid']))
                    await recipient.send(
                        f'Your {decalInfo["type"]} "{decalInfo["strippedname"]}" was approved!  \nNote: the category was changed to "{newCategory}.\nExpect the decal to appear on https://sprockettools.github.io in 3-5 minutes."')
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
                    await self.bot.sql.databaseExecuteDynamic(
                        f'''UPDATE imagecatalog SET approved = 'True' WHERE strippedname = $1''', values)
                    values = [newName, decalInfo['strippedname']]
                    await self.bot.sql.databaseExecuteDynamic(
                        f'''UPDATE imagecatalog SET name = $1 WHERE strippedname = $2''', values)
                    recipient = self.bot.get_user(int(decalInfo['ownerid']))
                    await recipient.send(
                        f'Your decal "{decalInfo["strippedname"]}" was approved!  \nNote: the image name was changed to "{newName}."\nExpect the decal to appear on https://sprockettools.github.io in 3-5 minutes.')
                    await ctx.send("## Approved! \n(with a name change)")
                    operatingRepo.index.add(imageCatalogFilepath)
                    operatingRepo.index.add(imageDisplayFilepath)
                else:
                    values = [decalInfo['strippedname']]
                    await self.bot.sql.databaseExecuteDynamic(f'''DELETE FROM imagecatalog WHERE strippedname = $1''',
                                                              values)
                    recipient = self.bot.get_user(int(decalInfo['ownerid']))
                    os.remove(imageCatalogFilepath)
                    os.remove(imageDisplayFilepath)
                    await recipient.send(
                        f'Your {decalInfo["type"]} "{decalInfo["strippedname"]}" was not approved.  Reason: {answer}')
                    await ctx.send(f"## Done!\nRejection letter was sent to <@{decalInfo['ownerid']}>")
        except Exception:
            await ctx.send("Looks like there are no more decals to approve!")
            result = await githubTools.updateHTML(self, ctx)

    async def updateHTML(self, ctx):
        # This is the unique body content from your DecalsRGBmaker.html file.
        rgb_maker_content = '''
            <div class="container">
            <center>
                <h1 class="text-center">Color Decal Generator</h1>
                <div class="wrap box boxauto">
                    <h3>Drag the sliders to find your color of choice, and click the box below to copy the decal's URL. </br><br> To use the decal, place down a decal on your tank, and paste the link into the decal's URL field in the top right of the UI.</h3>   
                </div>
                <br>
                <h4 id="redval">Red: 120</h4>
                <div class="slidecontainer">
                    <input type="range" min="0" max="17" oninput="setColor()" value="8" class="red_slider" id="red" >
                </div>
                <h6><h6>
                <h4 id="greenval">Green: 135</h4>
                <div class="slidecontainer">
                    <input type="range" min="0" max="17" oninput="setColor()" value="9" class="green_slider" id="green">
                </div>
                <h6><h6>
                <h4 id="blueval">Blue: 150</h4>
                <div class="slidecontainer">
                <input type="range" min="0" oninput="setColor()" max="17" value="10" class="blue_slider" id="blue"></h4>


                <h6><h6>
                <h6><h6>
                <div class="background_box">
                    <br>
                    <div id="color_box" onclick="copyText()" class="color_box">
                        <h3>Click here to copy the URL<h3>
                    </div>
                </div>
                <h4 id="output" style="color: var(--blue4)"></h4>
            </div>

            </center> 
        '''

        # The closing script and body tags for all pages
        HTMLending = '''	</ul></center></body><script>
                function copyText(inputText) {
                    // Copy the text inside the text field
                    navigator.clipboard.writeText(inputText);
                }	
                </script>
                </html>'''

        # The specific script for the RGB Maker page
        RGB_script = '''<script>
                var output = document.getElementById("output");
                output.innerHTML = "Move the sliders to pick a color, and the URL to the decal will appear here.";

                function setColor() {
                    var redSlider = document.getElementById("red").value;
                    var greenSlider = document.getElementById("green").value;
                    var blueSlider = document.getElementById("blue").value;
                    let red = 15*(redSlider);
                    let green = 15*(greenSlider);
                    let blue = 15*(blueSlider);

                    let color = 'rgb(' + red + ',' + green + ',' + blue + ')';
                    let output_text = 'https://sprockettools.github.io/colors/R' + red + 'G' + green + 'B' + blue + '.png';
                    output.innerHTML = output_text;
                    document.getElementById("redval").innerHTML = "Red: " + red;
                    document.getElementById("greenval").innerHTML = "Green: " + green;
                    document.getElementById("blueval").innerHTML = "Blue: " + blue;
                    var boxy=document.getElementById("color_box");
                    boxy.style.backgroundColor=color;
                }

                function copyText() {
                    var redSlider = document.getElementById("red").value;
                    var greenSlider = document.getElementById("green").value;
                    var blueSlider = document.getElementById("blue").value;
                    let red = 15*(redSlider);
                    let green = 15*(greenSlider);
                    let blue = 15*(blueSlider);

                    let color = 'rgb(' + red + ',' + green + ',' + blue + ')';
                    let output_text = 'https://sprockettools.github.io/colors/R' + red + 'G' + green + 'B' + blue + '.png';
                    output.innerHTML = "Copied!";
                    var boxy=document.getElementById("color_box");
                    document.getElementById("redval").innerHTML = "Red: " + red;
                    document.getElementById("greenval").innerHTML = "Green: " + green;
                    document.getElementById("blueval").innerHTML = "Blue: " + blue;

                    navigator.clipboard.writeText(output_text);
                    boxy.style.backgroundColor=color;
                }
        </script></html>'''

        # Update all the main decal pages first
        for category in imageCategoryList:
            inText = category
            # Handle page titles
            if category == "Featured":
                inText = "SprocketTools Decal Catalog"
            elif category == "RGB Maker":
                inText = "RGB Color Picker"

            # --- Build the common header and top navigation for every page ---
            HTMLdoc = f'''<html>
                <head>
                    <title>{inText}</title>
                    <link rel="stylesheet" href="https://use.typekit.net/oov2wcw.css">
                    <link rel="icon" type="image/x-icon" href="SprocketToolsLogo.png">
                    <link rel="stylesheet" href="stylesV3.css">
                </head>
            <body>
            <div class="navbar titlenavbar">
                <img src="SprocketToolsLogo.png"/>
                <a href="index.html">Home</a>
                <a href="TopGearCalculator.html">Gear Calculator</a>
                <a href="resources.html">Sprocket Guides</a>
                <a href="credits.html">Credits</a>
                <a href="https://www.youtube.com/watch?v=oHg5SJYRHA0">Get Trolled</a>
                <a class="active" href="DecalsFeatured.html">Decal Catalog</a>
                <a href="PaintsFeatured.html">Paint Catalog</a>
                <a href="DecalsRGBmaker.html">RGB Decal Maker</a>
            </div>
            <div class="container">
                <h1 class="text-center">{inText}</h1>
            </div>
            <div>
                <ul class="navbar">'''
            for subcategory in imageCategoryList:
                # Use .replace() to create valid filenames/URLs
                safe_name = subcategory.replace(" ", "")
                if subcategory == category:
                    appendation = f'''<li class="active" onclick="document.location='Decals{safe_name}.html'">{subcategory}</li>'''
                else:
                    appendation = f'''<li onclick="document.location='Decals{safe_name}.html'">{subcategory}</li>'''
                HTMLdoc = f'{HTMLdoc}{appendation}'

            # --- End of common header/nav generation ---

            # --- SPECIAL CASE for RGB Maker ---
            if category == "RGB Maker":
                HTMLdoc = f'{HTMLdoc}<li onclick="document.location=\'DecalsContribute.html\'">Contribute your own!</li></ul></div>'
                HTMLdoc = f'{HTMLdoc}{rgb_maker_content}'
                HTMLdoc = f'{HTMLdoc}</center></body>{RGB_script}'  # Add the unique script and close tags
            # --- REGULAR decal page generation ---
            else:
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
                decalList = [dict(row) for row in await self.bot.sql.databaseFetch(
                    f'''SELECT * FROM imagecatalog WHERE approved = 'True' AND category = '{category}' AND (type <> 'paint' OR type IS NULL) ORDER BY name;''')]
                for decalInfo in decalList:
                    print("Hi!")
                    decalLI = f'''<li><img src="imgbin/{decalInfo['strippedname']}" onclick="copyText('https://sprockettools.github.io/img/{decalInfo['strippedname']}')"/>
                    <h3>{decalInfo['name']}</h3>
                    <h5>Uploaded by: {decalInfo['ownername']}</h5>'''
                    HTMLdoc = f'{HTMLdoc}{decalLI}'
                HTMLdoc = HTMLdoc + HTMLending

            # Save the generated file with the URL-safe name
            safe_category_name = category.replace(" ", "")
            saveDirectory = f'{GithubDirectory}{OSslashLine}Decals{safe_category_name}.html'
            print(saveDirectory)
            with open(saveDirectory, "w", encoding="utf-8") as outfile:
                outfile.write(HTMLdoc)
            operatingRepo.index.add(saveDirectory)


        # Update the paint pages next
        for category in paintCategoryList:
            inText = category
            # Handle page titles
            if category == "Featured":
                inText = "SprocketTools Paint Catalog"

            # --- Build the common header and top navigation for every page ---
            HTMLdoc = f'''<html>
                <head>
                    <title>{inText}</title>
                    <link rel="stylesheet" href="https://use.typekit.net/oov2wcw.css">
                    <link rel="icon" type="image/x-icon" href="SprocketToolsLogo.png">
                    <link rel="stylesheet" href="stylesV3.css">
                </head>
            <body>
            <div class="navbar titlenavbar">
                <img src="SprocketToolsLogo.png"/>
                <a href="index.html">Home</a>
                <a href="TopGearCalculator.html">Gear Calculator</a>
                <a href="resources.html">Sprocket Guides</a>
                <a href="credits.html">Credits</a>
                <a href="https://www.youtube.com/watch?v=oHg5SJYRHA0">Get Trolled</a>
                <a href="DecalsFeatured.html">Decal Catalog</a>
                <a class="active" href="PaintsFeatured.html">Paint Catalog</a>
                <a href="DecalsRGBmaker.html">RGB Decal Maker</a>
            </div>
            <div class="container">
                <h1 class="text-center">{inText}</h1>
            </div>
            <div>
                <ul class="navbar">'''
            for subcategory in paintCategoryList:
                # Use .replace() to create valid filenames/URLs
                safe_name = subcategory.replace(" ", "")
                if subcategory == category:
                    appendation = f'''<li class="active" onclick="document.location='Paints{safe_name}.html'">{subcategory}</li>'''
                else:
                    appendation = f'''<li onclick="document.location='Paints{safe_name}.html'">{subcategory}</li>'''
                HTMLdoc = f'{HTMLdoc}{appendation}'

            # --- End of common header/nav generation ---

            if category == "Featured":
                HTMLdocmid = f'''<li onclick="document.location='DecalsContribute.html'">Contribute your own!</li>
                    </div>
                </div>
                <div class="wrap">
                    <div class="box">
                        <h2>Welcome to the biggest community collection of URL-embeddable paint jobs!</h2> 
                        <h3>Click on a picture to copy its embeddable URL.</h3>
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
                        <h3>Click on a picture to copy its embeddable URL.</h3>
                        <h4>Then, select a decal in Sprocket Tank Design, and then paste the link into the URL field.</h4>
                        <h4>Your decals will now automatically download and apply wherever you share your tank!</h4>
                    </div>
                </div>
                <ul class="catalog">'''
            HTMLdoc = f'{HTMLdoc}{HTMLdocmid}'
            decalList = [dict(row) for row in await self.bot.sql.databaseFetch(
                f'''SELECT * FROM imagecatalog WHERE approved = 'True' AND category = '{category}' AND type = 'paint' ORDER BY name;''')]
            for decalInfo in decalList:
                print("Hi!")
                decalLI = f'''<li><img src="imgbin/{decalInfo['strippedname']}" onclick="copyText('https://sprockettools.github.io/img/{decalInfo['strippedname']}')"/>
                <h3>{decalInfo['name']}</h3>
                <h5>Uploaded by: {decalInfo['ownername']}</h5>'''
                HTMLdoc = f'{HTMLdoc}{decalLI}'
            HTMLdoc = HTMLdoc + HTMLending

            # Save the generated file with the URL-safe name
            safe_category_name = category.replace(" ", "")
            saveDirectory = f'{GithubDirectory}{OSslashLine}Paints{safe_category_name}.html'
            print(saveDirectory)
            with open(saveDirectory, "w", encoding="utf-8") as outfile:
                outfile.write(HTMLdoc)
            operatingRepo.index.add(saveDirectory)



        # specialized entry for the contribution directory (paints)
        HTMLdoccontribute = f'''<html>
                        <head>
                            <title>Contribute Paints</title>
                            <link rel="stylesheet" href="https://use.typekit.net/oov2wcw.css">
                            <link rel="icon" type="image/x-icon" href="SprocketToolsLogo.png">
                            <link rel="stylesheet" href="stylesV3.css">
                        </head>
                    <body>
                    <div class="navbar titlenavbar">
                        <a href="index.html">Home</a>
                        <a href="TopGearCalculator.html">Gear Calculator</a>
                        <a href="resources.html">Sprocket Guides</a>
                        <a href="credits.html">Credits</a>
                        <a href="https://www.youtube.com/watch?v=oHg5SJYRHA0">Get Trolled</a>
                        <a href="DecalsFeatured.html">Decal Catalog</a>
                        <a class="active" href="PaintsFeatured.html">Paint Catalog</a>
                        <a href="DecalsRGBmaker.html">RGB Decal Maker</a>
                    </div>

                    <div>
                        <ul class="navbar">'''
        for subcategory in paintCategoryList:
            appendation = f'''<li onclick="document.location='Paints{subcategory}.html'">{subcategory}</li>'''
            HTMLdoccontribute = f'{HTMLdoccontribute}{appendation}'

        HTMLdoccontributemid = '''<li class="active" onclick="document.location='PaintsContribute.html'">Contribute your own!</li>
                            </div>
                        </div>
                        <div class="wrap">
                            <h1 class="text-center">Contributing Paints</h1>
                            <div class="box">
                                <h4>To contribute your own paint to the catalog, use the -submitDecal command in any discord server with Sprocket Bot.</h4> 
                                <h4>This includes the <a href="https://discord.gg/sprocket">Sprocket Official Discord</a>.</h4>
                                <h3>Decals need to meet the following criteria:</h3>   
                                <h5>- Files must be a .png</h5>
                                <h5>- Files should not exceed 1MB in size</h5>
                                <h5>- Decals need to be compliant with Discord TOS (no hateful symbols, NSFW, etc.)</h5>
                            </div>
                        </div>
                        </center></body></html>'''
        HTMLdoccontribute = f'{HTMLdoccontribute}{HTMLdoccontributemid}'
        saveDirectory = f'{GithubDirectory}{OSslashLine}PaintsContribute.html'
        print(saveDirectory)
        with open(saveDirectory, "w") as outfile:
            outfile.write(HTMLdoccontribute)
        operatingRepo.index.add(saveDirectory)



        # specialized entry for the contribution directory (decals)
        HTMLdoccontribute = f'''<html>
                                <head>
                                    <title>Contribute Decals</title>
                                    <link rel="stylesheet" href="https://use.typekit.net/oov2wcw.css">
                                    <link rel="icon" type="image/x-icon" href="SprocketToolsLogo.png">
                                    <link rel="stylesheet" href="stylesV3.css">
                                </head>
                            <body>
                            <div class="navbar titlenavbar">
                                <a href="index.html">Home</a>
                                <a href="TopGearCalculator.html">Gear Calculator</a>
                                <a href="resources.html">Sprocket Guides</a>
                                <a href="credits.html">Credits</a>
                                <a href="https://www.youtube.com/watch?v=oHg5SJYRHA0">Get Trolled</a>
                                <a class="active" href="DecalsFeatured.html">Decal Catalog</a>
                                <a href="PaintsFeatured.html">Paint Catalog</a>
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

        # await githubTools.updateActiveContests(self)
        await ctx.send("Done!")
        try:
            operatingRepo.git.add(update=True)
            operatingRepo.index.commit("Automated decal/paint updating sequence")
            origin = operatingRepo.remote(name='origin')
            origin.push().raise_if_error()
            await ctx.send("Decals are now pushed to GitHub!")
        except Exception as e:
            await ctx.send(f"Some error occurred pushing the decals to GitHub: {e}.")

    @commands.command(name="sanitizeFilenames", description="Scans for and fixes filenames with Windows-invalid characters.")
    async def sanitizeFilenames(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return

        await ctx.send("Scanning image catalog for invalid Windows characters (`< > : \" / \\ | ? *`).")

        # Fetch all names
        all_entries = [dict(row) for row in await self.bot.sql.databaseFetch('SELECT strippedname FROM imagecatalog')]

        # Windows invalid characters
        invalid_chars = '<>:"/\\|?*'
        found_entries = []

        # Find entries that have at least one invalid char
        for entry in all_entries:
            name = entry['strippedname']
            if any(char in name for char in invalid_chars):
                found_entries.append(name)

        if not found_entries:
            await ctx.send("No invalid filenames found.")
            return

        await ctx.send(f"Found {len(found_entries)} invalid filenames. Fixing...")

        fixed_count = 0
        skipped_count = 0
        error_count = 0
        errors = []

        for old_name in found_entries:
            new_name = old_name
            for char in invalid_chars:
                new_name = new_name.replace(char, "_")

            # Define paths
            old_catalog_path = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{old_name}"
            old_display_path = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}{OSslashLine}{old_name}"
            new_catalog_path = f"{GithubDirectory}{OSslashLine}{imgCatalogFolder}{OSslashLine}{new_name}"
            new_display_path = f"{GithubDirectory}{OSslashLine}{imgDisplayFolder}{OSslashLine}{new_name}"

            # Check existence of source (at least one file should exist to justify operation)
            if not os.path.exists(old_catalog_path) and not os.path.exists(old_display_path):
                # If neither exists, we just have a DB entry pointing to nothing.
                errors.append(f"Source files missing for `{old_name}`.")
                error_count += 1
                continue

            # Check collision: if new name exists and is not the same file
            if os.path.exists(new_catalog_path) or os.path.exists(new_display_path):
                if old_name != new_name:
                    skipped_count += 1
                    errors.append(f"Collision: `{new_name}` already exists.")
                    continue

            try:
                # Rename files
                if os.path.exists(old_catalog_path):
                    os.rename(old_catalog_path, new_catalog_path)
                if os.path.exists(old_display_path):
                    os.rename(old_display_path, new_display_path)

                # DB Update
                await self.bot.sql.databaseExecuteDynamic(
                    "UPDATE imagecatalog SET strippedname = $1 WHERE strippedname = $2",
                    [new_name, old_name]
                )

                # Stage files for git
                paths_to_add = []
                if os.path.exists(new_catalog_path):
                    paths_to_add.append(new_catalog_path)
                if os.path.exists(new_display_path):
                    paths_to_add.append(new_display_path)

                if paths_to_add:
                    operatingRepo.index.add(paths_to_add)

                fixed_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Error renaming `{old_name}`: {e}")

        await ctx.send(f"Complete.\nFixed: {fixed_count}\nSkipped: {skipped_count}\nErrors: {error_count}")

        if errors:
            err_str = "\n".join(errors[:15])
            if len(errors) > 15:
                err_str += "\n... (and more)"
            await ctx.send(f"Errors:\n{err_str}")

        if fixed_count > 0:
            # updateHTML commits and pushes
            await githubTools.updateHTML(self, ctx)

    @commands.command(name="changeDecalCategory", description="change a decal category from the SprocketTools website")
    async def changeDecalCategory(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return
        decalList = await self.bot.ui.getResponse(ctx, f"Reply with the a list of stripped names or URLs of the decal(s) you wish to change.  **Separate by newlines.**\nEx: `6_side_circle.png` or `https://sprockettools.github.io/img/dirt_stains.png`")
        listOut = decalList.split("\n")
        userPrompt = f"Alright then, pick a new category to use with these."
        newCategory = await ctx.bot.ui.getChoiceFromList(ctx, imageCategoryList, userPrompt)
        for decalName in listOut:
            values = [newCategory, decalName.replace("https://sprockettools.github.io/img/", "")]
            await self.bot.sql.databaseExecuteDynamic(
                f'''UPDATE imagecatalog SET category = $1 WHERE strippedname = $2''', values)
        await ctx.send("## Configs updated!")

    @commands.command(name="changeDecalName", description="change a decal name from the SprocketTools website")
    async def changeDecalName(self, ctx):
        if ctx.author.id != 712509599135301673:
            await ctx.send(await self.bot.error.retrieveError(ctx))
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
        await self.bot.sql.databaseExecuteDynamic(
            f'''UPDATE imagecatalog SET name = $1 WHERE strippedname = $2''', values)
        await ctx.send("## Config updated!")

    async def updateActiveContests(self):
        currentTime = int(time.time())
        contests = [dict(row) for row in await self.bot.sql.databaseFetch(
            f'''SELECT * FROM contests WHERE starttimestamp < '{currentTime}' AND endtimestamp > '{currentTime}' AND crossServer = 'True';''')]
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
            <div class="navbar titlenavbar">
            <a href="index.html">Home</a>
            <a href="TopGearCalculator.html">Gear Calculator</a>
            <a  class="active" href="ContestsList.html">Contests</a>
            <a href="VehicleGenerator.html">Random Tank Picker</a>
            <a href="resources.html">Guides</a>
            <a href="credits.html">Credits</a>
            <a href="https://www.youtube.com/watch?v=oHg5SJYRHA0">Get Trolled</a>
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(githubTools(bot))