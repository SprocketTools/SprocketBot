from pathlib import Path
import os, random, time, asyncio, asyncpg, datetime, json, copy
import platform
import discord
from discord.ext import tasks, commands
from discord.ui import View
import configparser
import nest_asyncio
nest_asyncio.apply()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
utc = datetime.timezone.utc

# Determines whether this is the live version of the bot or the testing version.
# development settings (running on Windows/PyCharm)
if platform.system() == "Windows":
    botMode = "development"
    configurationFilepath = "C:\\SprocketBot\\configuration.ini"
    OSslashLine = "\\"
    prefix = "?"

else:
    # default settings (running on Rasbian)
    botMode = "official"
    configurationFilepath = "/home/mumblepi/configuration.ini"
    OSslashLine = "/"
    prefix = "-"

# general settings
config = configparser.ConfigParser()
config.read(configurationFilepath)
config.sections()
discordToken = config[f"settings.{botMode}"]["Token"]
clientID = config[f"settings.{botMode}"]["clientID"]
SQLsettings = config["SECURITY"]
SQLsettings["database"] = config[f"settings.{botMode}"]["database"]
ownerID = int(config["settings"]["ownerID"])

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(prefix), help_command=None, intents=discord.Intents().all())
        self.cogslist = ["cogs.registerFunctions", "cogs.SQLfunctions", "cogs.blueprintFunctions", "cogs.imageFunctions"]

    async def setup_hook(self):
        for ext in self.cogslist:
            await self.load_extension(ext)
    async def on_ready(self):
        channel = bot.get_channel(1152377925916688484)
        await channel.send("I am now online!")
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        print('------')

bot = Bot()
bot.run(discordToken)

sanitizeKeywords = ["@", "/", "invalid_tank"]
async def sanitize(inputPhrase: str):
    outputPhrase = inputPhrase
    for phrase in sanitizeKeywords:
        outputPhrase = outputPhrase.replace(phrase, "")
    return outputPhrase

async def addLine(inputOne: str, inputTwo: str):
    return f"{inputOne}\n{inputTwo}"
