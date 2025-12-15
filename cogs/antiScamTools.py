import hashlib

from google import genai
import time, io
import os, discord
from discord.ext import commands
import json, requests
import random, asyncio, datetime
from discord import Webhook
import aiohttp
import type_hints
from cogs.textTools import textTools

userPacket = {}
userStrikes = []
inspected = []
nudeFlags = ["18+", "3.jpg", "3.png", "3.jpeg", "teen", "girls", "onlyfans", "hot", "nude", "e-womans", "plug", "invite", "free gifts", "gift", "leak", "executor roblox", "roblox executor", "earn", "earning"]
scamFlags = ["$", "steam", "asdfghjkl", "cdn.discordapp.com/attachments", "@everyone", "3.jpg", "3.png", "3.jpeg",]
linkFlags = ["steamcommunity.com/gift", "bit.ly", "sc.link", "1.jpg", "1.png", "1.jpeg", "2.jpg", "2.png", "2.jpeg", "qptr.ru", "https://temu.com/s/", "canary.discord.com", "https://", "http://", "discord.gg", "discordapp.com", "discord.com/invite", "https://t.me/"]
whitelist = ["https://tenor.com/view/", "https://cdn.discordapp.com/attachments"]

class antiScamFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.cooldown = 0
        self.color1 = (250, 250, 120)
        self.color2 = (119, 86, 35)
        self.operational = True
        #self.bot.add_check(adminFunctions.blacklist_test)
        print("Hi")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in inspected:
            await asyncio.sleep(0.25)
        inspected.append(message.author.id)
        # Collect data
        serverConfig = (await self.bot.sql.databaseFetchdictDynamic(f'SELECT * FROM serverconfig WHERE serverid = $1;', [message.guild.id]))[0]
        try:
            oldPacket = userPacket[message.author.id]
        except Exception:
            oldPacket = {"hashes": [], "content": "", "timestamp": message.created_at, "channelid": message.channel.id}

        # messageParse = message.content.lower()
        # nudeTrigger = 0
        # scamTrigger = 0
        # linkTrigger = 0
        #
        # for flag in nudeFlags:
        #     if flag in messageParse:
        #         nudeTrigger += 1
        # for flag in scamFlags:
        #     if flag in messageParse:
        #         scamTrigger += 1
        # for flag in linkFlags:
        #     if flag in messageParse:
        #         linkTrigger += 1

        hashes = []
        for attachment in message.attachments:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as response:
                    if response.status == 200:
                        content = await response.read()
                        hashes.append(hashlib.md5(content).hexdigest())
        userPacket[message.author.id] = {"hashes": hashes, "content": message.content, "timestamp": message.created_at, "channelid": message.channel.id}

        # Compare data
        hashesMatch = oldPacket["hashes"] == hashes
        contentMatch = oldPacket["content"] == message.content
        timestampMatch = (message.created_at - oldPacket["timestamp"]).total_seconds() < 60
        channelidMatch = (message.channel.id == oldPacket["channelid"])

        if contentMatch and hashesMatch and timestampMatch and (not channelidMatch):
            print("Match")
            userStrikes.append(message.author.id)
        #
        # if linkTrigger == 0 and (nudeTrigger == 0 or scamTrigger == 0) and len(message.content) > 0 and not any(keyword in message.content for keyword in whitelist):
        #     userStrikes[message.author.id] = 0
        # if linkTrigger > 0 and (nudeTrigger > 0 or scamTrigger > 0) and len(message.content) > 0 and not any(keyword in message.content for keyword in whitelist):
        #     print(f"{nudeTrigger}{scamTrigger}{linkTrigger}")
            logChannel = self.bot.get_channel(1152377925916688484)
            try:
                userStrikes[message.author.id] = int(userStrikes[message.author.id]) + 1
            except Exception:
                userStrikes[message.author.id] = 1
            action = serverConfig['flagaction']
            pingAction = serverConfig['flagping']
            preppedMessage = f"This message matches the criteria set for a hacked account:\nUser ID: {message.author.id}\nUser ping: <@{message.author.id}>\nMessage content:\n{message.content}"
            embed = discord.Embed(title=f"A hacked account has been detected!", color=discord.Color.blurple())
            if userStrikes[message.author.id] >= int(serverConfig['flagthreshold']):
                embed = discord.Embed(title=f"Action taken on a hacked account", color=discord.Color.red())
                embed.set_footer(text=f"Action taken: {action}")
            embed.add_field(name="Username", value=f"{message.author.name}", inline=False)
            embed.add_field(name="A.K.A.", value=f"{message.author.display_name}", inline=False)
            embed.add_field(name="User ID", value=f"{message.author.id}", inline=False)
            embed.add_field(name="User ping", value=f"<@{message.author.id}>", inline=False)
            embed.add_field(name="Server", value=f"<@{message.guild.name}>", inline=False)
            await logChannel.send(embed=embed)
            await logChannel.send(f'Message content:\n`{message.content}`')
            if userStrikes[message.author.id] == int(serverConfig['flagthreshold']) - 1:
                await message.add_reaction('⚠️')
                await message.author.send(f"## Warning: you are triggering Sprocket Bot's anti scam functions and risk a {action} in *{message.guild.name}.*  \nSend a message that does not contain a link or questionable words, such as \"a\". \nIf you believe this was an error, please report this at https://github.com/SprocketTools/SprocketBot/issues")
            if userStrikes[message.author.id] >= int(serverConfig['flagthreshold']):
                if action == "kick":
                    await message.author.send(f"You have been kicked from {message.guild.name} by Sprocket Bot's automated anti-scam functions.  \n This is not a permanent ban - rejoin the server once you gain control of your account again and have 2FA enabled.\nIf you believe this was an error, please report this at https://github.com/SprocketTools/SprocketBot/issues")
                    await message.author.ban(reason="Automated anti-scam functions", delete_message_seconds=600)
                    await message.author.unban(reason="Automated anti-scam functions")
                if action == "timeout for 12 hours":
                    await message.author.send(f"You have been timed out in {message.guild.name} by Sprocket Bot's automated anti-scam functions.  \nIf you believe this was an error, please report this at https://github.com/SprocketTools/SprocketBot/issues")
                    delta = (datetime.datetime.now().astimezone() + datetime.timedelta(hours=12))
                    await message.author.timeout(delta, reason="Hacked account")
                channel = self.bot.get_channel(serverConfig['managerchannelid'])
                await channel.send(embed=embed)
                await channel.send(f'Message content:\n`{message.content}`')
                if pingAction == "nobody":
                    pass
                elif pingAction == "custom":
                    await channel.send(f"<@&{serverConfig['flagpingid']}>")
                else:
                    await channel.send(f"@{serverConfig['flagping']}")
        else:
            userStrikes[message.author.id] = 0



async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(antiScamFunctions(bot))