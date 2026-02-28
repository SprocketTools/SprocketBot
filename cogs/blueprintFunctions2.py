import discord
import type_hints
from discord.ext import commands
import json
import random
import math
import io
from datetime import datetime
import numpy as np


class blueprintFunctions2(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Lists all blueprint submissions for a user.
        Usage: -myTanks [optional: @User]
        """
        if "the diddy files" not in message.content.lower():
            return
        target_user = message.author

        query = '''
                    SELECT b.*, c.name as contest_name 
                    FROM blueprint_stats b 
                    LEFT JOIN contests c ON b.host_id = c.contest_id 
                    WHERE b.owner_id = $1 
                    ORDER BY b.submission_date DESC;
                '''

        try:
            tanks = await self.bot.sql.databaseFetchdictDynamic(query, [target_user.id])
        except Exception:
            return await message.reply("The database isn't set up yet! Ask the owner to run `-setupStatsTables`.")

        if not tanks:
            msg = "You haven't" if target_user == message.author else f"{target_user.display_name} hasn't"
            return await message.reply(f"{msg} uploaded any tanks yet.")

        # Build the Embed
        embed = discord.Embed(
            title=f"Sprocket Bot's catalog of tanks from: {target_user.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="Don't say diddy touch next time.")
        description_lines = []

        for i, tank in enumerate(tanks, 1):
            tank_name = tank.get('vehicle_name', "Unknown Blueprint")
            weight_str = f"{tank['tank_weight'] / 1000:.1f}t" if tank.get('tank_weight') else "?t"
            cost_str = f"${tank['base_cost']:,}" if tank.get('base_cost') else "$?"
            era_str = tank.get('vehicle_era', 'Unknown Era')

            if tank.get('contest_name'):
                status = f"**{tank['contest_name']}**"
            elif tank.get('host_id') and tank['host_id'] != 0:
                status = f"*Linked to deleted contest ({tank['host_id']})*"
            else:
                status = "*In Garage*"

            links = []
            if tank.get('file_url'): links.append(f"[BP]({tank['file_url']})")
            if tank.get('gif_url'): links.append(f"[3D]({tank['gif_url']})")
            if tank.get('image_url'): links.append(f"[IMG]({tank['image_url']})")

            link_str = " | ".join(links) if links else "No files"

            line = (
                f"**{i}. {tank_name}** ({era_str})\n"
                f"└ `{weight_str}` • `{cost_str}` • {link_str}\n"
            )
            description_lines.append(line)

        current_chunk = ""
        field_count = 1

        for line in description_lines:
            if len(current_chunk) + len(line) > 1024:
                embed.add_field(name=f"Vehicles (Part {field_count})", value=current_chunk, inline=False)
                current_chunk = ""
                field_count += 1
            current_chunk += line

        if current_chunk:
            embed.add_field(name=f"Vehicles (Part {field_count})", value=current_chunk, inline=False)

        embed.set_footer(text=f"Total Vehicles: {len(tanks)}")
        await message.channel.send(embed=embed)

    @commands.command(name="setupStatsTables", description="[Owner] Safely create/update the blueprint stats table.")
    async def setup_stats_tables(self, ctx: commands.Context):
        if ctx.author.id != self.bot.ownerid:
            return await self.bot.error.sendError(ctx)
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS blueprint_stats;''')
        create_prompt = ('''CREATE TABLE IF NOT EXISTS blueprint_stats (
                                  vehicle_id BIGINT PRIMARY KEY,
                                  vehicle_name VARCHAR,
                                  vehicle_class VARCHAR(100),
                                  vehicle_era VARCHAR(20),
                                  host_id BIGINT,
                                  faction_id BIGINT,
                                  owner_id BIGINT,
                                  base_cost BIGINT,
                                  tank_weight REAL,
                                  tank_length REAL,
                                  tank_width REAL,
                                  tank_height REAL,
                                  tank_total_height REAL,
                                  fuel_tank_capacity REAL,
                                  ground_pressure REAL,
                                  horsepower INT,
                                  hpt REAL,
                                  top_speed INT,
                                  travel_range INT,
                                  crew_count INT,
                                  cannon_stats TEXT,
                                  armor_mass REAL,
                                  upper_frontal_angle REAL,
                                  lower_frontal_angle REAL,
                                  health INT, 
                                  attack INT,
                                  defense INT,
                                  breakthrough INT,
                                  piercing INT,
                                  armor INT,
                                  cohesion INT,
                                  file_url VARCHAR,
                                  submission_date TIMESTAMP,
                                  gif_url VARCHAR,
                                  image_url VARCHAR
                              );''')

        try:
            await self.bot.sql.databaseExecute(create_prompt)
            columns_to_ensure = [
                ("file_url", "VARCHAR"),
                ("submission_date", "TIMESTAMP"),
                ("vehicle_name", "VARCHAR"),
                ("host_id", "BIGINT"),
                ("faction_id", "BIGINT"),
                ("gif_url", "VARCHAR"),
                ("image_url", "VARCHAR")
            ]

            for col, dtype in columns_to_ensure:
                try:
                    await self.bot.sql.databaseExecute(
                        f"ALTER TABLE blueprint_stats ADD COLUMN IF NOT EXISTS {col} {dtype};")
                except Exception:
                    pass

            await ctx.send("**Success!** The `blueprint_stats` table is ready (schema updated).")
        except Exception as e:
            await ctx.send(f"**Error updating table:**\n```\n{e}\n```")

    @commands.command(name="analyzeBlueprint", description="Analyze a .blueprint file and save its stats.")
    async def analyze_blueprint(self, ctx: commands.Context):
        for attachment in ctx.message.attachments:
            if not ctx.message.attachments:
                await self.bot.error.sendCategorizedError(ctx, "blueprint")
                await ctx.send("You need to attach a `.blueprint` file to this command.")
                return

            blueprint_attachment = None
            image_attachment = None

            if attachment.filename.endswith(".blueprint"):
                blueprint_attachment = attachment
            elif attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                image_attachment = attachment

            if not blueprint_attachment:
                return await ctx.send("No `.blueprint` file found in your message!")

            try:
                await ctx.send(f"Analyzing `{blueprint_attachment.filename}`...")
                file_content = await blueprint_attachment.read()
                blueprint_data = json.loads(file_content)

                stats = await self.bot.analyzer._parse_blueprint_stats(ctx, blueprint_data)

                if 'error' in stats and stats['error']:
                    return await ctx.send(f"**Analysis Failed:** {stats.get('error')}")

                stats['file_url'] = blueprint_attachment.url
                stats['image_url'] = image_attachment.url if image_attachment else None
                stats['submission_date'] = datetime.now()
                stats['vehicle_name'] = blueprint_attachment.filename.replace('.blueprint', '').replace('_', ' ')

                valid_cols = [
                    "vehicle_id", "vehicle_name", "vehicle_class", "vehicle_era", "host_id", "faction_id", "owner_id",
                    "base_cost", "tank_weight", "tank_length", "tank_width", "tank_height", "tank_total_height",
                    "fuel_tank_capacity", "ground_pressure", "horsepower", "hpt", "top_speed", "travel_range",
                    "crew_count", "cannon_stats", "armor_mass", "upper_frontal_angle", "lower_frontal_angle",
                    "health", "attack", "defense", "breakthrough", "piercing", "armor", "cohesion",
                    "file_url", "submission_date", "image_url"
                ]

                insert_data = {k: v for k, v in stats.items() if k in valid_cols}
                columns = ", ".join(insert_data.keys())
                placeholders = ", ".join([f"${i + 1}" for i in range(len(insert_data))])

                prompt = f"""
                        INSERT INTO blueprint_stats ({columns}) 
                        VALUES ({placeholders})
                        ON CONFLICT (vehicle_id) DO UPDATE 
                        SET vehicle_name = EXCLUDED.vehicle_name,
                            file_url = EXCLUDED.file_url,
                            image_url = EXCLUDED.image_url,
                            submission_date = EXCLUDED.submission_date;
                    """
                await self.bot.sql.databaseExecuteDynamic(prompt, list(insert_data.values()))

                embed = discord.Embed(
                    title=f"{blueprint_data['header']['name']} Stats",
                    color=discord.Color.random()
                )
                embed.set_footer(text=f"Owner: {ctx.author.display_name} | Vehicle ID: {stats['vehicle_id']}")
                embed.add_field(name="Era", value=f"{stats['vehicle_era']}")
                embed.add_field(name="Weight", value=f"{stats['tank_weight'] / 1000.0:.2f} tons")
                embed.add_field(name="Dimensions",
                                value=f"L: {stats['tank_length']:.2f}m | W: {stats['tank_width']:.2f}m | H: {stats['tank_height']:.2f}m",
                                inline=False)
                embed.add_field(name="Crew", value=f"{stats['crew_count']} members")

                # --- ADDED ARMAMENT ---
                if stats.get('cannon_stats') and stats['cannon_stats'] != "None":
                    embed.add_field(name="Armament", value=f"```\n{stats['cannon_stats']}\n```", inline=False)

                embed.add_field(name="Powertrain", value=f"{stats['horsepower']} HP | {stats['hpt']:.2f} HP/T")
                embed.add_field(name="Top Speed", value=f"~{stats['top_speed']} km/h")
                embed.add_field(name="Fuel Capacity", value=f"{stats['fuel_tank_capacity']:.1f} L")
                embed.add_field(name="Ground Pressure", value=f"{stats['ground_pressure']:.2f} kg/cm²")
                embed.add_field(name="Armor Mass", value=f"{stats['armor_mass'] / 1000.0:.2f} tons")
                embed.add_field(name="Frontal Angles",
                                value=f"Upper: {stats['upper_frontal_angle']:.1f}°\nLower: {stats['lower_frontal_angle']:.1f}°")

                gif_file = None
                bp_cog = self.bot.get_cog("blueprintFunctions")
                iframes_in = 6

                baked_data = await self.bot.analyzer.bakeGeometryV3(ctx, blueprint_attachment)
                mesh_to_render = baked_data["meshes"][0]["meshData"]["mesh"]
                complexity_score = len(str(mesh_to_render))

                if complexity_score < 2000000:
                    iframes_in = 8
                if complexity_score < 600000:
                    iframes_in = 12
                if complexity_score < 200000:
                    iframes_in = 24
                if complexity_score < 120000:
                    iframes_in = 36

                if bp_cog and complexity_score < 3780000:
                    try:
                        if "0.2" in blueprint_data["header"]["gameVersion"]:
                            baked_data = await self.bot.analyzer.bakeGeometryV3(ctx, blueprint_attachment)
                            mesh_to_render = baked_data["meshes"][0]["meshData"]["mesh"]
                        else:
                            mesh_to_render = blueprint_data["meshes"][0]["meshData"]["mesh"]
                        await ctx.send("Generating GIF, this could take awhile...")
                        gif_file = await self.bot.analyzer.generate_blueprint_gif(mesh_to_render,
                                                                                  blueprint_data['header']['name'],
                                                                                  iframes=iframes_in)
                        if gif_file:
                            embed.set_image(url=f"attachment://{gif_file.filename}")
                    except Exception as e:
                        print(f"Failed to generate analysis GIF: {e}")

                sent_message = None
                if gif_file:
                    sent_message = await ctx.send(embed=embed, file=gif_file)
                else:
                    sent_message = await ctx.send(embed=embed)

                if sent_message and gif_file:
                    final_gif_url = sent_message.embeds[0].image.url
                    await self.bot.sql.databaseExecuteDynamic(
                        '''UPDATE blueprint_stats SET gif_url = $1 WHERE vehicle_id = $2;''',
                        [final_gif_url, stats['vehicle_id']]
                    )

            except json.JSONDecodeError:
                await ctx.send("**Error:** That file seems to be corrupted or not a valid JSON file.")
            except Exception as e:
                await ctx.send(f"**An unexpected error occurred:**\n```\n{e}\n```")
                import traceback
                traceback.print_exc()
                await ctx.send(await self.bot.error.retrieveError(ctx))  # Send a funny error


# This function is required by discord.py to load the cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(blueprintFunctions2(bot))