import main
import discord
import type_hints, re
from discord.ext import commands
promptResponses = {}
from cogs.textTools import textTools

class starboardFunctions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # Fetch the channel safely
        channel = self.bot.get_channel(payload.channel_id)
        if not channel: return

        # Fetch the message safely
        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return

        # Hardcoded date check
        if int(message.created_at.timestamp()) < 1738411320:
            return

        msg_guild = self.bot.get_guild(payload.guild_id)
        if not msg_guild: return

        # Fetch starboard configs
        data_rchannel = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM starboards WHERE sourcechannel = $1 OR (serverid = $2 AND sourcechannel < 5);''',
            [payload.channel_id, payload.guild_id]
        )
        if len(data_rchannel) == 0:
            data_rchannel = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM starboards WHERE serverid = $1 AND sourcechannel < 5;''',
                [msg_guild.id]
            )

        if len(data_rchannel) == 0:
            return

        # 1. Did the user click an emoji that is actually part of our configs?
        clicked_emoji_str = str(payload.emoji).strip()
        is_valid_trigger = any(str(sb["emoji"]).strip() == clicked_emoji_str for sb in data_rchannel)
        if not is_valid_trigger:
            return

        # Safety check for author reacting to themselves
        if payload.user_id != self.bot.owner_id:
            if message.author.id == payload.user_id or message.author.bot:
                return

        # 2. Group all starboard configs by their Destination Channel
        destinations = {}
        for sb in data_rchannel:
            dest = sb['channelsend']
            emoji_str = str(sb['emoji']).strip()

            if dest not in destinations:
                destinations[dest] = {'emojis': set(), 'thresholds': {}}

            destinations[dest]['emojis'].add(emoji_str)
            # Store the specific requirement for each emoji independently
            destinations[dest]['thresholds'][emoji_str] = sb['count']

        # 3. Process each destination channel
        for dest_channel_id, dest_data in destinations.items():

            if clicked_emoji_str not in dest_data['emojis']:
                continue

            display_parts = []
            meets_threshold = False
            has_any_reactions = False

            # Extract current reactions from the message safely
            active_reactions = {}
            active_ids = {}

            for r in message.reactions:
                raw_str = str(r.emoji).strip()
                active_reactions[raw_str] = r.count
                if hasattr(r.emoji, 'id') and r.emoji.id:
                    active_ids[str(r.emoji.id)] = {"count": r.count, "str": raw_str}

            # Explicitly check for every emoji configured for this destination
            for expected_emoji in dest_data['emojis']:
                count = 0
                display_str = expected_emoji

                # 1. Try exact string match first
                if expected_emoji in active_reactions:
                    count = active_reactions[expected_emoji]
                else:
                    # 2. Fallback: Extract ID and check if the emoji was renamed/animated
                    import re
                    match = re.search(r'<a?:[^:]+:(\d+)>', expected_emoji)
                    if match:
                        e_id = match.group(1)
                        if e_id in active_ids:
                            count = active_ids[e_id]["count"]
                            display_str = active_ids[e_id]["str"]

                if count > 0:
                    has_any_reactions = True
                    display_parts.append(f"{display_str} **{count}**")

                    # Check if THIS specific emoji met its specific requirement
                    if count >= dest_data['thresholds'][expected_emoji]:
                        meets_threshold = True

            if not has_any_reactions:
                continue

            # Format: ⭐ **5** | 🌟 **2** | #general
            display_content = " | ".join(display_parts) + f" | {message.channel.mention}"

            # --- Check if already starboarded in THIS channel ---
            existing_entries = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM starboarded WHERE messageid = $1;''',
                [message.id]
            )

            target_entry = None
            for row in existing_entries:
                if row.get("starboard_channel_id") == dest_channel_id:
                    target_entry = row
                    break

            if target_entry:
                # Update the combined count string
                sb_msg_id = target_entry.get("starboard_msg_id")
                if sb_msg_id:
                    sb_channel = self.bot.get_channel(dest_channel_id)
                    if sb_channel:
                        try:
                            sb_msg = await sb_channel.fetch_message(sb_msg_id)
                            await sb_msg.edit(content=display_content)
                        except Exception as e:
                            print(f"Failed to update existing starboard message: {e}")
                continue

            # --- Create NEW Starboard Entry ---
            # Now we use our boolean flag instead of a summed integer!
            if meets_threshold:
                starboard_channel = self.bot.get_channel(dest_channel_id)
                if not starboard_channel:
                    continue

                embed = discord.Embed(description=message.content, color=message.author.color)
                if message.attachments:
                    try:
                        embed.set_image(url=message.attachments[0].url)
                    except Exception:
                        pass

                avatar_url = message.author.display_avatar.url if hasattr(message.author,
                                                                          'display_avatar') else None
                embed.set_author(name=message.author.display_name, icon_url=avatar_url)
                embed.add_field(name="Source", value=f"[Jump to Message]({message.jump_url})")
                embed.set_footer(text=f"ID: {message.id}")

                try:
                    sent_msg = await starboard_channel.send(content=display_content, embed=embed)
                    await self.bot.sql.databaseExecuteDynamic(
                        '''INSERT INTO starboarded (messageid, starboard_msg_id, starboard_channel_id, author_id) VALUES ($1, $2, $3, $4)''',
                        [message.id, sent_msg.id, starboard_channel.id, message.author.id]
                    )
                except Exception as e:
                    print(f"Failed to send/save new starboard post: {e}")

    @commands.has_permissions(manage_guild=True)
    @commands.command(name="syncStarboard", description="Retroactively fills database with old starboard posts")
    async def syncStarboard(self, ctx: commands.Context, channel: discord.TextChannel):
        status = await ctx.send(f"Starting sync for {channel.mention}... This will take a while.")
        count = 0
        deleted_count = 0

        async for msg in channel.history(limit=None):
            if msg.author.id == self.bot.user.id and msg.embeds:
                embed = msg.embeds[0]
                if embed.footer and "id:" in str(embed.footer.text).lower():
                    # 1. Get Original Message ID from Footer
                    try:
                        orig_msg_id = int(str(embed.footer.text).lower().replace("id:", "").strip())
                    except ValueError:
                        continue

                    # 2. Extract original channel from the Jump Link to fetch the author ID
                    author_id = None
                    jump_link = embed.fields[0].value if embed.fields else ""
                    match = re.search(r'channels/\d+/(\d+)/(\d+)', jump_link)

                    if match:
                        orig_channel_id = int(match.group(1))
                        orig_channel = self.bot.get_channel(orig_channel_id)
                        if orig_channel:
                            try:
                                # Fetch the original message to get the exact author ID
                                orig_msg = await orig_channel.fetch_message(orig_msg_id)
                                author_id = orig_msg.author.id
                            except discord.NotFound:
                                deleted_count += 1  # Original message was deleted!
                            except Exception:
                                pass

                    # 3. Update or Insert into the database
                    existing = await self.bot.sql.databaseFetchdictDynamic(
                        "SELECT messageid FROM starboarded WHERE messageid = $1", [orig_msg_id])

                    if len(existing) > 0:
                        await self.bot.sql.databaseExecuteDynamic(
                            "UPDATE starboarded SET starboard_msg_id=$1, starboard_channel_id=$2, author_id=$3 WHERE messageid=$4",
                            [msg.id, channel.id, author_id, orig_msg_id]
                        )
                    else:
                        await self.bot.sql.databaseExecuteDynamic(
                            "INSERT INTO starboarded (messageid, starboard_msg_id, starboard_channel_id, author_id) VALUES ($1, $2, $3, $4)",
                            [orig_msg_id, msg.id, channel.id, author_id]
                        )

                    count += 1
                    if count % 50 == 0:
                        await status.edit(content=f"Syncing {channel.mention}... Processed {count} posts.")

        await status.edit(
            content=f"✅ **Sync Complete!** Processed {count} starboard posts. ({deleted_count} original messages were deleted, so their author IDs couldn't be recovered).")

    @commands.command(name="setupStarboardDatabase", description="Set up the starboards")
    async def setupStarboardDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS starboards (serverid BIGINT, emoji VARCHAR, count INT, channelsend BIGINT, sourcechannel BIGINT)''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS starboarded (messageid BIGINT)''')

        try:
            await self.bot.sql.databaseExecute('''ALTER TABLE starboarded ADD COLUMN starboard_msg_id BIGINT;''')
            await self.bot.sql.databaseExecute('''ALTER TABLE starboarded ADD COLUMN starboard_channel_id BIGINT;''')
        except Exception:
            pass
        try:
            await self.bot.sql.databaseExecute('''ALTER TABLE starboarded ADD COLUMN author_id BIGINT;''')
        except Exception:
            pass  # Column already exists

        await ctx.send("Done!")

    @commands.command(name="listStarboards", description="Add a new starboard")
    async def listStarboards(self, ctx: commands.Context):
        data_rchannel = await self.bot.sql.databaseFetchdictDynamic('''SELECT * FROM starboards WHERE serverid = $1;''',[ctx.guild.id])
        embed = discord.Embed(color=ctx.author.color, title=f"Starboards in {ctx.guild.name}")
        print(data_rchannel)
        for entry in data_rchannel:
            print(entry)
            if entry['sourcechannel'] == 0:
                embed.add_field(name=f"Server-wide default", value=f"{entry['count']}x {entry['emoji']}", inline=False)
            else:
                embed.add_field(name=f"<#{entry['sourcechannel']}>", value=f"{entry['count']}x {entry['emoji']}", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="boardrep", description="Check how many starboard posts a user has")
    async def boardrep(self, ctx: commands.Context, channel: discord.TextChannel = None):
        try:
            if channel is None:
                return await ctx.send(
                    "Please specify the starboard channel you want to check. Example: `-boardrep #starboard`")

            # 1. Lightning Fast SQL Query
            records = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM starboarded WHERE starboard_channel_id = $1 AND author_id = $2 ORDER BY starboard_msg_id ASC;''',
                [channel.id, ctx.author.id]
            )

            if not records or len(records) == 0:
                await ctx.send(await self.bot.error.retrieveError(ctx))
                return await ctx.send(
                    "Unfortunately you don't have any boards on that channel yet. Try bribing your friends with Discord Nitro or [a teaser for Sprocket's future updates!](<https://www.youtube.com/watch?v=CGSM48Qr1zs>)")

            # 2. Build the Embed
            embed = discord.Embed(color=ctx.author.color,
                                  title=f"Board posts by {ctx.author.display_name} in {channel.name}")

            # Helper function to construct jump links to the starboard messages
            def make_jump(sb_msg_id):
                return f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/{sb_msg_id}"

            if len(records) == 1:
                embed.add_field(name="The one (1) entry", value=make_jump(records[0]['starboard_msg_id']), inline=False)
            else:
                embed.add_field(name="The first entry", value=make_jump(records[0]['starboard_msg_id']), inline=False)
                embed.add_field(name="The latest entry", value=make_jump(records[-1]['starboard_msg_id']), inline=False)
                embed.add_field(name="Total", value=f"{len(records)} entries", inline=False)

            embed.set_footer(text=await self.bot.error.retrieveCategorizedError(ctx, "sprocket"))
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Error in boardrep: {e}")
            await ctx.send("An error occurred while fetching your starboard records.")

    @commands.has_permissions(manage_guild=True)
    @commands.command(name="addStarboard", description="Add a new starboard")
    async def addNewStarboard(self, ctx: commands.Context):
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
                await ctx.send(await self.bot.error.getError(ctx) + "\n\nSomething went wrong: " + e)

    @commands.has_permissions(manage_guild=True)
    @commands.command(name="deleteStarboard", description="Delete a new starboard")
    async def deleteStarboard(self, ctx: commands.Context):
        serverid = ctx.guild.id
        emojis = str(await textTools.getResponse(ctx, "What emojis do you want to remove?  List multiple by splitting with spaces.")).split(" ")
        await ctx.send("Are you deleting a channel-specific starboard?")
        channelsend = await textTools.getChannelResponse(ctx, "What is the destination channel?")
        if await ctx.bot.ui.getYesNoChoice(ctx):
            sourcechannel = await textTools.getChannelResponse(ctx, "What is the current source channel?")
        else:
            sourcechannel = 0
        for emoji in emojis:
            try:
                await self.bot.sql.databaseExecuteDynamic('''DELETE FROM starboards WHERE serverid = $1 AND emoji = $2 AND channelsend = $3 AND sourcechannel = $4;''', [serverid, emoji, channelsend, sourcechannel])
                await ctx.send("## Starboard deleted!")
            except Exception as e:
                await ctx.send(await self.bot.error.getError(ctx) + "\n\nSomething went wrong deleting a starboard: " + e)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(starboardFunctions(bot))



