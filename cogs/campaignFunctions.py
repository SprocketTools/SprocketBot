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

    async def fetchCampaignSettings(ctx: commands.Context):
        start_time = time.time()
        for list in campaignSettings:
            print("test")
            if list["hostserverid"] == ctx.guild.id:
                return list
        print("--- %s seconds ---" % (time.time() - start_time))


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