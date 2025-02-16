import os, random, time, asyncio, asyncpg, datetime, json, copy, sys, nest_asyncio, configparser, discord, platform
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
        self.pool = None
        print(self.master)
        for extension in cogsList:
            print(extension)
            await self.load_extension(extension)

        if self.master == "True":
            pass
            #await Bot.load_extension(self, name="cogs.githubTools")

    async def on_ready(self):
        print("database started")
        self.pool = await asyncpg.create_pool(**SQLsettings, command_timeout=60)

        print("database created!")
        await self.wait_until_ready()
        channel = self.get_channel(1152377925916688484)
        await channel.send("I am now online!")
        print(f'Logged in as {self.user.name} (ID: {self.user.id})')
        print('------')

bot_list = []
async def run_bot():
    print("Starting the run_bot loop")
    ini_data = []

    for filename in os.listdir(botconfigpath):

        if filename.lower().endswith(".ini"): # Check for .ini extension (case-insensitive)
            filepath = os.path.join(botconfigpath, filename)
            config = configparser.ConfigParser()
            config.read(filepath)
            file_dict = {}
            for section in config.sections():
                file_dict[section] = {}
                for option in config.options(section):
                    file_dict[section][option] = config.get(section, option)
            # Use filename without extension as key in the main dictionary
            file_key = os.path.splitext(filename)[0]
            ini_data.append(file_dict["botinfo"])

    # tasks = []
    # for data_out in ini_data:
    #     data_token = str(data_out["token"])
    #     print(f"making token for {data_token}")
    #     tasks.append(await asyncio.create_task(Bot(data_out).start(data_token)))
    # for task in tasks:
    #     await task

    tasks = []
    for data_out in ini_data:
        data_token = str(data_out["token"])
        print(f"making token for {data_token}")
        tasks.append(asyncio.create_task(Bot(data_out).start(data_token)))
    await asyncio.gather(*tasks)

def exception_handler(loop, context):
    exp = context['exception']
    # log exception
    print(f'Never-retrieved exception: {exp}')

if __name__ == "__main__":
    async def run_main():
        await run_bot()
    asyncio.run(run_main())
    # get the event loop
    loop = asyncio.get_running_loop()
    # set the exception handler
    loop.set_exception_handler(exception_handler)
# define an exception handler

#
# loop.run_until_complete(run_bot())





