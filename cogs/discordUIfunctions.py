import textwrap

import discord
from unicodedata import lookup
from discord.ext import commands
# promptResponses = {}
import os, platform, discord, configparser, ast, json
from discord.ext import commands

#from cogs.textTools import textTools


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

    async def getButtonChoice(ctx: commands.Context, inList: list):
        view = getButtonChoice(ctx, inList)
        messageOut = await ctx.send(view=view)
        await view.wait()
        await messageOut.delete(delay=10)
        return view.value


    async def getButtonChoiceReturnID(ctx: commands.Context, inList: list):
        view = getButtonChoiceReturnID(ctx, inList)
        await ctx.send(view=view)
        await view.wait()
        return view.id

    async def getYesNoChoice(ctx: commands.Context):
        view = YesNoButtons()
        await ctx.send(view=view)
        await view.wait()
        return view.value

    async def getYesNoModifyStopChoice(ctx: commands.Context):
        view = YesNoModifyStopButtons()
        await ctx.send(view=view)
        await view.wait()
        return view.value

    async def getResponse(ctx: commands.Context, prompt, action=None):
        promptMsg = await ctx.send(prompt)
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = await ctx.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            raise ValueError("User termination")
        if action == "delete":
            await promptMsg.delete()
            await msg.delete()
        return msg.content

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
        categoryList = list(set(categoryList))
        categoryList.sort()
        if len(categoryList) > 60:
            filtered_options = []
            while len(filtered_options) == 0:
                options = ["AB", "CD", "EF", "GH", "IJ", "KL", "MN", "OP", "QR", "ST", "UV", "WX", "YZ", "do not sort", "search"]
                await ctx.send(f"Yikes, there are {len(categoryList)} choices!  Pick the first letter of your desired option.")
                sortChoice = await discordUIfunctions.getButtonChoice(ctx, options)
                if sortChoice == "search":
                    query = await discordUIfunctions.getResponse(ctx, "reply with your search query")
                    filtered_options = [option for option in categoryList if query.lower() in option.lower()]  # ai suggestion
                    if len(filtered_options) == 0:
                        await ctx.send("There are no valid options that start with these letters - try again.")
                    else:
                        categoryList = filtered_options

                elif sortChoice != "do not sort":
                    filtered_options = [option for option in categoryList if option[0].lower() in sortChoice.lower()] #ai suggestion
                    if len(filtered_options) == 0:
                        await ctx.send("There are no valid options that start with these letters - try again.")
                    else:
                        categoryList = filtered_options


        print(categoryList)
        while chosen == False:
            categoryListSlice = categoryList[int:int+20]
            int = int + 20
            if len(categoryList) == 1:
                return categoryList[0]
            if len(categoryList) == 0:
                return
            view = listChoiceDropdownView(ctx, categoryListSlice)
            await ctx.send(content=userPrompt, view=view, ephemeral=True)
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
        if interaction.user == interaction.message.author:
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
    def __init__(self, ctx: commands.Context, itemList):
        self.categoryList = itemList
        self.ctx = ctx
        i = 0
        options = []
        for item in itemList:
            if str.isalpha(item[0].lower()):
                options.append(discord.SelectOption(label=item, emoji=chr(127365 + (ord(item[0].lower()))), value=item))
            else:
                options.append(discord.SelectOption(label=item, emoji='❔', value=item))
            i += 1
        if len(options) > 19:
            options.append(discord.SelectOption(label="Next page", emoji='➡️', value="Next page"))
        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user == self.ctx.author:
            # promptResponses[self.authorID] = self.values[0]
            self.view.result = self.values[0]
            await interaction.response.defer()
            self.view.stop()
        else:
            await interaction.response.send_message(content="Love the ambition, but this isn't your menu.", ephemeral=True)

class listChoiceDropdownView(discord.ui.View):
    def __init__(self, ctx: commands.Context, categoryList):
        super().__init__()
        self.contestList = categoryList
        self.add_item(listChoiceDropdown(ctx, categoryList))

class YesNoButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=360)
        self.value = None
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def callbackYes(self, a, b):
        self.value = True
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def callbackNo(self, a, b):
        self.value = False
        await a.response.defer()
        self.stop()




class YesNoModifyStopButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=360)
        self.value = None
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def callbackYes(self, a, b):
        self.value = "yes"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def callbackNo(self, a, b):
        self.value = "no"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="Modify", style=discord.ButtonStyle.grey)
    async def callbackModify(self, a, b):
        self.value = "modify"
        await a.response.defer()
        self.stop()

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.blurple)
    async def callbackStop(self, a, b):
        self.value = "stop"
        await a.response.defer()
        self.stop()










class buttonList(discord.ui.Button['getButtonChoice']):
    # https://github.com/Rapptz/discord.py/blob/master/examples/views/tic_tac_toe.py
    def __init__(self, ctx: commands.Context, value: str, pos: int):
        self.value = value
        self.row = int(pos/5)
        self.ctx = ctx
        if value.lower() == "exit" or value.lower() == "0" or value.lower() == "stop" or value.lower() == "cancel":
            super().__init__(style=discord.ButtonStyle.red, label=value, row=self.row)
        elif pos % 3 == 0:
            super().__init__(style=discord.ButtonStyle.blurple, label=value, row=self.row)
        elif pos % 3 == 1:
            super().__init__(style=discord.ButtonStyle.green, label=value, row=self.row)
        else:
            super().__init__(style=discord.ButtonStyle.secondary, label=value, row=self.row)


    async def callback(self, interaction: discord.Interaction):
        if interaction.user == self.ctx.author:
            assert self.view is not None
            view: getButtonChoice = self.view
            view.value = self.value
            await interaction.response.defer()
            view.stop()
        else:
            await interaction.response.send_message(content="### Ouchie!  \n[Don't touch my buttons, they aren't yours!](<https://www.youtube.com/watch?v=a6pbjksYUHY>)\n", ephemeral=True)

class getButtonChoice(discord.ui.View):
    value = ""
    def __init__(self, ctx: commands.Context, listIn: list):
        super().__init__(timeout=600)
        self.list = listIn
        self.ctx = ctx
        i = 0
        for str in self.list:
            self.add_item(buttonList(ctx, str, i))
            i += 1





class buttonListReturnID(discord.ui.Button['getButtonChoiceReturnID']):
    # https://github.com/Rapptz/discord.py/blob/master/examples/views/tic_tac_toe.py
    def __init__(self, ctx: commands.Context, value: str, id: str, pos: int):
        self.id = id
        self.value = value
        self.row = int(pos/5)
        self.ctx = ctx
        if value.lower() == "exit":
            super().__init__(style=discord.ButtonStyle.red, label=value, row=self.row)
        elif pos % 3 == 0:
            super().__init__(style=discord.ButtonStyle.blurple, label=value, row=self.row)
        elif pos % 3 == 1:
            super().__init__(style=discord.ButtonStyle.green, label=value, row=self.row)
        else:
            super().__init__(style=discord.ButtonStyle.secondary, label=value, row=self.row)

    async def callback(self, interaction: discord.Interaction):
        print(interaction.user)
        print(interaction.message.author)
        if interaction.user == self.ctx.author:
            assert self.view is not None
            view: getButtonChoiceReturnID = self.view
            view.id = self.id
            await interaction.response.defer()
            view.stop()
        else:
            await interaction.response.send_message(content="### Ouchie!  \n[Don't touch my buttons, they aren't yours!](<https://www.youtube.com/watch?v=a6pbjksYUHY>)\n", ephemeral=True)

class getButtonChoiceReturnID(discord.ui.View):
    value = ""
    def __init__(self, ctx: commands.Context, listIn: list):
        super().__init__(timeout=600)
        self.list = listIn
        i = 0
        for str in self.list:
            self.add_item(buttonListReturnID(ctx, str[0], str[1], i))
            i += 1