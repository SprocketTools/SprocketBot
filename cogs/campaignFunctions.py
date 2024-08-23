import discord, time
from discord.ext import commands
from cogs.SQLfunctions import SQLfunctions
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

    async def getUserCampaignData(ctx: commands.Context):
        return await SQLfunctions.databaseFetchrowDynamic('''SELECT * FROM campaigns WHERE hostserverid = $1;''', [ctx.guild.id])

    async def getCampaignName(campaignKey: int):
        data = await SQLfunctions.databaseFetchrowDynamic(f'SELECT * FROM campaigns WHERE campaignkey = $1',[campaignKey])
        if len(data) == 0:
            return
        return data["campaignname"]
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