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
userStrikes = {}
inspected = []
to_delete = {}

class antiScamFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.cooldown = 0
        self.color1 = (250, 250, 120)
        self.color2 = (119, 86, 35)
        self.operational = True

        self.scam_queue = asyncio.Queue()
        self.processing_task = self.bot.loop.create_task(self.process_scam_queue())
        print("Anti-Scam Queue Initialized")

    def cog_unload(self):
        self.processing_task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        serverConfig = (await self.bot.sql.databaseFetchdictDynamic(f'SELECT * FROM serverconfig WHERE serverid = $1;',
                                                                    [message.guild.id]))[0]
        hashes = []
        for attachment in message.attachments:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as response:
                        if response.status == 200:
                            content = await response.read()
                            hashes.append(hashlib.md5(content).hexdigest())
            except Exception as e:
                print(f"Error hashing attachment: {e}")
        try:
            print(to_delete[message.author.id][0])
        except Exception:
            to_delete[message.author.id] = []
        payload = {
            "message": message,
            "hashes": hashes,
            "serverConfig": serverConfig,
            "timestamp": message.created_at,
            "content": message.content
        }
        await self.scam_queue.put(payload)

    async def process_scam_queue(self):
        while True:
            try:
                payload = await self.scam_queue.get()
                message = payload["message"]
                hashes = payload["hashes"]
                serverConfig = payload["serverConfig"]
                await self.check_scam_logic(message, hashes, serverConfig)
            except Exception as e:
                print(f"Error in scam processing worker: {e}")
            finally:
                self.scam_queue.task_done()

    async def check_scam_logic(self, message, hashes, serverConfig):
        try:
            oldPacket = userPacket[message.author.id]
        except Exception:
            oldPacket = {"hashes": [], "content": "", "timestamp": message.created_at, "channelid": message.channel.id, "msg": message}

        userPacket[message.author.id] = {
            "hashes": hashes,
            "content": message.content,
            "timestamp": message.created_at,
            "channelid": message.channel.id,
            "msg": message
        }

        hashesMatch = (oldPacket["hashes"] == hashes) and (len(hashes) > 0)  # Only match if hashes exist
        contentMatch = (oldPacket["content"] == message.content) and (len(message.content) > 0)
        timestampMatch = (message.created_at - oldPacket["timestamp"]).total_seconds() < 30
        channelidMatch = (message.channel.id == oldPacket["channelid"])
        whitelist = ["<@1", "<@2", "<@3", "<@4", "<@5", "<@6", "<@7", "<@8", "<@9"]
        if (contentMatch or hashesMatch) and timestampMatch and (not channelidMatch) and (item not in message.content for item in whitelist):
            print(f"Match detected for {message.author}")

            logChannel = self.bot.get_channel(1152377925916688484)
            to_delete[message.author.id].append(message)
            to_delete[message.author.id].append(oldPacket["msg"])
            # Update strikes
            try:
                userStrikes[message.author.id] = userStrikes.get(message.author.id, 0) + 1
            except Exception:
                userStrikes[message.author.id] = 1

            action = serverConfig['flagaction']
            pingAction = serverConfig['flagping']

            embed = discord.Embed(title=f"A hacked account has been detected!", color=discord.Color.blurple())

            # Action Threshold Reached
            if userStrikes[message.author.id] >= int(serverConfig['flagthreshold']):
                embed = discord.Embed(title=f"Action taken on a hacked account", color=discord.Color.red())
                embed.set_footer(text=f"Action taken: {action}")

            embed.add_field(name="Username", value=f"{message.author.name}", inline=False)
            embed.add_field(name="User ID", value=f"{message.author.id}", inline=False)
            embed.add_field(name="User ping", value=f"<@{message.author.id}>", inline=False)
            embed.add_field(name="Server", value=f"{message.guild.name}>", inline=False)
            embed.add_field(name="Spacing", value=f'''{(message.created_at - oldPacket["timestamp"]).total_seconds()}s''', inline=False)
            # Send logs
            if logChannel:
                await logChannel.send(embed=embed)
                await logChannel.send(f'Message content:\n`{message.content}`')

            # Warning Stage
            if userStrikes[message.author.id] == int(serverConfig['flagthreshold']) - 1:
                await message.add_reaction('⚠️')
                try:
                    await message.author.send(f"### ⚠️ Warning: you are triggering Sprocket Bot's anti scam functions. ⚠️\nPlease go to any mutual servers and send a message different from your last one, in order to reset your counter.  Attachments are also tracked, so don't send the same ones.")
                except:
                    pass

            # Punishment Stage
            if userStrikes[message.author.id] >= int(serverConfig['flagthreshold']):
                channel = self.bot.get_channel(serverConfig['managerchannelid'])

                if action == "kick":
                    try:
                        delta = (datetime.datetime.now().astimezone() + datetime.timedelta(hours=1))
                        await message.author.timeout(delta, reason="Anti-scam tools: verifying user")
                        for message in to_delete[message.author.id]:
                            try:
                                await message.delete()
                            except Exception:
                                pass
                        await message.author.send("# ⚠️ READ THE FOLLOWING INSTRUCTIONS CAREFULLY ⚠️")
                        testMessage = await message.author.send("### You have tripped Sprocket Bot's automated anti-scam functions and are about to be kicked.")
                        response = await textTools.getResponse(await self.bot.get_context(testMessage), f"To remove your timeout, I need to verify that you are human.\nPlease reply with **exactly** the following sentence:\n`Sprocket Chan found the wrong bolt thief, let me free!`")
                        if len(response) < 5:
                            await message.author.send(f"You have been kicked from {message.guild.name}...")
                            await message.author.ban(reason="Automated anti-scam functions", delete_message_seconds=950)
                            await message.author.unban(reason="Automated anti-scam functions")
                        else:
                            await message.author.send(f"Acknowledged.")
                            await message.author.timeout(None, reason="Anti-scam tools: user verified in DMs")
                            userStrikes[message.author.id] = 0
                            to_delete[message.author.id] = []
                            await message.author.send(f"Record cleared and timeout removed.")
                    except Exception as e:
                        print(e)
                elif action == "timeout for 12 hours":
                    try:
                        await message.author.send(f"You have been timed out in {message.guild.name}...")
                        delta = (datetime.datetime.now().astimezone() + datetime.timedelta(hours=12))
                        await message.author.timeout(delta, reason="Hacked account")
                    except:
                        pass

                if channel:
                    await channel.send(embed=embed)
                    await channel.send(f'Message content:\n`{message.content}`')
                    if pingAction == "custom":
                        await channel.send(f"<@&{serverConfig['flagpingid']}>")
                    elif pingAction != "nobody":
                        await channel.send(f"@{serverConfig['flagping']}")
        else:
            userStrikes[message.author.id] = 0
            to_delete[message.author.id] = []
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(antiScamFunctions(bot))