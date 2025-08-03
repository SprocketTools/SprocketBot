import asyncpg, datetime

from tools.AITools import AITools, GeminiAITools
from tools.SQLtools import SQLtools
from tools.UItools import UItools
import platform
import discord
from discord.ext import commands
import configparser
import nest_asyncio

nest_asyncio.apply()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = False
utc = datetime.timezone.utc
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
cogsList = ["cogs.errorFunctions", "cogs.textTools", "cogs.registerFunctions", "cogs.campaignRegisterFunctions", "cogs.autoResponderFunctions",  "cogs.blueprintFunctions", "cogs.adminFunctions", "cogs.imageFunctions", "cogs.campaignMapsFunctions", "cogs.campaignInfoFunctions", "cogs.SprocketOfficialFunctions", "cogs.campaignManageFunctions", "cogs.campaignFinanceFunctions", "cogs.campaignUpdateFunctions",  "cogs.testingFunctions", "cogs.campaignTransactionFunctions", "cogs.timedMessageTools", "cogs.serverFunctions", "cogs.flyoutTools", "cogs.starboardFunctions", "cogs.roleColorTools"] #"cogs.VCfunctions",

class Bot(commands.Bot):
    def __init__(self, ai_wrapper: AITools):
        super().__init__(command_prefix=commands.when_mentioned_or(prefix), help_command=None, intents=intents, case_insensitive=True) #
        self.AI = ai_wrapper
        #self.AI.keys = baseConfig['settings']['geminiapis'].split(",")
        self.cogslist = cogsList
        self.synced = False
        self.baseConfig = baseConfig
        self.configurationFilepath = configurationFilepath
        self.ownerid = ownerID
        self.botMode = botMode
        self.serverids = []
        self.geminikey = baseConfig['settings']['geminiapis'].split(",")
        self.sql: SQLtools = None
        self.ui: UItools = None
        self.pool: asyncpg.Pool = None

    async def setup_hook(self):
        self.pool = await asyncpg.create_pool(**SQLsettings, command_timeout=20)
        self.sql = SQLtools(self.pool)
        self.ui = UItools(self)
        print(baseConfig['settings']['geminiapis'])
        if updateGithub == True:
            cogsList.append("cogs.githubTools")
            #await self.load_extension("cogs.githubTools")
        for ext in self.cogslist:
            await self.load_extension(ext)
            #setattr(self, ext.split('.')[1], self.get_cog(ext))

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

gemini_api_keys = tuple(baseConfig['settings']['geminiapis'].split(","))
gemini_ai_wrapper = GeminiAITools(APIkeys=gemini_api_keys)
bot = Bot(gemini_ai_wrapper)
bot.ishost = botMode
# tree = app_commands.CommandTree(bot)
bot.run(discordToken)



