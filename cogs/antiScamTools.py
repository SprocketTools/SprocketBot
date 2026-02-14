import hashlib
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
active_punishments = set()  # Prevents multiple punishment tasks for one user


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
        # 1. Ignore Bots
        if message.author.bot:
            return

        # 2. Ignore DMs
        if not message.guild:
            return

        # 3. Fast-Fail if User is already being processed/punished
        if message.author.id in active_punishments:
            try:
                await message.delete()
            except:
                pass
            return

        try:
            # Fetch config efficiently
            config_data = await self.bot.sql.databaseFetchdictDynamic(
                f'SELECT * FROM serverconfig WHERE serverid = $1;', [message.guild.id]
            )

            # If server isn't configured, ignore
            if not config_data:
                return

            serverConfig = config_data[0]

            # Hash Attachments
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

            # Initialize deletion list if needed
            if message.author.id not in to_delete:
                to_delete[message.author.id] = []

            payload = {
                "message": message,
                "hashes": hashes,
                "serverConfig": serverConfig,
                "timestamp": message.created_at,
                "content": message.content
            }
            await self.scam_queue.put(payload)

        except Exception as e:
            print(f"Error in on_message anti-scam: {e}")

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
            # Re-Check Active Punishment (in case it started while this item was in queue)
            if message.author.id in active_punishments:
                try:
                    await message.delete()
                except:
                    pass
                return

            oldPacket = userPacket.get(message.author.id, {
                "hashes": [],
                "content": "",
                "timestamp": message.created_at,
                "channelid": message.channel.id,
                "msg": message
            })

            userPacket[message.author.id] = {
                "hashes": hashes,
                "content": message.content,
                "timestamp": message.created_at,
                "channelid": message.channel.id,
                "msg": message
            }

            # Detection Logic
            hashesMatch = (oldPacket["hashes"] == hashes) and (len(hashes) > 0)
            contentMatch = (oldPacket["content"] == message.content) and (len(message.content) > 0)
            contentMismatch = (oldPacket["content"] != message.content) and (len(message.content) > 0)
            # Timestamp check (60s threshold)
            timestampMatch = (message.created_at - oldPacket["timestamp"]).total_seconds() < 12.1
            channelidMatch = (message.channel.id == oldPacket["channelid"])

            # Whitelist logic
            whitelist = ["<@1", "<@2", "<@3", "<@4", "<@5", "<@6", "<@7", "<@8", "<@9"]
            is_whitelisted = any(item in message.content for item in whitelist)

            if (contentMatch or hashesMatch) and timestampMatch and (not channelidMatch) and not is_whitelisted and not contentMismatch:
                print(f"Match detected for {message.author}")

                logChannel = self.bot.get_channel(1152377925916688484)
                to_delete[message.author.id].append(message)
                to_delete[message.author.id].append(oldPacket["msg"])

                # Update strikes
                userStrikes[message.author.id] = userStrikes.get(message.author.id, 0) + 1

                flag_threshold = int(serverConfig['flagthreshold'])

                # --- LOGGING ---
                if logChannel:
                    color = discord.Color.blurple()
                    title = "A hacked account has been detected!"

                    if userStrikes[message.author.id] >= flag_threshold:
                        color = discord.Color.red()
                        title = "Action taken on a hacked account"

                    embed = discord.Embed(title=title, color=color)
                    embed.add_field(name="Username", value=f"{message.author.name}", inline=False)
                    embed.add_field(name="User ID", value=f"{message.author.id}", inline=False)
                    embed.add_field(name="User ping", value=f"<@{message.author.id}>", inline=False)
                    embed.add_field(name="Server", value=f"{message.guild.name}", inline=False)
                    embed.add_field(name="Spacing",
                                    value=f'''{(message.created_at - oldPacket["timestamp"]).total_seconds():.2f}s''',
                                    inline=False)

                    if userStrikes[message.author.id] >= flag_threshold:
                        embed.set_footer(text=f"Action taken: {serverConfig['flagaction']}")

                    await logChannel.send(embed=embed)
                    await logChannel.send(f'Message content:\n`{message.content}`')

                # --- WARNING STAGE ---
                if userStrikes[message.author.id] == flag_threshold - 1:
                    await message.add_reaction('⚠️')
                    try:
                        await message.author.send(
                            f"### ⚠️ Warning: you are triggering Sprocket Bot's anti scam functions. ⚠️\nPlease go to any mutual servers and send a message different from your last one, in order to reset your counter. Attachments are also tracked, so don't send the same ones.")
                    except:
                        pass

                # --- PUNISHMENT STAGE (Non-Blocking & Single Instance) ---
                if userStrikes[message.author.id] >= flag_threshold:
                    if message.author.id not in active_punishments:
                        active_punishments.add(message.author.id)
                        self.bot.loop.create_task(
                            self.execute_punishment(message, serverConfig, logChannel)
                        )
                    else:
                        # If a task is already running, just delete the new spam
                        try:
                            await message.delete()
                        except:
                            pass

            else:
                # Reset if not a match
                userStrikes[message.author.id] = 0
                to_delete[message.author.id] = []
                # Ensure they aren't stuck in active_punishments if they somehow got reset
                active_punishments.discard(message.author.id)

        except Exception as e:
            print(f"Critical error in check_scam_logic: {e}")
            active_punishments.discard(message.author.id)

    async def execute_punishment(self, message, serverConfig, logChannel):
        """Handles the actual kicking/banning logic in a separate task."""
        try:
            action = serverConfig['flagaction']
            pingAction = serverConfig['flagping']
            channel = self.bot.get_channel(serverConfig['managerchannelid'])

            # Prepare Log Embed for Manager Channel
            embed = discord.Embed(title=f"Action taken on a hacked account", color=discord.Color.red())
            embed.set_footer(text=f"Action taken: {action}")
            embed.add_field(name="Username", value=f"{message.author.name}", inline=False)
            embed.add_field(name="User ID", value=f"{message.author.id}", inline=False)

            if action == "kick":
                # 1. Timeout immediately
                try:
                    # Using timedelta directly prevents timezone mismatch errors
                    await message.author.timeout(datetime.timedelta(hours=1), reason="Anti-scam tools: verifying user")
                except Exception as e:
                    print(f"Failed to apply timeout: {e}")
                    pass

                    # 2. Delete spam messages
                for msg in to_delete.get(message.author.id, []):
                    try:
                        await msg.delete()
                    except Exception:
                        pass

                # 3. Verification Process
                try:
                    await message.author.send("# ⚠️ READ THE FOLLOWING INSTRUCTIONS CAREFULLY ⚠️")
                    await message.author.send(
                        "### You have tripped Sprocket Bot's automated anti-scam functions and are about to be kicked.")

                    # We use native wait_for instead of textTools to ensure we catch the USER's reply in DMs
                    def check(m):
                        return m.author.id == message.author.id and isinstance(m.channel, discord.DMChannel)

                    await message.author.send(
                        "To remove your timeout, I need to verify that you are human.\n"
                        "Please reply with **exactly** the following sentence:\n"
                        "`Sprocket Chan found the wrong bolt thief, let me free!`"
                    )

                    response = await self.bot.wait_for('message', check=check, timeout=300)  # 5 min timeout

                    if response and "bolt" in response.content.lower():
                        await message.author.send(f"Acknowledged.")
                        try:
                            await message.author.timeout(None, reason="Anti-scam tools: user verified in DMs")
                        except:
                            pass

                        # Reset
                        userStrikes[message.author.id] = 0
                        to_delete[message.author.id] = []
                        active_punishments.discard(message.author.id)

                        await message.author.send(f"Record cleared and timeout removed.")
                        return  # Exit successfully
                    else:
                        raise Exception("Verification Failed")

                except (asyncio.TimeoutError, Exception) as e:
                    # Kick/Ban logic on failure or timeout
                    try:
                        await message.author.send(f"You have been kicked from {message.guild.name}...")
                    except:
                        pass

                    try:
                        await message.author.ban(reason="Automated anti-scam functions", delete_message_seconds=950)
                        await message.author.unban(reason="Automated anti-scam functions")  # Soft ban
                    except Exception as ban_err:
                        if logChannel:
                            await logChannel.send(f'Failed to execute ban/kick: {ban_err}')

                    # Clean up
                    active_punishments.discard(message.author.id)

            elif action == "timeout for 12 hours":
                try:
                    await message.author.send(f"You have been timed out in {message.guild.name}...")
                    # Updated to use timedelta here as well for consistency
                    await message.author.timeout(datetime.timedelta(hours=12), reason="Hacked account")
                except:
                    pass
                active_punishments.discard(message.author.id)

            # Notify Manager Channel
            if channel:
                await channel.send(embed=embed)
                await channel.send(f'Message content:\n`{message.content}`')
                if pingAction == "custom":
                    await channel.send(f"<@&{serverConfig['flagpingid']}>")
                elif pingAction != "nobody":
                    await channel.send(f"@{serverConfig['flagping']}")

        except Exception as e:
            print(f"Error in execute_punishment task: {e}")
            active_punishments.discard(message.author.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(antiScamFunctions(bot))