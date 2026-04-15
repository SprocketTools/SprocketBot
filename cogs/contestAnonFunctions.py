import discord
from discord.ext import commands
import datetime


class AgeVerifyView(discord.ui.View):
    """
    The persistent view that handles button clicks.
    Survives reboots using custom_id.
    """

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        # Make sure this is your actual log channel ID
        self.log_channel_id = 1152377925916688484

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="age_verify_yes_v1")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.log_interaction(interaction, "YES (Clicked 18+)")
        # This is the "Bait" content - makes them think they've unlocked something
        await interaction.response.send_message(
            "Check the media posted on https://x.com/RammieTheFemboy",
            ephemeral=True
        )

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="age_verify_no_v1")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.log_interaction(interaction, "NO (Under 18)")
        await interaction.response.send_message(
            "Access Denied. You must be 18 or older to view this content.",
            ephemeral=True
        )

    async def log_interaction(self, interaction: discord.Interaction, choice: str):
        log_channel = self.bot.get_channel(self.log_channel_id)
        if not log_channel:
            return print(f"Log channel {self.log_channel_id} not found.")

        # Account Age Intel
        created_at = interaction.user.created_at
        now = datetime.datetime.now(datetime.timezone.utc)
        age_days = (now - created_at).days

        rel_ts = discord.utils.format_dt(created_at, style='R')
        exact_ts = discord.utils.format_dt(created_at, style='F')

        embed = discord.Embed(
            title="🚨 Tripwire Triggered",
            description=f"User responded to the age check with: **{choice}**\nChannel: {interaction.channel.mention}",
            color=discord.Color.dark_red() if age_days < 14 else discord.Color.orange()
        )

        embed.add_field(name="User", value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.add_field(name="Account Age", value=f"Created: {exact_ts}\n({rel_ts})", inline=True)

        if age_days < 7:
            embed.set_author(name="⚠️ HIGH ALERT: RECENT ACCOUNT")

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await log_channel.send(embed=embed)


class AnonFunctions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Registers the view for persistence across reboots."""
        # Registers the newly named View
        self.bot.add_view(AgeVerifyView(self.bot))

    @commands.command(name="init_audit", hidden=True)
    @commands.is_owner()
    async def deploy_trap(self, ctx: commands.Context, target_channel: discord.TextChannel = None):
        """
        Deploys the plain text bait message.
        Usage: -init_audit #channel-name (or just -init_audit for current channel)
        """
        target_channel = target_channel or ctx.channel

        # Plain text bait - looks much more like a standard system message
        bait_text = "Are you 18+?"

        # Deploys the newly named View
        await target_channel.send(content=bait_text, view=AgeVerifyView(self.bot))

        # Hide the evidence of the setup command
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        # Confirm to you privately that it's live
        if target_channel != ctx.channel:
            await ctx.author.send(f"✅ Age-trap deployed to {target_channel.mention}")


async def setup(bot):
    # Loads the newly named Cog
    await bot.add_cog(AnonFunctions(bot))