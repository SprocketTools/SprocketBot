import json
import random
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

import main
from cogs.SQLfunctions import SQLfunctions
from cogs.campaignFunctions import campaignFunctions
from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions
from cogs.textTools import textTools
class campaignFinanceFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="addMoney", description="Add money to a faction")
    async def addMoney(self, ctx: commands.Context):
        if await campaignFunctions.isCampaignHost(ctx) == False:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        campaignKey = await campaignFunctions.getCampaignKey(ctx)
        availableFactionsList = await SQLfunctions.databaseFetchdictDynamic('''SELECT factionname, factionkey, money FROM campaignfactions WHERE campaignkey = $1;''', [campaignKey])
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
        prompt = "Select the faction you'd like to add money to."
        factionChoice = await discordUIfunctions.getChoiceFromList(ctx, factionList, prompt)
        moneyAdd = await textTools.getIntResponse(ctx, "How much money do you want to add?")
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        print(factionData)
        money = int(factionData[factionChoice]["money"]) + moneyAdd
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = $1 WHERE factionkey = $2;''', [money, factionData[factionChoice]["factionkey"]])
        await ctx.send(f"## Done!\n{factionChoice} now has {campaignData['currencysymbol']}{money} {campaignData['currencyname']}!")

    @commands.command(name="viewFinances", description="View the statistics of your faction")
    async def viewFinances(self, ctx: commands.Context):
        variablesList = await campaignFunctions.getUserFactionData(ctx)
        await campaignFunctions.showFinances(ctx, variablesList)

    @commands.command(name="logMaintenance", description="Log maintenance costs for a country")
    async def logMaintenance(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        moneyAdd = await textTools.getFlooredIntResponse(ctx, "How much is the maintenance going to be?  Reply with a number.", 1)
        logDetails = await textTools.getResponse(ctx, "Reply with a short description for the maintenance and what it entails.  This will be logged for the campaign managers to view.")
        logDetails = await textTools.mild_sanitize(logDetails)
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''', [moneyAdd, factionData["factionkey"]])
        await ctx.send(f"## Done!\n{factionData['factionname']} has spent {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']} on maintenance costs!")
        channel = self.bot.get_channel(int(campaignData["privatemoneychannelid"]))
        await channel.send(f"### Maintenance costs log\nPurchaser: {factionData['factionname']}\nCost: {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}\nDetails: {logDetails}")

    @commands.command(name="logcivilsale", description="Log a sale into your country")
    async def logcivilsale(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        moneyAdd = await textTools.getIntResponse(ctx, "How much will the sale be for?  Reply with a number.\nNote: this command is only for sales to civilians.  Don't use this to log sales to other factions.")
        if moneyAdd < 1:
            await ctx.reply(await errorFunctions.retrieveError(ctx))
            return
        taxTransfer = 0
        taxTransferChannel = 0
        taxTransferName = ""
        if factionData["iscountry"] == False:
            moneyProfit = await textTools.getIntResponse(ctx, f"How much will you profit from this transaction?\nNote: subtract all expenses from the sale to get this value.")
            factionTaxerData = await campaignFunctions.getFactionData(factionData["landlordfactionkey"])
            taxTransfer = int(factionTaxerData["taxrich"]*moneyProfit)
            taxTransferChannel = factionTaxerData["logchannel"]
            taxTransferName = factionTaxerData["factionname"]
        logDetails = await textTools.getResponse(ctx, "Reply with a short description for the sale and what it entails.  This will be logged for the campaign managers to view.")
        logDetails = await textTools.mild_sanitize(logDetails)
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 - $2 WHERE factionkey = $3;''', [moneyAdd, taxTransfer, factionData["factionkey"]])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''', [taxTransfer, factionData["landlordfactionkey"]])
        await ctx.send(f"## Done!\n{factionData['factionname']} has spent {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']} on maintenance costs!")
        channel = self.bot.get_channel(int(campaignData["privatemoneychannelid"]))
        await channel.send(f"### Maintenance costs log\nPurchaser: {factionData['factionname']}\nCost: {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}\nDetails: {logDetails}")
        if factionData["iscountry"] == False:
            await channel.send(f"Taxes paid to {taxTransferName}: {campaignData['currencysymbol']}{taxTransfer} {campaignData['currencyname']}")
            channel3 = self.bot.get_channel(taxTransferChannel)
            await channel3.send(f"You have received income taxes from {factionData['factionname']}!\nAmount: {campaignData['currencysymbol']}{taxTransfer} {campaignData['currencyname']}")
    @commands.command(name="logPurchase", description="Log a purchase made between players")
    async def logPurchase(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        if not factionData['factionname']:
            return
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        factionChoiceName, factionChoiceKey = await campaignFunctions.pickCampaignFaction(ctx, "Who are you purchasing equipment from?")
        factionChoiceData = await campaignFunctions.getFactionData(factionChoiceKey)
        taxTransfer = 0
        taxTransferChannel = 0
        taxTransferName = ""
        moneyAdd = await textTools.getIntResponse(ctx, "How much is the purchase going to be?")
        if moneyAdd > factionData["money"]:
            await errorFunctions.sendError(ctx)
            await ctx.send("You don't have enough money to finance this transaction!")
            return
        if moneyAdd < 1:
            await errorFunctions.sendError(ctx)
            await ctx.send("A bit crafty, but unfortunately not legal here.")
            return
        if factionChoiceData["iscountry"] == False:
            moneyProfit = await textTools.getIntResponse(ctx, f"How much {factionChoiceName} profit from this transaction?\nNote: subtract all expenses from {campaignData['currencysymbol']}{moneyAdd} to get this value.")
            factionTaxerData = await campaignFunctions.getFactionData(factionChoiceData["landlordfactionkey"])
            taxTransfer = int(factionTaxerData["taxrich"]*moneyProfit)
            taxTransferChannel = factionTaxerData["logchannel"]
            taxTransferName = factionTaxerData["factionname"]

        @commands.command(name="addAutoPurchase", description="Log a purchase made between players")
        async def addAutoPurchase(self, ctx: commands.Context):
            factionData = await campaignFunctions.getUserFactionData(ctx)
            if not factionData['factionname']:
                return
            campaignData = await campaignFunctions.getUserCampaignData(ctx)
            factionChoiceName, factionChoiceKey = await campaignFunctions.pickCampaignFaction(ctx,"Who are you purchasing equipment from?")
            factionChoiceData = await campaignFunctions.getFactionData(factionChoiceKey)
            taxTransfer = 0
            taxTransferChannel = 0
            taxTransferName = ""
            moneyAdd = await textTools.getIntResponse(ctx, "How much is the purchase going to be?")
            if moneyAdd > factionData["money"]:
                await errorFunctions.sendError(ctx)
                await ctx.send("You don't have enough money to finance this transaction!")
                return
            if moneyAdd < 1:
                await errorFunctions.sendError(ctx)
                await ctx.send("A bit crafty, but unfortunately not legal here.")
                return
            if factionChoiceData["iscountry"] == False:
                moneyProfit = await textTools.getIntResponse(ctx,
                                                             f"How much {factionChoiceName} profit from this transaction?\nNote: subtract all expenses from {campaignData['currencysymbol']}{moneyAdd} to get this value.")
                factionTaxerData = await campaignFunctions.getFactionData(factionChoiceData["landlordfactionkey"])
                taxTransfer = int(factionTaxerData["taxrich"] * moneyProfit)
                taxTransferChannel = factionTaxerData["logchannel"]
                taxTransferName = factionTaxerData["factionname"]

        shipDate = await textTools.getResponse(ctx, "When do you anticipate the order being completed?  Specify the month and year.")
        logDetails = await textTools.getResponse(ctx, "Describe anything else about the transaction, such as what equipment is being transferred.  This will be logged for the campaign managers to view.")
        logDetails = await textTools.mild_sanitize(logDetails)
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 - $3 WHERE factionkey = $2;''', [moneyAdd, factionChoiceKey, taxTransfer]) # the faction being purchased from
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''', [moneyAdd, factionData["factionkey"]])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''',[taxTransfer, factionChoiceData["landlordfactionkey"]])
        await ctx.send(f"## Done!\n{factionChoiceName} now has {campaignData['currencysymbol']}{moneyAdd} more {campaignData['currencyname']}!")
        channel = self.bot.get_channel(int(campaignData["privatemoneychannelid"]))
        await channel.send(f"### Transaction log\nPurchaser: {factionData['factionname']}\nSeller: {factionChoiceName}\nCost: {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}\nDetails: {logDetails}\nCompletion date: {shipDate}")
        channel2 = self.bot.get_channel(int(factionChoiceData["logchannel"]))
        await channel2.send(f"### Transaction log\nPurchaser: {factionData['factionname']}\nSeller: you ({factionChoiceName})\nCost: {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}\nDetails: {logDetails}\nCompletion date: {shipDate}")
        if factionChoiceData["iscountry"] == False:
            await channel.send(f"Taxes paid to {taxTransferName}: {campaignData['currencysymbol']}{taxTransfer} {campaignData['currencyname']}")
            await channel2.send(f"Taxes paid to {taxTransferName}: {campaignData['currencysymbol']}{taxTransfer} {campaignData['currencyname']}")
            channel3 = self.bot.get_channel(taxTransferChannel)
            await channel3.send(f"You have received income taxes from {factionChoiceName}!\nAmount: {campaignData['currencysymbol']}{taxTransfer} {campaignData['currencyname']}")

    @commands.command(name="editFaction", description="Log a purchase made between players")
    async def editFaction(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        if factionData['iscountry'] == True:
            await campaignFunctions.showStats(ctx, factionData)
            salary = await textTools.getFlooredIntResponse(ctx, "What will your new median salary be?  Reply with a whole number.  \nTake note that this will directly affect your GDP.  The equation is:\n\n `GDP` = `population` * `average salary` / `population per worker ratio`", 1)
            await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET averagesalary = $1 WHERE factionkey = $2;''', [salary, factionData["factionkey"]])
        bankbal = await textTools.getFlooredIntResponse(ctx,"How much money does your faction have in storage now?  Reply with a whole number.", 1)
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = $1 WHERE factionkey = $2;''', [bankbal, factionData["factionkey"]])
        await ctx.send(f"## Done!\nYour new stats have been set!")


    @commands.command(name="setTaxes", description="Log a purchase made between players")
    async def setTaxes(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        poorTax = await textTools.getIntResponse(ctx, "What will your poor man's income tax percentage be?  Reply with a whole number.")
        richTax = await textTools.getIntResponse(ctx,"What will your rich man's income tax percentage be?  Reply with a whole number.")
        if poorTax > 500 or poorTax < -8:
            await errorFunctions.sendError(ctx)
            await ctx.send()
            return
        if richTax > 500 or richTax < -8:
            await ctx.send(await errorFunctions.retrieveError(ctx))
            return
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET taxpoor = $1 WHERE factionkey = $2;''', [round(poorTax/100, 4), factionData["factionkey"]])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET taxrich = $1 WHERE factionkey = $2;''', [round(richTax/100, 4), factionData["factionkey"]])
        await ctx.send(f"## Done!\nYour new tax rates have been set!")


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignFinanceFunctions(bot))