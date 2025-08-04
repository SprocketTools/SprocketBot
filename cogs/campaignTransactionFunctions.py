import datetime
from random import random
import main
import discord
from discord.ext import commands
promptResponses = {}
from cogs.textTools import textTools

class campaignTransactionFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name="setupTransactionDatabase", description="testing some stuff")
    async def setupTransactionDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS transactions;''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS transactions (customerkey BIGINT, sellerkey BIGINT, campaignkey BIGINT, description VARCHAR, cost BIGINT, saldedate TIMESTAMP, completiondate TIMESTAMP, vehicleid BIGINT, type VARCHAR, repeat INT);''')
        await ctx.send("## Done!")

    @commands.command(name="purchase", description="Log a purchase made between players")
    async def purchase(self, ctx: commands.Context):
        campaignData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        if ctx.channel.id == campaignData['privatemoneychannelid'] or ctx.channel.id == campaignData['publiclogchannelid']:
            await self.bot.error.sendCategorizedError(ctx, "insult")
            await ctx.send("\nLast I checked, this was your server's logging channel.  Typically these are not for running bot commands in.")
            return
        factionData = await ctx.bot.campaignTools.getUserFactionData(ctx)
        if not factionData['factionname']:
            return
        await ctx.send("What type of transaction are you making?")
        transactionType = str.lower(await ctx.bot.ui.getButtonChoice(ctx, ["General purchase transaction", "Maintenance payments", "Sales of equipment to civilians"]))
        if transactionType == "sales of equipment to civilians" or transactionType == "maintenance payments":
            factionChoiceName = "N/A"
            factionChoiceKey = 0
        else:
            factionChoiceData = await ctx.bot.campaignTools.pickCampaignFaction(ctx, "Who are you purchasing equipment from?")
            factionChoiceName = factionChoiceData['factionname']
            factionChoiceKey = factionChoiceData['factionkey']

        moneyAdd = await textTools.getFlooredIntResponse(ctx, "How much is the purchase or sale going to be?", 1)
        if moneyAdd > factionData["money"] and transactionType != "sales of equipment to civilians":
            await self.bot.error.sendError(ctx)
            await ctx.send("You don't have enough money to finance this transaction!")
            return

        await ctx.send("Specify the desired frequency of this transaction recurring, in months.\nEx: selecting '12' means the transaction will repeat every 12 months.\nIf you do not want this transaction to repeat, select 0.")
        repeatFrequency = int(await ctx.bot.ui.getButtonChoice(ctx, ['0', '1', '2', '3', '4', '6', '12']))
        # the processor for these will need to use a 12 - current_month
        shipDate = await textTools.getFlooredIntResponse(ctx, "How many months will this order take to complete?", 0)
        logDetails = await textTools.getResponse(ctx, "Describe anything else about the transaction, such as what equipment is being transferred.  This will be logged for the campaign managers to view.")
        if transactionType == "sales of equipment to civilians":
            await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''', [moneyAdd, factionData["factionkey"]]) # the faction being purchased from
            customerID = 0
            sellerID = factionData["factionkey"]
            customerName = f"Citizens of {factionData['factionname']}"
            sellerName = factionData['factionname']
        if transactionType == "maintenance payments":
            await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''', [moneyAdd, factionData["factionkey"]]) # the faction being purchased from
            customerID = 0
            sellerID = factionData["factionkey"]
            customerName = f"Citizens of {factionData['factionname']}"
            sellerName = factionData['factionname']
        else:
            await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;''',[moneyAdd, factionChoiceKey])  # the faction being purchased from
            await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;''',[moneyAdd, factionData["factionkey"]]) # the user's faction
            customerID = factionData["factionkey"]
            sellerID = factionChoiceKey
            customerName = factionData['factionname']
            sellerName = factionChoiceName
        await ctx.send(f"## Done!\n{factionChoiceName} now has {campaignData['currencysymbol']}{moneyAdd} more {campaignData['currencyname']}!")
        time = await ctx.bot.campaignTools.getTime(campaignData['timedate'])
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO transactions VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)''', [customerID, sellerID, campaignData['campaignkey'], logDetails, moneyAdd, campaignData['timedate'], campaignData['timedate'] + datetime.timedelta(days=(shipDate*30)), 0, transactionType, repeatFrequency])
        embed = discord.Embed(title=f"Transaction log", color=discord.Color.random())
        embed.add_field(name="Customer:", value=f"{customerName}", inline=False)
        embed.add_field(name="Seller", value=f"{sellerName}", inline=False)
        embed.add_field(name="Cost", value=f"{campaignData['currencysymbol']}{'{:,}'.format(moneyAdd)} {campaignData['currencyname']}", inline=False)
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

    @commands.command(name="sendMessage", description="Send a message to a campaign")
    async def sendMessage(self, ctx: commands.Context):
        factionData = await self.getUserFactionData(ctx)
        targetData = await self.pickCampaignFaction(ctx, "Choose who you're sending your message to.")
        originName = factionData["factionname"]
        isVulnerable = False
        isIntercepted = False
        if factionData["espionagestaff"] > 10 or ctx.author.id == ctx.bot.ownerID:
            messagetype = await ctx.bot.ui.getButtonChoice(ctx, ["Send a diplomatic message", "Try to impersonate another country"])
            if messagetype == "Try to impersonate another country":
                espionageStaff = factionData['espionagestaff']
                vulnerableThreshold = espionageStaff/(1000+espionageStaff)
                originData = await self.pickCampaignFaction(ctx,"Choose who you're trying to impersonate.")
                originName = originData["factionname"]
                opponentStaff = targetData['espionagestaff']
                interceptThreshold = opponentStaff / (50 + opponentStaff)
                isVulnerable = random() > vulnerableThreshold
                isIntercepted = random() < interceptThreshold

        message = await textTools.getCappedResponse(ctx, "Type out your message here!", 1700)
        messageDescriptor = f"## Message from {originName}:"
        if isVulnerable and isIntercepted:
            messageDescriptor = f"**{factionData['factionname']}** tried to impersonate **{originName}** and sent you this message under their name:"
        await self.sendMessageToFaction(targetData['factionkey'], messageDescriptor)
        await self.sendMessageToFaction(targetData['factionkey'], message)
        await ctx.send(f"## Message delivered to {targetData['factionname']}!")

    @commands.command(name="cancelTransaction", description="Cancel an automatic purchase")
    async def cancelTransaction(self, ctx: commands.Context):
        campaignData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        factionData = await ctx.bot.campaignTools.getUserFactionData(ctx)
        data = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM transactions WHERE customerkey = $1 AND repeat > 0;''', [factionData['factionkey']])
        nameList = []
        for item in data:
            nameList.append(f"{campaignData['currencysymbol']}{str(item['cost'])} - {item['description']}")
        data = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM transactions WHERE sellerkey = $1 AND customerkey = 0 AND repeat > 0;''', [factionData['factionkey']])
        for item in data:
            nameList.append(f"{campaignData['currencysymbol']}{str(item['cost'])} - {item['description']}")
        nameChoice = await ctx.bot.ui.getChoiceFromList(ctx, nameList, "Which automatic transaction do you want to cancel?")
        dataOut = nameChoice.split(" - ")
        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM transactions WHERE cost = $1 AND description = $2 AND campaignkey = $3 AND factionkey = $4;''', [int(dataOut[0].strip(campaignData['currencysymbol'])), dataOut[1], campaignData['campaignkey'], factionData['factionkey']])
        await ctx.send("Done!")

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(campaignTransactionFunctions(bot))