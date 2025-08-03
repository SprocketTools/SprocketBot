from tools.campaignFunctions import campaignFunctions
from discord.ext import commands
from cogs.errorFunctions import errorFunctions


class campaignMapsFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="exampleCommand", description="This is an example command")
    async def exampleCommand(self, ctx: commands.Context):
        await ctx.send("Hello World!")
        await errorFunctions.sendError(ctx)
        await campaignFunctions.showSettings(ctx)
        factionData = await campaignFunctions.getUserFactionData(ctx)
        await campaignFunctions.showStats(ctx, variablesList=factionData)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignMapsFunctions(bot))