
from discord.ext import commands
import type_hints

class campaignMapsFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.command(name="exampleCommand", description="This is an example command")
    async def exampleCommand(self, ctx: commands.Context):
        await ctx.send("Hello World!")
        await self.bot.error.sendError(ctx)
        await ctx.bot.campaignTools.showSettings(ctx)
        factionData = await ctx.bot.campaignTools.getUserFactionData(ctx)
        await ctx.bot.campaignTools.showStats(ctx, variablesList=factionData)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignMapsFunctions(bot))