import json, io
import discord
import type_hints
from discord.ext import commands
from cogs.textTools import textTools

class flyoutTools(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    @commands.command(name="parseFlyout", description="Add a moderation rule or subrule")
    async def getFlyoutData(self, ctx: commands.Context):
        for attachment in ctx.message.attachments:
            if "data.txt" in attachment.filename:
                data = await flyoutTools.parseFlyoutData(self, attachment)
                print(data)
                stringOut = json.dumps(data, indent=4)
                dataExport = io.BytesIO(stringOut.encode())
                fileOut = discord.File(dataExport, f'{data["name"]}.json')
                await ctx.send(content=f"Parsed data of {data['name']}", file=fileOut)

    @commands.command(name="verifyVehicle", description="Add a moderation rule or subrule")
    async def verifyVehicle(self, ctx: commands.Context):
        campaignData = await ctx.bot.campaignTools.getUserCampaignData(ctx)
        factionData = await ctx.bot.campaignTools.getUserFactionData(ctx)
        gdp = max(min(factionData['gdp'],10000000000), 1000000000)
        attachments = await textTools.getManyFilesResponse(ctx, "Upload your data.txt files (search through `%userprofile%\AppData\LocalLow\Stonext Games\Flyout\Craft` to find them)")
        for attachment in attachments:
            if "data.txt" in attachment.filename:
                data = (await flyoutTools.parseFlyoutData(self, attachment))['post_process_info']
                for part in data:
                    if part['resource_path'] == 'Parts/ProceduralEngine':
                        print(part)
                        subdata = part['*ProceduralEngine']
                        specific_power_active = await textTools.getFlooredFloatResponse(ctx, "What is your specific power in KW/L?", 1)
                        octane_active = await textTools.getFlooredFloatResponse(ctx, "What is your octane rating?", 1)
                        compression_active = float(subdata['cpr'])
                        valve_diam_active = float(subdata["valve_diam"])
                        specific_power_int = (3778/1000)*gdp/1000000000+(12222/1000)
                        octane_int = (3111/1000)*gdp/1000000000+(83889/1000)
                        compression_int = (444/1000)*gdp/1000000000+(5556/1000)
                        valve_diam_int = (4444/1000)*gdp/1000000000+(5556/100)
                        if specific_power_active > specific_power_int:
                            await self.bot.error.sendCategorizedError(ctx, "blueprint")
                            await ctx.send(f"Your specific power is invalid and should not exceed {round(specific_power_int, 3)}kW/L.")
                        elif octane_active > octane_int:
                            await self.bot.error.sendCategorizedError(ctx, "blueprint")
                            await ctx.send(f"Your octane rating is invalid and should not exceed {round(octane_int, 7)}.")
                        elif compression_active > compression_int:
                            await self.bot.error.sendCategorizedError(ctx, "blueprint")
                            await ctx.send(f"Your compression ratio of {compression_active} is invalid and should not exceed {round(compression_int, 3)}x.")
                        elif valve_diam_active > valve_diam_int/99.999:
                            await self.bot.error.sendCategorizedError(ctx, "blueprint")
                            await ctx.send(f"Your valve diameter of {valve_diam_active} is invalid and should not exceed {round(valve_diam_int, 3)}% of your maximum rating.")
                        else:
                            await ctx.send("All good here!")



                # stringOut = json.dumps(data, indent=4)
                # dataExport = io.BytesIO(stringOut.encode())
                # fileOut = discord.File(dataExport, f'{data["name"]}.json')
                # await ctx.send(content=f"Parsed data of {data['name']}", file=fileOut)

    async def parseFlyoutData(self, attachment: discord.Attachment):
        rawdata = await attachment.read()
        data = rawdata.decode("utf-8").splitlines()
        spares = []
        dataOut = {}
        i = 0
        dataOut['name'] = 'name'
        name = data[0].strip()
        while i < len(data):
            line = data[i].strip()
            if '=' in line:
                key, value = await flyoutTools.getData(self, line)
                dataOut[key] = value
            elif line == '{':
                i += 1
                dataCollected, e, newSpares = await flyoutTools.getList(self, data, i)
                key = f'{str(data[i - 2]).strip()} ({i})'
                if "ProceduralEngine" in str(data[i - 2]):
                    key = str(data[i - 2]).strip()
                dataOut[key] = dataCollected
                i = e
                #spares[len(spares)-1] = data[i]
                try:
                    if "Parts/ProceduralEngine" in dataCollected["resource_path"]:
                        spares.append(dataCollected)
                except Exception:
                    pass
            elif line == '':
                pass
            #else:
                #spares[len(spares)-1] = data[i]
            i+=1
        # blueprintData = demjson3.decode()
        dataOut['post_process_info'] = spares
        dataOut['name'] = name
        return dataOut
        # stringOut = json.dumps(dataOut, indent=4)
        # data = io.BytesIO(stringOut.encode())
        # fileOut = discord.File(data, f'{spares[0]}.json')
        # await ctx.author.send(content=f"Parsed data of {spares[0]}", file=fileOut)


    async def getList(self, data: list, pos: int):
        i = pos
        dataOut = {}
        spares = []
        while data[i].strip() != '}':
            line = data[i].strip()
            if '=' in line:
                key, value = await flyoutTools.getData(self, line)
                dataOut[key] = value
            elif line == '{':
                i += 1
                key = f'{str(data[i - 2]).strip()} ({i})'
                if "ProceduralEngine" in str(data[i - 2]):
                    key = str(data[i - 2]).strip()
                dataOut[key], e, newSpares = await flyoutTools.getList(self, data, i)
                i = e
                #spares[len(spares)-1] = data[i]
            elif line == '':
                pass
            i += 1
        return dataOut, i, spares

    async def getData(self, line: str):
        data = line.split('=')
        key = data[0].strip()
        value = data[1]
        if 'RGBA' in data[1]:
            value = data[1].strip('RGBA').strip('(').strip(')').split(',')
        elif ',' in data[1]:
            value = data[1].split(',')
        return key, value

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(flyoutTools(bot))