import json
import random

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
        if await campaignFunctions.isCampaignManager(ctx) == False:
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

    @commands.command(name="logMaintenance", description="Log maintenance costs for a country")
    async def logMaintenance(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        moneyAdd = await textTools.getIntResponse(ctx, "How much is the maintenance going to be?  Reply with a number.")
        if moneyAdd < 1:
            await ctx.reply(await errorFunctions.retrieveError(ctx))
            return
        logDetails = await textTools.getResponse(ctx, "Reply with a short description for the maintenance and what it entails.  This will be logged for the campaign managers to view.")
        logDetails = await textTools.mild_sanitize(logDetails)
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''', [moneyAdd, factionData["factionkey"]])
        await ctx.send(f"## Done!\n{factionData['factionname']} has spent {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']} on maintenance costs!")
        channel = self.bot.get_channel(int(campaignData["privatemoneychannelid"]))
        await channel.send(f"### Maintenance costs log\nPurchaser: {factionData['factionname']}\nCost: {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}\nDetails: {logDetails}")
    @commands.command(name="logPurchase", description="Log a purchase made between players")
    async def logPurchase(self, ctx: commands.Context):
        factionData = await campaignFunctions.getUserFactionData(ctx)
        campaignData = await campaignFunctions.getUserCampaignData(ctx)
        factionChoiceName, factionChoiceKey = await campaignFunctions.pickCampaignFaction(ctx, "Who are you purchasing equipment from?")
        factionChoiceData = await campaignFunctions.getFactionData(factionChoiceKey)
        moneyAdd = await textTools.getIntResponse(ctx, "How much is the purchase going to be?")
        logDetails = await textTools.getResponse(ctx, "Describe the transaction and what it entails.  This will be logged for the campaign managers to view.")
        logDetails = await textTools.mild_sanitize(logDetails)
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''', [moneyAdd, factionChoiceKey])
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''', [moneyAdd, factionData["factionkey"]])
        await ctx.send(f"## Done!\n{factionChoiceName} now has {campaignData['currencysymbol']}{moneyAdd} more {campaignData['currencyname']}!")
        channel = self.bot.get_channel(int(campaignData["privatemoneychannelid"]))
        await channel.send(f"### Transaction log\nPurchaser: {factionData['factionname']}\nSeller: {factionChoiceName}\nCost: {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}\nDetails: {logDetails}")
        channel = self.bot.get_channel(int(factionChoiceData["logchannel"]))
        await channel.send(f"### Transaction log\nPurchaser: {factionData['factionname']}\nSeller: you ({factionChoiceName})\nCost: {campaignData['currencysymbol']}{moneyAdd} {campaignData['currencyname']}\nDetails: {logDetails}")

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignFinanceFunctions(bot))