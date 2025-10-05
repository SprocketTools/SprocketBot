# main.py

import asyncpg, datetime, sys
import asyncio, signal
import platform
# ... (rest of your imports are unchanged)
from tools.AITools import AITools, GeminiAITools
from tools.SQLtools import SQLtools
from tools.UItools import UItools
from tools.errorTools import errorTools
from tools.campaignTools import campaignTools
import discord, configparser, nest_asyncio
from discord.ext import commands

# ... (all code down to the Bot class is unchanged) ...
nest_asyncio.apply()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = False
intents.voice_states = True
utc = datetime.timezone.utc

## configuration
if len(sys.argv) > 1:
    configName = sys.argv[1]
else:
    configName = "development" if platform.system() == "Windows" else "official"

print(f"[{configName}] Did the update work??????!!!!????!!!!!!!!!!!?????????????")

# Find the config file
if platform.system() == "Windows":
    configurationFilepath = "C:\\SprocketBot\\configuration.ini"
    instanceFilepath = "C:\\SprocketBot\\bots\\" + configName + ".ini"
else:
    configurationFilepath = "/home/mumblepi/configuration.ini"
    instanceFilepath = "/home/mumblepi/bots/" + configName + ".ini"

# load the config files
baseConfig = configparser.ConfigParser()
baseConfig.read(configurationFilepath)
instanceConfig = configparser.ConfigParser()
instanceConfig.read(instanceFilepath)

botMode = instanceConfig.getboolean(f"botinfo", "master", fallback=False)
if botMode:
    print(f"[{configName}] Launching master instance")

discordToken = instanceConfig[f"botinfo"]["Token"]
prefix = instanceConfig[f"botinfo"]["prefix"]
SQLsettings = baseConfig["SECURITY"]
SQLsettings["database"] = instanceConfig[f"botinfo"]["sqldatabase"]
ownerID = int(baseConfig["settings"]["ownerID"])
updateGithub = instanceConfig.getboolean("botinfo", "updateGithub", fallback=False)
if updateGithub:
    print(f"[{configName}] Launching master instance with GitHub tools.")

cogsList = ["cogs.textTools", "cogs.registerFunctions", "cogs.campaignRegisterFunctions", "cogs.autoResponderFunctions",
            "cogs.blueprintFunctions", "cogs.errorFunctions", "cogs.adminFunctions", "cogs.imageFunctions",
            "cogs.campaignMapsFunctions", "cogs.campaignInfoFunctions", "cogs.SprocketOfficialFunctions",
            "cogs.campaignManageFunctions", "cogs.campaignFinanceFunctions", "cogs.campaignUpdateFunctions",
            "cogs.testingFunctions", "cogs.campaignTransactionFunctions", "cogs.VCfunctions", "cogs.timedMessageTools",
            "cogs.serverFunctions", "cogs.flyoutTools", "cogs.clickupFunctions", "cogs.starboardFunctions",
            "cogs.roleColorTools", "cogs.observatoryFunctions"]


class Bot(commands.Bot):
    def __init__(self, ai_wrapper: AITools):
        super().__init__(command_prefix=commands.when_mentioned_or(prefix), help_command=None, intents=intents,
                         case_insensitive=True)
        self.cogslist = cogsList
        self.baseConfig = baseConfig
        self.ownerid = ownerID
        self.botMode = botMode
        self.geminikey = baseConfig['settings']['geminiapis'].split(",")
        self.AI = ai_wrapper
        self.sql: SQLtools = None
        self.ui: UItools = None
        self.pool: asyncpg.Pool = None
        self.campaignTools: campaignTools = None
        self.error: errorTools = None

    async def setup_hook(self):
        self.pool = await asyncpg.create_pool(**SQLsettings, command_timeout=20)
        self.sql = SQLtools(self.pool)
        self.ui = UItools(self)
        self.campaignTools = campaignTools(self)
        self.error = errorTools(self)
        if updateGithub:
            cogsList.append("cogs.githubTools")
        for ext in self.cogslist:
            await self.load_extension(ext)

    async def on_ready(self):
        await self.wait_until_ready()
        channel_id = 1152377925916688484
        channel = self.get_channel(channel_id)
        if channel:
            await channel.send(f"I am now online! Instance: `{configName}`")
        print(f'Logged in as {self.user} (ID: {self.user.id}) on instance: {configName}')
        print('------')

    async def close(self):
        print(f"[{configName}] Closing database connection pool.")
        if self.pool:
            await self.pool.close()
        await super().close()


# --- Main Execution Block ---
gemini_api_keys = tuple(baseConfig['settings']['geminiapis'].split(","))
gemini_ai_wrapper = GeminiAITools(APIkeys=gemini_api_keys)
bot = Bot(gemini_ai_wrapper)
bot.ishost = botMode


async def main():
    loop = asyncio.get_running_loop()

    async def shutdown(sig):
        print(f"[{configName}] Received exit signal {sig.name}, shutting down gracefully.")
        await bot.close()

    # MODIFIED: Add SIGINT handler for Windows compatibility
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        # On Windows, only SIGINT is really catchable this way.
        try:
            loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(s)))
        except NotImplementedError:
            # This can happen on Windows for signals other than SIGINT
            print(f"Could not add handler for {s.name}, may not be supported on this OS.")

    async with bot:
        await bot.start(discordToken)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"[{configName}] Bot instance shut down by KeyboardInterrupt.")