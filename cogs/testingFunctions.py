import discord
from discord.ext import commands
promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools
class testingFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="testcommand3", description="testing some stuff")
    async def testcommand3(self, ctx: commands.Context):
        """Sends a message with our dropdown containing colours"""
        result = "blank"
        view = DropdownView(ctx.author.id)
        await ctx.send('Pick your favourite colour:', view=view)
        await view.wait()

        print(promptResponses[ctx.author.id])
        promptResponses.__delitem__(ctx.author.id)


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(testingFunctions(bot))

class Dropdown(discord.ui.Select):
    def __init__(self, authorID):
        self.authorID = authorID
        options = [
            discord.SelectOption(label='Red', description='Your favourite colour is red', emoji='🟥'),
            discord.SelectOption(label='Green', description='Your favourite colour is green', emoji='🟩'),
            discord.SelectOption(label='Blue', description='Your favourite colour is blue', emoji='🟦'),
        ]
        super().__init__(placeholder='Choose your favourite colour...', min_values=1, max_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Your favourite colour is {self.values[0]}')
        promptResponses[self.authorID] = self.values[0]
        self.view.stop()

class DropdownView(discord.ui.View):
    def __init__(self, authorID):
        super().__init__()
        self.authorID = authorID
        self.add_item(Dropdown(authorID))