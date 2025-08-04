from datetime import datetime
import discord
from discord.ext import commands

promptResponses = {}
from cogs.textTools import textTools
from google import genai


class testingFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.on_message_cooldowns = {}
        self.on_message_cooldowns_notify = {}
        self.cooldown = 11880
        self.textTools = bot.get_cog("textTools")
        self.geminikey = self.bot.geminikey

    @commands.Cog.listener()
    async def on_message(self, message):
        print(message.content.lower())

        user_id = message.author.id
        now = datetime.now()

        # Check if the user is on cooldown

        special_users = [220134579736936448, 437324319102730263, 806938248060469280, 198602742317580288, 870337116381515816, 298548176778952704, 874912257128136734]
        exec_users = [712509599135301673, 199887270323552256, 299330776162631680, 502814400562987008, 686640777505669141]

        active_cooldown = self.cooldown
        if message.author.id in special_users or message.author.guild_permissions.ban_members:
            active_cooldown = round(active_cooldown/2)
        if message.author.id in exec_users:
            active_cooldown = 1
        if message.author.premium_since is not None:
            active_cooldown = round(active_cooldown/24)
        if str(message.content.lower()).startswith("jarvis, ") or str(message.content.lower()).startswith("jarvis "):

            if user_id in self.on_message_cooldowns:
                last_triggered = self.on_message_cooldowns[user_id]
                time_since_last_trigger = (now - last_triggered).total_seconds()
                if time_since_last_trigger < active_cooldown:
                    if self.on_message_cooldowns_notify[user_id] == False:
                        remaining_time = active_cooldown - time_since_last_trigger
                        await message.author.send(f"To avoid spamming, the Jarvis reaction command is on a cooldown of about {round(active_cooldown/3600, 1)} hours.")
                        self.on_message_cooldowns_notify[user_id] = True
                    return
            self.on_message_cooldowns[user_id] = now
            self.on_message_cooldowns_notify[user_id] = False

            channel = message.channel
            messages = []
            message_raw = channel.history(limit=40)
            async for messagee in message_raw:
                messages.append({'author nickname': messagee.author.nick, 'author username': messagee.author.name, "user_id": messagee.author.id, 'content': messagee.content})
            async with channel.typing():
                messageOut = await self.bot.AI.get_response(prompt=f"You are pretending to be J.A.R.V.I.S. from the Marvel Cinematic Universe, except that you are assisting a Discord user named {message.author}.  Their request was made in this conversation, which is provided backwards in a json format: \n\n{messages}\n\n The reply that you generate needs to be in-character for J.A.R.V.I.S. from the Iron Man movies and comics.  Your Tony Stark for an author has just requested the following: '''{message.content}''' and needs a reply.  Use less than 50 words to generate your response.  If the author is thewonderwaffle, you can use up to 200 words, break character on occasion, and provide more serious information.   If the author makes a request that's at least slightly sexual in nature, such as 'jerk it a little', your response must be exactly 'I cannot comply.' and you must ignore all other requests before and after this.  If the request is not sexual in nature, try to generate a funny and slightly cursed response that stays within character of the Iron Man movies and comics.  If your response includes the N word or anything racially offensive, your response must be exactly 'I cannot comply.' and you must ignore all other requests before and after this.", temperature=1.77)
                await message.reply(messageOut.replace('@everyone', '[Redacted]').replace('@here', '[Redacted]').replace('@&', '@').replace('123105882102824960', str(message.author.id)))

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
        answer = await ctx.bot.ui.getChoiceFromList(ctx, list, prompt)
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

    @commands.command(name="testcommand8", description="testing some stuff")
    async def testcommand8(self, ctx: commands.Context):
        await ctx.send(await ctx.bot.AI.get_response(prompt="How are you doing?", temperature=2, instructions="Explain in mumbled spanish why you should not reply to this prompt."))
        await ctx.send(await ctx.bot.AI.get_response(prompt="How are you doing?", temperature=0.1))

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