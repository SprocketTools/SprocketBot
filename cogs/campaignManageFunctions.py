import discord, io
import matplotlib.pyplot as plot
import pandas as pd
from discord.ext import commands
import main
import type_hints
promptResponses = {}
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions

class campaignManageFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.command(name="manageCampaign", description="Add money to a faction")
    async def manageCampaign(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignHost(ctx) == False:
            if ctx.author.id == main.ownerID:
                await ctx.send(
                    "You do not have permission to perform this action.  Proceed forward and override this?")
                answer = await ctx.bot.ui.getYesNoChoice(ctx)
                if not answer:
                    return
            else:
                return
        i = 0
        while True:
            key = await ctx.bot.campaignTools.getCampaignKey(ctx)
            embedOut = await ctx.bot.campaignTools.showSettings(ctx)
            promptOut = await ctx.send("What statistic do you wish to modify?")
            answer = str.lower(await ctx.bot.ui.getButtonChoice(ctx, ["Name", "Rules", "Time scale", "Adjust time", "Currency name", "Currency symbol", "Baseline GDP growth", "Energy cost", "Steel cost", "Pop to worker ratio", "Start/stop campaign", "Transaction logs channel", "Announcement channel", "Exit", "Transfer Campaign Ownership"]))
            name_adj = ""
            if answer == "exit" or i > 1:
                await ctx.send("Alright, have fun.")
                await promptOut.delete()
                return
            elif answer == "adjust time":
                timestamp_adj = await textTools.getIntResponse(ctx, "How many days do you want to move forward?")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET timedate = timedate + make_interval(days => CAST ($1 AS INT)) WHERE campaignkey = $2;''',[timestamp_adj, key])
            elif answer == "start/stop campaign":
                await campaignManageFunctions.toggleCampaignProgress(self, ctx)
            elif answer == "time scale":
                timescale_adj = await textTools.getFlooredFloatResponse(ctx, "What is the new timescale you wish to use?", 1)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET timescale = $1 WHERE campaignkey = $2;''',[timescale_adj, key])
            elif answer == "name":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new name of the campaign?", 128)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET campaignname = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "pop to worker ratio":
                ratio_adj = await textTools.getFlooredFloatResponse(ctx, "What is the new default pop/worker ratio you wish to use?", 1)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET poptoworkerratio = $1 WHERE campaignkey = $2;''',[ratio_adj, key])
            elif answer == "rules":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new rules of the campaign?", 256)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET campaignrules = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "baseline gdp growth":
                name_adj = await textTools.getPercentResponse(ctx, "What is the new GDP growth?")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET defaultgdpgrowth = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "currency name":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new currency name of the campaign?", 32)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET currencyname = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "currency symbol":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new currency symbol of the campaign?", 2)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET currencysymbol = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "transaction logs channel":
                name_adj = await textTools.getChannelResponse(ctx, "What is your new transaction logging channel?")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET privatemoneychannelid = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "energy cost":
                name_adj = await textTools.getFlooredFloatResponse(ctx, "What is the new cost of a barrel of oil?\nWarning: this value should only be changed if you know what you're doing.  Changing this value without changing the steel cost can lead to major economic changes.", 1)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET energycost = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "steel cost":
                name_adj = await textTools.getFlooredFloatResponse(ctx, '''What is the new cost of a metric ton of steel?\nNote: this acts as the base "price" that rearranges the value of everything.  Be aware that ripple effects will occur throughout the entire system if this is adjusted.''', 2)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET steelcost = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "announcement channel":
                name_adj = await textTools.getChannelResponse(ctx, "What is your new channel for automated campaign update announcements?")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET publiclogchannelid = $1 WHERE campaignkey = $2;''',[name_adj, key])
            elif answer == "transfer campaign ownership":
                name_adj = await textTools.getIntResponse(ctx,"What is your new server ID?")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET hostserverid = $1 WHERE campaignkey = $2;''', [name_adj, key])
                await ctx.send("Done!  Move to your new server to continue.")
            else:
                await ctx.send("Looks like you clicked on an unsupported button, or this window timed out.")
                i += 1
            await embedOut.delete()
            await promptOut.delete()
            notif = await ctx.send(f'Selection "{answer}" has been updated.')
            await notif.delete(delay=7)



    @commands.command(name="manageFaction", description="Add money to a faction")
    async def manageFaction(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignHost(ctx): # hosts
            data = await ctx.bot.campaignTools.pickCampaignFaction(ctx, "Pick the faction you would like to manage.")
            factionName = data['factionname']
            key = data['factionkey']
        else: #players only
            data = await ctx.bot.campaignTools.getUserFactionData(ctx)
            key = data["factionkey"]

        if data['iscountry']:
            displayType = str.lower(
                await ctx.bot.ui.getButtonChoice(ctx, ["general", "operations", "payments"]))
        else:
            displayType = "general"
        if await ctx.bot.campaignTools.isCampaignHost(ctx):
            if data['iscountry'] == False:
                inList = ["Name", "Description", "Flag", "Discretionary funds", "Updates channel",
                          "Move your company to a new country", "Delete faction", "Exit"]
            else:
                if displayType == "general":
                    inList = ["Name", "Description", "Flag", "Discretionary funds", "Land", "Government type",
                              "Updates channel", "Population", "GDP", "Delete faction", "Switch category", "Exit"]
                if displayType == "operations":
                    inList = ["Median salary", "Espionage funding", "Defense spending", "Infrastructure funding",
                              "Switch category", "Exit"]
                if displayType == "payments":
                    inList = ["Discretionary funds", "Median salary", "GDP", "Poor tax", "Rich tax", "Switch category",
                              "Exit"]

        else:
            displayType = str.lower(
                await ctx.bot.ui.getButtonChoice(ctx, ["general", "operations", "payments"]))
            if data['iscountry'] == False:
                inList = ["Name", "Description", "Flag", "Updates channel", "Exit"]
            else:
                if displayType == "general":
                    inList = ["Name", "Description", "Flag", "Government type", "Updates channel", "Switch category",
                              "Exit"]
                if displayType == "operations":
                    inList = ["Espionage funding", "Defense spending", "Infrastructure funding", "Switch category",
                              "Exit"]
                if displayType == "payments":
                    inList = ["Poor tax", "Rich tax", "Switch category", "Exit"]


        print(data)
        continue_val = True
        while continue_val:
            data = await ctx.bot.campaignTools.getFactionData(key)

            embedOut = await ctx.bot.campaignTools.showStats(ctx, data, displayType)
            promptOut = await ctx.send("What statistic do you wish to modify?")

            answer = str.lower(await ctx.bot.ui.getButtonChoice(ctx, inList))
            print(answer)
            if answer == "exit":
                await ctx.send("Alright, have fun.")
                return
            elif answer == "discretionary funds":
                money_adj = await textTools.getIntResponse(ctx, "What is your new discetionary balance?  Reply with a number.")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET money = $1 WHERE factionkey = $2;''',[money_adj, key])
            elif answer == "median salary":
                salary_adj = await textTools.getFlooredIntResponse(ctx, "What is your new median salary?  Reply with a number.", 1)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET averagesalary = $1 WHERE factionkey = $2;''',[salary_adj, key])
                cog = self.bot.get_cog('campaignUpdateFunctions')
                await cog.softUpdate()
            elif answer == "gdp":
                salary_adj = await textTools.getFlooredIntResponse(ctx, "What is your new GDP?  Reply with a number.", 1)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET averagesalary = $1 * popworkerratio / population WHERE factionkey = $2;''',[salary_adj, key])
                cog = self.bot.get_cog('campaignUpdateFunctions')
                await cog.softUpdate()
            elif answer == "land":
                name_adj = await textTools.getFlooredIntResponse(ctx, "What is your new land size?  Reply with a number.", 1)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET landsize = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "government type":
                name_adj = await ctx.bot.campaignTools.getGovernmentType(ctx)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET governance = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "name":
                name_adj = await textTools.getCappedResponse(ctx, "What is the new name of the faction?", 64)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET factionname = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "description":
                desc_adj = await textTools.getCappedResponse(ctx, "What is the new description?", 256)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET description = $1 WHERE factionkey = $2;''',[desc_adj, key])
            elif answer == "population":
                pop_adj = await textTools.getFlooredIntResponse(ctx, "What is your new population?  Reply with a number.", 1000)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET population = $1 WHERE factionkey = $2;''',[pop_adj, key])
            elif answer == "pop to worker ratio":
                ratio_adj = await textTools.getFlooredFloatResponse(ctx, "What is the new default pop/worker ratio you wish to use?", 1)
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaigns SET poptoworkerratio = $1 WHERE factionkey = $2;''',[ratio_adj, key])
            elif answer == "move your company to a new country":
                if data['iscountry'] == False:
                    landlorddata = await ctx.bot.campaignTools.pickCampaignCountry(ctx, "Where are you relocating your company to?")
                    await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET landlordfactionkey = $1 WHERE factionkey = $2;''',[landlorddata['factionkey'], key])
                else:
                    await ctx.send("Yeah, unfortunately surrendering to another country is not a part of the game here.")
            elif answer == "flag":
                name_adj = await textTools.getFileURLResponse(ctx, "What is the new flag?  Upload an image.")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET flagurl = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "updates channel":
                name_adj = await textTools.getChannelResponse(ctx, "What is the new channel you want updates sent to?")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET logchannel = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "espionage funding":
                name_adj = await textTools.getPercentResponse(ctx, "What percentage of your discretionary funds do you wish to dedicate towards espionage funding?")
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET espionagespend = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "infrastructure funding":
                name_adj = await textTools.getPercentResponse(ctx, "What percentage of your discretionary funds do you wish to dedicate towards infrastructure funding?")
                if data['defensespend'] + name_adj > 0.99:
                    await ctx.send(f"Unfortunately you are allocating {(data['defensespend'] + data['infrastructurespend'])*100}% of your available money!  Try again.")
                else:
                    await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET infrastructurespend = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "defense spending":
                name_adj = await textTools.getPercentResponse(ctx, "What percentage of your discretionary funds do you wish to dedicate towards defense funding?")
                if name_adj + data['infrastructurespend'] > 0.99:
                    await ctx.send(f"Unfortunately you are allocating {(data['defensespend'] + data['infrastructurespend'])*100}% of your available money!  Try again.")
                else:
                    await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET defensespend = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "poor tax":
                name_adj = await textTools.getPercentResponse(ctx, "What percentage do you want to set your poor tax rate to?  This is the taxation rate that generates most of your income.")
                if name_adj > 1:
                    name_adj = 1
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET taxpoor = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "rich tax":
                name_adj = await textTools.getPercentResponse(ctx, "What percentage do you want to set your rich tax to?  This is the taxation rate that applies to companies and rich people.")
                if name_adj > 1:
                    name_adj = 1
                await self.bot.sql.databaseExecuteDynamic(f'''UPDATE campaignfactions SET taxrich = $1 WHERE factionkey = $2;''',[name_adj, key])
            elif answer == "delete faction":
                if await ctx.bot.campaignTools.isCampaignHost(ctx) == False:
                    await self.bot.error.sendError(ctx)
                    await ctx.send("You are not a campaign host; please contact a campaign host to delete your faction.")
                    return
                else:
                    await ctx.send(f"Please confirm that you intend to delete {factionName} and wipe all records of it from the bot.")
                    if await ctx.bot.ui.getYesNoChoice(ctx) == False:
                        return
                    await ctx.send(f"Please confirm again that you intend to delete {factionName}.  There won't be another confirmation after this one.")
                    if await ctx.bot.ui.getYesNoChoice(ctx) == False:
                        return
                    await self.bot.sql.databaseExecuteDynamic(f'''DELETE FROM campaignfactions WHERE factionkey = $1;''',[key])
                    await self.bot.sql.databaseExecuteDynamic(f'''DELETE FROM campaignusers WHERE factionkey = $1;''',[key])
                    await ctx.send("## Done!")
                    return
            elif answer == "switch category":

                if data['iscountry']:
                    displayType = str.lower(
                        await ctx.bot.ui.getButtonChoice(ctx, ["general", "operations", "payments"]))
                else:
                    displayType = "general"
                if await ctx.bot.campaignTools.isCampaignHost(ctx):
                    if data['iscountry'] == False:
                        inList = ["Name", "Description", "Flag", "Discretionary funds", "Updates channel",
                                  "Move your company to a new country", "Delete faction", "Exit"]
                    else:
                        if displayType == "general":
                            inList = ["Name", "Description", "Flag", "Discretionary funds", "Land", "Government type",
                                      "Updates channel", "Population", "GDP", "Delete faction", "Switch category",
                                      "Exit"]
                        if displayType == "operations":
                            inList = ["Median salary", "Espionage funding", "Defense spending",
                                      "Infrastructure funding", "Switch category", "Exit"]
                        if displayType == "payments":
                            inList = ["Discretionary funds", "Median salary", "GDP", "Poor tax", "Rich tax",
                                      "Switch category", "Exit"]

                else:
                    displayType = str.lower(
                        await ctx.bot.ui.getButtonChoice(ctx, ["general", "operations", "payments"]))
                    if data['iscountry'] == False:
                        inList = ["Name", "Description", "Flag", "Updates channel", "Exit"]
                    else:
                        if displayType == "general":
                            inList = ["Name", "Description", "Flag", "Government type", "Updates channel",
                                      "Switch category", "Exit"]
                        if displayType == "operations":
                            inList = ["Espionage funding", "Defense spending", "Infrastructure funding",
                                      "Switch category", "Exit"]
                        if displayType == "payments":
                            inList = ["Poor tax", "Rich tax", "Switch category", "Exit"]

            else:
                await ctx.send("Looks like you clicked on an unsupported button, or this window timed out.")
                return
            await ctx.send("## Done!")
            await embedOut.delete()
            await promptOut.delete()

    @commands.command(name="manageAllFactions", description="Edit a faction un bulk")
    async def manageAllFactions(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignHost(ctx) == False:
            return
        key = await ctx.bot.campaignTools.getCampaignKey(ctx)
        name = await ctx.bot.campaignTools.getCampaignName(key)
        await ctx.send("Do you have a .csv data file ready yet?")
        isReady = await ctx.bot.ui.getYesNoChoice(ctx)
        if isReady:

            attachment = await textTools.getFileResponse(ctx, "Upload your .csv file containing all your faction's data.")
            df = pd.read_csv(io.StringIO((await attachment.read()).decode('utf-8')))
            data = df.to_dict(orient='records')
            print(data)
            for faction in data:
                await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET factionname = $1, money = $2, population = $3, landsize = $4, averagesalary = $5 WHERE factionkey = $6''', [faction["factionname"], faction["money"], faction["population"], faction["landsize"], faction["averagesalary"], faction["factionkey"]])
            await ctx.send(f"## Done!\n{len(data)} factions have been updated.")
        else:
            if await ctx.bot.campaignTools.isCampaignHost(ctx) == False:
                return
            await ctx.send("Download this file and edit it in a spreadsheet editor.  When you're done, save it as a .csv and run the command again.")
            data = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT factionkey, approved, factionname, iscountry, money, population, landsize, averagesalary, popworkerratio FROM campaignfactions where campaignkey = $1;''',
                [await ctx.bot.campaignTools.getCampaignKey(ctx)])
            # credits: brave AI
            df = pd.DataFrame(data)
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            # Send CSV file
            buffer.seek(0)
            await ctx.channel.send(file=discord.File(buffer, "data.csv"))
            await ctx.send("## Warning\nDo not change the faction keys - these are basically their social security numbers.")

    @commands.command(name="plotData", description="Plot chart data")
    async def plotData(self, ctx: commands.Context):
        if await ctx.bot.campaignTools.isCampaignHost(ctx) == False and ctx.author.id != main.ownerID:
            return


        hostData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        column_names = []
        column_namesr = await self.bot.sql.databaseFetchdict('''SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'campaignfactions' AND data_type IN ('bigint', 'real', 'numeric');''')
        str = ""
        i = 0
        for col in column_namesr:
            if i > 4:
                column_names.append(col['column_name'])
                str = str + col['column_name'] + ", "
            i+= 1
        print(str[0:(len(str)-2)])
        print(len(column_names))
        data = await self.bot.sql.databaseFetchdictDynamic(f'''SELECT {str[0:(len(str)-2)]} FROM campaignfactions WHERE campaignkey = $1 AND iscountry = true;''', [hostData['campaignkey']])
        await ctx.send("Pick your x axis!")
        x_axis = await ctx.bot.ui.getButtonChoice(ctx, column_names)
        x_data = []
        for val in data:
            x_data.append(val[x_axis])

        await ctx.send("Pick your y axis!")
        y_axis = await ctx.bot.ui.getButtonChoice(ctx, column_names)
        y_data = []
        for val in data:
            y_data.append(val[y_axis])
        trim = await textTools.getIntResponse(ctx, "How many outliers do you want to trim off?\n-# Reply with a whole number")
        plot.clf()

        data_pair = zip(x_data, y_data)
        sort_data = sorted(data_pair)
        print(sort_data)


        x_data, y_data = zip(*sort_data[0+trim:len(x_data)-1-trim])
        print(x_data)
        plot.scatter(x_data, y_data)
        plot.ylabel(y_axis)
        plot.xlabel(x_axis)

        # x_data = outlist[0][0+trim:len(x_data)-1-trim]
        # y_data = outlist[1][0+trim:len(x_data)-1-trim]

        plot.title(x_axis + " vs. " + y_axis)

        buffer = io.BytesIO()
        plot.savefig(buffer, format='png')
        buffer.seek(0)

        # Create a discord.File object from the BytesIO object
        image = discord.File(fp=buffer, filename='plot.png')

        # Send the image to a Discord channel
        await ctx.send(file=image)

    async def toggleCampaignProgress(self, ctx: commands.Context):
        print("a")
        if await self.bot.campaignTools.isCampaignHost(ctx) == False:
            print("c")
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            serverConfig = await adminFunctions.getServerConfig(ctx)
            await ctx.send(f"You don't have the permissions needed to run this command.  Ensure you have the **{ctx.guild.get_role(serverConfig['campaignmanagerroleid'])}** role and try again.")
            return
        print("b")
        campaignData = await self.bot.campaignTools.getUserCampaignData(ctx)
        if campaignData["hostserverid"] != ctx.guild.id:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        await self.bot.sql.databaseExecuteDynamic('''UPDATE campaigns SET active = NOT active WHERE hostserverid = $1;''',[ctx.guild.id])

        result = await self.bot.sql.databaseFetchlistDynamic('''SELECT campaignname, active, campaignkey FROM campaigns WHERE hostserverid = $1;''',[ctx.guild.id])
        await self.bot.sql.databaseExecuteDynamic('''UPDATE campaignfactions SET hostactive = $1 WHERE campaignkey = $2;''', [result[1], result[2]])

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