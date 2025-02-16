import os, sys, random, time, asyncio, asyncpg, datetime, json, copy, sys, nest_asyncio, configparser, discord, platform
from discord.ext import tasks, commands
#nest_asyncio.apply()
intents = discord.Intents.all()
utc = datetime.timezone.utc

# Determines how to access the file system.

if platform.system() == "Windows":
    configurationFilepath = "C:\\SprocketBot\\configuration.ini"
    botconfigpath = "C:\\SprocketBot\\bots\\"
    OSslashLine = "\\"

else:   # default settings (running on Rasbian)
    configurationFilepath = "/home/mumblepi/sprocket_bot_config/configuration.ini"
    botconfigpath = "/home/mumblepi/sprocket_bot_config/bots/"
    OSslashLine = "/"

config = configparser.ConfigParser()
config.read(configurationFilepath)
config.sections()
SQLsettings = config["SECURITY"]
githubPAT = str(config["settings"]["githubPAT"])
updateGithub = str(config["settings"]["updateGithub"])
cogsList = ["cogs.errorFunctions", "cogs.textTools",  "cogs.registerFunctions", "cogs.VCfunctions", "cogs.campaignFunctions", "cogs.campaignRegisterFunctions", "cogs.autoResponderFunctions",  "cogs.blueprintFunctions", "cogs.adminFunctions", "cogs.imageFunctions",  "cogs.campaignMapsFunctions", "cogs.campaignInfoFunctions", "cogs.SprocketOfficialFunctions", "cogs.campaignManageFunctions", "cogs.campaignFinanceFunctions", "cogs.campaignUpdateFunctions", "cogs.testingFunctions", "cogs.campaignTransactionFunctions", "cogs.serverFunctions", "cogs.flyoutTools", "cogs.roleColorTools"]



class Bot(commands.Bot):
    def __init__(self, botConfig):

        # output_dict = dict()
        # for section in botConfig:
        #     items = botConfig.items(section)
        #     output_dict[section] = dict(items)


        self.config = config
        self.githubPAT = githubPAT
        self.clientID = botConfig["clientid"]
        self.prefix = botConfig["prefix"]
        self.token = botConfig["token"]
        self.mode = botConfig["mode"]
        self.SQLsettings = botConfig["database"]
        self.master = botConfig["master"]
        self.flavor = botConfig["flavor"]
        self.ownerID = config["settings"]["ownerID"]
        super().__init__(command_prefix=commands.when_mentioned_or(self.prefix), help_command=None, intents=intents, case_insensitive=True) #
        self.cogslist = cogsList
        self.synced = False

    async def setup_hook(self):
        print(self.master)
        for extension in cogsList:
            print(extension)
            await self.load_extension(extension)
        if self.master == "True":
            pass
            #await Bot.load_extension(self, name="cogs.githubTools")

    async def on_ready(self):
        self.pool = await asyncpg.create_pool(**SQLsettings, command_timeout=60)
        await self.wait_until_ready()
        channel = self.get_channel(1152377925916688484)
        await channel.send("I am now online!")
        print(f'Logged in as {self.user.name} (ID: {self.user.id})')
        print('------')

