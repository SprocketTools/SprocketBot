# main.py

import asyncpg, datetime, sys, os
import asyncio, signal  # Signal is no longer used for shutdown but other libs might need it
import platform
from tools.AITools import AITools, GeminiAITools
from tools.SQLtools import SQLtools
from tools.UItools import UItools
from tools.errorTools import errorTools
from tools.campaignTools import campaignTools
import discord, configparser, nest_asyncio
from discord.ext import commands

nest_asyncio.apply()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = False
intents.voice_states = True
utc = datetime.timezone.utc

# ... (config loading is unchanged) ...
if len(sys.argv) > 1:
    configName = sys.argv[1]
else:
    configName = "development" if platform.system() == "Windows" else "official"
if platform.system() == "Windows":
    config_base_path = "C:\\SprocketBot\\"
else:
    config_base_path = os.path.join(os.path.expanduser("~"), "")
configurationFilepath = os.path.join(config_base_path, "configuration.ini")
instanceFilepath = os.path.join(config_base_path, "bots", f"{configName}.ini")
baseConfig = configparser.ConfigParser();
baseConfig.read(configurationFilepath)
instanceConfig = configparser.ConfigParser();
instanceConfig.read(instanceFilepath)
botMode = instanceConfig.getboolean(f"botinfo", "master", fallback=False)
discordToken = instanceConfig[f"botinfo"]["Token"]
prefix = instanceConfig[f"botinfo"]["prefix"]
SQLsettings = baseConfig["SECURITY"]
SQLsettings["database"] = instanceConfig[f"botinfo"]["sqldatabase"]
ownerID = int(baseConfig["settings"]["ownerID"])
updateGithub = instanceConfig.getboolean("botinfo", "updateGithub", fallback=False)

cogsList = ["cogs.textTools", "cogs.registerFunctions", "cogs.campaignRegisterFunctions", "cogs.autoResponderFunctions",
            "cogs.blueprintFunctions", "cogs.errorFunctions", "cogs.adminFunctions", "cogs.imageFunctions",
            "cogs.campaignMapsFunctions", "cogs.campaignInfoFunctions", "cogs.SprocketOfficialFunctions",
            "cogs.campaignManageFunctions", "cogs.campaignFinanceFunctions", "cogs.campaignUpdateFunctions",
            "cogs.testingFunctions", "cogs.campaignTransactionFunctions", "cogs.VCfunctions", "cogs.timedMessageTools",
            "cogs.serverFunctions", "cogs.flyoutTools", "cogs.clickupFunctions", "cogs.starboardFunctions",
            "cogs.roleColorTools", "cogs.observatoryFunctions"]


class Bot(commands.Bot):
    def __init__(self, ai_wrapper: AITools):
        # ... (__init__ is unchanged) ...
        super().__init__(command_prefix=commands.when_mentioned_or(prefix), help_command=None, intents=intents,
                         case_insensitive=True)
        self.cogslist = cogsList;
        self.baseConfig = baseConfig;
        self.ownerid = ownerID
        self.botMode = botMode;
        self.geminikey = baseConfig['settings']['geminiapis'].split(",")
        self.AI = ai_wrapper;
        self.sql: SQLtools = None;
        self.ui: UItools = None
        self.pool: asyncpg.Pool = None;
        self.campaignTools: campaignTools = None;
        self.error: errorTools = None

    async def setup_hook(self):
        # ... (setup_hook is unchanged) ...
        self.pool = await asyncpg.create_pool(**SQLsettings, command_timeout=20, max_inactive_connection_lifetime=60)
        self.sql = SQLtools(self.pool);
        self.ui = UItools(self);
        self.campaignTools = campaignTools(self);
        self.error = errorTools(self)
        if updateGithub: cogsList.append("cogs.githubTools")
        for ext in self.cogslist: await self.load_extension(ext)

    # ADDED: New background task to watch for the shutdown file
    async def monitor_shutdown_signal(self):
        signal_file = "shutdown.signal"
        await self.wait_until_ready()
        while not self.is_closed():
            if os.path.exists(signal_file):
                print(f"[{configName}] Shutdown signal file detected. Shutting down gracefully.")
                await self.close()
                break
            await asyncio.sleep(5)  # Check every 5 seconds

    async def on_ready(self):
        await self.wait_until_ready()
        # ADDED: Start the new background task
        self.loop.create_task(self.monitor_shutdown_signal())

        channel = self.get_channel(1152377925916688484)
        if channel:
            await channel.send(f"I am now online! Instance: `{configName}`")
        print(f'Logged in as {self.user} (ID: {self.user.id}) on instance: {configName}')
        print('------')

    async def close(self):
        # ... (close is unchanged) ...
        print(f"[{configName}] Closing database connection pool.")
        if self.pool:
            await self.pool.close()
        await super().close()


# --- Main Execution Block ---
gemini_api_keys = tuple(baseConfig['settings']['geminiapis'].split(","))
gemini_ai_wrapper = GeminiAITools(APIkeys=gemini_api_keys)
bot = Bot(gemini_ai_wrapper)
bot.ishost = botMode


# MODIFIED: Removed all the old signal handling logic
async def main():
    try:
        await bot.start(discordToken)
    except KeyboardInterrupt:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())