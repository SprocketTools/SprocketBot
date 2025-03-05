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
            await self.updateHappiness()
            await self.updatePopulation()

            await self.collectTaxes()
            await self.updateGDP()

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
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = 0.01 WHERE happiness < 0.01 AND iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET averagesalary = 1 WHERE averagesalary < 1 AND iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET lifeexpectancy = 0.01 WHERE lifeexpectancy < 0.01 AND iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET infrastructureindex = 0.01 WHERE infrastructureindex < 0.01 AND iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET educationindex = 0.01 WHERE educationindex < 0.01 AND iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET gdp = 1 WHERE gdp < 0 AND iscountry = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET happiness = LEAST(GREATEST(happiness, 0.01), 1) WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET socialspend = LEAST(GREATEST(socialspend, 0), 1) WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET povertyrate = LEAST(GREATEST(povertyrate, 0), 1) WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET popworkerratio = LEAST(GREATEST(popworkerratio, 1), 5) WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET averagesalary = LEAST(GREATEST(averagesalary, 1), 50000) WHERE iscountry = true AND hostactive = true;''')


    async def updateTime(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET timedate = timedate + make_interval(secs => timescale * $1) WHERE active = true AND active = true;''', [updateFrequency])

    async def updatePopulation(self):
        # data = await SQLfunctions.databaseFetch('''SELECT factionkey FROM campaignfactions;''')
        # for faction in data:
        #     print(faction)
        #     await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions
        #     SET population = GREATEST(population + ROUND(((CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT)) * population * ((0.5*ATAN(500000/landsize) + 0.3*(1-latitude/90) + 0.2*(LN(population) + LN(gdp))) + (1 - 0.3*educationindex) + (4-lifeexpectancy/20) + (0.5*POWER(povertyrate, 0.5) - 0.2)))), 0)
        #     FROM (SELECT timescale, populationperkm FROM campaigns WHERE campaignkey = campaignkey) AS subquery
        #     WHERE factionkey = $3 AND iscountry = true;''', [updateFrequency, secondsInYear, int(faction[0])]) #iscountry = true AND hostactive = true
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions 
        SET population = GREATEST(population + ROUND(((CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT)) * population * 0.001 * ((0.5*ATAN(500000/landsize) + 0.3*(1-latitude/90) + 0.2*(LN(population) + LN(gdp))) + (1 - 0.3*educationindex) + (4-lifeexpectancy/20) + (0.5*POWER(povertyrate, 0.5) - 0.2)))), 0)
        FROM (SELECT timescale, populationperkm FROM campaigns WHERE campaignkey = campaignkey) AS subquery 
        WHERE iscountry = true AND hostactive = true;''', [updateFrequency, secondsInYear]) #iscountry = true AND hostactive = true

        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions 
                SET popgrowth = ((population * 0.001 * ((0.5*ATAN(500000/landsize) + 0.3*(1-latitude/90) + 0.2*(LN(population) + LN(gdp))) + (1 - 0.3*educationindex) + (4-lifeexpectancy/20) + (0.5*POWER(povertyrate, 0.5) - 0.2)))/population)
                FROM (SELECT timescale, populationperkm FROM campaigns WHERE campaignkey = campaignkey) AS subquery 
                WHERE iscountry = true AND hostactive = true;''')  # iscountry = true AND hostactive = true

    async def updatePoverty(self):
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions
        SET povertyrate = (2 * (ATAN(POWER((subquery.energycost * subquery.steelcost / 7 * popworkerratio)/averagesalary, 2.4))/PI()))
        FROM campaigns AS subquery 
        WHERE campaignfactions.iscountry = true AND subquery.campaignkey = campaignfactions.campaignkey AND campaignfactions.hostactive = true;''')

    async def collectTaxes(self):
        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET money = money + (gdp * ((taxrich * 0.25) + (taxpoor * 0.75)) * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * subquery.timescale * defensespend) FROM (SELECT timescale FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true AND hostactive = true;''', [updateFrequency, secondsInYear])

    async def updateGDP(self):
        #         await SQLfunctions.databaseExecute(
        #             f'''UPDATE campaignfactions
        #             SET gdpgrowth = defaultgdpgrowth + (1 - EXP(-0.6*infrastructureindex + 0.4*taxpoor + 0.1*taxrich + 0.3*povertyrate - 0.5*educationindex))
        #             FROM (SELECT defaultgdpgrowth FROM campaigns WHERE campaignkey = campaignkey) AS subquery
        #             WHERE iscountry = true AND hostactive = true;''')

        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET popworkerratio = 4.0 - (5.02 * CAST(povertyrate AS numeric))/2.01;''')


        print("made it here")
        await SQLfunctions.databaseExecute(
            f'''UPDATE campaignfactions 
            SET gdpgrowth = subquery.defaultgdpgrowth + (0.5 * (1-(1.000*(0.9*CAST(taxpoor AS FLOAT) + 0.1*CAST(taxrich AS FLOAT)))) * (0.5 * 2*ATAN(2*(infrastructureindex - 0.5)) + 0.5*2*ATAN(2*(0.5 - taxpoor)) + 0.5*2*ATAN(2*(0.5 - taxrich)) + 0.5*2*ATAN(2*(povertyrate - 0.5)) + 0.5*2*ATAN(2*(educationindex - 0.5))  ))/(2.71*PI()) 
            FROM (SELECT defaultgdpgrowth FROM campaigns WHERE campaignkey = campaignkey) AS subquery 
            WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET corespend = (1.0 - (socialspend + infrastructurespend + defensespend)) WHERE iscountry = true AND hostactive = true;''')

        await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET averagesalary = averagesalary + averagesalary * gdpgrowth * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * subquery.timescale  FROM (SELECT timescale, defaultgdpgrowth FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true AND hostactive = true;''', [updateFrequency, secondsInYear])
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET gdp = population * averagesalary / popworkerratio / (1-(1.000*(0.9*CAST(taxpoor AS FLOAT) + 0.1*CAST(taxrich AS FLOAT)))) WHERE iscountry = true AND hostactive = true;''')
        #await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET averagesalary = CAST(averagesalary * (1-(1.00012*(0.9*CAST(taxpoor AS FLOAT) + 0.1*CAST(taxrich AS FLOAT)))) AS INT);''')

    async def updateIncome(self):
        pass
        # await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = CASE WHEN @gdp/population > 20 THEN (1 - (3*(LN((gdp/population) + 182.5)/((gdp/population) + 2)))) ELSE 0 END;''')
        #await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = 1 - 30*(ln((gdp/population)+EXP(1)) / ((gdp/population) + 2))/subquery.poptoworkerratio FROM (SELECT poptoworkerratio FROM campaigns WHERE campaignkey = campaignkey) AS subquery WHERE iscountry = true AND hostactive = true;''')
        #await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = 0.01 WHERE incomeindex < 0 AND iscountry = true AND hostactive = true;''')

    async def updateEspionage(self):
        # await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET incomeindex = CASE WHEN @gdp/population > 20 THEN (1 - (3*(LN((gdp/population) + 182.5)/((gdp/population) + 2)))) ELSE 0 END;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET espionagestaff = ROUND((((gdp * ((taxrich * 0.25) + (taxpoor * 0.75))) * espionagespend)/(averagesalary*10) - espionagestaff)*0.1 + espionagestaff) WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET espionagestaff = 0 WHERE espionagestaff < 0 AND iscountry = true AND hostactive = true;''')

    async def updateEducation(self):

        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET lifeexpectancy = GREATEST(((65 + 30*(0.2*happiness - 1*LN(povertyrate + taxpoor  + 1.5 - socialspend) + 0.4*infrastructureindex)) - lifeexpectancy) * 0.902 + lifeexpectancy, 0) WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET infrastructureindex = GREATEST(((1.6*ATAN(infrastructurespend * (gdp * ((taxrich * 0.25) + (taxpoor * 0.75)))/population)/PI() + 0.1*governance) - infrastructureindex) * 0.902 + infrastructureindex, 0) WHERE iscountry = true AND hostactive = true;''')

        #await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET educationindex = LEAST(GREATEST(((0.5*LN(socialspend * (gdp * ((taxrich * 0.25) + (taxpoor * 0.75)))/population + 0.1) + 0.3/(1 + EXP(-0.1*(population/landsize))) + 0.2*governance) - educationindex) * 0.902 + educationindex, 0.005), 1) WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions SET socialspend = corespend * (0.5 + governance/2) WHERE iscountry = true AND hostactive = true;''')

    async def updateHappiness(self):
        # await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions
        # SET happiness = LEAST(1, GREATEST( (1-povertyrate)*ATAN(socialspend*(1-((taxpoor*0.75)+(taxrich*0.75))) + (5/9))/2        + (0.3*(lifeexpectancy/80)) + (0.2*LOG((gdp/population) + 0.25) / LOG(1.25)) + (0.1*((governance + 1) / 2)) - (0.1*(taxpoor*((4 - governance) / 5))), 0))
        # WHERE iscountry = true AND hostactive = true;''')
        await SQLfunctions.databaseExecute(f'''UPDATE campaignfactions
        SET happiness = LEAST(1, GREATEST(     (2/PI())*ATAN(0.5*(               (1 - povertyrate) * (ATAN(socialspend * (1 - (0.75 * taxpoor + 0.75 * taxrich)) + (5/9)) / 2) + 0.3 * (lifeexpectancy / 80) + 0.2 * (LN((gdp / population) + 0.25) / ln(1.25))  + 0.1 * ((governance + 1)^2) + 0.1 * (taxpoor * 5 * (4 - governance))               ))    , 0))
        WHERE iscountry = true AND hostactive = true;''')




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

    @commands.command(name="backup", description="test")
    async def backup(self, ctx):
        await self.sendBackup()


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
        await self.errorPrevention()
        await self.updatePoverty()
        await self.updateTime()
        print("Time is complete!")

        await self.updatePopulation()
        #await self.sendBackup()
        await self.updatePoverty()
        #resultStr = await self.runAutoTransactions()


        print("Population is complete!")
        await self.collectTaxes()
        print("Taxes is complete!")
        await self.updateGDP()
        print("GDP is complete!")
        await self.updateIncome()
        await self.updateHappiness()
        print("Income is complete!")
        await self.updateEducation()
        print("Education is complete!")

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