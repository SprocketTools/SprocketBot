import discord
from discord.ext import commands
import os, platform, discord, configparser, ast, json
from discord.ext import commands
from discord import app_commands
import json, asyncio
from pathlib import Path
from cogs.textTools import textTools
from cogs.SQLfunctions import SQLfunctions
from cogs.blueprintFunctions import blueprintFunctions
from cogs.discordUIfunctions import discordUIfunctions
from discord import app_commands
from cogs.textTools import textTools
class adminFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="resetServerConfig", description="Reset everyone's server configurations")
    async def resetServerConfig(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        prompt = "DROP TABLE IF EXISTS serverconfig"
        await SQLfunctions.databaseExecute(prompt)
        prompt = ('''CREATE TABLE IF NOT EXISTS serverconfig (
                              serverid BIGINT, 
                              ownerID BIGINT,
                              generalchannelID BIGINT,
                              allowfunny BOOL,
                              updateschannelID BIGINT,
                              commandschannelID BIGINT,
                              managerchannelID BIGINT,
                              serverboosterroleID BIGINT,
                              contestmanagerroleID BIGINT,
                              campaignmanagerroleID BIGINT);''')
        await SQLfunctions.databaseExecute(prompt)
        await ctx.send("Done!  Now go DM everyone that their config was reset.")

    @commands.command(name="sendGlobalUpdate", description="Send a global update to all servers.")
    async def sendGlobalUpdate(self, ctx: commands.Context):
        view = globalSendDropdownView()
        await ctx.send(content="Where are you sending today's update to?", view=view)
        await view.wait()
        await ctx.send("You will be sending a message to:")
        for server in self.bot.guilds:
            await ctx.send(f"{server.name}")
        result = view.result
        await ctx.send("Type your message here!")
        # get the message that is to be sent
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            message_out_text = msg.content
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        if result == "direct":
            for server in self.bot.guilds:
                if server.owner.id != 123105882102824960:
                    serverOwner = self.bot.get_user(server.owner.id)
                    await serverOwner.send(message_out_text)
        else:
            for server in self.bot.guilds:
                channel = int([dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {server.id}')][0][result.lower()])
                if channel < 5:
                    if server.owner.id != 123105882102824960:
                        serverOwner = self.bot.get_user(server.owner.id)
                        await serverOwner.send(message_out_text)
                else:
                    serverChannel = self.bot.get_channel(channel)
                    await serverChannel.send(message_out_text)

        await ctx.send("## Delivered!")

    @commands.command(name="rebootServer", description="setup the server")
    async def rebootServer(self, ctx: commands.Context):
        if ctx.author.id == 712509599135301673:
            pass
        else:
            return
        os.system("systemctl reboot -i")

    @commands.command(name="setup", description="setup the server")
    async def setup(self, ctx: commands.Context):
        if ctx.author.guild_permissions.administrator == True:
            pass
        else:
            return
        responses = {}
        responses["serverid"] = ctx.guild.id
        responses["ownerid"] = ctx.guild.owner.id

        await ctx.send("Before we begin: it is recommended to run this command in an admin channel, as you will be asked to ping up to three roles.  Reply with 'continue' if this is an appropriate channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            if msg.content.lower() == "continue":
                pass
            else:
                return
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("Awesome!  Let's get started. \n\nWhat is your server's general chat?  Reply to this message with a mention of that channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["generalchannelID"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What channel do you want Sprocket Bot update notes to appear in?  This should be set to any publicly-visible channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["updateschannelID"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What is your bot commands channel?  This channel will be the only location that utility commands can be ran, as a result it should be a publicly-visible channel.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["commandschannelID"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What channel do you want administrative Sprocket Bot information to appear in?  This channel should only be visible to trusted server managers.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["managerchannelID"] = msg.channel_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What is your server booster role?  Reply to this message with a ping of that role.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["serverboosterroleID"] = msg.role_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What role do you want to designate as your server contest managers?  Reply to this message with a ping of that role.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["contestmanagerroleID"] = msg.role_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("What role do you want to designate as your server campaign managers?  Reply to this message with a ping of that role.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            responses["campaignmanagerroleID"] = msg.role_mentions[0].id
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("Sprocket Bot can interact with users in your general chat!  Do you wish to enable the fun module for exclusively your general chat?")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30000.0)
            if msg.content.lower() == "true" or msg.content.lower() == "yes":
                responses["allowfunny"] = True
            else:
                responses["allowfunny"] = False
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return

        await ctx.send("## All data successfully collected!\nBeginning processing now...")
        keystr, valuestr = await textTools.getSQLprompt(responses)
        await SQLfunctions.databaseExecute(f'''DELETE FROM serverconfig WHERE serverid = {ctx.guild.id};''')
        await SQLfunctions.databaseExecute(f'''INSERT INTO serverconfig ({keystr}) VALUES ({valuestr});''')
        await ctx.send("## Done!")

    @commands.command(name="troll", description="send a message wherever you want")
    async def troll(self, ctx: commands.Context, channelin: str, *, message):
        if ctx.author.id == 712509599135301673:
            import re
            channelin = int(re.sub(r'[^0-9]', '', channelin))
            print(channelin)
            channel = self.bot.get_channel(channelin)
            await ctx.send("Message is en route.")
            await channel.send(message)
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                await channel.send(file=file, content="")

















async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(adminFunctions(bot))

class globalSendDropdown(discord.ui.Select):
    def __init__(self):
        options = []
        options.append(discord.SelectOption(label="Server Owners' DMs", emoji='🏆', value="direct"))
        options.append(discord.SelectOption(label="General Chats", emoji='🏆', value="generalchannelID"))
        options.append(discord.SelectOption(label="Bot Updates", emoji='🏆', value="updateschannelID"))
        options.append(discord.SelectOption(label="Server Managers", emoji='🏆', value="managerchannelID"))

        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # promptResponses[self.authorID] = self.values[0]
        self.view.result = self.values[0]
        await interaction.response.defer()
        self.view.stop()

class globalSendDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(globalSendDropdown())