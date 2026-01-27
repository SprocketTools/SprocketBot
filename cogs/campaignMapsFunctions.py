import random

import discord
import aiohttp
import io
import cv2
import numpy as np
import csv
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
        # Added 'integrity' column (Float, Default 100.0)
        await self.bot.sql.databaseExecute('''DROP TABLE IF EXISTS campaign_pois;''')
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaign_pois (
                poi_id SERIAL PRIMARY KEY,
                campaign_id BIGINT,
                name VARCHAR(100),
                type VARCHAR(50), 
                latitude FLOAT,
                longitude FLOAT,
                output FLOAT DEFAULT 0,
                controller_faction_id BIGINT DEFAULT 0,
                integrity FLOAT DEFAULT 100.0
            );''')

        # Schema Migration for existing databases
        try:
            await self.bot.sql.databaseExecute("ALTER TABLE campaign_pois ADD COLUMN integrity FLOAT DEFAULT 100.0;")
        except Exception:
            pass  # Column likely exists

        # 2. Update Factions Table (Add Color)
        try:
            await self.bot.sql.databaseExecute(
                "ALTER TABLE campaignfactions ADD COLUMN color VARCHAR(20) DEFAULT '#808080';")
        except Exception:
            pass

            # 3. Update Servers Table (Add Map URL)
        try:
            await self.bot.sql.databaseExecute("ALTER TABLE campaignservers ADD COLUMN map_url TEXT DEFAULT NULL;")
        except Exception:
            pass

        await ctx.send("## Map Database Initialized!\nTables created and 'integrity' column added.")
    # ----------------------------------------------------------------------------------
    # CONFIG: Map & Colors
    # ----------------------------------------------------------------------------------
    @commands.command(name="updateMap", description="Set the background map image for this campaign")
    async def updateMap(self, ctx: commands.Context):
        if not await ctx.bot.campaignTools.isCampaignHost(ctx):
            return await ctx.send("Only the Campaign Host can update the map.")

        if not ctx.message.attachments:
            return await ctx.send("Please upload the base map image (PNG).")

        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith('.png'):
            return await ctx.send("Map must be a **.png** file.")

        # Store URL in database
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

    # ----------------------------------------------------------------------------------
    # MANAGEMENT: POI CSV Handling
    # ----------------------------------------------------------------------------------
    @commands.command(name="updatePOIs", description="Upload/Download POI list via CSV")
    async def updatePOIs(self, ctx: commands.Context):
        if not await ctx.bot.campaignTools.isCampaignHost(ctx):
            return await ctx.send("Only the Campaign Host can manage POIs.")

        campaign_key = await ctx.bot.campaignTools.getCampaignKey(ctx)

        # OPTION 1: Download current list
        if not ctx.message.attachments:
            # Added 'integrity' to the fetch list
            data = await self.bot.sql.databaseFetchdictDynamic(
                "SELECT name, type, latitude, longitude, output, controller_faction_id, integrity FROM campaign_pois WHERE campaign_id = $1",
                [campaign_key]
            )

            if not data:
                # Send template if empty
                data = [{'name': 'Example City', 'type': 'city', 'latitude': 51.5, 'longitude': -0.12, 'output': 0,
                         'controller_faction_id': 0, 'integrity': 100.0}]

            # Convert to CSV
            df = pd.DataFrame(data)
            s_buf = io.StringIO()
            df.to_csv(s_buf, index=False)
            s_buf.seek(0)

            await ctx.send("## Current POI Database\nEdit this file and re-upload it to apply changes.",
                           file=discord.File(io.BytesIO(s_buf.getvalue().encode()), "pois.csv"))
            return

        # OPTION 2: Upload new list
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.csv'):
            return await ctx.send("Please upload a **.csv** file.")

        try:
            # Read CSV
            content = await attachment.read()
            s_buf = io.StringIO(content.decode('utf-8'))
            reader = csv.DictReader(s_buf)

            # Clear old POIs
            await self.bot.sql.databaseExecuteDynamic("DELETE FROM campaign_pois WHERE campaign_id = $1",
                                                      [campaign_key])

            count = 0
            for row in reader:
                # Handle integrity: defaults to 100.0 if missing in an older CSV
                integrity_val = float(row.get('integrity', 100.0))

                await self.bot.sql.databaseExecuteDynamic(
                    '''INSERT INTO campaign_pois (campaign_id, name, type, latitude, longitude, output, controller_faction_id, integrity)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)''',
                    [
                        campaign_key,
                        row['name'],
                        row['type'],
                        float(row['latitude']),
                        float(row['longitude']),
                        float(row['output']),
                        int(row['controller_faction_id']),
                        integrity_val
                    ]
                )
                count += 1

            await ctx.send(f"## Success!\nUpdated {count} Points of Interest.")

        except Exception as e:
            await ctx.send(f"Error processing CSV: `{e}`")

    # ----------------------------------------------------------------------------------
    # GENERATION: Map Rendering
    # ----------------------------------------------------------------------------------
    @commands.command(name="populateRandomPOIs", description="[Debug] Add random POIs on valid land")
    async def populateRandomPOIs(self, ctx: commands.Context, count: int = 50):
        if not await ctx.bot.campaignTools.isCampaignHost(ctx):
            return await ctx.send("Only the Campaign Host can run debug commands.")

        # 1. Fetch Map Data
        campaign_data = await self.bot.sql.databaseFetchrowDynamic(
            "SELECT campaignkey, map_url FROM campaignservers WHERE serverid = $1", [ctx.guild.id])
        if not campaign_data or not campaign_data['map_url']:
            return await ctx.send("No map configured! Use `-updateMap` first.")

        campaign_key = campaign_data['campaignkey']

        status_msg = await ctx.send("Fetching map data to identify landmasses...")

        # 2. Download Image for Analysis
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(campaign_data['map_url']) as resp:
                    if resp.status != 200: return await ctx.send("Failed to download map image.")
                    image_data = await resp.read()
        except Exception as e:
            return await ctx.send(f"Network error: {e}")

        # Decode Image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # BGR format
        height, width, _ = img.shape

        # 3. Get Factions for random ownership
        factions = await self.bot.sql.databaseFetchdictDynamic(
            "SELECT factionkey FROM campaignfactions WHERE campaignkey = $1",
            [campaign_key]
        )
        faction_ids = [f['factionkey'] for f in factions]
        if not faction_ids: faction_ids = [0]

        types = ['city', 'oil_well', 'iron_mine']
        added = 0
        attempts = 0
        max_attempts = count * 100  # Safety break

        await status_msg.edit(content=f"Generating {count} POIs on valid terrain...")

        while added < count and attempts < max_attempts:
            attempts += 1

            # Generate Random Coordinate
            r_lat = random.uniform(-80, 80)
            r_lon = random.uniform(-180, 180)

            # Convert to Pixel Coordinates
            x = int((r_lon + 180) * (width / 360))
            y = int((90 - r_lat) * (height / 180))

            # Clamp to bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))

            # Check Pixel Color (BGR)
            b, g, r = img[y, x]
            b, g, r = int(b), int(g), int(r)
            # Logic:
            # - Water: Blue Channel is dominant (e.g. 255, 0, 0)
            # - Border: All channels are low (Black)
            # - Land: White (255, 255, 255) or Green (0, 255, 0)

            # Simple threshold check
            is_water = (b > r + 30) and (b > g + 30)  # Blue is significantly higher than R and G
            is_border = (b < 200) and (g < 200) and (r < 200)  # Very dark pixel

            if not is_water and not is_border:
                # Valid Land found!
                r_type = random.choice(types)
                r_owner = random.choice(faction_ids)
                r_output = random.randint(10, 500)

                name = f"Test {r_type.title()} {added + 1}"

                await self.bot.sql.databaseExecuteDynamic(
                    '''INSERT INTO campaign_pois (campaign_id, name, type, latitude, longitude, output, controller_faction_id, integrity)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, 100.0)''',
                    [campaign_key, name, r_type, r_lat, r_lon, r_output, r_owner]
                )
                added += 1

        if added < count:
            await status_msg.edit(
                content=f"## Finished with Warnings\nCould only place {added}/{count} POIs. The map might be mostly water?")
        else:
            await status_msg.edit(
                content=f"## Done!\nSuccessfully placed {added} POIs on land (checked {attempts} locations). Run `-generateMap` to see them.")

    @commands.command(name="generateMap", description="Render the current campaign map")
    async def generateMap(self, ctx: commands.Context):
        status_msg = await ctx.send("Fetching map data...")

        # 1. Get Campaign Config
        campaign_data = await self.bot.sql.databaseFetchrowDynamic(
            "SELECT campaignkey, map_url FROM campaignservers WHERE serverid = $1", [ctx.guild.id])
        if not campaign_data or not campaign_data['map_url']:
            return await ctx.send("No map configured! Use `-updateMap` first.")

        # 2. Get Cities (These are the flood-fill seeds)
        # We join with factions to get the owner's color
        cities = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT p.latitude, p.longitude, f.color 
               FROM campaign_pois p
               LEFT JOIN campaignfactions f ON p.controller_faction_id = f.factionkey
               WHERE p.campaign_id = $1 AND p.type = 'city' AND f.color IS NOT NULL''',
            [campaign_data['campaignkey']]
        )

        # 3. Download Map Image
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(campaign_data['map_url']) as resp:
                    if resp.status != 200: return await ctx.send("Failed to download map image.")
                    image_data = await resp.read()
        except Exception as e:
            return await ctx.send(f"Network error: {e}")

        # 4. Processing with OpenCV
        await status_msg.edit(content="Processing geometry...")

        # Decode image to numpy array (BGR format)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        height, width, channels = img.shape

        # 5. Paint Regions
        for city in cities:
            try:
                # Convert Lat/Long to Pixel X/Y (Equirectangular Projection)
                # Lat: +90 (Top) to -90 (Bottom) -> 0 to Height
                # Long: -180 (Left) to +180 (Right) -> 0 to Width
                lat = city['latitude']
                lon = city['longitude']

                x = int((lon + 180) * (width / 360))
                y = int((90 - lat) * (height / 180))

                # Clamp to bounds
                x = max(0, min(x, width - 1))
                y = max(0, min(y, height - 1))

                # Parse Hex Color (#RRGGBB) -> BGR tuple
                hex_color = city['color'].lstrip('#')
                r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
                bgr_color = (b, g, r)  # OpenCV uses BGR

                # Flood Fill
                # loDiff/upDiff: Tolerance for color matching (0 means strict match)
                # We assume the base map regions are solid white (255, 255, 255).
                mask = np.zeros((height + 2, width + 2), np.uint8)
                cv2.floodFill(img, mask, (x, y), bgr_color, loDiff=(10, 10, 10), upDiff=(10, 10, 10))

            except Exception as e:
                print(f"Error painting city at {lat}, {lon}: {e}")

        # 6. Encode and Send
        is_success, buffer = cv2.imencode(".png", img)
        io_buf = io.BytesIO(buffer)

        await status_msg.delete()
        await ctx.send(file=discord.File(io_buf, "campaign_map.png"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(campaignMapsFunctions(bot))