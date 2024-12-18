import datetime

import discord
from discord.ext import commands
from discord import app_commands

import main
from cogs.SQLfunctions import SQLfunctions
from cogs.campaignFunctions import campaignFunctions
from cogs.discordUIfunctions import discordUIfunctions
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput

from cogs.errorFunctions import errorFunctions

promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools

class campaignTransactionFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name="setupTransactionDatabase", description="testing some stuff")
    async def setupTransactionDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS transactions;''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS transactions (customerkey BIGINT, sellerkey BIGINT, description VARCHAR, cost BIGINT, saldedate TIMESTAMP, completiondate TIMESTAMP, vehicleid BIGINT, type VARCHAR, repeat INT);''')
        await ctx.send("## Done!")

    @commands.command(name="purchase", description="Log a purchase made between players")
    async def purchase(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        if not factionData['factionname']:
            return
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        await ctx.send("What type of transaction are you making?")
        transactionType = str.lower(await discordUIfunctions.getButtonChoice(ctx, ["General purchase transaction", "Maintenance payments", "Sales of equipment to civilians"]))
        if transactionType == "sales of equipment to civilians" or transactionType == "maintenance payments":
            factionChoiceName = "N/A"
            factionChoiceKey = 0
        else:
            factionChoiceData = await campaignFunctions.pickCampaignFaction(ctx, "Who are you purchasing equipment from?")
            factionChoiceName = factionChoiceData['factionname']
            factionChoiceKey = factionChoiceData['factionkey']

        moneyAdd = await textTools.getFlooredIntResponse(ctx, "How much is the purchase or sale going to be?", 1)
        if moneyAdd > factionData["money"]:
            await errorFunctions.sendError(ctx)
            await ctx.send("You don't have enough money to finance this transaction!")
            return

        await ctx.send("Specify the desired frequency of this transaction auto-recurring.  If you do not want this transaction to recur, select 0.")
        repeatFrequency = int(await discordUIfunctions.getButtonChoice(ctx, ['0', '1', '2', '3', '4', '6', '12']))
        # the processor for these will need to use a 12 - current_month
        shipDate = await textTools.getFlooredIntResponse(ctx, "How many months will this order take to complete?", 0)
        logDetails = await textTools.getResponse(ctx, "Describe anything else about the transaction, such as what equipment is being transferred.  This will be logged for the campaign managers to view.")
        if transactionType == "sales of equipment to civilians":
            await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''', [moneyAdd, factionData["factionkey"]]) # the faction being purchased from
            customerID = 0
            sellerID = factionData["factionkey"]
            customerName = f"Citizens of {factionData['factionname']}"
            sellerName = factionData['factionname']
        if transactionType == "maintenance payments":
            await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''', [moneyAdd, factionData["factionkey"]]) # the faction being purchased from
            customerID = 0
            sellerID = factionData["factionkey"]
            customerName = f"Citizens of {factionData['factionname']}"
            sellerName = factionData['factionname']
        else:
            await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''',[moneyAdd, factionChoiceKey])  # the faction being purchased from
            await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''',[moneyAdd, factionData["factionkey"]]) # the user's faction
            customerID = factionData["factionkey"]
            sellerID = factionChoiceKey
            customerName = factionData['factionname']
            sellerName = factionChoiceName
        await ctx.send(f"## Done!\n{factionChoiceName} now has {campaignData['currencysymbol']}{moneyAdd} more {campaignData['currencyname']}!")
        time = await campaignFunctions.getTime(campaignData['timedate'])
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO transactions VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)''', [customerID, sellerID, logDetails, moneyAdd, campaignData['timedate'], campaignData['timedate'] + datetime.timedelta(days=(shipDate*30)), 0, transactionType, repeatFrequency])
        embed = discord.Embed(title=f"Transaction log", color=discord.Color.random())
        embed.add_field(name="Customer:", value=f"{customerName}", inline=False)
        embed.add_field(name="Seller", value=f"{sellerName}", inline=False)
        embed.add_field(name="Cost", value=f"{campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}", inline=False)
        embed.add_field(name="Time of purchase", value=f"{time}", inline=False)
        embed.add_field(name="Details", value=f"{logDetails}", inline=False)
        embed.set_thumbnail(url=factionData['flagurl'])
        newTime = campaignData['timedate'] + datetime.timedelta(days=shipDate*30)
        format_string = "%Y-%m-%d %H:%M:%S"
        dt = datetime.datetime.strptime(str(newTime), format_string)
        print(dt.year)
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


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignTransactionFunctions(bot))