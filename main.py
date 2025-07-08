from pathlib import Path
import os, random, time, asyncio, asyncpg, datetime, json, copy
from cogs.SQLfunctions import SQLfunctions
import platform
import discord
from discord.ext import tasks, commands
from discord import app_commands
from discord.ui import View
import configparser
import nest_asyncio
from google import genai
from google.genai import types
nest_asyncio.apply()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = False
utc = datetime.timezone.utc
import sys
#sys.setrecursionlimit(100)

## configuration

###############################################################################
## Sprocket Bot looks for two config files - the general config file, and the instance config file.
## This name determines what configuration gets loaded.

#configName = "official"
configName = "development"
#configName = "clone1"

###############################################################################

# Find the config file

if platform.system() == "Windows":
    configurationFilepath = "C:\\SprocketBot\\configuration.ini"
    instanceFilepath = "C:\\SprocketBot\\bots\\" + configName + ".ini"
    OSslashLine = "\\"

else:
    configurationFilepath = "/home/mumblepi/configuration.ini"
    instanceFilepath = "/home/mumblepi/bots/" + configName + ".ini"
    OSslashLine = "/"

# load the config files

baseConfig = configparser.ConfigParser()
baseConfig.read(configurationFilepath)
baseConfig.sections()

instanceConfig = configparser.ConfigParser()
instanceConfig.read(instanceFilepath)
instanceConfig.sections()

# Set all the settings

botMode = False
if instanceConfig[f"botinfo"]["master"] == "true":
    botMode = True
    print("Launching master instance")
discordToken = instanceConfig[f"botinfo"]["Token"]
clientID = instanceConfig[f"botinfo"]["clientid"]
prefix = instanceConfig[f"botinfo"]["prefix"]
SQLsettings = baseConfig["SECURITY"]
SQLsettings["database"] = instanceConfig[f"botinfo"]["sqldatabase"]
ownerID = int(baseConfig["settings"]["ownerID"])
githubPAT = str(baseConfig["settings"]["githubpat"])
print("Gtok: " + githubPAT)
updateGithub = False
if str(instanceConfig["botinfo"]["updateGithub"]) == "true":
    updateGithub = True
    print("Launching master instance")
cogsList = ["cogs.errorFunctions", "cogs.textTools",  "cogs.registerFunctions", "cogs.VCfunctions", "cogs.campaignFunctions", "cogs.campaignRegisterFunctions", "cogs.autoResponderFunctions",  "cogs.blueprintFunctions", "cogs.adminFunctions", "cogs.imageFunctions",  "cogs.campaignMapsFunctions", "cogs.campaignInfoFunctions", "cogs.SprocketOfficialFunctions", "cogs.campaignManageFunctions", "cogs.campaignFinanceFunctions", "cogs.campaignUpdateFunctions",  "cogs.testingFunctions", "cogs.campaignTransactionFunctions", "cogs.timedMessageTools", "cogs.serverFunctions", "cogs.flyoutTools", "cogs.starboardFunctions", "cogs.roleColorTools"]

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(prefix), help_command=None, intents=intents, case_insensitive=True) #
        self.cogslist = cogsList
        self.synced = False
        self.baseConfig = baseConfig
        self.configurationFilepath = configurationFilepath
        self.serverids = []
        self.geminikey = baseConfig['settings']['geminiapi']

    async def setup_hook(self):
        self.pool = await asyncpg.create_pool(**SQLsettings, command_timeout=60)

        print(baseConfig['settings']['geminiapi'])
        if updateGithub == True:
            cogsList.append("cogs.githubTools")
            #await self.load_extension("cogs.githubTools")
        for ext in self.cogslist:
            await self.load_extension(ext)

    async def on_ready(self):

        await self.wait_until_ready()
        # await bot.tree.sync()
        # if not self.synced:
        #     await tree.sync(guild=discord.Object(id=1137849402891960340))
        #     self.synced = True
        channel = bot.get_channel(1152377925916688484)
        await channel.send("I am now online!")
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        print('------')

bot = Bot()
bot.ishost = botMode
# tree = app_commands.CommandTree(bot)
bot.run(discordToken)



