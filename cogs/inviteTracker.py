import discord
from discord.ext import commands

# --- HARDCODED TARGETS ---
TARGET_GUILD_ID = 788349365466038283  # Replace with your Server ID
LOG_CHANNEL_ID = 788555721343500339  # Replace with your Log Channel ID


class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dictionary to store our "snapshot" of invites: {invite_code: use_count}
        self.invites_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """Take the initial snapshot of invites when the bot boots up."""
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(TARGET_GUILD_ID)

        if guild:
            try:
                invites = await guild.invites()
                self.invites_cache = {invite.code: invite.uses for invite in invites}
                print(f"Invite Tracker: Cached {len(self.invites_cache)} invites for target server.")
            except discord.Forbidden:
                print("Invite Tracker: Missing 'Manage Server' permissions to view invites!")

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Add new invites to the cache as they are created."""
        if invite.guild.id == TARGET_GUILD_ID:
            self.invites_cache[invite.code] = invite.uses

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Remove deleted invites from the cache."""
        if invite.guild.id == TARGET_GUILD_ID:
            self.invites_cache.pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """The detective work: Compare old invites to new invites to find the culprit."""
        # 1. Ignore joins from other servers
        if member.guild.id != TARGET_GUILD_ID:
            return

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return

        try:
            # 2. Grab the old cache and fetch a fresh list of invites
            invites_before = self.invites_cache.copy()
            invites_after = await member.guild.invites()

            used_invite = None

            # 3. Find the invite whose use count increased
            for invite in invites_after:
                # Update our live cache while we iterate
                self.invites_cache[invite.code] = invite.uses

                if invite.code in invites_before:
                    if invite.uses > invites_before[invite.code]:
                        used_invite = invite
                        break
                elif invite.uses > 0:
                    # Edge case: Invite was created while the bot was offline and used immediately
                    used_invite = invite
                    break

            # 4. Log the result
            if used_invite:
                inviter = used_invite.inviter
                embed = discord.Embed(title="📥 Member Joined", color=discord.Color.green())
                embed.description = f"**{member.mention}** joined the server."
                embed.add_field(name="Invited By", value=f"{inviter.mention} (`{inviter.name}`)")
                embed.add_field(name="Invite Link", value=f"`{used_invite.code}`")
                embed.add_field(name="Total Link Uses", value=f"{used_invite.uses}")
                embed.set_thumbnail(url=member.display_avatar.url)

                await log_channel.send(embed=embed)
            else:
                # If no invite increased, it might be a Vanity URL, Server Discovery, or a temporary one-time link that vanished.
                await log_channel.send(
                    f"📥 **{member.name}** joined. *(Could not determine invite source - likely Vanity URL or Server Discovery)*")

        except discord.Forbidden:
            await log_channel.send(f"📥 **{member.name}** joined, but I lack permissions to read the invite list!")


async def setup(bot):
    await bot.add_cog(InviteTracker(bot))