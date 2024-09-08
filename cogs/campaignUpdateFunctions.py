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
updateFrequency = 86400 # time in seconds
secondsInYear = 31536000 + 21600
## secondsInYear = 20
class campaignUpdateFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        now = datetime.datetime.now()
        current_minute = now.minute
        current_second = now.second
        seconds_count = int(3600 - (current_minute*60 + current_second))
        seconds_count = seconds_count % updateFrequency
        status_log_channel = self.bot.get_channel(1152377925916688484)
        await status_log_channel.send(f"First campaign update is scheduled for: **{int(seconds_count/60)} minutes,** **{int(seconds_count % 60)} seconds** from now.")
        await asyncio.sleep(seconds_count)
        await self.loopUpdate.start()
    @tasks.loop(seconds=updateFrequency)
    async def loopUpdate(self):
        status_log_channel = self.bot.get_channel(1152377925916688484)
        await status_log_channel.send("Update is starting!")
        await self.errorPrevention()
        await self.updateTime()
        await self.updatePopulation()
        await self.collectTaxes()
        await self.updateGDP()
        await self.updateHappiness()
        await status_log_channel.send("Update is complete!")

    async def errorPrevention(self):
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = 0 WHERE gdp/population < 0 AND iscountry = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = 0 WHERE gdp/population < 0 AND iscountry = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET gdp = 0 WHERE gdp < 0 AND iscountry = true;''')
    async def updateTime(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET timedate = timedate + make_interval(secs => timescale * $1);''', [updateFrequency])

    async def updatePopulation(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET population = population + population * POWER((farmefficiency*farmsize*subquery.populationperkm/population), 0.1) * incomeindex * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * subquery.timescale FROM (SELECT timescale, populationperkm FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true;''', [updateFrequency, secondsInYear])

    async def collectTaxes(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET money = money + (gdp * ((taxrich * 0.25) + (taxpoor * 0.75)) * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * subquery.timescale * subquery.taxestoplayer) FROM (SELECT timescale, taxestoplayer FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true;''', [updateFrequency, secondsInYear])

    async def updateGDP(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET gdp = gdp + gdp * defaultgdpgrowth * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * subquery.timescale  FROM (SELECT timescale, defaultgdpgrowth FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true;''', [updateFrequency, secondsInYear])

    async def updateHappiness(self):
        # await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = CASE WHEN @gdp/population > 20 THEN (1 - (3*(LN((gdp/population) + 182.5)/((gdp/population) + 2)))) ELSE 0 END;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = 1 - 30*(ln((gdp/population)+EXP(1)) / ((gdp/population) + 2))/subquery.poptoworkerratio FROM (SELECT poptoworkerratio FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = 0 WHERE gdp/population < 0 AND iscountry = true;''')

        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET lifeexpectancy = 70/governance WHERE iscountry = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET educationindex = EXP(-2/(POWER((incomeindex * 2000), 0.4))) WHERE iscountry = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = POWER((incomeindex * (lifeexpectancy-20)/(85-20) * educationindex * (1 - (POWER(100*taxpoor + 8, 2)/(POWER(100*taxpoor + 8, 2) + 1000)))), 0.333) WHERE iscountry = true;''')
        # cleanup for extreme cases, such as falling below zero
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = 0 WHERE gdp/population < 0 AND iscountry = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = 0 WHERE happiness < 0 AND iscountry = true;''')

    @commands.command(name="forceUpdate", description="test")
    async def forceUpdate(self, ctx: commands.Context):
        status_log_channel = self.bot.get_channel(1152377925916688484)
        await status_log_channel.send("Update is starting!")
        await self.updateTime()
        await self.updatePopulation()
        await self.collectTaxes()
        await self.updateGDP()
        await self.updateHappiness()
        await status_log_channel.send("Update is complete!")
        await ctx.send("## Done!")

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignUpdateFunctions(bot))