import asyncio
import math
import random
import time
import io

import pandas as pd
from discord.ext import tasks

import discord
from discord.ext import commands

import main
from datetime import datetime, timedelta
from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions

promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions
from cogs.SQLfunctions import SQLfunctions
class timedMessageTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.startup = True
        self.updateFrequency = 300
        self.startupdelay = 150

    @commands.Cog.listener()
    async def on_ready(self):
        print("setup hook")
        data = await SQLfunctions.databaseFetchdict('''SELECT id, ownerid, channelid, content, EXTRACT(EPOCH FROM (time - CURRENT_TIMESTAMP)) FROM timedmessages;''') # WHERE time > CURRENT_TIMESTAMP
        for message_data in data:
            print(data)
            await self.sendScheduledMessage(message_data)
    async def sendScheduledMessage(self, data):
        print(data)
        delay_secs = max(int(data['extract']), 0)
        await asyncio.sleep(delay_secs)
        channel = await self.bot.fetch_channel((int(data['channelid'])))
        await channel.send(data['content'])
        await SQLfunctions.databaseFetchdictDynamic('''DELETE FROM timedmessages WHERE id = $1;''', [data['id']])
    # @tasks.loop(seconds=300)
    # async def updateRoles(self):
    #     await timedMessageTools.roleUpdater(self)
    #
    # @commands.command(name="updateColorChangers",description="Update the color changers by force")
    # async def updateColorChangers(self, ctx: commands.Context):
    #     try:
    #         self.startup = False
    #         await timedMessageTools.roleUpdater(self)
    #         self.startup = True
    #         print("test")
    #         await ctx.send("## Done!")
    #     except Exception as e:
    #         await ctx.send(f"{e}")
    #
    # async def roleUpdater(self):
    #     if self.startup == True:
    #         await asyncio.sleep(self.startupdelay)
    #         self.startup = False
    #     else:
    #         print("hi")
    #
    @commands.command(name="setupTimedMessageDatabase", description="generate a key that can be used to initiate a campaign")
    async def setupTimedMessageDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        await SQLfunctions.databaseExecute('''DROP TABLE IF EXISTS timedmessages;''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS timedmessages (id VARCHAR, ownerid BIGINT, channelid BIGINT, content VARCHAR(2500), time TIMESTAMP);''')
        await ctx.send("## Done!")

    @commands.command(name="cancelMessage", description="generate a key that can be used to initiate a campaign")
    async def cancelMessage(self, ctx: commands.Context, *, messageID):
        if ctx.author.id not in [686640777505669141, 712509599135301673]:
            return
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM timedmessages WHERE id = $1;''', [messageID])
        await ctx.send("Dropped any that match.")

    @commands.command(name="scheduleMessage", description="generate a key that can be used to initiate a campaign")
    async def scheduleMessage(self, ctx: commands.Context):
        if ctx.author.id not in [686640777505669141, 712509599135301673]:
            return
        channelDest = await textTools.getChannelResponse(ctx, "What channel is the message going to?")
        time_stamp = str(await textTools.getResponse(ctx, "When do you want the message to send?  Reply with a timestamp generated at https://r.3v.fi/discord-timestamps/ (any type is fine)")).split(":")[1]
        print(time_stamp)
        content = await textTools.getResponse(ctx, "What do you want the message contents to contain?", "raw")
        id = time_stamp+str(int(random.random()*10000))
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO timedmessages VALUES($1, $2, $3, $4, TO_TIMESTAMP($5));''',[id, ctx.author.id, channelDest, content, int(time_stamp)])
        await ctx.send(f"## Message queued!\nYour ID is: {id}")
        await self.sendScheduledMessage({'id': id, 'ownerid': ctx.author.id, 'channelid': channelDest, 'content': content, 'extract': int(time_stamp)-time.time()})

        print(await SQLfunctions.databaseFetchdict('''SELECT * FROM timedmessages;'''))

    @commands.command(name="scheduleBatch", description="Edit a faction un bulk")
    async def scheduleBatch(self, ctx: commands.Context):
        if ctx.author.id not in [686640777505669141, 712509599135301673]:
            return
        await ctx.send("Do you have a .csv data file ready yet?")
        isReady = await discordUIfunctions.getYesNoChoice(ctx)
        if isReady:
            attachment = await textTools.getFileResponse(ctx, "Upload your .csv file containing your msg strings.")
            df = pd.read_csv(io.StringIO((await attachment.read()).decode('utf-8')))
            data = df.to_dict(orient='records')
            print(data)
            channelDest = await textTools.getChannelResponse(ctx, "What channel is the message going to?")
            time_stamp_num = int(str(await textTools.getResponse(ctx,"When do you want the message to send?  Reply with a timestamp generated at https://r.3v.fi/discord-timestamps/ (any type is fine)")).split(":")[1])
            print(time_stamp_num)
            tasks = []
            id = str(time_stamp_num + (int(random.random() * 10000000)))
            await ctx.send("Do you want to have messages automatically delay a little bit?")
            stagger = await discordUIfunctions.getYesNoChoice(ctx)
            for message in data:
                content = message["Insert raw strings below this line and don't erase this line."]
                if stagger:
                    time_stamp_num += int(len(content)/40 + 0.5)  # assumes a 40 character?schedule per minute speed
                await SQLfunctions.databaseExecuteDynamic('''INSERT INTO timedmessages VALUES($1, $2, $3, $4, TO_TIMESTAMP($5));''',[id, ctx.author.id, channelDest, content, time_stamp_num])
                tasks.append(self.sendScheduledMessage({'id': id, 'ownerid': ctx.author.id, 'channelid': channelDest, 'content': content,'extract': time_stamp_num - time.time()}))
            await ctx.send(f"## Message batch queued!\nYour ID is: {id}")
            await asyncio.gather(*tasks)
            await ctx.send(f"## Your message batch has been sent.")






        else:
            await ctx.send("Download this file and edit it in a spreadsheet editor.  Add new text lines moving downwards.  When you're done, save it as a .csv and run the command again.")
            data = [
                {"Insert raw strings below this line and don't erase this line.": "Why hello there"},
                {"Insert raw strings below this line and don't erase this line.": "golden warrior."}
            ]
            # credits: brave AI
            df = pd.DataFrame(data)
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            # Send CSV file
            buffer.seek(0)
            await ctx.channel.send(file=discord.File(buffer, "data.csv"))
            await ctx.send("## Warning\nDo not change the faction keys - these are basically their social security numbers.")


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(timedMessageTools(bot))
    #await timedMessageTools(bot).setup_hook()