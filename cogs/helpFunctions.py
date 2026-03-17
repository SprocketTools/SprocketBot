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
        embed = discord.Embed(title=f"**Sprocket Bot Commands**",description="*Sprocket Bot's prefix is* `-`\n",color=discord.Color.random())
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="SprocketHelp", value="Get help with building in Sprocket", inline=False)
        embed.add_field(name="bakeGeometry", value="Bake 0.127 compartments together", inline=False)
        embed.add_field(name="trasplant", value="Copy turrets between 0.2 tanks", inline=False)
        embed.add_field(name="submitDecal", value="Submit decals to the SprocketTools decal repository", inline=False)
        embed.add_field(name="addError", value="Add a funny response to Sprocket Bot's error catalog", inline=False)
        embed.add_field(name="weather", value="Apply wear and tear effects to attached photos", inline=False)
        embed.add_field(name="help", value="Shows this message", inline=False)
        embed.add_field(name="settings", value="Adjust the server configuration", inline=False)
        embed.set_thumbnail(url='https://sprockettools.github.io/SprocketToolsLogo.png')
        embed.set_footer(text=await self.bot.error.retrieveError(ctx))
        await ctx.send(embed=embed)



async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(helpFunctions(bot))