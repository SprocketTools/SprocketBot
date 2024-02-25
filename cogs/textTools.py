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

  async def getSQLprompt(inputList: list):
      names = list(inputList.keys())
      values = list(inputList.values())
      names_string = str(names[0])
      values_string = "'" + str(values[0]) + "'"
      i = 1
      while i < len(names):
          names_string = names_string + f', {names[i]}'
          values_string = values_string + f", '{values[i]}'"
          i += 1
      #print(names_string)
      #print(values_string)
      return names_string, values_string

  async def addLine(inputOne: str, inputTwo: str):
      return f"{inputOne}\n{inputTwo}"



async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(textTools(bot))