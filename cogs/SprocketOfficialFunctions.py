import datetime
import random

import discord
from discord.ext import commands

import main
from cogs.errorFunctions import errorFunctions
from cogs.textTools import textTools
class SprocketOfficialFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="serverSuggestion", description="Make a server suggestion")
    async def serverSuggestion(self, ctx: commands.Context):

        await ctx.send(f"Process started. \nSend a message containing your game suggestion and any attached media.")
        message = "This is a default response"
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = ""
        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=1800.0)
            message = await textTools.sanitize(msg.content)
        except Exception:
            pass

        avatarURL = ctx.author.display_avatar.url
        embed = discord.Embed(title=ctx.author.name, description=message, color=discord.Color.random())
        embed.set_thumbnail(url=avatarURL)
        channel = self.bot.get_channel(1033317092876881991)
        sent_message = await channel.send(embed=embed)
        await sent_message.add_reaction(":plus1:881246627510239323")
        await sent_message.add_reaction(":minus1:881246627770282015")
        for attachment in msg.attachments:
            file = await attachment.to_file()
            await channel.send(file=file, content="")

    @commands.command(name="askHamish", description="Ask Hamish a question.")
    async def askHamish(self, ctx: commands.Context):
        role = ctx.author.roles


        if main.botMode == "development":
            channel = self.bot.get_channel(1142053423370481747)
        else:
            channel = self.bot.get_channel(788410377268363264)
            if str(879050882107473990) not in str(role):
                await ctx.send(f'{await errorFunctions.retrieveError(ctx)}\n\nYou need the FAQ enjoyer role to use this command.  Look in <#882618434834284594> for more info.')
                return

        await ctx.send(f"## Process started. \n\nSend a message containing your question.\n- Make sure that you have searched for previous replies on similar questions\n- Do not use this to post game suggestions, use the [Github tracker](https://github.com/Muushy/Sprocket-Feedback/issues) for this.")
        messageOut = "This is a default response"
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        msg = ""
        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=1800.0)
            messageOut = await textTools.mild_sanitize(msg.content)
        except Exception:
            await ctx.reply(await errorFunctions.retrieveError(ctx))
            return

        await ctx.send(f"Confirm that you wish to send the following question: \n\n{messageOut}\n\nReply with 'yes' to confirm.")

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=1800.0)
            if msg.content.lower() != "yes":
                return
            if random.random() < 0.033:
                if random.random() < 0.3:
                    messageOut = "Dearest Hamish Dunn, I come bearing a humble question to offer to thus.  " + messageOut
                elif random.random() < 0.6:
                    messageOut = "Daddy Hamish, " + messageOut
                elif random.random() < 0.8:
                    messageOut = "Testing testing 1-2-3\n" + messageOut
                else:
                    message = messageOut + "\nBTW, Dario has an assignment for you."

            avatarURL = ctx.author.display_avatar.url
            userName = ctx.author.name
            choiceV = random.random()

            if ctx.author.id == 220134579736936448:
                if choiceV < 0.25: userName = "dario xn"
            if ctx.author.id == 712509599135301673:
                if choiceV < 0.25: userName = "thewonderpancake"
            if ctx.author.id == 834279720279474176:
                if choiceV < 0.25: userName = "theflyingtexan"
            if ctx.author.id == 658461485055606795:
                if choiceV < 0.25: userName = "bored_frenchman"

            if random.random() < 0.02:

                if choiceV < 0.333:
                    userName = "sprocket chan"
                    avatarURL = "https://raw.githubusercontent.com/SprocketTools/SprocketBot/main/images/Sprocket_chan_Aprilful.jpg"
                    messageOut = messageOut + "\nAlso, got any tips on trying to escape Bulgaria?"
                elif choiceV < 0.6667:
                    userName = "Jacob"
                    avatarURL = "https://raw.githubusercontent.com/SprocketTools/SprocketBot/main/images/Jacob.png"
                    messageOut = messageOut + "\nUnrelated: why have you forsaken me to this perpetual hell?  Driving all these tanks is a fate worse than death!"
                else:
                    userName = "muuushy"
                    avatarURL = "https://raw.githubusercontent.com/SprocketTools/SprocketBot/main/images/hamish.png"

            embed = discord.Embed(color=discord.Color.random(), description=messageOut)
            embed.set_footer(text=f"Question by {userName}", icon_url=avatarURL)
            sent_message = await channel.send(embed=embed, content=messageOut)
            await sent_message.create_thread(name=f"Question by {userName}", auto_archive_duration=10080, reason=f"{ctx.author.name} asked for it.")
            if main.botMode != "development":
                await sent_message.add_reaction(":plus1:881246627510239323")
                await sent_message.add_reaction(":minus1:881246627770282015")
            for attachment in msg.attachments:
                file = await attachment.to_file()
                await channel.send(file=file, content=" ")
        except Exception:
            await ctx.reply(await errorFunctions.retrieveError(ctx))
            return




async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(SprocketOfficialFunctions(bot))