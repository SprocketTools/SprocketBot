import discord
import aiohttp
import io
import cv2
import numpy as np
import csv
import json
import random
import pandas as pd
from discord.ext import commands
import type_hints
import main
from cogs.textTools import textTools


class campaignMapsFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------
    # SETUP: POI Database
    # ----------------------------------------------------------------------------------
    @commands.is_owner()
    @commands.command(name="setupPOIdatabase", description="Initialize tables for Map POIs and Configs")
    async def setupPOIdatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return await self.bot.error.sendCategorizedError(ctx, "campaign")

        # 1. Campaign POIs Table
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaign_pois (
            poi_id SERIAL PRIMARY KEY,
            campaign_id BIGINT,
            name VARCHAR(100),
            type VARCHAR(50), 
            latitude FLOAT,
            longitude FLOAT,
            output FLOAT DEFAULT 0,
            controller_faction_id BIGINT DEFAULT 0,
            integrity FLOAT DEFAULT 100.0,
            population BIGINT DEFAULT 0,
            province VARCHAR(100)
        );''')

        # Schema Migrations
        updates = [
            ("campaign_pois", "integrity", "FLOAT DEFAULT 100.0"),
            ("campaign_pois", "population", "BIGINT DEFAULT 0"),
            ("campaign_pois", "province", "VARCHAR(100)"),
            ("campaignfactions", "color", "VARCHAR(20) DEFAULT '#808080'"),
            ("campaignservers", "map_url", "TEXT DEFAULT NULL")
        ]

        for table, col, dtype in updates:
            check = await self.bot.sql.databaseFetchrowDynamic(
                f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}';"
            )
            if not check:
                try:
                    await self.bot.sql.databaseExecute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype};")
                except:
                    pass

        await ctx.send("## Map Database Initialized!\nTables checked and updated.")

    # ----------------------------------------------------------------------------------
    # IMPORT: Azgaar CSV Importer (Manual Canvas Size)
    # ----------------------------------------------------------------------------------
    @commands.command(name="importMap", description="Import CSV. Usage: -importAzgaarMap [CanvasW] [CanvasH]")
    async def importMap(self, ctx: commands.Context, canvas_w: int = 0, canvas_h: int = 0):
        if not await ctx.bot.campaignTools.isCampaignHost(ctx):
            return await ctx.send("Only the Campaign Host can import maps.")

        # --- STEP 1: Instructions (If no file) ---
        if not ctx.message.attachments:
            embed = discord.Embed(title="Map Import Instructions", color=discord.Color.blue())
            embed.description = (
                "## ⚠️ Prerequisite: Upload Map Image First\n"
                "Run `-updateMap` and upload your map PNG.\n\n"
                "## How to get the Data File\n"
                "1. Open Azgaar -> **Tools** -> **Burgs**.\n"
                "2. Click **Download** (Bottom Icon) -> Select **CSV**.\n"
                "3. Run this command again with the CSV attached.\n\n"
                "## 🔧 Canvas Configuration\n"
                "You can specify the coordinate system used by your CSV:\n"
                "`?importAzgaarMap 1980 1080` (Standard Azgaar)\n"
                "`?importAzgaarMap 1920 1080` (1080p)\n"
                "`?importAzgaarMap` (Auto-Detect from Data)"
            )
            return await ctx.send(embed=embed)

        # --- STEP 2: Processing ---
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.csv'):
            return await ctx.send("Please upload the **Burgs CSV** file (ends in `.csv`).")

        campaign_key = await ctx.bot.campaignTools.getCampaignKey(ctx)

        # 2a. Fetch MAP IMAGE for Raycasting
        campaign_data = await self.bot.sql.databaseFetchrowDynamic(
            "SELECT map_url FROM campaignservers WHERE serverid = $1", [ctx.guild.id])
        if not campaign_data or not campaign_data['map_url']:
            return await ctx.send(
                "## Error: No Map Image Found\nI need the map image to check for valid terrain. Please run `-updateMap` first.")

        status_msg = await ctx.send("⬇️ Downloading Map & Reading CSV...")

        try:
            # Get Image (For Raycasting only)
            async with aiohttp.ClientSession() as session:
                async with session.get(campaign_data['map_url']) as resp:
                    if resp.status != 200: return await ctx.send("Failed to download map image.")
                    image_data = await resp.read()

            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            map_h, map_w, _ = img.shape

            # Download CSV
            file_bytes = await attachment.read()
            csv_content = file_bytes.decode('utf-8')
            s_buf = io.StringIO(csv_content)
            reader = csv.DictReader(s_buf)
            rows = list(reader)

            if not rows: return await status_msg.edit(content="**Error:** CSV file is empty.")

            required_cols = ['Burg', 'State', 'Province', 'X', 'Y', 'Population']
            if not all(col in rows[0] for col in required_cols):
                return await status_msg.edit(
                    content=f"**Error:** CSV missing required columns. Need 'X' and 'Y'. Found: {list(rows[0].keys())}")

            # --- COORDINATE SYSTEM ---
            # Determine the "Grid Size" to use for normalization (0.0 - 1.0)

            if canvas_w > 0 and canvas_h > 0:
                # User specified dimensions
                grid_w = float(canvas_w)
                grid_h = float(canvas_h)
                scale_msg = f"📏 **Manual Canvas:** Normalizing to {int(grid_w)}x{int(grid_h)}."
            else:
                # Auto-Detect from Data Extents
                max_x = max([float(r.get('X', 0)) for r in rows])
                max_y = max([float(r.get('Y', 0)) for r in rows])

                # Heuristic for standard Azgaar padding
                grid_w = max_x * 1.01
                grid_h = max_y * 1.01
                scale_msg = f"📏 **Auto-Detect:** Normalizing to data bounds {int(grid_w)}x{int(grid_h)}."

            await status_msg.edit(content=f"{scale_msg}\nProcessing **{len(rows)}** cities with Terrain Validation...")

            # --- PHASE 1: FACTIONS ---
            unique_states = {}
            for row in rows:
                s_name = row.get('State', 'Neutral')
                if s_name == 'Neutral': continue
                if s_name not in unique_states:
                    desc = row.get('State Full Name', s_name)
                    unique_states[s_name] = desc

            existing_factions = await self.bot.sql.databaseFetchdictDynamic(
                "SELECT factionkey, factionname FROM campaignfactions WHERE campaignkey = $1", [campaign_key]
            )
            existing_names = {f['factionname'].lower(): f['factionkey'] for f in existing_factions}

            state_db_map = {}
            created_factions = []

            cols_to_check = ["orderschannelid", "socialchannelid", "leaderchannelid", "flagchannelid", "joinrole"]
            for col in cols_to_check:
                try:
                    await self.bot.sql.databaseExecute(
                        f"ALTER TABLE campaignfactions ADD COLUMN {col} BIGINT DEFAULT 0;")
                except:
                    pass

            for name, desc in unique_states.items():
                if name.lower() in existing_names:
                    state_db_map[name] = existing_names[name.lower()]
                else:
                    new_id = int(random.random() * 1000000000)
                    rand_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                    await self.bot.sql.databaseExecuteDynamic(
                        '''INSERT INTO campaignfactions 
                           (campaignkey, factionkey, factionname, description, money, color, 
                            orderschannelid, socialchannelid, leaderchannelid, flagchannelid, joinrole)
                           VALUES ($1, $2, $3, $4, $5, $6, 0, 0, 0, 0, 0)''',
                        [campaign_key, new_id, name, desc, 1000000000, rand_color]
                    )
                    state_db_map[name] = new_id
                    created_factions.append(name)

            # --- PHASE 2: CITIES (With Raycast & Normalization) ---
            provinces = {}
            for row in rows:
                p_name = row.get('Province', 'Unknown')
                if p_name not in provinces: provinces[p_name] = {'pop': 0, 'cities': []}
                try:
                    pop = int(row.get('Population', 0))
                except:
                    pop = 0
                provinces[p_name]['pop'] += pop
                provinces[p_name]['cities'].append(row)

            pois_created = 0
            skipped_water = 0

            await self.bot.sql.databaseExecuteDynamic("DELETE FROM campaign_pois WHERE campaign_id = $1",
                                                      [campaign_key])

            for p_name, p_data in provinces.items():
                cities = p_data['cities']
                total_pop = p_data['pop']
                if not cities: continue

                # Sort by population desc
                sorted_cities = sorted(cities, key=lambda x: int(x.get('Population', 0)) if x.get('Population',
                                                                                                  '0').isdigit() else 0,
                                       reverse=True)
                valid_capital = None

                # Find best valid capital on land
                for candidate in sorted_cities:
                    try:
                        raw_x = float(candidate.get('X', 0))
                        raw_y = float(candidate.get('Y', 0))

                        # --- RAYCAST CHECK ---
                        # Map the "Data Coordinate" to the "Image Coordinate"
                        norm_x = raw_x / grid_w
                        norm_y = raw_y / grid_h

                        img_x = int(norm_x * map_w)
                        img_y = int(norm_y * map_h)

                        # Bounds check
                        if 0 <= img_x < map_w and 0 <= img_y < map_h:
                            b, g, r = img[img_y, img_x]
                            b, g, r = int(b), int(g), int(r)

                            # Heuristic: Water is Blue dominant, Borders are Black/Dark
                            is_water = (b > r + 5) and (b > g + 5)
                            is_border = (b < 140) and (g < 140) and (r < 140)

                            if not is_water and not is_border:
                                valid_capital = candidate
                                break
                    except:
                        continue

                if not valid_capital:
                    skipped_water += 1
                    continue

                poi_name = valid_capital.get('Burg', 'Unknown')
                state_name = valid_capital.get('State', 'Neutral')
                owner_id = state_db_map.get(state_name, 0)

                # --- NORMALIZE FOR DB ---
                final_x = float(valid_capital.get('X', 0)) / grid_w
                final_y = float(valid_capital.get('Y', 0)) / grid_h

                await self.bot.sql.databaseExecuteDynamic(
                    '''INSERT INTO campaign_pois 
                       (campaign_id, name, type, latitude, longitude, output, 
                        controller_faction_id, integrity, population, province)
                       VALUES ($1, $2, 'city', $3, $4, 0, $5, 100.0, $6, $7)''',
                    [campaign_key, poi_name, final_y, final_x, owner_id, total_pop, p_name]
                )
                pois_created += 1

            report = f"## Import Complete!\n"
            report += f"**{len(created_factions)}** New Factions.\n"
            report += f"**{pois_created}** Regions Imported.\n"
            if skipped_water > 0:
                report += f"⚠️ **{skipped_water}** Provinces skipped (Capitals fell on Water/Borders).\n"
            if created_factions:
                report += "**New Factions:**\n" + ", ".join(created_factions[:10])
                if len(created_factions) > 10: report += "..."

            await status_msg.edit(content=report)

        except Exception as e:
            await status_msg.edit(content=f"**Critical Import Error:** `{e}`")
            import traceback
            traceback.print_exc()

    # ----------------------------------------------------------------------------------
    # GENERATION: Map Rendering (Restored FloodFill)
    # ----------------------------------------------------------------------------------
    @commands.command(name="generateMap", description="Render the current campaign map")
    async def generateMap(self, ctx: commands.Context):
        status_msg = await ctx.send("Fetching map data...")

        campaign_data = await self.bot.sql.databaseFetchrowDynamic(
            "SELECT campaignkey, map_url FROM campaignservers WHERE serverid = $1", [ctx.guild.id])
        if not campaign_data or not campaign_data['map_url']:
            return await ctx.send("No map configured! Use `-updateMap` first.")

        cities = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT p.name, p.latitude, p.longitude, f.color 
               FROM campaign_pois p
               LEFT JOIN campaignfactions f ON p.controller_faction_id = f.factionkey
               WHERE p.campaign_id = $1 AND p.type = 'city' AND f.color IS NOT NULL''',
            [campaign_data['campaignkey']]
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(campaign_data['map_url']) as resp:
                    if resp.status != 200: return await ctx.send("Failed to download map image.")
                    image_data = await resp.read()
        except Exception as e:
            return await ctx.send(f"Network error: {e}")

        await status_msg.edit(content="Rendering Map (Flood Fill)...")

        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width, _ = img.shape

        for city in cities:
            try:
                y_ratio = city['latitude']
                x_ratio = city['longitude']

                # Apply stored ratio to CURRENT image size
                x = int(x_ratio * width)
                y = int(y_ratio * height)

                x = max(0, min(x, width - 1))
                y = max(0, min(y, height - 1))

                # Flood Fill Mode
                hex_color = city['color'].lstrip('#')
                r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
                bgr_color = (b, g, r)

                # Small tolerance to fill neighboring pixels
                mask = np.zeros((height + 2, width + 2), np.uint8)
                cv2.floodFill(img, mask, (x, y), bgr_color, loDiff=(10, 10, 10), upDiff=(10, 10, 10))

            except Exception as e:
                print(f"Error painting city: {e}")

        is_success, buffer = cv2.imencode(".png", img)
        io_buf = io.BytesIO(buffer)

        await status_msg.delete()
        await ctx.send(file=discord.File(io_buf, "campaign_map.png"))

    @commands.command(name="generateTestMap", description="Render map with Debug Markers")
    async def generateTestMap(self, ctx: commands.Context):
        status_msg = await ctx.send("Fetching map data...")

        campaign_data = await self.bot.sql.databaseFetchrowDynamic(
            "SELECT campaignkey, map_url FROM campaignservers WHERE serverid = $1", [ctx.guild.id])
        if not campaign_data or not campaign_data['map_url']:
            return await ctx.send("No map configured! Use `-updateMap` first.")

        cities = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT p.name, p.latitude, p.longitude, f.color 
               FROM campaign_pois p
               LEFT JOIN campaignfactions f ON p.controller_faction_id = f.factionkey
               WHERE p.campaign_id = $1 AND p.type = 'city' ''',
            [campaign_data['campaignkey']]
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(campaign_data['map_url']) as resp:
                    if resp.status != 200: return await ctx.send("Failed to download map image.")
                    image_data = await resp.read()
        except Exception as e:
            return await ctx.send(f"Network error: {e}")

        await status_msg.edit(content="Rendering Map...")

        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width, _ = img.shape

        for city in cities:
            try:
                # Retrieve Normalized Ratios
                y_ratio = city['latitude']
                x_ratio = city['longitude']

                # Scale to Actual Image Size
                x = int(x_ratio * width)
                y = int(y_ratio * height)

                # Clamp
                x = max(0, min(x, width - 1))
                y = max(0, min(y, height - 1))

                # DEBUG: Red X
                cv2.drawMarker(img, (x, y), (0, 0, 255), markerType=1, markerSize=20, thickness=2)

            except Exception as e:
                print(f"Error marking city: {e}")

        is_success, buffer = cv2.imencode(".png", img)
        io_buf = io.BytesIO(buffer)

        await status_msg.delete()
        await ctx.send(file=discord.File(io_buf, "debug_map.png"))

    @commands.command(name="updateMap", description="Set the background map image for this campaign")
    async def updateMap(self, ctx: commands.Context):
        if not await ctx.bot.campaignTools.isCampaignHost(ctx):
            return await ctx.send("Only the Campaign Host can update the map.")

        if not ctx.message.attachments:
            return await ctx.send("Please upload the base map image (PNG).")

        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith('.png'):
            return await ctx.send("Map must be a **.png** file.")

        await self.bot.sql.databaseExecuteDynamic(
            "UPDATE campaignservers SET map_url = $1 WHERE serverid = $2",
            [attachment.url, ctx.guild.id]
        )
        await ctx.send(f"## Map Updated!\nNew base map set to: {attachment.url}")

    @commands.command(name="setFactionColor", description="Set a faction's map color (Hex Code)")
    async def setFactionColor(self, ctx: commands.Context):
        faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)

        color = await textTools.getResponse(ctx, "Enter Hex Color Code (e.g. #FF5733):")
        if not color.startswith("#") or len(color) != 7:
            return await ctx.send("Invalid Hex Code. Format: `#RRGGBB`")

        await self.bot.sql.databaseExecuteDynamic(
            "UPDATE campaignfactions SET color = $1 WHERE factionkey = $2",
            [color, faction_data['factionkey']]
        )
        await ctx.send(f"Faction color set to **{color}**.")

    @commands.command(name="updatePOIs", description="Upload/Download POI list via CSV")
    async def updatePOIs(self, ctx: commands.Context):
        if not await ctx.bot.campaignTools.isCampaignHost(ctx):
            return await ctx.send("Only the Campaign Host can manage POIs.")

        campaign_key = await ctx.bot.campaignTools.getCampaignKey(ctx)

        if not ctx.message.attachments:
            data = await self.bot.sql.databaseFetchdictDynamic(
                "SELECT name, type, latitude, longitude, output, controller_faction_id, integrity, population, province FROM campaign_pois WHERE campaign_id = $1",
                [campaign_key]
            )

            if not data:
                data = [{'name': 'Example City', 'type': 'city', 'latitude': 0.5, 'longitude': 0.5, 'output': 0,
                         'controller_faction_id': 0, 'integrity': 100.0, 'population': 0, 'province': 'None'}]

            df = pd.DataFrame(data)
            s_buf = io.StringIO()
            df.to_csv(s_buf, index=False)
            s_buf.seek(0)

            await ctx.send("## Current POI Database\nEdit this file and re-upload it to apply changes.",
                           file=discord.File(io.BytesIO(s_buf.getvalue().encode()), "pois.csv"))
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.csv'):
            return await ctx.send("Please upload a **.csv** file.")

        try:
            content = await attachment.read()
            s_buf = io.StringIO(content.decode('utf-8'))
            reader = csv.DictReader(s_buf)

            await self.bot.sql.databaseExecuteDynamic("DELETE FROM campaign_pois WHERE campaign_id = $1",
                                                      [campaign_key])

            count = 0
            for row in reader:
                await self.bot.sql.databaseExecuteDynamic(
                    '''INSERT INTO campaign_pois (campaign_id, name, type, latitude, longitude, output, controller_faction_id, integrity, population, province)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)''',
                    [
                        campaign_key,
                        row['name'],
                        row['type'],
                        float(row['latitude']),
                        float(row['longitude']),
                        float(row['output']),
                        int(row['controller_faction_id']),
                        float(row.get('integrity', 100.0)),
                        int(row.get('population', 0)),
                        row.get('province', 'Unknown')
                    ]
                )
                count += 1

            await ctx.send(f"## Success!\nUpdated {count} Points of Interest.")

        except Exception as e:
            await ctx.send(f"Error processing CSV: `{e}`")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(campaignMapsFunctions(bot))