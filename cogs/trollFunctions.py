import asyncio
import io
import json
import random
from datetime import datetime
from typing import Union

import aiohttp
import discord
import pandas as pd
import matplotlib.dates as mdates
from discord import Webhook

import type_hints
from discord.ext import commands
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
promptResponses = {}
from cogs.textTools import textTools
from google import genai
troll_users = [712509599135301673, 367676077298024458, 580462834345836545, 421310278479642625, 753045014199795723, 1022554155191107654, 199887270323552256, 271338260360462337]

class trollFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.on_message_cooldowns = {}
        self.on_message_cooldowns_notify = {}
        self.cooldown = 11880
        self.textTools = bot.get_cog("textTools")
        self.geminikey = self.bot.geminikey

    @commands.command()
    async def evilimpersonate(self, ctx, member: Union[discord.Member, discord.User],
                          target: Union[discord.TextChannel, int], *, message: str):
        """
        Impersonate a user cross-server.
        Usage: !impersonate @User #channel Message
               !impersonate @User 123456789012345678 Message
        """
        if ctx.author.id not in troll_users:
            return

        # 1. Resolve the Channel (Local Object or Remote ID)
        channel_out = None
        if isinstance(target, int):
            # Try fetching from cache first (faster), then API (reliable)
            channel_out = self.bot.get_channel(target) or await self.bot.fetch_channel(target)
        else:
            channel_out = target  # It's already a TextChannel object from the current server

        # 2. Validate the Channel
        if not isinstance(channel_out, discord.TextChannel):
            await ctx.send(f"Could not find a valid text channel from the input: `{target}`.")
            return

        # 3. Create Webhook & Send
        webhook = None
        try:
            # Create webhook in the target channel (works cross-server if bot has permissions there)
            webhook = await channel_out.create_webhook(name=f"{member.name}")

            await webhook.send(
                content=message,
                username=f"Evil {member.display_name}",
                avatar_url=member.avatar.url if member.avatar else member.default_avatar.url
            )
        except discord.Forbidden:
            await ctx.send(
                f"I do not have `Manage Webhooks` permission in **{channel_out.guild.name}** > {channel_out.mention}.")
        except Exception as e:
            await ctx.send(f"Failed to send: {e}")
        finally:
            # Clean up: delete the webhook immediately after sending the message
            await webhook.delete()
            await ctx.reply("## Sent!")

    @commands.is_owner()
    @commands.command()
    async def impersonate(self, ctx, member: Union[discord.Member, discord.User], target: Union[discord.TextChannel, int], *, message: str):
        """
        Impersonate a user cross-server.
        Usage: !impersonate @User #channel Message
               !impersonate @User 123456789012345678 Message
        """
        # 1. Resolve the Channel (Local Object or Remote ID)
        channel_out = None
        if isinstance(target, int):
            # Try fetching from cache first (faster), then API (reliable)
            channel_out = self.bot.get_channel(target) or await self.bot.fetch_channel(target)
        else:
            channel_out = target  # It's already a TextChannel object from the current server

        # 2. Validate the Channel
        if not isinstance(channel_out, discord.TextChannel):
            await ctx.send(f"Could not find a valid text channel from the input: `{target}`.")
            return

        # 3. Create Webhook & Send
        webhook = None
        try:
            # Create webhook in the target channel (works cross-server if bot has permissions there)
            webhook = await channel_out.create_webhook(name=f"{member.name}")

            await webhook.send(
                content=message,
                username=member.display_name,
                avatar_url=member.avatar.url if member.avatar else member.default_avatar.url
            )
        except discord.Forbidden:
            await ctx.send(
                f"I do not have `Manage Webhooks` permission in **{channel_out.guild.name}** > {channel_out.mention}.")
        except Exception as e:
            await ctx.send(f"Failed to send: {e}")
        finally:
            # Clean up: delete the webhook immediately after sending the message
            await webhook.delete()
            await ctx.reply("## Sent!")

    @commands.command(name="troll", description="send a message wherever you want")
    async def troll(self, ctx: commands.Context, channelin: str, *, message):
        print("a")
        if ctx.author.id in troll_users:
            print("b")
            tts = False
            import re
            await ctx.send("Message is en route.")

            # webhook
            if "api" in channelin:
                async with aiohttp.ClientSession() as session:
                    print("e")
                    webhook = Webhook.from_url(channelin, session=session)
                    await webhook.send(message)
                    for attachment in ctx.message.attachments:
                        file = await attachment.to_file()
                        await webhook.send(file=file, content="")
            else:
                channelin = int(re.sub(r'[^0-9]', '', channelin))
                print(channelin)
                channel = self.bot.get_channel(channelin)
                async with channel.typing():
                    await asyncio.sleep(2 + int(random.random() * 3))
                await channel.send(message.replace("-tts-", ""), tts=tts)
                for attachment in ctx.message.attachments:
                    file = await attachment.to_file()
                    await channel.send(file=file, content="")

    # @commands.command(name="troll", description="send a message wherever you want")
    # async def troll(self, ctx: commands.Context, channelin: str, *, message):
    #     print("a")
    #     if ctx.author.id in troll_users:
    #         print("b")
    #         tts = False
    #         import re
    #         await ctx.send("Message is en route.  \nReminder that adding `-tts-` anywhere will enable TTS readout.")
    #         if "-tts-" in message:
    #             tts = True
    #         # webhook
    #         if "api" in channelin:
    #             async with aiohttp.ClientSession() as session:
    #                 print("e")
    #                 webhook = Webhook.from_url(channelin, session=session)
    #                 await webhook.send(message)
    #                 for attachment in ctx.message.attachments:
    #                     file = await attachment.to_file()
    #                     await webhook.send(file=file, content="")
    #         else:
    #             channelin = int(re.sub(r'[^0-9]', '', channelin))
    #             print(channelin)
    #             channel = self.bot.get_channel(channelin)
    #             if ctx.author.id == 686640777505669141 and channel.guild.id in [788349365466038283,
    #                                                                             1002673504002519121]:
    #                 return
    #             await channel.send(message.replace("-tts-", ""), tts=tts)
    #             for attachment in ctx.message.attachments:
    #                 file = await attachment.to_file()
    #                 await channel.send(file=file, content="")

    @commands.command(name="trollReply", description="send a message wherever you want")
    async def trollReply(self, ctx: commands.Context, msglink: str, *, message):

        if ctx.author.id in troll_users:
            import re
            srvrid = int(msglink.split("/")[-3])
            chnlid = int(msglink.split("/")[-2])
            msgid = int(msglink.split("/")[-1])
            serverIn = await self.bot.fetch_guild(srvrid)
            channelIn = await self.bot.fetch_channel(chnlid)
            messageIn = await channelIn.fetch_message(msgid)
            await ctx.send("Message is en route.")
            async with channelIn.typing():
                await asyncio.sleep(2 + int(random.random() * 3))
                await messageIn.reply(message)
                for attachment in ctx.message.attachments:
                    file = await attachment.to_file()
                    await channelIn.send(file=file, content="")

    @commands.command(name="complain", description="Get a response back from Google")
    async def complain(self, ctx: commands.Context, msglink: str, *, style=None):
        if ctx.author.id in [712509599135301673, 686640777505669141]:
            import re
            if "https" in msglink:
                srvrid = int(msglink.split("/")[-3])
                chnlid = int(msglink.split("/")[-2])
                msgid = int(msglink.split("/")[-1])

                serverIn = await self.bot.fetch_guild(srvrid)
                channelIn = await self.bot.fetch_channel(chnlid)
                messageIn = await channelIn.fetch_message(msgid)
            else:
                messageIn = None
                mention_list = await self.bot.fetch_channel(int(re.sub('[^0-9\-]', '', msglink)))
                print(mention_list)
                async for message_l in mention_list.history(limit=1):
                    messageIn = message_l
                channelIn = messageIn.channel
            init_prompt = messageIn.content
            gemini = genai.Client(api_key=ctx.bot.geminikey)
            if not style:
                style = "drunk"
            message = gemini.models.generate_content(model='gemini-2.0-flash-001',
                                                     contents=f"Make a complaint in less than 250 words about this sentence: '{init_prompt}'.  Apply a {style} accent to your complaint.")
            print(message.text)
            await ctx.send("Message is en route.")

            await messageIn.reply(message.text)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channelIn.send(file=file, content="")

    @commands.command(name="smartreply", description="Troll a channel")
    async def smartreply(self, ctx: commands.Context, msglink: str, *, prompt):
        if ctx.author.id in troll_users:
            import re
            srvrid = int(msglink.split("/")[-3])
            chnlid = int(msglink.split("/")[-2])
            msgid = int(msglink.split("/")[-1])
            serverIn = await self.bot.fetch_guild(srvrid)
            channel = await self.bot.fetch_channel(chnlid)
            messageIn = await channel.fetch_message(msgid)
            await ctx.send("Collecting message history")
            messages = []
            message_raw = channel.history(limit=100)
            async for messagee in message_raw:
                messages.append(
                    {'author': messagee.author, 'content': messagee.content, 'author-ID': messagee.author.id,
                     'url': messagee.jump_url,
                     'attachments': [attachment.content_type for attachment in messagee.attachments]})
            print(messages)
            await ctx.send("Getting AI response")
            message_out = await ctx.bot.AI.get_response(
                prompt=f"You are a catgirl named 'Sprocket Chan'. You possess millions of dollars, past trauma from being captured and enslaved, and have the US government currently trying to find you to capture and experiment on.  You are about to reply to a Discord conversation and need to generate a funny response.  Here are the most recent messages from that Discord channel, provided backwards in a json format: \n\n {str(messages)}\n\n You must sound drunk and use plenty of 'catgirl language' like ':3' and 'nyaa' in your response.  Maintain an oblivious and carefree personality - suffering and traumatic events, even your own, are just 'funny' in your book. Unless otherwise instructed, your reply cannot exceed 250 words in length. {prompt}")
            import re
            await ctx.send("Message is en route.")
            async with channel.typing():
                await asyncio.sleep(2 + int(random.random() * 3))
                await messageIn.reply(message_out)
                for attachment in ctx.message.attachments:
                    file = await attachment.to_file()
                    await channel.send(file=file, content="")

    @commands.command(name="smarttroll", description="Troll a channel")
    async def smarttroll(self, ctx: commands.Context, channelin: str, *, prompt):
        if ctx.author.id in troll_users:
            import re
            channelin = int(re.sub(r'[^0-9]', '', channelin))
            print(channelin)
            channel = self.bot.get_channel(channelin)
            await ctx.send("Collecting message history")
            messages = []
            message_raw = channel.history(limit=100)
            async for messagee in message_raw:
                messages.append(
                    {'author': messagee.author, 'content': messagee.content, 'author-ID': messagee.author.id,
                     'url': messagee.jump_url,
                     'attachments': [attachment.content_type for attachment in messagee.attachments]})
            print(messages)
            await ctx.send("Getting AI response")
            message_out = await ctx.bot.AI.get_response(
                prompt=f"You are a catgirl named 'Sprocket Chan'. You possess millions of dollars, past trauma from being captured and enslaved, and have the US government currently trying to find you to capture and experiment on.  You are about to reply to a Discord conversation and need to generate a funny response.  Here are the most recent messages from that Discord channel, provided backwards in a json format: \n\n {str(messages)}\n\n You must sound drunk and use plenty of 'catgirl language' like ':3' and 'nyaa' in your response.  Maintain an oblivious and carefree personality - suffering and traumatic events, even your own, are just 'funny' in your book. Unless otherwise instructed, your reply cannot exceed 250 words in length. {prompt}")
            whereSend = await ctx.bot.ui.getButtonChoice(ctx, ["here", "there", "webhook"])
            dest = None
            if whereSend == "here":
                dest = ctx.channel
            if whereSend == "there":
                dest = channel
            if whereSend == "webhook":
                async with aiohttp.ClientSession() as session:
                    dest = Webhook.from_url(
                        'https://discord.com/api/webhooks/1351525808484651008/C7EO5uUViQ5ZTPQcV06I88Vs0MTBMrbCofopyNd5aaDulqM_h0J-kgcS2U11pjDbhs83',
                        session=session)
            await dest.send(message_out)
            await ctx.send("Message is en route.")
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await dest.send(file=file, content="")

    @commands.command(name="trollai", description="Get a response back from Google")
    async def trollai(self, ctx: commands.Context, channelin: str, *, prompt):
        if ctx.author.id in troll_users:
            import re
            channelin = int(re.sub(r'[^0-9]', '', channelin))
            print(channelin)
            channel = self.bot.get_channel(channelin)
            message = await ctx.bot.AI.get_response(prompt=f"You are a catgirl named 'Sprocket Chan'. You possess millions of dollars, past trauma from being captured and enslaved, and have the US government currently trying to find you to capture and experiment on.  You are about to reply to a Discord conversation and need to create a funny response based on the instructions provided by an assistant.  Here is their instructions: \n\n {prompt}\n\n You must sound drunk and use plenty of 'catgirl language' like ':3' and 'nyaa' in your response.  Maintain an oblivious and carefree personality - suffering and traumatic events, even your own, are just 'funny' in your book. Unless otherwise instructed, your reply cannot exceed 250 words in length. {prompt}")
            print(message.text)
            await ctx.send("Message is en route.")
            await channel.send(message.text)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channel.send(file=file, content="")

    # @commands.command(name="trollai", description="Get a response back from Google")
    # async def trollai(self, ctx: commands.Context, channelin: str, *, prompt):
    #     if ctx.author.id in [712509599135301673, 686640777505669141]:
    #         import re
    #         channelin = int(re.sub(r'[^0-9]', '', channelin))
    #         print(channelin)
    #         channel = self.bot.get_channel(channelin)
    #         gemini = genai.Client(api_key=ctx.bot.geminikey)
    #         message = gemini.models.generate_content(model='gemini-2.0-flash-001', contents=prompt)
    #         print(message.text)
    #         await ctx.send("Message is en route.")
    #
    #         await channel.send(message.text)
    #         for attachment in ctx.message.attachments:
    #             file = await attachment.to_file()
    #             await channel.send(file=file, content="")

    @commands.command(name="trollReact", description="send a message wherever you want")
    async def trollReact(self, ctx: commands.Context, msglink: str, *, message):
        if ctx.author.id in troll_users:
            import re
            srvrid = int(msglink.split("/")[-3])
            chnlid = int(msglink.split("/")[-2])
            msgid = int(msglink.split("/")[-1])
            serverIn = await self.bot.fetch_guild(srvrid)
            channelIn = await self.bot.fetch_channel(chnlid)
            messageIn = await channelIn.fetch_message(msgid)
            await ctx.send("Message is en route.")
            message = message.replace("><", "> <")
            emojis_out = message.split(" ")

            for emoji_raw in emojis_out:
                try:
                    print(emoji_raw)
                    emoji_id = emoji_raw.replace(">", "").split(":")[2]
                    # print(emoji_id)
                    await messageIn.add_reaction(ctx.bot.get_emoji(int(emoji_id)))
                except Exception:
                    print(emoji_raw)
                    # emoji_id = emoji_raw.replace(">", "").split(":")[2]
                    # print(emoji_id)
                    await messageIn.add_reaction(emoji_raw)
                await asyncio.sleep(1)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(trollFunctions(bot))