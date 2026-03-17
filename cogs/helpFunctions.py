import io
import json
from datetime import datetime
import discord
import pandas as pd
import matplotlib.dates as mdates
import type_hints
from discord.ext import commands
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
promptResponses = {}
from cogs.textTools import textTools
from google import genai


class helpFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.command(name="help", description="View all the bot commands")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(title=f"**Quick Help**",description="*Sprocket Bot's prefix is* `-`\nUse `-adminhelp`, `-modhelp`, or `-campaignhelp` for additional help menus.",color=discord.Color.random())
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="SprocketHelp", value="Get help with building in Sprocket", inline=False)
        embed.add_field(name="bakeGeometry", value="Bake 0.2 compartments together", inline=False)
        embed.add_field(name="analyzeBlueprint", value="Get a stat card of your Sprocket tank", inline=False)
        embed.add_field(name="trasplant", value="Copy turrets between 0.2 tanks", inline=False)
        embed.add_field(name="submitDecal", value="Submit decals to the SprocketTools decal repository", inline=False)
        embed.add_field(name="addError", value="Add a funny response to Sprocket Bot's error catalog", inline=False)
        embed.add_field(name="weather", value="Apply wear and tear effects to attached photos", inline=False)
        embed.add_field(name="askDevs", value="Ask the Sprocket devs a question (main Discord server only)", inline=False)
        embed.add_field(name="help", value="Shows this message", inline=False)
        embed.set_thumbnail(url='https://sprockettools.github.io/SprocketToolsLogo.png')
        embed.set_footer(text=await self.bot.error.retrieveError(ctx))
        await ctx.send(embed=embed)

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="adminhelp", description="View all the bot commands")
    async def adminhelp(self, ctx: commands.Context):
        embed = discord.Embed(title=f"**Admin Tools**",description="*Sprocket Bot's prefix is* `-`\nUse `-adminhelp`, `-modhelp`, or `-campaignhelp` for additional help menus.",color=discord.Color.random())
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="settings", value="Adjust the server configuration", inline=False)
        embed.add_field(name="configureChannel", value="Configure a channel's policies on commands", inline=False)
        embed.add_field(name="listStarboards", value="Lists all active starboards", inline=False)
        embed.add_field(name="addNewStarboard", value="Add a new starboard to the server", inline=False)
        embed.add_field(name="deleteStarboard", value="Delete a starboard (does not wipe channel)", inline=False)
        embed.add_field(name="codeSetup", value="Activate a word-guess game in a channel", inline=False)
        embed.add_field(name="resetCodeProgress", value="Reset the server's word-guess game", inline=False)
        embed.add_field(name="IAmError", value="Change the server's word-guess phrase", inline=False)

        embed.set_thumbnail(url='https://sprockettools.github.io/SprocketToolsLogo.png')
        embed.set_footer(text=await self.bot.error.retrieveError(ctx))
        await ctx.send(embed=embed)

    @commands.has_permissions(mute_members=True)
    @commands.command(name="modhelp", description="View all the bot commands")
    async def modhelp(self, ctx: commands.Context):
        embed = discord.Embed(title=f"**Moderation Help**",description="Note: commands with a \\ are slash commands.",color=discord.Color.random())
        embed.add_field(name="\\warn", value="Issue a warning to a user in DMs", inline=False)
        embed.add_field(name="\\note", value="Leave a note on a user's record (does not DM)", inline=False)
        embed.add_field(name="\\warnings", value="show a user's warnings", inline=False)
        embed.add_field(name="\\ban", value="ban a user", inline=False)
        embed.add_field(name="manageAllRules", value="Manage the list of server rules", inline=False)
        embed.add_field(name="addRule", value="Add a server rule", inline=False)
        embed.set_thumbnail(url='https://sprockettools.github.io/SprocketToolsLogo.png')
        embed.set_footer(text=await self.bot.error.retrieveError(ctx))
        await ctx.send(embed=embed)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(helpFunctions(bot))