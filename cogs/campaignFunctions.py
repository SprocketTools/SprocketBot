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
        factionData = await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignusers WHERE userid = $1 AND campaignkey = $2 AND status = true;''', [ctx.author.id, campaignKey])
        factionKey = factionData["factionkey"]
        return await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionkey = $1;''', [factionKey])

    async def getFactionData(factionkey: int):
        return await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaignfactions WHERE factionkey = $1;''', [factionkey])

    async def pickCampaignFaction(ctx: commands.Context, prompt: str):
        campaignKey = await campaignFunctions.getCampaignKey(ctx)
        availableFactionsList = await SQLfunctions.databaseFetchdictDynamic(
            '''SELECT factionname, factionkey, money FROM campaignfactions WHERE campaignkey = $1;''', [campaignKey])
        factionList = []
        factionData = {}
        print(availableFactionsList)
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
        return await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])

    async def getGovernmentType(ctx: commands.Context):
        options = ["Republic", "Democracy", "Statist", "Monarchy", "Socialism"]
        prompt = "Pick a type of government."
        answer = await discordUIfunctions.getChoiceFromList(ctx, options, prompt)
        if answer == "Republic":
            return 0.8
        if answer == "Democracy":
            return 0.9
        if answer == "Statist":
            return 1.0
        if answer == "Monarchy":
            return 1.1
        if answer == "Socialism":
            return 1.2

    async def getGovernmentName(answerIn: float):
        answer = round(answerIn, 3)
        if answer == 0.8:
            return "Republic"
        if answer == 0.9:
            return "Democracy"
        if answer == 1.0:
            return "Statist"
        if answer == 1.1:
            return "Monarchy"
        if answer == 1.2:
            return "Socialism"
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