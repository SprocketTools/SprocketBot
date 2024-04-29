import discord
from discord.ext import commands
from discord import app_commands

class registerFunctions(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command(name="cog1", description="Sends hello!")
  async def cog1(self, ctx):
    await ctx.send(content="Hello!")

  @commands.command(name="setupDatabase", description="Wipe literally everything.")
  async def cog2(self, ctx):
    await ctx.send(content="Hello!")




async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(registerFunctions(bot))