import discord
from discord.ext import commands
# promptResponses = {}
import os, platform, discord, configparser, ast, json
from discord.ext import commands
from discord import app_commands
import json, asyncio
from pathlib import Path
from cogs.textTools import textTools
from cogs.SQLfunctions import SQLfunctions
from discord import app_commands
from cogs.textTools import textTools
class discordUIfunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    async def getContestChoice(ctx: commands.Context, contestList: list, userPrompt: str):
        view = DropdownView(contestList)
        await ctx.send(content=userPrompt, view=view)
        await view.wait()
        result = view.result
        # result = promptResponses[contestHostID]
        # promptResponses.__delitem__(contestHostID)
        return result

    async def getCategoryChoice(ctx: commands.Context, categoryList: list, userPrompt: str):
        chosen = False
        int = 0
        while chosen == False:
            categoryListSlice = categoryList[int:int+20]
            int = int + 20
            view = categoryDropdownView(categoryListSlice)
            await ctx.send(content=userPrompt, view=view)
            await view.wait()
            result = view.result
            if result != "Next page":
                return result

    async def getContestTypeChoice(ctx: commands.Context):
        if ctx.channel.type is discord.ChannelType.private:
            return "Global"
        view = buttonConfirm()
        await ctx.send(content="Are you submitting into a global contest or a server-specific contest?", view=view)
        await view.wait()
        if view.value is None:
            await ctx.reply("Response timed out.")
        elif view.value:
            return "Global"
        else:
            return "Server"

    async def getChoiceFromList(ctx: commands.Context, categoryList: list, userPrompt: str):
        chosen = False
        int = 0
        while chosen == False:
            categoryListSlice = categoryList[int:int+20]
            int = int + 20
            view = listChoiceDropdownView(categoryListSlice)
            await ctx.send(content=userPrompt, view=view)
            await view.wait()
            result = view.result
            if result != "Next page":
                return result


async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(discordUIfunctions(bot))

class Dropdown(discord.ui.Select):
    def __init__(self, contestList):
        self.contestList = contestList
        i = 0
        options = []
        for contest in contestList:
            options.append(discord.SelectOption(label=contest["name"], emoji='🏆', value=contest["name"]))
            i += 1
        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        # promptResponses[self.authorID] = self.values[0]
        self.view.result = self.values[0]
        await interaction.response.defer()
        self.view.stop()

class DropdownView(discord.ui.View):
    def __init__(self, contestList):
        super().__init__()
        self.contestList = contestList
        self.add_item(Dropdown(contestList))

class buttonConfirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Global', emoji='🌎', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Server', emoji='🌆', style=discord.ButtonStyle.blurple)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

class categoryDropdown(discord.ui.Select):
    def __init__(self, categoryList):
        self.categoryList = categoryList
        i = 0
        options = []
        for category in categoryList:
            options.append(discord.SelectOption(label=category["categoryname"], emoji='🏆', value=category["categoryname"]))
            i += 1
        if len(options) > 19:
            options.append(discord.SelectOption(label="Next page", emoji='➡️', value="Next page"))
        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        # promptResponses[self.authorID] = self.values[0]
        self.view.result = self.values[0]
        await interaction.response.defer()
        self.view.stop()

class categoryDropdownView(discord.ui.View):
    def __init__(self, categoryList):
        super().__init__()
        self.contestList = categoryList
        self.add_item(categoryDropdown(categoryList))

class listChoiceDropdown(discord.ui.Select):
    def __init__(self, itemList):
        self.categoryList = itemList
        i = 0
        options = []
        for item in itemList:
            options.append(discord.SelectOption(label=item, emoji='⚫', value=item))
            i += 1
        if len(options) > 19:
            options.append(discord.SelectOption(label="Next page", emoji='➡️', value="Next page"))
        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        # promptResponses[self.authorID] = self.values[0]
        self.view.result = self.values[0]
        await interaction.response.defer()
        self.view.stop()

class listChoiceDropdownView(discord.ui.View):
    def __init__(self, categoryList):
        super().__init__()
        self.contestList = categoryList
        self.add_item(listChoiceDropdown(categoryList))
