import discord
from discord.ext import commands

import type_hints
from cogs.textTools import textTools

class ChannelConfig(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.categories = ["autoai", "ai", "autoerror", "error", "utility"]

    @commands.command(name="setupChannelConfigTables", description="[Owner] Create tables for channel permissions")
    async def setupChannelConfigTables(self, ctx: commands.Context):
        if ctx.author.id != self.bot.ownerid:
            return
        await self.bot.sql.databaseExecute('''
            CREATE TABLE IF NOT EXISTS channel_blocks (
                server_id BIGINT,
                channel_id BIGINT,
                category VARCHAR(50),
                PRIMARY KEY (server_id, channel_id, category)
            );
        ''')
        await ctx.send("## Done!") ## apparently you can use this PRIMARY KEY thing to expedite searches and prevent duplicates.  Need to investigate more.

    @commands.command(name="configureChannel", description="Enable/Disable a command category in a channel")
    async def configureChannel(self, ctx: commands.Context, channel: discord.TextChannel = None):

        if not (ctx.author.guild_permissions.manage_guild or ctx.author.id == self.bot.ownerid):
            return await self.bot.error.sendError(ctx)
        target_channel = channel or ctx.channel
        embed = discord.Embed(title=f"Config for {target_channel.mention}",
                              description="Use the buttons to toggle the settings for this channel.",
                              color=discord.Color.random())
        msg_out = await ctx.send(embed=embed)
        while True:
            embed = discord.Embed(title=f"Config for {target_channel.mention}", description="Use the buttons to toggle the settings for this channel.", color=discord.Color.random())
            embed.add_field(name="Automatic AI Interactions (coming soon)", value=f"{"Disabled" if len(await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM channel_blocks WHERE channel_id = $1 AND category = 'autoai';''', [target_channel.id])) > 0 else "Enabled"}", inline=False)
            embed.add_field(name="Manual AI Interactions (Jarvis, etc.)", value=f"{"Disabled" if len(await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM channel_blocks WHERE channel_id = $1 AND category = 'ai';''', [target_channel.id])) > 0 else "Enabled"}", inline=False)
            embed.add_field(name="Automatic Non-AI Fun Stuff (random -error posts, etc.)", value=f"{"Disabled" if len(await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM channel_blocks WHERE channel_id = $1 AND category = 'autoerror';''', [target_channel.id])) > 0 else "Enabled"}", inline=False)
            embed.add_field(name="Fun Commands (-addError, -getError, etc.)", value=f"{"Disabled" if len(await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM channel_blocks WHERE channel_id = $1 AND category = 'error';''', [target_channel.id])) > 0 else "Enabled"}", inline=False)
            embed.add_field(name="Utility (-weather, -submitDecal, etc.)", value=f"{"Disabled" if len(await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM channel_blocks WHERE channel_id = $1 AND category = 'utility';''', [target_channel.id])) > 0 else "Enabled"}", inline=False)
            await msg_out.edit(embed=embed)

            options = [["Automatic AI", "autoai"], ["Manual AI", "ai"], ["Automatic Fun Stuff", "autoerror"], ["Manual Fun Stuff", "error"], ["Utility Commands", "utility"], ["Exit", "exit"]]
            selection = await self.bot.ui.getButtonChoiceReturnID(ctx, options)
            print(selection)
            if selection == "exit":
                await self.bot.error.sendError(ctx)
                return

            exists = await self.bot.sql.databaseFetchrowDynamic(
                '''SELECT * FROM channel_blocks WHERE channel_id = $1 AND category = $2;''',
                [target_channel.id, selection]
            )

            if exists:
                await self.bot.sql.databaseExecuteDynamic(
                    '''DELETE FROM channel_blocks WHERE channel_id = $1 AND category = $2;''',
                    [target_channel.id, selection]
                )
            else:
                await self.bot.sql.databaseExecuteDynamic(
                    '''INSERT INTO channel_blocks (server_id, channel_id, category) VALUES ($1, $2, $3);''',
                    [ctx.guild.id, target_channel.id, selection]
                )

    @commands.command(name="viewChannelConfig", description="See disabled categories for a channel")
    async def viewChannelConfig(self, ctx: commands.Context, channel: discord.TextChannel = None):
        target_channel = channel or ctx.channel

        blocks = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT category FROM channel_blocks WHERE channel_id = $1;''',
            [target_channel.id]
        )

        if not blocks:
            await ctx.send(f"**{target_channel.mention}** has no restrictions. All commands allowed.")
        else:
            disabled_list = [f"• {b['category']}" for b in blocks]
            embed = discord.Embed(title=f"🔒 Restrictions for #{target_channel.name}", color=discord.Color.red())
            embed.add_field(name="Disabled Categories", value="\n".join(disabled_list))
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ChannelConfig(bot))