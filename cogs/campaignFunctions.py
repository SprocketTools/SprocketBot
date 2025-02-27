import math
import datetime
import random
from datetime import datetime
import discord, time
from discord.ext import commands

import main
from cogs.SQLfunctions import SQLfunctions
from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions
from cogs.textTools import textTools
campaignSettings = {}
campaignServers = {}

class campaignFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        updateCampaignsAtStartup()
        self.bot = bot

    async def updateCampaignServerSettings(ctx: commands.Context):
        campaignFunctions.campaignSettings = await SQLfunctions.databaseFetchdict(f'''SELECT * FROM campaignservers''')

    async def showSettings(ctx: commands.Context):
        try:
            campaignKey = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
            data = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE campaignkey = $1;''', [campaignKey["campaignkey"]])
            date_string = str(data['timedate'])
            format_string = "%Y-%m-%d %H:%M:%S"
            dt = datetime.strptime(date_string, format_string)
            print(dt.year)
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
            embed.add_field(name="Starting pop/worker ratio", value=f"{data['poptoworkerratio']}", inline=False)
            embed.add_field(name="Cost of one ton of steel", value=f"{data['currencysymbol']}{data['steelcost']}", inline=False)
            embed.add_field(name="Cost of barrel of oil", value=f"{data['currencysymbol']}{data['energycost']}",inline=False)
            if data['active'] == True:
                embed.add_field(name="Current status", value=f"**Campaign is running**", inline=False)
            if data['active'] == False:
                embed.add_field(name="Current status", value=f"**Campaign is NOT running**", inline=False)
            embed.set_footer(text=f"It is {hour}:{min} on {day}, {dt.year}")
            return await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error:\n-# {e}\n\nMake sure that you have set up your server and joined, or started, a campaign.")

    async def getUserFactionData(ctx: commands.Context):
        campaignData = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignKey = campaignData['campaignkey']
        factionUserData = await SQLfunctions.databaseFetchdictDynamic('''SELECT factionkey FROM campaignusers WHERE status = true AND userid = $1 AND campaignkey = $2;''', [ctx.author.id, campaignKey])
        campaignNameList = []
        campaignDataList = {}
        for faction in factionUserData:
            name = await campaignFunctions.getFactionName(faction["factionkey"])
            campaignNameList.append(name)
            campaignDataList[str(name)] = faction["factionkey"]
        if len(campaignNameList) == 1:
            factionKey = campaignDataList[campaignNameList[0]]
        elif len(campaignNameList) == 0:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            await ctx.send("You aren't a part of any factions within this campaign!  Join one using `-joinFaction` and then try again.")
        else:
            factionName = await discordUIfunctions.getChoiceFromList(ctx, campaignNameList, "Choose your faction below:")
            factionKey = campaignDataList[factionName]

        factionData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionkey = $1;''', [factionKey])
        print(factionData)

        return factionData

    @commands.command(name="sendMessage", description="Send a message to a campaign")
    async def sendMessage(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        targetData = await campaignFunctions.pickCampaignFaction(ctx, "Choose who you're sending your message to.")
        originName = factionData["factionname"]
        isVulnerable = False
        isIntercepted = False
        if factionData["espionagestaff"] > 10 or ctx.author.id == main.ownerID:
            messagetype = await discordUIfunctions.getButtonChoice(ctx, ["Send a diplomatic message", "Try to impersonate another country"])
            if messagetype == "Try to impersonate another country":
                espionageStaff = factionData['espionagestaff']
                vulnerableThreshold = espionageStaff/(1000+espionageStaff)
                originData = await campaignFunctions.pickCampaignFaction(ctx,"Choose who you're trying to impersonate.")
                originName = originData["factionname"]
                opponentStaff = targetData['espionagestaff']
                interceptThreshold = opponentStaff / (50 + opponentStaff)
                # determine if the message is vulnerable to interception
                isVulnerable = random.random() > vulnerableThreshold
                isIntercepted = random.random() < interceptThreshold

        message = await textTools.getCappedResponse(ctx, "Type out your message here!", 1700)
        messageDescriptor = f"## Message from {originName}:"
        if isVulnerable and isIntercepted:
            messageDescriptor = f"**{factionData['factionname']}** tried to impersonate **{originName}** and sent you this message under their name:"
        await campaignFunctions.sendMessageToFaction(self, targetData['factionkey'], messageDescriptor)
        await campaignFunctions.sendMessageToFaction(self, targetData['factionkey'], message)
        await ctx.send(f"## Message delivered to {targetData['factionname']}!")

    async def sendMessageToFaction(self, factionkey: int, message: str):
        data = await SQLfunctions.databaseFetchrowDynamic('''SELECT logchannel FROM campaignfactions WHERE factionkey = $1;''', [factionkey])
        channel = self.bot.get_channel(data['logchannel'])
        await channel.send(message)


    async def getFactionData(factionkey: int):
        return await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionkey = $1;''', [factionkey])

    async def getFactionName(factionkey: int):
        result = await SQLfunctions.databaseFetchrowDynamic('''SELECT factionname FROM campaignfactions WHERE factionkey = $1;''', [factionkey])
        return result["factionname"]

    async def pickCampaignFaction(ctx: commands.Context, prompt: str):
        # try:
        campaignKey = await campaignFunctions.getCampaignKey(ctx)
        availableFactionsList = await SQLfunctions.databaseFetchdictDynamic(
            '''SELECT factionname, factionkey, money FROM campaignfactions WHERE campaignkey = $1 ORDER BY factionname;''', [campaignKey])
        factionList = []
        factionData = {}
        #print(availableFactionsList)
        for faction in availableFactionsList:
            name = faction["factionname"]
            if name not in factionList:
                factionList.append(name)
                subFactionData = {}
                subFactionData["factionkey"] = faction["factionkey"]
                subFactionData["money"] = faction["money"]
                factionData[name] = subFactionData
        factionChoiceName = await discordUIfunctions.getChoiceFromList(ctx, factionList, prompt)
        dataout = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionname = $1;''', [factionChoiceName])
        print("aaa")
        print(dataout)
        return dataout
        # except Exception:
        #     await errorFunctions.sendError(ctx)
        #     await ctx.send("This server does not have any campaign factions.")

    async def pickCampaignCountry(ctx: commands.Context, prompt: str):
        campaignKey = await campaignFunctions.getCampaignKey(ctx)
        availableFactionsList = await SQLfunctions.databaseFetchdictDynamic(
            '''SELECT * FROM campaignfactions WHERE campaignkey = $1 AND iscountry = true ORDER BY factionname;''', [campaignKey])
        factionList = []
        factionData = {}
        #print(availableFactionsList)
        for faction in availableFactionsList:
            name = faction["factionname"]
            factionList.append(name)
            factionData[name] = faction
        factionChoiceName = await discordUIfunctions.getChoiceFromList(ctx, factionList, prompt)
        return factionData[factionChoiceName]

    async def getUserCampaignData(ctx: commands.Context):
        return await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE campaignkey = (SELECT campaignkey FROM campaignservers WHERE serverid = $1);''', [ctx.guild.id])

    async def getGovernmentType(ctx: commands.Context):
        options = ["Direct Democracy", "Multi Party System", "Two Party System", "Constitutional Monarchy", "Single Party System", "Appointed Successor"]
        prompt = "Pick a type of government."
        answer = await discordUIfunctions.getChoiceFromList(ctx, options, prompt)
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

    async def getGovernmentName(answerIn: float):
        answer = round(answerIn, 3)
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

    async def getTime(date_string: str):
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(str(date_string), format_string)
        print(dt.year)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        return f"{hour}:{min} on {day}, {dt.year}"

    async def getFarmingLatitudeScalar(latitudeI: float):
        latitude = abs(latitudeI)
        if latitude <= 30:
            return 1
        elif latitude <= 66:
            k = 1/26
            init = 30
            return round(1/(math.exp(k*(latitude - init))), 3)
        else:
            return 0.25

    @commands.command(name="farmingTest", description="Ask Hamish a question.")
    async def farmingTest(self, ctx: commands.Context, latitude: float):
        await ctx.send(str(await campaignFunctions.getFarmingLatitudeScalar(latitude)))

    async def showStats(ctx: commands.Context, variablesList, displayType = None):
        if not displayType:
            displayType = "general"
        campaignInfoList = await campaignFunctions.getUserCampaignData(ctx)

        date_string = str(campaignInfoList['timedate'])
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(date_string, format_string)
        print(displayType)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        embed = discord.Embed(title=variablesList["factionname"],description=variablesList["description"], color=discord.Color.random())
        embed.add_field(name="Operational", value=str(variablesList["hostactive"]), inline=False)
        embed.add_field(name="Updates channel", value=f'<#{variablesList["logchannel"]}>', inline=False)
        embed.add_field(name="Discretionary funds", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["money"]))) + " " + campaignInfoList["currencyname"], inline=False)
        if variablesList["iscountry"] == True and displayType == "general":
            embed.add_field(name="Land", value="{:,}".format(int(variablesList["landsize"])) + " km²",inline=False)
            embed.add_field(name="Population size", value=("{:,}".format(int(variablesList["population"]))),inline=False)
            embed.add_field(name="Government type", value=await campaignFunctions.getGovernmentName(variablesList["governance"]), inline=False)
            embed.add_field(name="GDP",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["gdp"]))), inline=False)
        elif variablesList["iscountry"] == True and displayType == "operations":
            embed.add_field(name="Populace happiness", value=str(round(float(variablesList["happiness"])*100, 1)) + "%", inline=False)
            embed.add_field(name="Poverty rate", value=str(round(float(variablesList["povertyrate"]) * 100, 1)) + "%",inline=False)
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
            embed.add_field(name="Median salary", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["averagesalary"]))), inline=False)
            embed.add_field(name="GDP growth",value=str(round(float(variablesList["gdpgrowth"]) * 100, 1)) + "%",inline=False)
            embed.add_field(name="Poor tax", value=str(round(float(variablesList["taxpoor"]) * 100, 1)) + "%", inline=False)
            embed.add_field(name="Rich tax", value=str(round(float(variablesList["taxrich"]) * 100, 1)) + "%", inline=False)
        else:
            embed.add_field(name="Country of origin",value=await campaignFunctions.getFactionName(variablesList["landlordfactionkey"]), inline=False)
        embed.set_footer(text=f"\nIt is {hour}:{min} on {day}, {dt.year}")
        embed.set_thumbnail(url=variablesList["flagurl"])
        return await ctx.send(embed=embed)

    async def showFinances(ctx: commands.Context, variablesList):
        campaignInfoList = await campaignFunctions.getUserCampaignData(ctx)
        if variablesList["iscountry"] == False:
            return
        print(campaignInfoList)
        date_string = str(campaignInfoList['timedate'])
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(date_string, format_string)
        print(dt.year)
        hour = dt.strftime("%I")
        min = dt.strftime("%M %p")
        day = dt.strftime("%A %B %d")
        embed = discord.Embed(title=f'''{variablesList["factionname"]}'s finances''',description=f"These are your finances as of \n{day}, {dt.year}", color=discord.Color.random())

        embed.add_field(name="Discretionary funds", value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["money"]))) + " " + campaignInfoList["currencyname"], inline=False)
        embed.add_field(name="GDP",value=campaignInfoList["currencysymbol"] + ("{:,}".format(int(variablesList["gdp"]))), inline=False)
        embed.add_field(name="GDP growth", value=str(round(float(variablesList["gdpgrowth"]) * 100, 1)) + "%", inline=False)
        embed.add_field(name="Poor tax rate", value=f"{round(float(variablesList['taxpoor'])*100, 3)} %", inline=False) #test
        embed.add_field(name="Rich tax rate", value=f"{round(float(variablesList['taxrich']) * 100, 3)} %", inline=False)
        embed.add_field(name="Average lifespan", value=str(round(float(variablesList["lifeexpectancy"]), 1)) + " years", inline=False)
        embed.add_field(name="Average salary", value=campaignInfoList["currencysymbol"] + str(round(float(variablesList["averagesalary"]), 1)) + " " + campaignInfoList["currencyname"],inline=False)
        embed.add_field(name="Economic index", value=str(round(float(variablesList["incomeindex"]) * 100, 1)) + "%", inline=False)
        embed.add_field(name="Educational funding boost", value=str(round(float(variablesList["educationspend"]) * 100, 1)) + "% of discretionary funds", inline=False)
        embed.add_field(name="Social spending", value=str(round(float(variablesList["socialspend"]) * 100, 1)) + "% of discretionary funds", inline=False)
        embed.add_field(name="Infrastructure investments", value=str(round(float(variablesList["infrastructurespend"]) * 100, 1)) + "% of discretionary funds", inline=False)
        embed.add_field(name="Espionage funding",value=str(round(float(variablesList["espionagespend"]) * 100, 2)) + "% of discretionary funds", inline=False)
        embed.add_field(name="Spy agency staff", value=str(variablesList["espionagestaff"]) + " employees", inline=False)
        embed.set_thumbnail(url=variablesList["flagurl"])
        await ctx.send(embed=embed)

    async def getCampaignName(campaignKey: int):
        data = await SQLfunctions.databaseFetchrowDynamic(f'SELECT * FROM campaigns WHERE campaignkey = $1',[campaignKey])
        if len(data) == 0:
            return
        return data["campaignname"]

    async def getCampaignKey(ctx: commands.Context):
        campaignData = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        return int(campaignData['campaignkey'])

    async def isCampaignManager(ctx: commands.Context):
        try:
            data = await SQLfunctions.databaseFetchrowDynamic(f'SELECT * FROM serverconfig WHERE serverid = $1', [ctx.guild.id])
            roleid = data["campaignmanagerroleid"]
            role = discord.utils.get(ctx.guild.roles, id=roleid)
            if role in ctx.author.roles:
                return True
            return False
        except Exception:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            await ctx.send("It appears your server has not set up its roles correctly.  Ask an administrator to use the `-setup` command and give you the campaign manager role.")
            return False
    async def isCampaignHost(ctx: commands.Context):
        # try:
        data = await SQLfunctions.databaseFetchrowDynamic(f'SELECT * FROM serverconfig WHERE serverid = $1', [ctx.guild.id])
        roleid = data["campaignmanagerroleid"]
        role = discord.utils.get(ctx.guild.roles, id=roleid)
        campaignServData = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        campaignData = await SQLfunctions.databaseFetchrowDynamic('''SELECT hostserverid FROM campaigns WHERE campaignkey = $1;''', [campaignServData["campaignkey"]])
        print(campaignData)
        if role in ctx.author.roles and campaignData["hostserverid"] == ctx.guild.id:
            return True
        return False
        # except Exception:
        #     await errorFunctions.sendError(ctx)
        #     await ctx.send("It appears your server has not set up its roles correctly.  Ask an administrator to use the `-setup` command and give you the campaign manager role.  Note: you must also run this command in the server that the campaign is being hosted from.")
        #     return False



    async def updateCampaignSettings(ctx: commands.Context):
        campaignFunctions.campaignSettings = await SQLfunctions.databaseFetchdict(f'''SELECT * FROM campaigns''')


    async def verifyManager(self, ctx: commands.Context):
        status = False

        if ctx.author.roles.__contains__():
            return status

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignFunctions(bot))

def updateCampaignsAtStartup():
    campaignFunctions.campaignSettings = SQLfunctions.databaseFetchdict(f'''SELECT * FROM campaigns''')
    campaignFunctions.campaignServers = SQLfunctions.databaseFetchdict(f'''SELECT * FROM campaignservers''')