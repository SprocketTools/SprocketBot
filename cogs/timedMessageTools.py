import asyncio
import io
import random
import time

import discord
import type_hints
import pandas as pd
from discord import Webhook
import aiohttp
from discord.ext import commands
import main

promptResponses = {}
from cogs.textTools import textTools
class timedMessageTools(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.startup = True
        self.updateFrequency = 300
        self.startupdelay = 150

    @commands.Cog.listener()
    async def on_ready(self):
        print("setup hook")
        data = await self.bot.sql.databaseFetchdict('''SELECT id, ownerid, channelid, content, webhookid, EXTRACT(EPOCH FROM (time - CURRENT_TIMESTAMP)) as extract FROM timedmessages;''') # WHERE time > CURRENT_TIMESTAMP
        if not data:
            print("No timed messages to restore.")
        else:
            tasks = []
            for message_data in data:
                print(f"task: {message_data['id']}")
                tasks.append(self.sendScheduledMessage(message_data))
            if tasks:
                await asyncio.gather(*tasks)

    async def sendScheduledMessage(self, data):
        """
        Handles messages scheduled for a specific time/date.
        """
        # --- SAFETY GUARD ---
        # If the timestamp is < 2 (Interaction-based), ignore it here.
        # This prevents the bot from spamming interaction replies on startup.
        extract_val = float(data.get('extract', 0))
        if extract_val < -1000000:  # Interaction messages will have a huge negative extract
            return

        # Wait for the scheduled time
        delay_secs = max(int(extract_val), 0)
        await asyncio.sleep(delay_secs)

        try:
            # 1. Resolve Channel and Target User
            channel = None
            if int(data['channelid']) > 0:
                channel = await self.bot.fetch_channel(int(data['channelid']))

            # In time-based messages, ownerid is the person we are 'targeting'
            target_user = await self.bot.fetch_user(int(data['ownerid']))

            if channel and target_user:
                # 2. Check for jumpscare tag
                if "[jumpscare]" in data['content'].lower():
                    await self.bot.ui.generate_jumpscare(None, memberin=target_user, channelin=channel)

                # 3. Otherwise, send as a normal message
                else:
                    async with channel.typing():
                        await asyncio.sleep(2)
                    await channel.send(data['content'])

            # 4. Cleanup
            await self.bot.sql.databaseExecuteDynamic(
                '''DELETE FROM timedmessages WHERE id = $1;''',
                [data['id']]
            )

        except Exception as e:
            print(f"[ERROR] Scheduled Task ID {data.get('id')} failed: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignore bots to prevent loops
        if message.author.bot:
            return

        # 2. Fetch the next 'Trap' message (Interaction flag TS < 2)
        # We use ORDER BY time ASC to ensure sequential batching
        query = '''
                SELECT * FROM timedmessages 
                WHERE (EXTRACT(EPOCH FROM (time)) < 2) 
                AND (ownerid = $1) 
                AND ((channelid = $2) OR (channelid = 0)) 
                ORDER BY time ASC 
                LIMIT 1;
            '''

        try:
            data = await self.bot.sql.databaseFetchdictDynamic(query, [message.author.id, message.channel.id])
            if not data:
                return
            print("msg data:", data)
            for msg in data:
                content = msg.get('content', '')

                # 3. Branching Logic: Jumpscare vs Text
                if "[jumpscare]" in content.lower():
                    # Pass 'None' for ctx and explicitly provide member/channel
                    await self.bot.ui.generate_jumpscare(None, memberin=message.author, channelin=message.channel)

                elif content.strip():
                    # Process text placeholders
                    string = await self.bot.error.errorfyText(message, content)

                    # Human-like typing delay
                    async with message.channel.typing():
                        await asyncio.sleep(min(len(string) / 20, 3))

                    await message.reply(string)

                # 4. Clean up the database so we move to the next message in the batch
                await self.bot.sql.databaseExecuteDynamic(
                    '''DELETE FROM timedmessages WHERE id = $1;''',
                    [msg['id']]
                )

        except Exception as e:
            print(f"[CRITICAL] on_message Trap Error: {e}")

    @commands.command(name="setupTimedMessageDatabase", description="generate a key that can be used to initiate a campaign")
    async def setupTimedMessageDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await self.bot.error.sendCategorizedError(ctx, "campaign")
            return
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS timedmessages;''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS timedmessages (id VARCHAR, ownerid BIGINT, channelid BIGINT, content VARCHAR(2500), time TIMESTAMP, webhookid VARCHAR);''')
        await ctx.send("## Done!")

    @commands.command(name="cancelMessage", description="generate a key that can be used to initiate a campaign")
    async def cancelMessage(self, ctx: commands.Context, *, messageID):
        if ctx.author.id not in [712509599135301673, 367676077298024458, 580462834345836545, 421310278479642625, 753045014199795723, 1022554155191107654, 199887270323552256, 271338260360462337]:
            return
        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM timedmessages WHERE id = $1;''', [messageID])
        await ctx.send("Dropped any that match.")

    @commands.command(name="cancelMessageForUser", description="generate a key that can be used to initiate a campaign")
    async def cancelMessageForUser(self, ctx: commands.Context, *, messageID):
        if ctx.author.id not in [712509599135301673, 367676077298024458, 580462834345836545, 421310278479642625, 753045014199795723, 1022554155191107654, 199887270323552256, 271338260360462337]:
            return
        await self.bot.sql.databaseExecuteDynamic('''DELETE FROM timedmessages WHERE ownerid = $1;''', [messageID])
        await ctx.send("Dropped any that match.")

    @commands.command(name="scheduleMessage", description="generate a key that can be used to initiate a campaign")
    async def scheduleMessage(self, ctx: commands.Context):
        if ctx.author.id not in [686640777505669141, 712509599135301673]:
            return
        await ctx.send("Is this a webhook?")
        type = await ctx.bot.ui.getButtonChoice(ctx, ["Yes", "No", "Both"])
        channelDest = 0
        webhookDest = "n/a"
        if type != "Yes":
            channelDest = await textTools.getChannelResponse(ctx, "What channel is the message going to?")
        if type != "No":
            webhookDest = await textTools.getResponse(ctx, "What is the webhook you are sending to?", action="raw")
        time_stamp = str(await textTools.getResponse(ctx, "When do you want the message to send?  Reply with a timestamp generated at https://r.3v.fi/discord-timestamps/ (any type is fine)")).split(":")[1]
        print(time_stamp)
        content = await textTools.getResponse(ctx, "What do you want the message contents to contain?", "raw")
        id = time_stamp+str(int(random.random()*10000))
        await self.bot.sql.databaseExecuteDynamic('''INSERT INTO timedmessages VALUES($1, $2, $3, $4, TO_TIMESTAMP($5), $6);''',[id, ctx.author.id, channelDest, content, int(time_stamp), webhookDest])
        await ctx.send(f"## Message queued!\nYour ID is: {id}")
        await self.sendScheduledMessage({'id': id, 'ownerid': ctx.author.id, 'channelid': channelDest, 'content': content, 'extract': int(time_stamp)-time.time(), 'webhookid': webhookDest})

        print(await self.bot.sql.databaseFetchdict('''SELECT * FROM timedmessages;'''))

    @commands.is_owner()
    @commands.command(name="scheduleBatchReply",description="Queue a sequence of replies triggered by user interaction.")
    async def scheduleBatchReply(self, ctx: commands.Context):
        # Admin check (matching your existing list)
        # if ctx.author.id not in [712509599135301673, 367676077298024458, 580462834345836545]:
        #     return

        # 1. Get the Victim
        userDest = await textTools.getIntResponse(ctx, "What user is being replied to? Reply with their ID.")

        # 2. Collect the Messages
        await ctx.send(
            "Enter your messages one by one.\n"
            "- Use `[jumpscare]` to trigger the animated GIF.\n"
            "- Send `[continue]` to finish or `[cancel]` to abort."
        )

        data = []
        while True:
            msg = await textTools.awaitResponse(ctx, action="raw")
            if msg == "[cancel]":
                return await ctx.send("Aborted.")
            if msg == "[continue]":
                break
            data.append(msg)

        if not data:
            return await ctx.send("No messages provided. Aborting.")

        # 3. Get Channel Restriction
        channelDest = await textTools.getIntResponse(ctx, "Specify a channel **id** for the trap, or `0` for anywhere.")

        # 4. Queue the Interaction Batch
        # We start at 1.0. The on_message listener looks for anything < 2.0.
        base_interaction_ts = 1.0
        ids_log = "Messages Queued:"

        for i, content in enumerate(data):
            # Increment by 0.001 per message so order is preserved (1.001, 1.002, etc.)
            staggered_ts = base_interaction_ts + (i * 0.001)

            # Create a unique ID for database tracking
            msg_id = f"TRAP_{int(time.time())}_{i}"

            # Insert into the database
            # ownerid stores the 'Victim', content stores the text/tag, time stores the interaction flag
            await self.bot.sql.databaseExecuteDynamic(
                '''INSERT INTO timedmessages VALUES($1, $2, $3, $4, TO_TIMESTAMP($5), $6);''',
                [msg_id, userDest, channelDest, content, staggered_ts, "empty"]
            )

            ids_log += f"\n- {msg_id}: {content[:20]}..."

        await ctx.send(f"## Interaction Trap Armed!\n{ids_log}")

    @commands.command(name="scheduleBatch", description="Edit a faction un bulk")
    async def scheduleBatch(self, ctx: commands.Context):
        if ctx.author.id not in [712509599135301673]:
            return
        await ctx.send("Continue sending unique messages unitl you have your chain of messages complete.  \n- Send `[continue]` to confirm or `[cancel]` to abort.  \n- Code ticks (`) will be stripped from the front and back of the message.\n- Use code ticks to help ensure pings of format <@userid> or <@&roleid> get included.\n   - Similarly, channel mentions are <#channelid>")
        data = []
        status = True
        while status:
            msg = await textTools.awaitResponse(ctx, action="raw")
            print(msg)
            if msg != "[cancel]" and msg != "[continue]":
                data.append(msg)
            else:
                status = False
        print(data)
        if data[-1] == "[cancel]":
            await ctx.send("## Aborting...")
            return

        await ctx.send("Is this a webhook?")
        type = await ctx.bot.ui.getButtonChoice(ctx, ["Yes", "No", "Both"])
        channelDest = 0
        webhookDest = "n/a"
        if type != "Yes":
            channelDest = await textTools.getChannelResponse(ctx, "What channel is the message going to?")
        if type != "No":
            webhookDest = await textTools.getResponse(ctx, "What is the webhook you are sending to?", action="raw")
        time_stamp_num = int(str(await textTools.getResponse(ctx,"When do you want the message to send?  Reply with a timestamp generated at https://r.3v.fi/discord-timestamps/ (any type is fine)")).split(":")[1])
        print(time_stamp_num)
        tasks = []
        await ctx.send("Do you want to have messages automatically delay a little bit?")
        stagger = await ctx.bot.ui.getYesNoChoice(ctx)
        cpm = 30
        if stagger:
            cpm = await textTools.getIntResponse(ctx, "How many characters per minute do you want to see the bot type at?\n-# This is not the same as words per minute.")
        ids = ""
        for message in data:
            id = str(time_stamp_num + (int(random.random() * 10000000)))
            content = message
            if stagger:
                time_stamp_num += int(len(content)/cpm + 0.5)  # assumes a 40 character?schedule per minute speed
            await self.bot.sql.databaseExecuteDynamic('''INSERT INTO timedmessages VALUES($1, $2, $3, $4, TO_TIMESTAMP($5), $6);''',[id, ctx.author.id, channelDest, content, time_stamp_num, webhookDest])
            tasks.append(self.sendScheduledMessage({'id': id, 'ownerid': ctx.author.id, 'channelid': channelDest, 'content': content,'extract': time_stamp_num - time.time(), 'webhookid': webhookDest}))
            ids = ids + f"{id}\n"
        await ctx.send(f"## Message batch queued!\nYour IDs are: {ids}")
        await asyncio.gather(*tasks)
        await ctx.send(f"## Your message batch has been sent.")

    @commands.command(name="scheduleFromCSV", description="Schedule many messages to send")
    async def scheduleFromCSV(self, ctx: commands.Context):
        if ctx.author.id not in [712509599135301673]:
            return
        await ctx.send("Do you have a .csv data file ready yet?")
        isReady = await ctx.bot.ui.getYesNoChoice(ctx)
        if isReady:

            attachment = await textTools.getFileResponse(ctx,
                                                         "Upload your .csv file containing all your faction's data.")
            df = pd.read_csv(io.StringIO((await attachment.read()).decode('utf-8')))
            data = df.to_dict(orient='records')
            print(data)
            tasks = []
            for queue in data:
                print("h")
                try:
                    time_stamp = queue["time"]
                    id = (time_stamp) + (int(random.random() * 10000))

                    await self.bot.sql.databaseExecuteDynamic('''INSERT INTO timedmessages
                                                             VALUES ($1, $2, $3, $4, TO_TIMESTAMP($5), $6);''',
                                                          [str(id), ctx.author.id, queue["channelid"], queue["content"], int(time_stamp),
                                                           str(queue["webhookid"])])
                except Exception as e:
                    print(e)
                await ctx.send(f"## Message queued!\nYour ID is: {id}")
                asyncio.create_task(self.sendScheduledMessage(
                    {'id': id, 'ownerid': ctx.author.id, 'channelid': queue["channelid"], 'content': queue["content"],
                     'extract': int(time_stamp) - time.time(), 'webhookid': str(queue["webhookid"])}))
            await ctx.send(f"## Done!\n{len(data)} messages have been added.")
            await ctx.send(f"## Your message batch has been sent.")
        else:
            if await ctx.bot.campaignTools.isCampaignHost(ctx) == False:
                return
            await ctx.send(
                "Download this file and edit it in a spreadsheet editor.  When you're done, save it as a .csv and run the command again.")
            data = await self.bot.sql.databaseFetchdict('''SELECT channelid, content, time, webhookid FROM timedmessages LIMIT 1;''')
            # credits: brave AI
            df = pd.DataFrame(data)
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            # Send CSV file
            buffer.seek(0)
            await ctx.channel.send(file=discord.File(buffer, "data.csv"))
            await ctx.send("Make sure to delete the example entry when you're done, so that it doesn't double-send.\nEnter the timestamps as plain unix timestamps, it'll auto-convert.")





        # else:
        #     await ctx.send("Create a .txt file on your computer and ")
        #     await ctx.send("Download this file and edit it in a spreadsheet editor.  Add new text lines moving downwards.  When you're done, save it as a .csv and run the command again.")
        #     # data = [
        #     #     {"Insert raw strings below this line and don't erase this line.": "Why hello there"},
        #     #     {"Insert raw strings below this line and don't erase this line.": "golden warrior."}
        #     # ]
        #     # # credits: brave AI
        #     # df = pd.DataFrame(data)
        #     # buffer = io.StringIO()
        #     # df.to_csv(buffer, index=False)
        #     # # Send CSV file
        #     # buffer.seek(0)
        #     # await ctx.channel.send(file=discord.File(buffer, "data.csv"))
        #     # await ctx.send("## Warning\nDo not change the faction keys - these are basically their social security numbers.")


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(timedMessageTools(bot))
    #await timedMessageTools(bot).setup_hook()