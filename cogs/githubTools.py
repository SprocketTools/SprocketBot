import discord, os, platform
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from git import Repo
# Github config
if platform.system() == "Windows":
    GithubURL = "https://github.com/SprocketTools/SprocketTools.github.io"
    GithubDirectory = "C:\\Users\\colson\\Documents\\GitHub\\Testing\\SprocketTools.github.io"
    OSslashLine = "\\"

else:
    # default settings (running on Rasbian)
    GithubURL = "https://github.com/SprocketTools/SprocketTools.github.io"
    GithubDirectory = "/home/mumblepi/SprocketTools.github.io"
    OSslashLine = "/"
imgCatalogFolder = "img"
imgCandidateFolder = "imgbin"

Path(GithubDirectory).mkdir(parents=True, exist_ok=True)
try:
    repo = Repo.clone_from(GithubURL, GithubDirectory)
except Exception:
    repo = Repo(GithubDirectory)

class githubTools(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot




  @commands.command(name="cog5", description="lol")
  async def cog5(self, ctx):
    await ctx.send(content="Hello!")



async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(githubTools(bot))