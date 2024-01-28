import discord
from discord.ext import commands
from discord import app_commands

class textTools(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
  async def sanitize(inputPhrase: str):
      sanitizeKeywords = ["@", "/", "invalid_tank"]
      outputPhrase = inputPhrase
      for phrase in sanitizeKeywords:
          outputPhrase = outputPhrase.replace(phrase, "")
      return outputPhrase

  async def addLine(inputOne: str, inputTwo: str):
      return f"{inputOne}\n{inputTwo}"



async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(textTools(bot))