import discord
from discord.ext import commands
from discord import app_commands
from cogs.textTools import textTools
class testingFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="testcommand3", description="Register a contest for the server.")
    async def testcommand3(self, ctx: commands.Context):
        print("Hi!")

    @commands.command(name="dropdowntest", description="Register a contest for the server.")
    async def dropdowntest(self, ctx):
        view = discord.ui.View(timeout=1)
        dropdown = discord.ui.Select(
            placeholder="Select an option",
            options=[
                discord.SelectOption(label="Option 1", value="1"),
                discord.SelectOption(label="Option 2", value="2"),
                discord.SelectOption(label="Option 3", value="3"),
            ],
        )
        view.add_item(dropdown)
        await ctx.send("Select an option:", view=view)
        await view.wait()
        value = dropdown.values[0]

        await ctx.send(f"You selected: {value}")



async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(testingFunctions(bot))