import main
import discord
from discord.ext import commands
from cogs.errorFunctions import errorFunctions
promptResponses = {}
from cogs.textTools import textTools

class starboardFunctions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):



        # Fetch the message
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        try:
            await message.add_reaction('310177266011340803')
        except discord.Forbidden:
            print("blocked")
            return False
        except Exception:
            pass

        if int(message.created_at.timestamp()) < 1738411320:
            return

        msg_guild = self.bot.get_guild(payload.guild_id)
        data_rchannel = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM starboards WHERE sourcechannel = $1 OR (serverid = $2 AND sourcechannel < 5);''',[payload.channel_id, payload.guild_id])
        #print(data_rchannel)
        if len(data_rchannel) == 0:
            data_rchannel = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM starboards WHERE serverid = $1 AND sourcechannel < 5;''',[msg_guild.id])
        #print(data_rchannel)
        for starboard in data_rchannel:
            #print(starboard["emoji"] + " vs. " + str(payload.emoji))
            # Check if the reaction is the star emoji
            if str(payload.emoji) != str(starboard["emoji"]):
                #print("no match")
                continue



            # Check if the user who reacted is the same as the message author
            if payload.member.id != self.bot.owner_id:
                if message.author.id == payload.user_id:
                    #await channel.send(f"{payload.member.mention}, you cannot star your own messages.")
                    continue

                # Check if the message author is a bot
                if message.author.bot:
                    #await channel.send(f"{payload.member.mention}, you cannot star bot messages.")
                    continue

            if len(await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM starboarded WHERE messageid = $1;''', [message.id])) > 0:
                continue
            # Fetch the starboard channel
            starboard_channel = self.bot.get_channel(starboard["channelsend"])
            if not starboard_channel:
                print("Invalid channel")
                continue

            # Fetch the last 100 messages in the starboard channel to check for existing starboard messages
            # Count the number of star reactions on the message

            try:
                star_reaction = discord.utils.get(message.reactions, emoji=payload.emoji)
                print("got here")
                print(star_reaction.count)
            except Exception:
                star_reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
                print("got here")
                print(star_reaction.count)

            if star_reaction and star_reaction.count >= starboard['count']:
                print("got here too")
                # Create the embed for the starboard message
                embed = discord.Embed(description=message.content, color=message.author.color)
                if message.attachments:
                    try:
                        embed.set_image(url=message.attachments[0])
                    except Exception:
                        pass
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
                embed.add_field(name="Link to message", value=f"[Jump to Message]({message.jump_url})")
                embed.set_footer(text=f"id: {message.id}")

                # Send the embed to the starboard channel
                await starboard_channel.send(embed=embed)
                await self.bot.sql.databaseExecuteDynamic('''INSERT INTO starboarded VALUES ($1)''', [message.id])

    @commands.command(name="setupStarboardDatabase", description="Set up the starboards")
    async def setupStarboardDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS starboards (serverid BIGINT, emoji VARCHAR, count INT, channelsend BIGINT, sourcechannel BIGINT)''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS starboarded (messageid BIGINT)''')
        await ctx.send("Done!")

    @commands.command(name="addStarboard", description="Add a new starboard")
    async def addNewStarboard(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        serverid = ctx.guild.id
        emojis = str(await textTools.getResponse(ctx, "What is the emoji?  List multiple by splitting with spaces.")).split(" ")
        count = await textTools.getIntResponse(ctx, "What is the reaction requirement?")
        channelsend = await textTools.getChannelResponse(ctx, "What is the destination channel?")
        await ctx.send("Do you want to make this setting only apply to one channel?")
        if await ctx.bot.ui.getYesNoChoice(ctx):
            sourcechannel = await textTools.getChannelResponse(ctx, "What is the source channel?")
        else:
            sourcechannel = 0
        for emoji in emojis:
            print(emoji)
            try:
                await self.bot.sql.databaseExecuteDynamic('''INSERT INTO starboards VALUES ($1, $2, $3, $4, $5)''', [serverid, emoji, count, channelsend, sourcechannel])
                await ctx.send("## Done!")
            except Exception as e:
                await ctx.send(await errorFunctions.getError(ctx) + "\n\nSomething went wrong: " + e)



async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(starboardFunctions(bot))



