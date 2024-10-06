import discord
from discord.ext import commands
from typing import List

from cogs.campaignFunctions import campaignFunctions
from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions
from discord.ui import Button, View
promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions
from cogs.SQLfunctions import SQLfunctions
class campaignManageFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="manageCampaign", description="Add money to a faction")
    async def manageCampaign(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignHost(ctx) == False:
            return
        while True:
            key = await campaignFunctions.getCampaignKey(ctx)
            await campaignFunctions.showSettings(ctx)
            await ctx.send("What statistic do you wish to modify?")
            answer = str.lower(await discordUIfunctions.getButtonChoice(ctx, ["Name", "Rules", "Time scale", "Adjust time", "Currency name", "Currency symbol", "Pop to worker ratio", "Start/stop campaign", "Exit"]))
            print(answer)
            if answer == "exit":
                await ctx.send("Alright, have fun.")
                return
            elif answer == "adjust time":
                timestamp_adj = await textTools.getIntResponse(ctx, "How many days do you want to move forward?")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET timedate = timedate + make_interval(days => CAST ($1 AS INT)) WHERE campaignkey = $2;''',[timestamp_adj, key])
            elif answer == "start/stop campaign":
                await campaignManageFunctions.toggleCampaignProgress(ctx)
            elif answer == "time scale":
                timescale_adj = await textTools.getFlooredFloatResponse(ctx, "What is the new timescale you wish to use?", 1)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET timescale = $1 WHERE campaignkey = $2;''',[timescale_adj, key])
            elif answer == "name":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new name of the campaign?", 128)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET campaignname = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "pop to worker ratio":
                ratio_adj = await textTools.getFlooredFloatResponse(ctx, "What is the new default pop/worker ratio you wish to use?", 1)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET poptoworkerratio = $1 WHERE campaignkey = $2;''',[ratio_adj, key])
            elif answer == "rules":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new rules of the campaign?", 256)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET campaignrules = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "currency name":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new currency name of the campaign?", 32)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET currencyname = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "currency symbol":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new currency symbol of the campaign?", 2)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET currencysymbol = $1 WHERE campaignkey = $2;''',[name_adj, key])
            else:
                await ctx.send("Looks like you clicked on an unsupported button, or this window timed out.")
            await ctx.send("## Done!")

    @commands.command(name="manageFaction", description="Add money to a faction")
    async def manageFaction(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignHost(ctx) == True:
            factionName, key = await campaignFunctions.pickCampaignFaction(ctx, "Pick the faction you would like to manage.")
            data = await campaignFunctions.getFactionData(key)
        else:
            data = await campaignFunctions.getUserFactionData(ctx)
            key = data["factionkey"]
        print(data)

        while True:
            data = await campaignFunctions.getFactionData(key)
            await campaignFunctions.showStats(ctx, data)
            await ctx.send("What statistic do you wish to modify?")
            answer = str.lower(await discordUIfunctions.getButtonChoice(ctx, ["Name", "Description", "Discretionary funds", "Median salary", "Population", "Exit"]))
            print(answer)
            if answer == "exit":
                await ctx.send("Alright, have fun.")
                return
            elif answer == "discretionary funds":
                money_adj = await textTools.getIntResponse(ctx, "What is your new discetionary balance?  Reply with a number.")
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET money = $1 WHERE factionkey = $2;''',[money_adj, key])
            elif answer == "median salary":
                salary_adj = await textTools.getFlooredIntResponse(ctx, "What is your new median salary?  Reply with a number.", 1)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET averagesalary = $1 WHERE factionkey = $2;''',[salary_adj, key])
            elif answer == "name":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new name of the faction?", 64)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET factionname = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "description":
                desc_adj = await textTools.getCappedResponse(ctx, "What is the new description?", 256)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET description = $1 WHERE factionkey = $2;''',[desc_adj, key])
            elif answer == "population":
                pop_adj = await textTools.getFlooredIntResponse(ctx, "What is your new population?  Reply with a number.", 1000)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaignfactions SET population = $1 WHERE factionkey = $2;''',[pop_adj, key])
            elif answer == "pop to worker ratio":
                ratio_adj = await textTools.getFlooredFloatResponse(ctx, "What is the new default pop/worker ratio you wish to use?", 1)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET poptoworkerratio = $1 WHERE campaignkey = $2;''',[ratio_adj, key])
            elif answer == "rules":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new rules of the campaign?", 256)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET campaignrules = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "currency name":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new currency name of the campaign?", 32)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET currencyname = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "currency symbol":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new currency symbol of the campaign?", 2)
                await SQLfunctions.databaseExecuteDynamic(f'''UPDATE campaigns SET currencysymbol = $1 WHERE campaignkey = $2;''',[name_adj, key])
            else:
                await ctx.send("Looks like you clicked on an unsupported button, or this window timed out.")
            await ctx.send("## Done!")

    async def toggleCampaignProgress(ctx: commands.Context):
        if await campaignFunctions.isCampaignHost(ctx) == False:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        if campaignData["hostserverid"] != ctx.guild.id:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaigns SET active = NOT active WHERE hostserverid = $1;''',[ctx.guild.id])

        result = await SQLfunctions.databaseFetchlistDynamic('''SELECT campaignname, active, campaignkey FROM campaigns WHERE hostserverid = $1;''',[ctx.guild.id])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET hostactive = $1 WHERE campaignkey = $2;''', [result[1], result[2]])
async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignManageFunctions(bot))

class getCampaignSettingButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=360)
        self.value = None

    @discord.ui.button(label="Description", style=discord.ButtonStyle.blurple)
    async def callbackDesc(self, a, b):
        self.value = "description"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="Rules link", style=discord.ButtonStyle.grey)
    async def callbackRules(self, a, b):
        self.value = "rules"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="Time scale", style=discord.ButtonStyle.green)
    async def callbackTimescale(self, a, b):
        self.value = "timescale"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="Adjust time", style=discord.ButtonStyle.blurple)
    async def callbackTime(self, a, b):
        self.value = "time"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="pop/worker ratio", style=discord.ButtonStyle.grey)
    async def callbackRatio(self, a, b):
        self.value = "incomeratio"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="Start/stop campaign", style=discord.ButtonStyle.red)
    async def callbackProgress(self, a, b):
        self.value = "startstop"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.green)
    async def callbackExit(self, a, b):
        self.value = "exit"
        await a.response.defer()
        self.stop()