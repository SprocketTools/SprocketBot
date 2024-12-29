import json
import random, asyncio, datetime
from calendar import calendar
from datetime import datetime
import io
import datetime as dtime
import pandas as pd
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
updateFrequency = 900 # time in seconds

secondsInYear = 31536000 + 21600
## secondsInYear = 20
class campaignUpdateFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        now = datetime.now()
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
        current_time = int(datetime.now().timestamp())
        last_time = int(main.config["settings"]['lastupdated'])
        #print(f'{last_time} --> {current_time}')
        while last_time + (updateFrequency/2) < current_time:
            status_log_channel = self.bot.get_channel(1152377925916688484)
            await status_log_channel.send("Update is starting!")
            await self.errorPrevention()
            await self.updateTime()
            resultStr = await self.runAutoTransactions()
            await self.updatePopulation()
            await self.collectTaxes()
            await self.updateGDP()
            await self.updateHappiness()
            await self.updateEspionage()
            await self.updateLastUpdated()
            if datetime.now().minute < 2:
                await self.sendBackup()
            else:
                print("Campaign update triggered")
            main.config["settings"]['lastupdated'] = str(last_time + updateFrequency)
            await status_log_channel.send(f"Campaigns have updated from <t:{last_time}:f> to <t:{last_time + updateFrequency}:f>")
            last_time = last_time + updateFrequency
        main.config["settings"]['lastupdated'] = str(current_time)
        with open(main.configurationFilepath, "w") as configfile:
            main.config.write(configfile)

    async def errorPrevention(self):
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = 0 WHERE gdp/population < 0 AND iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = 0 WHERE gdp/population < 0 AND iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET gdp = 0 WHERE gdp < 0 AND iscountry = true;''')
    async def updateTime(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET timedate = timedate + make_interval(secs => timescale * $1) WHERE active = true AND active = true;''', [updateFrequency])

    async def updatePopulation(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET population = population + population * 0.1 * POWER((subquery.populationperkm/population), 0.1) * incomeindex * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * subquery.timescale FROM (SELECT timescale, populationperkm FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true AND hostactive = true;''', [updateFrequency, secondsInYear])

    async def collectTaxes(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET money = money + (gdp * ((taxrich * 0.25) + (taxpoor * 0.75)) * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * subquery.timescale * subquery.taxestoplayer * (1 - espionagespend)) FROM (SELECT timescale, taxestoplayer FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true AND hostactive = true;''', [updateFrequency, secondsInYear])

    async def updateGDP(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET averagesalary = averagesalary + averagesalary * defaultgdpgrowth * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * subquery.timescale  FROM (SELECT timescale, defaultgdpgrowth FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true AND hostactive = true;''', [updateFrequency, secondsInYear])
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET gdp = population * averagesalary / popworkerratio WHERE iscountry = true AND hostactive = true;''')

    async def updateIncome(self):
        # await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = CASE WHEN @gdp/population > 20 THEN (1 - (3*(LN((gdp/population) + 182.5)/((gdp/population) + 2)))) ELSE 0 END;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = 1 - 30*(ln((gdp/population)+EXP(1)) / ((gdp/population) + 2))/subquery.poptoworkerratio FROM (SELECT poptoworkerratio FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = 0.01 WHERE incomeindex < 0 AND iscountry = true AND hostactive = true;''')

    async def updateEspionage(self):
        # await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = CASE WHEN @gdp/population > 20 THEN (1 - (3*(LN((gdp/population) + 182.5)/((gdp/population) + 2)))) ELSE 0 END;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET espionagestaff = ROUND(((money*espionagespend)/(averagesalary*10) - espionagestaff)*0.1 + espionagestaff) WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET espionagestaff = 0 WHERE espionagestaff < 0 AND iscountry = true AND hostactive = true;''')

    async def updateEducation(self):
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET lifeexpectancy = 70/governance WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET educationindex = EXP(-2/(POWER((incomeindex * 2000), 0.4))) WHERE iscountry = true AND hostactive = true;''')

    async def updateHappiness(self):
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = POWER((incomeindex * (lifeexpectancy-20)/(85-20) * educationindex * (1 - (POWER(100*taxpoor + 8, 2)/(POWER(100*taxpoor + 8, 2) + 1000)))), 0.333) WHERE iscountry = true AND hostactive = true;''')
        # cleanup for extreme cases, such as falling below zero
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = 0 WHERE gdp/population < 0 AND iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = 0 WHERE happiness < 0 AND iscountry = true AND hostactive = true;''')

    async def sendBackup(self):
        tables = await SQLfunctions.databaseFetchdict('''SELECT table_schema, table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema');''')
        for table in tables:
            tablename = table['table_name']
            print(tablename)
            data = await SQLfunctions.databaseFetchdict(f'SELECT * FROM {tablename};')
            df = pd.DataFrame(data)
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            # Send CSV file
            buffer.seek(0)
            channel = self.bot.get_channel(1156854471767367680)
            await channel.send(file=discord.File(buffer, f'{tablename}-{datetime.now()}.csv'))

    async def runAutoTransactions(self):
        #print("executing auto transactions")
        Wdata = await SQLfunctions.databaseFetchdict('''SELECT * FROM campaigns where EXTRACT(MONTH FROM timedate) != EXTRACT(MONTH FROM lastupdated);''')
        #print(len(Wdata))
        for campaignData in Wdata:
            channel = self.bot.get_channel(campaignData['privatemoneychannelid'])
            await channel.send(f'''---Transactions for: {campaignData['timedate'].strftime("%B")} {campaignData['timedate'].strftime("%Y")}---''')
            subData = await SQLfunctions.databaseFetchdictDynamic('''SELECT * FROM transactions WHERE repeat > 0 AND campaignkey = $1;''', [campaignData['campaignkey']])
            print(f"There are {len(subData)} auto transactions queued")
            for data in subData:

                timeOut = datetime.strptime(str(campaignData['timedate']).split(" ")[0], "%Y-%m-%d")
                print((timeOut.month - 1) % data['repeat'])
                if (timeOut.month - 1) % data['repeat'] == 0:
                    # customerkey BIGINT, sellerkey BIGINT, description VARCHAR, cost BIGINT, saldedate TIMESTAMP, completiondate TIMESTAMP, vehicleid BIGINT, type VARCHAR, repeat INT
                    transactionType = data['type']
                    moneyAdd = data['cost']
                    try:
                        factionData = await campaignFunctions.getFactionData(data['customerkey'])
                    except Exception:
                        factionData = await campaignFunctions.getFactionData(data['sellerkey'])
                    try:
                        factionChoiceData = await campaignFunctions.getFactionData(data['sellerkey'])
                        factionChoiceName = await campaignFunctions.getFactionName(data['sellerkey'])
                    except Exception:
                        factionChoiceData = await campaignFunctions.getFactionData(data['customerkey'])
                        factionChoiceName = "Citizens"
                    factionChoiceKey = data['sellerkey']

                    logDetails = data['description']
                    shipDate = data['repeat']
                    repeatFrequency = data['repeat']

                    if transactionType == "sales of equipment to civilians":
                        await SQLfunctions.databaseExecuteDynamic(
                            '''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''',
                            [moneyAdd, factionData["factionkey"]])  # the faction being purchased from
                        customerID = 0
                        sellerID = factionData["factionkey"]
                        customerName = f"Citizens of {factionData['factionname']}"
                        sellerName = factionData['factionname']
                    if transactionType == "maintenance payments":
                        await SQLfunctions.databaseExecuteDynamic(
                            '''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''',
                            [moneyAdd, factionData["factionkey"]])  # the faction being purchased from
                        customerID = 0
                        sellerID = factionData["factionkey"]
                        customerName = f"Citizens of {factionData['factionname']}"
                        sellerName = factionData['factionname']
                    else:
                        await SQLfunctions.databaseExecuteDynamic(
                            '''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''',
                            [moneyAdd, factionChoiceKey])  # the faction being purchased from
                        await SQLfunctions.databaseExecuteDynamic(
                            '''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''',
                            [moneyAdd, factionData["factionkey"]])  # the user's faction
                        customerID = factionData["factionkey"]
                        sellerID = factionChoiceKey
                        customerName = factionData['factionname']
                        sellerName = factionChoiceName
                    time = await campaignFunctions.getTime(campaignData['timedate'])
                    embed = discord.Embed(title=f"Automatic transaction log", color=discord.Color.random())
                    embed.add_field(name="Customer:", value=f"{customerName}")
                    embed.add_field(name="Seller", value=f"{sellerName}")
                    embed.add_field(name="Cost", value=f"{campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}")
                    embed.add_field(name="Time of purchase", value=f"{time}", inline=False)
                    embed.add_field(name="Details", value=f"{logDetails}", inline=False)
                    embed.set_thumbnail(url=factionData['flagurl'])
                    newTime = campaignData['timedate'] + dtime.timedelta(days=shipDate * 30)
                    format_string = "%Y-%m-%d %H:%M:%S"
                    dt = datetime.strptime(str(newTime), format_string)
                    hour = dt.strftime("%I")
                    min = dt.strftime("%M %p")
                    day = dt.strftime("%A %B %d")
                    embed.add_field(name="Completion date:", value=f"{day}, {dt.year}", inline=False)
                    if repeatFrequency > 0:
                        embed.add_field(name="Repeat frequency:", value=f"{repeatFrequency} months", inline=False)
                    channel = self.bot.get_channel(int(campaignData["privatemoneychannelid"]))
                    await channel.send(embed=embed)
                    if transactionType != "sales of equipment to civilians":
                        channel2 = self.bot.get_channel(int(factionChoiceData["logchannel"]))
                        await channel2.send(embed=embed)
        return "Complete!"













    async def sendTimeUpdates(self):
        data = await SQLfunctions.databaseFetchdict('''SELECT * FROM campaigns where EXTRACT(YEAR FROM timedate) != EXTRACT(YEAR FROM lastupdated);''')
        for campaignData in data:
            channel = self.bot.get_channel(campaignData['publiclogchannelid'])
            date_string = str(campaignData['timedate'])
            format_string = "%Y-%m-%d %H:%M:%S"
            dt = datetime.strptime(date_string, format_string)
            print(dt.year)
            hour = dt.strftime("%I")
            min = dt.strftime("%M %p")
            day = dt.strftime("%A %B %d")
            await channel.send(f"## Happy new year! :tada:\nThe year is now **{dt.year}** in **{campaignData['campaignname']}**")

    async def updateLastUpdated(self):
        await SQLfunctions.databaseExecute(f'''UPDATE campaigns SET lastupdated = timedate;''')

    @commands.command(name="forceTransactions", description="test")
    async def forceTransactions(self, ctx: commands.Context):
        await self.runAutoTransactions()
        await ctx.send("Done!")
    @commands.command(name="forceUpdate", description="test")
    async def forceUpdate(self, ctx: commands.Context):
        current_time = int(datetime.now().timestamp())
        last_time = int(main.config["settings"]['lastupdated'])
        print(f'{last_time} --> {current_time}')
        status_log_channel = self.bot.get_channel(1152377925916688484)
        await status_log_channel.send("Update is starting!")
        await self.updateTime()
        print("Time is complete!")
        resultStr = await self.runAutoTransactions()
        await self.updatePopulation()
        print("Population is complete!")
        await self.collectTaxes()
        print("Taxes is complete!")
        await self.updateGDP()
        print("GDP is complete!")
        await self.updateIncome()
        print("Income is complete!")
        await self.updateEducation()
        print("Education is complete!")
        await self.updateHappiness()
        await self.sendTimeUpdates()
        await self.updateEspionage()
        await self.updateLastUpdated()
        # if datetime.now().minute < 2:
        #     await self.sendBackup()
        # else:
        #     await self.sendBackup()
        main.config["settings"]['lastupdated'] = str(last_time + updateFrequency)
        await status_log_channel.send("Update is complete!")
        main.config["settings"]['lastupdated'] = str(current_time)
        with open(main.configurationFilepath, "w") as configfile:
            main.config.write(configfile)
        await ctx.send("## Done!")

    async def softUpdate(self):
        await self.updateGDP()
        await self.updateHappiness()

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignUpdateFunctions(bot))