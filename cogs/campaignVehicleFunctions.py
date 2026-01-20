import io

import discord
import json
import aiohttp
import os
import random
import datetime
from discord.ext import commands
import type_hints
import main
from cogs.textTools import textTools


class campaignVehicleFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------
    # VALIDATION LOGIC
    # ----------------------------------------------------------------------------------
    async def _get_faction_tech_limits(self, faction_id: int):
        """
        Calculates the absolute maximums for a faction based on unlocked tech.
        Returns a dict: {'max_weight': 15.0, 'max_speed': 25, ...}
        """
        # 1. Fetch all effects from unlocked technologies
        # We join tech_definitions to get the effects_json
        query = '''
            SELECT t.effects_json 
            FROM tech_definitions t
            JOIN faction_tech_unlocked u ON t.tech_id = u.tech_id
            WHERE u.faction_id = $1
        '''
        techs = await self.bot.sql.databaseFetchdictDynamic(query, [faction_id])

        # 2. Base Limits (Starting Tech)
        # You can adjust these base values to represent a "Tier 0" nation.
        limits = {
            "max_weight": 10.0,  # Tons
            "max_velocity": 15.0,  # km/h
            "max_armor": 15.0,  # mm
            "max_caliber": 37.0,  # mm
            "ground_pressure": 2.0,
            # kg/cm^2 (Lower is better, but usually tech increases tolerance or decreases pressure)
            "engine_power": 100.0  # HP
        }

        # 3. Apply Modifiers
        for entry in techs:
            if not entry['effects_json']: continue
            try:
                effects = json.loads(entry['effects_json'])
                for stat, value in effects.items():
                    # Assuming effects are additive (e.g. "max_weight": 5.0 adds 5 tons)
                    if stat in limits:
                        limits[stat] += float(value)
                    else:
                        limits[stat] = float(value)
            except json.JSONDecodeError:
                continue

        return limits

    async def _validate_design(self, ctx, stats, faction_id):
        """
        Compares blueprint stats against faction limits.
        """
        limits = await self._get_faction_tech_limits(faction_id)
        violations = []

        # 1. Weight
        weight_t = stats.get('tank_weight', 0) / 1000.0
        if weight_t > limits['max_weight']:
            violations.append(f"Weight: {weight_t:.1f}t > Limit {limits['max_weight']}t")

        # 2. Speed (Top Speed)
        speed = stats.get('top_speed', 0)
        if speed > limits['max_velocity']:
            violations.append(f"Speed: {speed}km/h > Limit {limits['max_velocity']}km/h")

        # 3. Ground Pressure
        # Note: Usually we want pressure to be LOWER, but tech might allow building heavier tanks
        # OR tech restricts the *Maximum Allowed* ground pressure.
        # Let's assume the limit is a Maximum allowed (e.g. cannot exceed 1.2 kg/cm2)
        pressure = stats.get('ground_pressure', 0)
        # If stats have 0, skip check
        if pressure > 0 and pressure > limits.get('ground_pressure', 10.0):
            violations.append(f"Ground Pressure: {pressure:.2f} > Limit {limits.get('ground_pressure')}kg/cm2")

        # 4. Engine Power
        hp = stats.get('horsepower', 0)
        if hp > limits.get('engine_power', 9999):
            violations.append(f"Horsepower: {hp} > Limit {limits.get('engine_power')}")

        # 5. Future Checks (Armor/Caliber)
        # These rely on blueprintAnalysisTools being updated to extract them.
        if 'max_thickness' in stats:
            if stats['max_thickness'] > limits['max_armor']:
                violations.append(f"Armor: {stats['max_thickness']}mm > Limit {limits['max_armor']}mm")

        if 'max_caliber' in stats:
            if stats['max_caliber'] > limits['max_caliber']:
                violations.append(f"Caliber: {stats['max_caliber']}mm > Limit {limits['max_caliber']}mm")

        if violations:
            return False, violations
        return True, []

    # ----------------------------------------------------------------------------------
    # COMMAND: Submit Design
    # ----------------------------------------------------------------------------------
    @commands.command(name="submitDesign", description="Submit a vehicle design for validation and approval")
    async def submitDesign(self, ctx: commands.Context):
        if not ctx.message.attachments:
            return await ctx.send("You must upload a `.blueprint` file.")

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(".blueprint"):
            return await ctx.send("Invalid file type. Please upload a `.blueprint` file.")

        # 1. Get Faction Data
        try:
            faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)
            faction_id = faction_data['factionkey']
        except Exception:
            return await ctx.send("You are not part of a faction! Join a campaign first.")

        # 2. Get Campaign Config
        campaign_data = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        design_channel_id = campaign_data.get('designsubmissionchannelid')

        if not design_channel_id:
            design_channel_id = campaign_data.get('publiclogchannelid')

        if not design_channel_id:
            return await ctx.send("Error: No Design Submission channel configured for this campaign.")

        target_channel = ctx.guild.get_channel(design_channel_id)
        if not target_channel:
            return await ctx.send("Error: Design Submission channel not found.")

        msg = await ctx.send("Analyzing blueprint and checking Technology Levels...")

        # 3. Download & Analyze
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return await ctx.send("Failed to download file.")
                    file_bytes = await resp.read()

            bp_json = json.loads(file_bytes.decode('utf-8'))

            # Use the Analyzer Tool
            stats = await self.bot.analyzer._parse_blueprint_stats(ctx, bp_json)

            if 'error' in stats and stats['error']:
                return await msg.edit(content=f"**Analysis Failed:** {stats['error']}")

            # 4. Tech Validation
            valid, violations = await self._validate_design(ctx, stats, faction_id)

            if not valid:
                embed = discord.Embed(title="Design Rejected: Tech Limits Exceeded", color=discord.Color.red())
                embed.description = "Your vehicle exceeds the capabilities of your researched technology."
                embed.add_field(name="Violations", value="\n".join(violations))
                return await msg.edit(content=None, embed=embed)

            # 5. Success - Save & Send to Approval
            await msg.edit(content="Design valid! Sending for approval...")

            stats['owner_id'] = ctx.author.id
            stats['vehicle_name'] = attachment.filename.replace('.blueprint', '').replace('_', ' ')

            valid_cols = [
                "vehicle_id", "vehicle_name", "vehicle_class", "vehicle_era", "host_id", "faction_id", "owner_id",
                "base_cost", "tank_weight", "tank_length", "tank_width", "tank_height", "tank_total_height",
                "fuel_tank_capacity", "ground_pressure", "horsepower", "hpt", "top_speed", "travel_range",
                "crew_count", "armor_mass", "upper_frontal_angle", "lower_frontal_angle"
            ]

            insert_data = {k: v for k, v in stats.items() if k in valid_cols}
            insert_data['faction_id'] = faction_id

            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join([f"${i + 1}" for i in range(len(insert_data))])

            await self.bot.sql.databaseExecuteDynamic(
                f"INSERT INTO blueprint_stats ({columns}) VALUES ({placeholders}) ON CONFLICT (vehicle_id) DO NOTHING",
                list(insert_data.values())
            )

            # Generate GIF using the Analyzer's Baker
            gif_file = None
            try:
                if "0.2" in bp_json["header"]["gameVersion"]:
                    # Create bytesIO for the baker
                    f = io.BytesIO(file_bytes)
                    # UPDATED CALL: Uses analyzer instead of calling cog directly
                    baked = await self.bot.analyzer.bakeGeometryV3(ctx, f)
                    mesh = baked["meshes"][0]["meshData"]["mesh"]
                else:
                    mesh = bp_json["meshes"][0]["meshData"]["mesh"]

                gif_file = await self.bot.analyzer.generate_blueprint_gif(mesh, stats['vehicle_name'])
            except Exception as e:
                print(f"GIF Gen failed: {e}")

            embed = discord.Embed(title="New Design Submission", color=discord.Color.gold())
            embed.add_field(name="Faction", value=faction_data['factionname'])
            embed.add_field(name="Author", value=ctx.author.mention)
            embed.add_field(name="Vehicle", value=stats['vehicle_name'])
            embed.add_field(name="Stats",
                            value=f"{stats.get('tank_weight', 0) / 1000:.1f}t | ${stats.get('base_cost', 0):,} | {stats.get('top_speed')}km/h")
            embed.set_footer(text=f"Vehicle ID: {stats['vehicle_id']}")

            if gif_file:
                embed.set_image(url=f"attachment://{gif_file.filename}")
                approval_msg = await target_channel.send(embed=embed, file=gif_file)
            else:
                approval_msg = await target_channel.send(embed=embed)

            await approval_msg.add_reaction("✅")
            await approval_msg.add_reaction("❌")

            await ctx.send(f"Design **{stats['vehicle_name']}** submitted to {target_channel.mention}!")

        except Exception as e:
            await ctx.send(f"Error processing submission: {e}")
            import traceback
            traceback.print_exc()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(campaignVehicleFunctions(bot))