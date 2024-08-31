import json
import random, asyncio, datetime
from discord.ext import tasks
import discord
from discord.ext import commands
from discord import app_commands

import main
from cogs.SQLfunctions import SQLfunctions
from cogs.campaignFunctions import campaignFunctions
from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions
from cogs.textTools import textTools

class campaignUpdateFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        now = datetime.datetime.now()
        current_minute = now.minute
        current_second = now.second
        seconds_count = int(3600 - (current_minute*60 + current_second))
        if seconds_count > 1810:
            seconds_count = seconds_count - 1800
        status_log_channel = self.bot.get_channel(1152377925916688484)
        await status_log_channel.send(f"First campaign update is scheduled for: **{int(seconds_count/60)} minutes,** **{int(seconds_count % 60)} seconds** from now.")
        await asyncio.sleep(seconds_count)
        await self.loopUpdate.start()
    @tasks.loop(seconds=1800)
    async def loopUpdate(self):
        status_log_channel = self.bot.get_channel(1152377925916688484)
        await status_log_channel.send("Update is complete!")

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignUpdateFunctions(bot))