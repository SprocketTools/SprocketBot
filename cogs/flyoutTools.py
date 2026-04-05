import json, io
import discord
import type_hints
from discord.ext import commands
import re
from cogs.textTools import textTools


class flyoutTools(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.command(name="parseFlyout", description="Parse a Flyout data.txt file into JSON")
    async def getFlyoutData(self, ctx: commands.Context):
        for attachment in ctx.message.attachments:
            if "data.txt" in attachment.filename:
                data = await self.parseFlyoutData(attachment)
                stringOut = json.dumps(data, indent=4)
                dataExport = io.BytesIO(stringOut.encode())
                fileOut = discord.File(dataExport, f'{data.get("name", "FlyoutData")}.json')
                await ctx.send(content=f"Parsed data of {data.get('name', 'Blueprint')}", file=fileOut)

    @commands.command(name="verifyVehicle", description="Verify a Flyout engine's legality based on GDP")
    async def verifyVehicle(self, ctx: commands.Context):
        campaignData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        factionData = await ctx.bot.campaignTools.getUserFactionData(ctx)
        gdp = max(min(factionData['gdp'], 10000000000), 1000000000)

        attachments = await textTools.getManyFilesResponse(ctx,
                                                           r"Upload your data.txt files (search through `%userprofile%\AppData\LocalLow\Stonext Games\Flyout\Craft` to find them)")

        for attachment in attachments:
            if "data.txt" in attachment.filename:
                parsed_blueprint = await self.parseFlyoutData(attachment)
                engines = parsed_blueprint.get('post_process_info', [])

                if not engines:
                    await ctx.send("No Procedural Engines found in this blueprint!")
                    continue

                for part in engines:
                    if part.get('resource_path') == 'Parts/ProceduralEngine':
                        subdata = part.get('*ProceduralEngine', {})

                        # Note: If the parser split these by comma, grab the first element, otherwise just float it
                        cpr_raw = subdata.get('cpr', [0])[0] if isinstance(subdata.get('cpr'), list) else subdata.get(
                            'cpr', 0)
                        valve_raw = subdata.get('valve_diam', [0])[0] if isinstance(subdata.get('valve_diam'),
                                                                                    list) else subdata.get('valve_diam',
                                                                                                           0)

                        specific_power_active = await textTools.getFlooredFloatResponse(ctx,
                                                                                        "What is your specific power in KW/L?",
                                                                                        1)
                        octane_active = await textTools.getFlooredFloatResponse(ctx, "What is your octane rating?", 1)
                        compression_active = float(cpr_raw)
                        valve_diam_active = float(valve_raw)

                        specific_power_int = (3778 / 1000) * gdp / 1000000000 + (12222 / 1000)
                        octane_int = (3111 / 1000) * gdp / 1000000000 + (83889 / 1000)
                        compression_int = (444 / 1000) * gdp / 1000000000 + (5556 / 1000)
                        valve_diam_int = (4444 / 1000) * gdp / 1000000000 + (5556 / 100)

                        if specific_power_active > specific_power_int:
                            await self.bot.error.sendCategorizedError(ctx, "blueprint")
                            await ctx.send(
                                f"Your specific power is invalid and should not exceed {round(specific_power_int, 3)}kW/L.")
                        elif octane_active > octane_int:
                            await self.bot.error.sendCategorizedError(ctx, "blueprint")
                            await ctx.send(
                                f"Your octane rating is invalid and should not exceed {round(octane_int, 7)}.")
                        elif compression_active > compression_int:
                            await self.bot.error.sendCategorizedError(ctx, "blueprint")
                            await ctx.send(
                                f"Your compression ratio of {compression_active} is invalid and should not exceed {round(compression_int, 3)}x.")
                        elif valve_diam_active > valve_diam_int / 99.999:
                            await self.bot.error.sendCategorizedError(ctx, "blueprint")
                            await ctx.send(
                                f"Your valve diameter of {valve_diam_active} is invalid and should not exceed {round(valve_diam_int, 3)}% of your maximum rating.")
                        else:
                            await ctx.send("All good here!")

    async def parseFlyoutData(self, attachment: discord.Attachment) -> dict:
        """
        Clean, recursive parser that converts Flyout .txt format into a dictionary.
        """
        raw_text = (await attachment.read()).decode('utf-8')

        # Strip the visual separators used in Flyout files
        text_data = re.sub(r'\|-+\|', '', raw_text)
        lines = text_data.splitlines()

        # Grab the very first line as the internal name
        name = lines[0].strip() if lines and lines[0].strip() else "Unknown_Aircraft"

        def parse_block(index):
            result = {}
            while index < len(lines):
                line = lines[index].strip()

                if not line:
                    index += 1
                    continue

                if line == '}':
                    return result, index

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Emulate your old `getData` comma/RGBA splitting logic
                    if 'RGBA' in value:
                        value = value.strip('RGBA').strip('(').strip(')').split(',')
                    elif ',' in value:
                        value = value.split(',')

                    result[key] = value

                elif line != '{':
                    block_name = line
                    index += 1
                    if index < len(lines) and lines[index].strip() == '{':
                        block_content, index = parse_block(index + 1)

                        # Group multiple blocks with the same name into a list (e.g. "Part")
                        if block_name in result:
                            if not isinstance(result[block_name], list):
                                result[block_name] = [result[block_name]]
                            result[block_name].append(block_content)
                        else:
                            result[block_name] = block_content
                index += 1

            return result, index

        # Execute parser
        parsed_data, _ = parse_block(0)
        parsed_data['name'] = name

        # Isolate the ProceduralEngines into post_process_info so verifyVehicle easily finds them
        engines = []
        parts = parsed_data.get('Part', [])

        # Ensure 'parts' is always a list even if there is only 1 part
        if not isinstance(parts, list):
            parts = [parts]

        for part in parts:
            if isinstance(part, dict) and part.get('resource_path') == 'Parts/ProceduralEngine':
                engines.append(part)

        parsed_data['post_process_info'] = engines

        return parsed_data


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(flyoutTools(bot))