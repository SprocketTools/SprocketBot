from pathlib import Path
import os, random, time, asyncio, asyncpg, datetime, json, copy
import platform
import discord
from discord.ext import tasks, commands
from discord import app_commands
from discord.ui import View
import configparser
import nest_asyncio
nest_asyncio.apply()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
utc = datetime.timezone.utc
# botMode = "official"
# Determines whether this is the live version of the bot or the testing version.
# development settings (running on Windows/PyCharm)
if platform.system() == "Windows":
    botMode = "development"
    configurationFilepath = "C:\\SprocketBot\\configuration.ini"
    OSslashLine = "\\"

else:
    # default settings (running on Rasbian)
    botMode = "official"
    configurationFilepath = "/home/mumblepi/configuration.ini"
    OSslashLine = "/"


if botMode != "official":
    prefix = "?"
    defaultURL = "https://github.com/SprocketTools/SprocketBot/blob/main/assets/SprocketBotDevLogo.gif?raw=true"
    defaultName = "Testing Bot"

else:
    prefix = "-"
    defaultURL = "https://sprockettools.github.io/SprocketToolsLogo.png"
    defaultName = "Sprocket Bot"

# general settings
config = configparser.ConfigParser()
config.read(configurationFilepath)
config.sections()
print(config)
discordToken = config[f"settings.{botMode}"]["Token"]
clientID = config[f"settings.{botMode}"]["clientID"]
SQLsettings = config["SECURITY"]
SQLsettings["database"] = config[f"settings.{botMode}"]["database"]
ownerID = int(config["settings"]["ownerID"])
githubPAT = str(config["settings"]["githubPAT"])
updateGithub = str(config["settings"]["updateGithub"])
cogsList = ["cogs.SQLfunctions", "cogs.textTools", "cogs.registerFunctions", "cogs.VCfunctions", "cogs.errorFunctions", "cogs.campaignRegisterFunctions", "cogs.autoResponderFunctions",  "cogs.blueprintFunctions", "cogs.adminFunctions", "cogs.imageFunctions", "cogs.campaignFunctions", "cogs.campaignInfoFunctions", "cogs.SprocketOfficialFunctions", "cogs.contestFunctions", "cogs.campaignFinanceFunctions", "cogs.campaignUpdateFunctions", "cogs.testingFunctions"]

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(prefix), help_command=None, intents=discord.Intents().all(), case_insensitive=True) #
        self.cogslist = cogsList
        self.synced = False

    async def setup_hook(self):
        for ext in self.cogslist:
            await self.load_extension(ext)
        if updateGithub == "Y":
            await self.load_extension("cogs.githubTools")

    async def on_ready(self):
        await self.wait_until_ready()
        # if not self.synced:
        #     await tree.sync(guild=discord.Object(id=1137849402891960340))
        #     self.synced = True
        channel = bot.get_channel(1152377925916688484)
        await channel.send("I am now online!")
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        print('------')

class Management:
    def __init__(self, bot):
        self.bot = bot
    @commands.command(name="reloadCogs", description="reload all extensions")
    async def reloadCogs(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        for cog in self.bot.cogslist:
            await bot.reload_extension(cog)
        await ctx.send("Reloaded!")



sanitizeKeywords = ["@", "/", "invalid_tank"]
async def sanitize(inputPhrase: str):
    outputPhrase = inputPhrase
    for phrase in sanitizeKeywords:
        outputPhrase = outputPhrase.replace(phrase, "")
    return outputPhrase

async def addLine(inputOne: str, inputTwo: str):
    return f"{inputOne}\n{inputTwo}"
bot = Bot()
# tree = app_commands.CommandTree(bot)
bot.run(discordToken)

blacklist_ids = ['712509599135301673']
