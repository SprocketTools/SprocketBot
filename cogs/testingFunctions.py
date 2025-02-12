import discord
from discord.ext import commands
from discord import app_commands


from cogs.discordUIfunctions import discordUIfunctions
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput
promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools

class testingFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="channeltest", description="testing some stuff")
    async def channeltest(self, ctx: commands.Context):
        await textTools.getChannelResponse(ctx, "test")
    @commands.command(name="contactlength", description="testing some stuff")
    async def contactlength(self, ctx: commands.Context):
        startingLength = int(await textTools.getResponse(ctx,f"User-specified wheel array length.  All values in mm."))
        wheelDiameter = int(await textTools.getResponse(ctx, f"Wheel diameter"))
        wheelSpacing = int(await textTools.getResponse(ctx, f"Wheel spacing"))
        groupSize = int(await textTools.getResponse(ctx, f"Group size"))
        groupOffset = int(await textTools.getResponse(ctx, f"Group offset"))
        groupSpacing = int(await textTools.getResponse(ctx, f"Group spacing"))

        # startingLength = 5289
        # wheelDiameter = 700
        # wheelSpacing = 30
        # groupSize = 2
        # groupOffset = 1
        # groupSpacing = 500

        wheelCount = 1
        maxLength = startingLength + wheelSpacing + groupSpacing - wheelDiameter

        # numbers that update as the loop runs
        wheel = 1
        currentLength = -1*wheelSpacing
        wheelGroupPos = groupOffset
        finalLength = 0

        while currentLength <= maxLength:
            print(f"Wheel {wheel}: {currentLength}mm")
            finalLength = currentLength
            currentLength += wheelDiameter + wheelSpacing
            wheel += 1
            wheelGroupPos += 1
            if wheelGroupPos == groupSize:
                currentLength += groupSpacing
                wheelGroupPos -= groupSize

        print(f"{currentLength}mm vs {maxLength}mm vs {finalLength}mm")
        await ctx.send(f"Your distance is {finalLength +wheelSpacing} mm")

    @commands.command(name="testcommand6", description="testing some stuff")
    async def testcommand6(self, ctx: commands.Context):
        list = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        prompt = 'choose'
        answer = await discordUIfunctions.getChoiceFromList(ctx, list, prompt)
        await ctx.send(f"You picked {answer}!")
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