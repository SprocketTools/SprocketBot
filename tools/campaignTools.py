import math
import datetime
import random
from datetime import datetime
import discord
import type_hintsfrom discord.ext import commands
from cogs.errorFunctions import errorFunctions

class campaignTools:
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    async def updateCampaignServerSettings(self, ctx: commands.Context):
        # This function might need to store settings on `self` instead of a global variable
        # For now, it fetches but doesn't store.
        return await self.bot.sql.databaseFetchdict(f'''SELECT * FROM campaignservers''')

    async def showSettings(self, ctx: commands.Context):
        campaignKey = await self.bot.sql.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        data = await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE campaignkey = $1;''', [campaignKey["campaignkey"]])
        date_string = str(data['timedate'])
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(date_string, format_string)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        embed = discord.Embed(title=f"{data['campaignname']} settings", description="These are the settings encompassing your entire campaign!", color=discord.Color.random())
        embed.add_field(name="Campaign rules", value=f"{data['campaignrules']}", inline=False)
        embed.add_field(name="Time scale", value=f"{data['timescale']}x", inline=False)
        embed.add_field(name="Announcements channel", value=f"<#{data['publiclogchannelid']}>", inline=False)
        embed.add_field(name="Transaction logger", value=f"<#{data['privatemoneychannelid']}>", inline=False)
        embed.add_field(name="Currency symbol", value=f"{data['currencysymbol']}", inline=False)
        embed.add_field(name="Currency name", value=f"{data['currencyname']}", inline=False)
        embed.add_field(name="Baseline GDP growth", value=f"{round(float(data['defaultgdpgrowth'])*100, 2)}%", inline=False)
        embed.add_field(name="Cost of one ton of steel", value=f"{data['currencysymbol']}{data['steelcost']}", inline=False)
        embed.add_field(name="Cost of barrel of oil", value=f"{data['currencysymbol']}{data['energycost']}",inline=False)
        if data['active'] == True:
            embed.add_field(name="Current status", value=f"**Campaign is running**", inline=False)
        if data['active'] == False:
            embed.add_field(name="Current status", value=f"**Campaign is NOT running**", inline=False)
        embed.set_footer(text=f"It is {hour}:{min} on {day}, {dt.year}")
        return await ctx.send(embed=embed)

    async def getUserFactionData(self, ctx: commands.Context):
        campaignData = await self.bot.sql.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignKey = campaignData['campaignkey']
        factionUserData = await self.bot.sql.databaseFetchdictDynamic('''SELECT factionkey FROM campaignusers WHERE status = true AND userid = $1 AND campaignkey = $2;''', [ctx.author.id, campaignKey])
        campaignNameList = []
        campaignDataList = {}
        for faction in factionUserData:
            name = await self.getFactionName(faction["factionkey"])
            campaignNameList.append(name)
            campaignDataList[str(name)] = faction["factionkey"]
        if len(campaignNameList) == 1:
            factionKey = campaignDataList[campaignNameList[0]]
        elif len(campaignNameList) == 0:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            await ctx.send("You aren't a part of any factions within this campaign!  Join one using `-joinFaction` and then try again.")
        else:
            factionName = await ctx.bot.ui.getChoiceFromList(ctx, campaignNameList, "Choose your faction below:")
            factionKey = campaignDataList[factionName]

        factionData = await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionkey = $1;''', [factionKey])
        return factionData

    async def sendMessageToFaction(self, factionkey: int, message: str):
        data = await self.bot.sql.databaseFetchrowDynamic('''SELECT logchannel FROM campaignfactions WHERE factionkey = $1;''', [factionkey])
        channel = self.bot.get_channel(data['logchannel'])
        await channel.send(message)

    async def getFactionData(self, factionkey: int):
        return await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionkey = $1;''', [factionkey])

    async def getFactionName(self, factionkey: int):
        result = await self.bot.sql.databaseFetchrowDynamic('''SELECT factionname FROM campaignfactions WHERE factionkey = $1;''', [factionkey])
        return result["factionname"]

    async def pickCampaignFaction(self, ctx: commands.Context, prompt: str):
        campaignKey = await self.getCampaignKey(ctx)
        availableFactionsList = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT factionname, factionkey, money FROM campaignfactions WHERE campaignkey = $1 ORDER BY factionname;''', [campaignKey])
        factionList = []
        factionData = {}
        for faction in availableFactionsList:
            name = faction["factionname"]
            if name not in factionList:
                factionList.append(name)
                subFactionData = {}
                subFactionData["factionkey"] = faction["factionkey"]
                subFactionData["money"] = faction["money"]
                factionData[name] = subFactionData
        factionChoiceName = await ctx.bot.ui.getChoiceFromList(ctx, factionList, prompt)
        dataout = await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionname = $1;''', [factionChoiceName])
        return dataout

    async def pickCampaignCountry(self, ctx: commands.Context, prompt: str):
        campaignKey = await self.getCampaignKey(ctx)
        availableFactionsList = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND iscountry = true ORDER BY factionname;''', [campaignKey])
        factionList = []
        factionData = {}
        for faction in availableFactionsList:
            name = faction["factionname"]
            factionList.append(name)
            factionData[name] = faction
        factionChoiceName = await ctx.bot.ui.getChoiceFromList(ctx, factionList, prompt)
        return factionData[factionChoiceName]

    async def getUserCampaignData(self, ctx: commands.Context):
        return await self.bot.sql.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE campaignkey = (SELECT campaignkey FROM campaignservers WHERE serverid = $1);''', [ctx.guild.id])

    async def getGovernmentType(self, ctx: commands.Context):
        options = ["Open Council", "Coalition Party System", "Multi Party System", "Two Party System", "Dominant Party System", "Single Party System", "Appointed Successor"]
        prompt = "Pick a type of government."
        answer = await ctx.bot.ui.getChoiceFromList(ctx, options, prompt)
        if answer == "Open Council":
            return -1
        if answer == "Coalition Party System":
            return -0.6
        if answer == "Multi Party System":
            return -0.2
        if answer == "Two Party System":
            return 0.0
        if answer == "Dominant Party System":
            return 0.2
        if answer == "Single Party System":
            return 0.6
        if answer == "Appointed Successor":
            return 1.0
        else:
            return 0.0

    async def getGovernmentName(self, answerIn: float):
        try:
            answer = round(answerIn, 3)
        except Exception:
            return "SET GOVERNMENT TYPE ASAP"

        if answer == -1:
            return "Open Council"
        if answer == -0.6:
            return "Coalition Party System"
        if answer == -0.2:
            return "Multi Party System"
        if answer == 0:
            return "Two Party System"
        if answer == 0.2:
            return "Dominant Party System"
        if answer == 0.6:
            return "Single Party System"
        if answer == 1.0:
            return "Appointed Successor"
        else:
            return "Error"

    async def getTime(self, date_string: str):
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(str(date_string), format_string)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        return f"{hour}:{min} on {day}, {dt.year}"

    async def getFarmingLatitudeScalar(self, latitudeI: float):
        latitude = abs(latitudeI)
        if latitude <= 30:
            return 1
        elif latitude <= 66:
            k = 1/26
            init = 30
            return round(1/(math.exp(k*(latitude - init))), 3)
        else:
            return 0.25

    async def showStats(self, ctx: commands.Context, variablesList, displayType = None):
        if not displayType:
            displayType = "general"
        campaignInfoList = await self.getUserCampaignData(ctx)

        date_string = str(campaignInfoList['timedate'])
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(date_string, format_string)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        embed = discord.Embed(title=variablesList["factionname"],description=variablesList["description"], color=discord.Color.random())
        embed.add_field(name="Operational", value=str(variablesList["hostactive"]), inline=False)
        embed.add_field(name="Updates channel", value=f'<#{variablesList["logchannel"]}>', inline=False)
        try:
            embed.add_field(name="Discretionary funds", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["money"]))) + " " + campaignInfoList["currencyname"], inline=False)
        except Exception:
            await ctx.send("Somehow you had [null] money")

        if variablesList["iscountry"] == True and displayType == "general":
            embed.add_field(name="Land", value="{:,}".format(int(variablesList["landsize"])) + " km²",inline=False)
            embed.add_field(name="Population size", value=("{:,}".format(int(variablesList["population"]))),inline=False)
            embed.add_field(name="Population growth", value=str(round(float(variablesList["popgrowth"])*100, 1)) + "%", inline=False)
            embed.add_field(name="Government type", value=await self.getGovernmentName(variablesList["governance"]), inline=False)
            embed.add_field(name="GDP",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["gdp"]))), inline=False)
        elif variablesList["iscountry"] == True and displayType == "operations":
            embed.add_field(name="Populace happiness", value=str(round(float(variablesList["happiness"])*100, 1)) + "%", inline=False)
            embed.add_field(name="Average lifespan", value=str(round(float(variablesList["lifeexpectancy"]), 1)) + " years", inline=False)
            embed.add_field(name="Education index", value=str(round(float(variablesList["educationindex"]) * 100, 1)) + "%", inline=False)
            embed.add_field(name="Infrastructure index", value=str(round(float(variablesList["infrastructureindex"]) * 100, 1)) + "%", inline=False)
            embed.add_field(name="Core government spending", value=str(round(float(variablesList["corespend"]) * 100, 1)) + "% of tax income", inline=False)
            embed.add_field(name="Infrastructure spending", value=str(round(float(variablesList["infrastructurespend"]) * 100, 1)) + "% of tax income", inline=False)
            embed.add_field(name="Defense spending (your money)", value=str(round(float(variablesList["defensespend"]) * 100, 1)) + "% of tax income", inline=False)
            embed.add_field(name="Espionage funding", value=str(round(float(variablesList["espionagespend"]) * 100, 2)) + "% of discretionary funds", inline=False)
            embed.add_field(name="Spy agency staff", value=str(variablesList["espionagestaff"]) + " employees",inline=False)
            embed.add_field(name="Social spending", value=str(round(float(variablesList["socialspend"]) * 100, 1)) + "% of tax income", inline=False)
        elif variablesList["iscountry"] == True and displayType == "payments":
            povertySalary = campaignInfoList['energycost'] * campaignInfoList['steelcost'] / 7 * variablesList['popworkerratio']
            embed.add_field(name="Poverty rate", value=str(round(float(variablesList["povertyrate"]) * 100, 1)) + "%",inline=False)
            embed.add_field(name="Poverty salary",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(povertySalary))), inline=False)
            embed.add_field(name="Median salary", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["averagesalary"]))), inline=False)
            embed.add_field(name="GDP growth",value=str(round(float(variablesList["gdpgrowth"]) * 100, 1)) + "%",inline=False)
            embed.add_field(name="Pop/Worker ratio", value=str(round(float(variablesList["popworkerratio"]), 1)),inline=False)
            embed.add_field(name="Poor tax", value=str(round(float(variablesList["taxpoor"]) * 100, 1)) + "%", inline=False)
            embed.add_field(name="Rich tax", value=str(round(float(variablesList["taxrich"]) * 100, 1)) + "%", inline=False)
        else:
            embed.add_field(name="Country of origin",value=await self.getFactionName(variablesList["landlordfactionkey"]), inline=False)
        embed.set_footer(text=f"\nIt is {hour}:{min} on {day}, {dt.year}")
        embed.set_thumbnail(url=variablesList["flagurl"])
        return await ctx.send(embed=embed)

    async def showFinances(self, ctx: commands.Context, variablesList):
        campaignInfoList = await self.getUserCampaignData(ctx)
        if variablesList["iscountry"] == False:
            return
        date_string = str(campaignInfoList['timedate'])
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(date_string, format_string)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        embed = discord.Embed(title=f'''{variablesList["factionname"]}'s finances''',description=f"These are your finances as of \n{day}, {dt.year}", color=discord.Color.random())
        embed.add_field(name="Discretionary funds", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["money"]))) + " " + campaignInfoList["currencyname"], inline=False)
        embed.add_field(name="GDP",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["gdp"]))), inline=False)
        embed.add_field(name="GDP growth", value=str(round(float(variablesList["gdpgrowth"]) * 100, 1)) + "%", inline=False)
        embed.add_field(name="Poor tax rate", value=f"{round(float(variablesList['taxpoor'])*100, 3)} %", inline=False)
        embed.add_field(name="Rich tax rate", value=f"{round(float(variablesList['taxrich']) * 100, 3)} %", inline=False)
        embed.add_field(name="Average lifespan", value=str(round(float(variablesList["lifeexpectancy"]), 1)) + " years", inline=False)
        embed.add_field(name="Average salary", value=campaignInfoList["currencysymbol"] + str(round(float(variablesList["averagesalary"]), 1)) + " " + campaignInfoList["currencyname"],inline=False)
        embed.add_field(name="Educational funding boost", value=str(round(float(variablesList["educationspend"]) * 100, 1)) + "% of discretionary funds", inline=False)
        embed.add_field(name="Social spending", value=str(round(float(variablesList["socialspend"]) * 100, 1)) + "% of discretionary funds", inline=False)
        embed.add_field(name="Infrastructure investments", value=str(round(float(variablesList["infrastructurespend"]) * 100, 1)) + "% of discretionary funds", inline=False)
        embed.add_field(name="Espionage funding",value=str(round(float(variablesList["espionagespend"]) * 100, 2)) + "% of discretionary funds", inline=False)
        embed.add_field(name="Spy agency staff", value=str(variablesList["espionagestaff"]) + " employees", inline=False)
        embed.set_thumbnail(url=variablesList["flagurl"])
        await ctx.send(embed=embed)

    async def getCampaignName(self, campaignKey: int):
        data = await self.bot.sql.databaseFetchrowDynamic(f'SELECT * FROM campaigns WHERE campaignkey = $1',[campaignKey])
        if len(data) == 0:
            return
        return data["campaignname"]

    async def getCampaignKey(self, ctx: commands.Context):
        campaignData = await self.bot.sql.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        return int(campaignData['campaignkey'])

    async def isCampaignManager(self, ctx: commands.Context):
        try:
            data = await self.bot.sql.databaseFetchrowDynamic(f'SELECT * FROM serverconfig WHERE serverid = $1', [ctx.guild.id])
            roleid = data["campaignmanagerroleid"]
            role = discord.utils.get(ctx.guild.roles, id=roleid)
            if role in ctx.author.roles:
                return True
            return False
        except Exception:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            await ctx.send("It appears your server has not set up its roles correctly.  Ask an administrator to use the `-setup` command and give you the campaign manager role.")
            return False

    async def isCampaignHost(self, ctx: commands.Context):
        data = await self.bot.sql.databaseFetchrowDynamic(f'SELECT * FROM serverconfig WHERE serverid = $1', [ctx.guild.id])
        roleid = data["campaignmanagerroleid"]
        role = discord.utils.get(ctx.guild.roles, id=roleid)
        campaignServData = await self.bot.sql.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignData = await self.bot.sql.databaseFetchrowDynamic('''SELECT hostserverid FROM campaigns WHERE campaignkey = $1;''', [campaignServData["campaignkey"]])
        if role in ctx.author.roles and campaignData["hostserverid"] == ctx.guild.id:
            return True
        return False

    async def updateCampaignSettings(self, ctx: commands.Context):
        # This function might need to store settings on `self` instead of a global variable
        return await self.bot.sql.databaseFetchdict(f'''SELECT * FROM campaigns''')

    async def verifyManager(self, ctx: commands.Context):
        status = False

        if ctx.author.roles.__contains__():
            return status