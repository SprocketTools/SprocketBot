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
nest_asyncio.apply()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = False
utc = datetime.timezone.utc
import sys
#sys.setrecursionlimit(100)
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

#botMode = "official" # dev on live flag

if botMode != "official":
    prefix = "?"
    defaultURL = "https://github.com/SprocketTools/SprocketBot/blob/main/assets/SprocketBotDevLogo.gif?raw=true"
    defaultName = "Testing Bot"

else:
    prefix = "-"
    defaultURL = "https://sprockettools.github.io/SprocketToolsLogo.png"
    defaultName = "Sprocket Bot"

#prefix = "?" # dev on live variable

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
cogsList = ["cogs.errorFunctions", "cogs.textTools",  "cogs.registerFunctions", "cogs.VCfunctions", "cogs.campaignFunctions", "cogs.campaignRegisterFunctions", "cogs.autoResponderFunctions",  "cogs.blueprintFunctions", "cogs.adminFunctions", "cogs.imageFunctions",  "cogs.campaignMapsFunctions", "cogs.campaignInfoFunctions", "cogs.SprocketOfficialFunctions", "cogs.campaignManageFunctions", "cogs.campaignFinanceFunctions", "cogs.campaignUpdateFunctions", "cogs.testingFunctions", "cogs.campaignTransactionFunctions", "cogs.serverFunctions", "cogs.flyoutTools", "cogs.roleColorTools"]



class Bot(commands.Bot):
    def __init__(self):
        print("starting")
        super().__init__(command_prefix=commands.when_mentioned_or(prefix), help_command=None, intents=intents, case_insensitive=True) #
        self.cogslist = cogsList
        self.synced = False

    async def setup_hook(self):

        if updateGithub == "Y":
            cogsList.append("cogs.githubTools")
            #await self.load_extension("cogs.githubTools")
        for ext in self.cogslist:
            await self.load_extension(ext)


    async def on_ready(self):
        self.pool = await asyncpg.create_pool(**SQLsettings, command_timeout=60)
        self.ownerID = self.owner_id

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
# tree = app_commands.CommandTree(bot)
bot.run(discordToken)

bot.run(config[f"settings.official"]["Token"])

sanitizeKeywords = ["@", "/", "invalid_tank"]
# async def sanitize(inputPhrase: str):
#     outputPhrase = inputPhrase
#     for phrase in sanitizeKeywords:
#         outputPhrase = outputPhrase.replace(phrase, "")
#     return outputPhrase
#
# async def addLine(inputOne: str, inputTwo: str):
#     return f"{inputOne}\n{inputTwo}"

