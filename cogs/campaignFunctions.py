import math

import discord, time
from discord.ext import commands
from cogs.SQLfunctions import SQLfunctions
from cogs.discordUIfunctions import discordUIfunctions
from cogs.textTools import textTools
campaignSettings = {}
campaignServers = {}

class campaignFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        updateCampaignsAtStartup()
        self.bot = bot

    async def updateCampaignServerSettings(ctx: commands.Context):
        campaignFunctions.campaignSettings = await SQLfunctions.databaseFetchdict(f'''SELECT * FROM campaignservers''')

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
        if len(campaignDataList) == 1:
            factionKey = campaignDataList[campaignNameList[0]]
        else:
            factionName = await discordUIfunctions.getChoiceFromList(ctx, campaignNameList, "Pick your faction below:")
            factionKey = campaignDataList[factionName]

        factionData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionkey = $1;''', [factionKey])
        print(factionData)

        return factionData


    async def getFactionData(factionkey: int):
        return await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionkey = $1;''', [factionkey])

    async def getFactionName(factionkey: int):
        result = await SQLfunctions.databaseFetchrowDynamic('''SELECT factionname FROM campaignfactions WHERE factionkey = $1;''', [factionkey])
        return result["factionname"]

    async def pickCampaignFaction(ctx: commands.Context, prompt: str):
        campaignKey = await campaignFunctions.getCampaignKey(ctx)
        availableFactionsList = await SQLfunctions.databaseFetchdictDynamic(
            '''SELECT factionname, factionkey, money FROM campaignfactions WHERE campaignkey = $1 ORDER BY factionname;''', [campaignKey])
        factionList = []
        factionData = {}
        #print(availableFactionsList)
        for faction in availableFactionsList:
            name = faction["factionname"]
            factionList.append(name)
            subFactionData = {}
            subFactionData["factionkey"] = faction["factionkey"]
            subFactionData["money"] = faction["money"]
            factionData[name] = subFactionData
        factionChoiceName = await discordUIfunctions.getChoiceFromList(ctx, factionList, prompt)
        return factionChoiceName, factionData[factionChoiceName]["factionkey"]

    async def pickCampaignCountry(ctx: commands.Context, prompt: str):
        campaignKey = await campaignFunctions.getCampaignKey(ctx)
        availableFactionsList = await SQLfunctions.databaseFetchdictDynamic(
            '''SELECT factionname, factionkey, money FROM campaignfactions WHERE campaignkey = $1 AND iscountry = true ORDER BY factionname;''', [campaignKey])
        factionList = []
        factionData = {}
        #print(availableFactionsList)
        for faction in availableFactionsList:
            name = faction["factionname"]
            factionList.append(name)
            subFactionData = {}
            subFactionData["factionkey"] = faction["factionkey"]
            subFactionData["money"] = faction["money"]
            factionData[name] = subFactionData
        factionChoiceName = await discordUIfunctions.getChoiceFromList(ctx, factionList, prompt)
        return factionChoiceName, factionData[factionChoiceName]["factionkey"]

    async def getUserCampaignData(ctx: commands.Context):
        return await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE campaignkey = (SELECT campaignkey FROM campaignservers WHERE serverid = $1);''', [ctx.guild.id])

    async def getGovernmentType(ctx: commands.Context):
        options = ["Direct Democracy", "Multi Party System", "Two Party System", "Single Party System", "Appointed Successor"]
        prompt = "Pick a type of government."
        answer = await discordUIfunctions.getChoiceFromList(ctx, options, prompt)
        if answer == "Direct Democracy":
            return 0.8
        if answer == "Multi Party System":
            return 0.9
        if answer == "Two Party System":
            return 1.0
        if answer == "Single Party System":
            return 1.1
        if answer == "Appointed Successor":
            return 1.2

    async def getGovernmentName(answerIn: float):
        answer = round(answerIn, 3)
        if answer == 0.8:
            return "Direct Democracy"
        if answer == 0.9:
            return "Multi Party System"
        if answer == 1.0:
            return "Two Party System"
        if answer == 1.1:
            return "Single Party System"
        if answer == 1.2:
            return "Appointed Successor"
        else:
            return "Error"

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

    async def getCampaignName(campaignKey: int):
        data = await SQLfunctions.databaseFetchrowDynamic(f'SELECT * FROM campaigns WHERE campaignkey = $1',[campaignKey])
        if len(data) == 0:
            return
        return data["campaignname"]

    async def getCampaignKey(ctx: commands.Context):
        campaignData = await SQLfunctions.databaseFetchrowDynamic('''SELECT campaignkey FROM campaignservers WHERE serverid = $1;''', [ctx.guild.id])
        return int(campaignData['campaignkey'])

    async def isCampaignManager(ctx: commands.Context):
        data = await SQLfunctions.databaseFetchrowDynamic(f'SELECT * FROM serverconfig WHERE serverid = $1', [ctx.guild.id])
        roleid = data["campaignmanagerroleid"]
        role = discord.utils.get(ctx.guild.roles, id=roleid)
        if role in ctx.author.roles:
            return True
        return False



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