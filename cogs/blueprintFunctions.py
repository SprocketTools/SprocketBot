import random
import discord, json, math, numpy, copy, io, requests
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from discord.ext import commands
import cv2 as cv
import main
from cogs.textTools import textTools
from scipy.spatial.transform import Rotation as R
from PIL import Image
class blueprintFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="bakeGeometry", description="merge compartment geometry into itself.")
    async def bakeGeometry(self, ctx: commands.Context):
        # country = await getUserCountry(ctx)
        serverID = (ctx.guild.id)
        try:
            channel = int([dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel and ctx.author.id != main.ownerID:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
            await ctx.send(await self.bot.error.retrieveCategorizedError(ctx, "blueprint"))
            await ctx.send(f"Utility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
            return
        # received if else statement from stackoverflow: https://stackoverflow.com/questions/65169339/download-csv-file-sent-by-user-discord-py
        for attachment in ctx.message.attachments:

            blueprintData = json.loads(await attachment.read())
            name = blueprintData["header"]["name"]
            version = 0.127
            if "0.2" in blueprintData["header"]["gameVersion"]:
                await ctx.send("Detected a 0.2 blueprint.")
                blueprintDataSave = await blueprintFunctions.bakeGeometry200(ctx, attachment)
            elif float(blueprintData["header"]["gameVersion"]) < 0.128:
                await ctx.send(f"Detected a legacy {blueprintData['header']['gameVersion']} blueprint.")
                blueprintDataSave = await blueprintFunctions.bakeGeometry127(ctx, attachment)
            stringOut = json.dumps(blueprintDataSave, indent=4)
            data = io.BytesIO(stringOut.encode())
            await ctx.send(file=discord.File(data, f'{name}(merged).blueprint'))

            stringOut = json.dumps(blueprintDataSave, indent=4)
            data = io.BytesIO(stringOut.encode())
            fileOut = discord.File(data, f'{name}.json')
            await ctx.author.send(content=f"Baked geometry of {name}", file=fileOut)


    async def bakeGeometry200old(ctx: commands.Context, attachment):
        blueprintData = json.loads(await attachment.read())
        blueprintDataSave = json.loads(await attachment.read())
        name = blueprintData["header"]["name"]
        version = blueprintData["header"]["gameVersion"]
        compartmentList = {}

        # add all compartments to a list that can be called back from later
        i = 0
        for component in blueprintData["blueprints"]:
            if component["type"] == "structure":
                if blueprintData["blueprints"][i]["blueprint"]["name"] is None:
                    blueprintData["blueprints"][i]["blueprint"]["name"] = "Hull"
                nameOut = blueprintData["blueprints"][i]["blueprint"]["name"]
                if nameOut in compartmentList:
                    blueprintData["blueprints"][i]["blueprint"]["name"] = f"{nameOut} (Vuid {i})"
                positionID = blueprintData["blueprints"][i]["id"]
                meshID = blueprintData["blueprints"][i]["blueprint"]["bodyMeshVuid"]
                compartmentList[positionID] = {"PositionID": positionID, "meshID": meshID}
                for object in blueprintData["objects"]:
                    if "structureBlueprintVuid" in object:
                        if object["structureBlueprintVuid"] == positionID:
                            compartmentList[positionID]["transform"] = object["transform"]
                            compartmentList[positionID]["pvuid"] = int(object["pvuid"])
                            compartmentList[positionID]["vuid"] = int(object["vuid"])

                # usage of this is questionable
                for object in blueprintData["objects"]:
                    if "basketBlueprintVuid" in object:
                        if object["compartmentBodyID"]["structureVuid"] == compartmentList[positionID]["vuid"]:
                            compartmentList[positionID]["transform"] = numpy.add(object["transform"]["pos"], compartmentList[positionID]["transform"]["pos"]).tolist()
                            compartmentList[positionID]["pvuid"] = int(object["pvuid"])
                            compartmentList[positionID]["vuid"] = int(object["vuid"])

                # for object in blueprintData["objects"]:
                #     for compartment in compartmentList:
                #         if int(object["vuid"]) == int(compartment["pvuid"]):
                #             print("Hi!")
                #             positionID = compartment["positionID"]
                #             compartmentList[positionID]["transform"]["pos"] = numpy.add(object["transform"]["pos"], compartmentList[positionID]["transform"]["pos"])
                #             compartmentList[positionID]["transform"]["rot"] = numpy.add(object["transform"]["rot"], compartmentList[positionID]["transform"]["rot"])
                #             compartmentList[positionID]["transform"]["scale"] = numpy.multiply(object["transform"]["scale"], compartmentList[positionID]["transform"]["scale"])
            i += 1
        # i = 0
        # # apply offsets to have all compartments centered at [0,0,0]




        print(compartmentList)
        #copy all the meshes over to the hull
        verticesList = []
        facesList = []
        verticesOffset = 0
        for component in blueprintData["blueprints"]:
            if component["type"] == "structure":
                objectID = component["id"]
                relevantBodyMeshID = component["blueprint"]["bodyMeshVuid"]
                sourcePartInfo = compartmentList[objectID]["transform"]
                for meshData in blueprintData["meshes"]:

                    if meshData["vuid"] == relevantBodyMeshID:
                        print("Hi!")


                        sourcePartPosX = sourcePartInfo["pos"][0]
                        sourcePartPosY = sourcePartInfo["pos"][1]
                        sourcePartPosZ = sourcePartInfo["pos"][2]
                        sourcePartRotX = math.radians(sourcePartInfo["rot"][0])
                        sourcePartRotY = math.radians(sourcePartInfo["rot"][1])
                        sourcePartRotZ = math.radians(sourcePartInfo["rot"][2])
                        sourcePartPoints = meshData["meshData"]["mesh"]["vertices"]
                        sourcePartPointsLength = len(sourcePartPoints)
                        netPartPointsLength = len(verticesList)
                        netPartPointCount = int(netPartPointsLength)/3
                        # sourcePartSharedPoints = sourcePartInfo["compartment"]["sharedPoints"]
                        # sourcePartThicknessMap = sourcePartInfo["compartment"]["thicknessMap"]
                        # sourcePartFaceMap = sourcePartInfo["compartment"]["faceMap"]
                        # point positions (accounting for position + rotation)
                        pos = 0
                        # vector rotation
                        while pos < sourcePartPointsLength:
                            roundPoint = 6
                            vector = [sourcePartPoints[pos], sourcePartPoints[pos + 1], sourcePartPoints[pos + 2]]
                            # angles = [sourcePartRotZ, sourcePartRotY, -1*sourcePartRotX]
                            angles = [-1 * sourcePartRotX, -1 * sourcePartRotY, -1 * sourcePartRotZ]

                            newVector = braveRotateVector(vector, angles)

                            # newVector = rotateVector(vector, angles)
                            sourcePartPoints[pos] = round(newVector[0] + sourcePartPosX, roundPoint)
                            sourcePartPoints[pos + 1] = round(newVector[1] + sourcePartPosY, roundPoint)
                            sourcePartPoints[pos + 2] = round(newVector[2] + sourcePartPosZ, roundPoint)
                            pos += 3
                        # shared point lists (adjusted to not overlap with current faces)
                        verticesList = verticesList + sourcePartPoints
                        for facein in meshData["meshData"]["mesh"]["faces"]:
                            face = copy.deepcopy(facein)
                            i = 0
                            for facepoint in face["v"]:
                                face["v"][i] = int(int(face["v"][i]) + int(netPartPointCount))
                                #print(face["v"][i])
                                i += 1
                            facesList.append(face)
                        print(facesList)

        print(verticesList)
        blueprintData["meshes"][0]["meshData"]["mesh"]["vertices"] = verticesList
        blueprintData["meshes"][0]["meshData"]["mesh"]["faces"] = facesList
        netPartPointsLength = len(verticesList)
        netPartPointCount = max(int(netPartPointsLength) / 3 - 1, 0)
        print(f"There is {netPartPointsLength} vector elements and {netPartPointCount} points.")

        return blueprintData

        #     print(component)
        #     if component["type"] == "structure":
        #         nameOut = blueprintData["blueprints"][i]["blueprint"]["name"]
        #         if nameOut in structureList and dupeStatus == False:
        #             await ctx.send(await self.bot.error.retrieveError(ctx))
        #             await ctx.send(
        #                 f"Note: you have multiple compartments named {nameOut}.  To make things easier for yourself later, it's recommended to through your blueprint and give your compartments unique names.")
        #             dupeStatus = True
        #             nameOut = f"{nameOut} (Vuid {i})"
        #         structureList.append(nameOut)
        #         structureVuidList[blueprintData["blueprints"][i]["blueprint"]["name"]] = int(
        #             component["blueprint"]["bodyMeshVuid"])
        #     i += 1
        #
        # userPrompt = f"Pick the name of the compartment you wish to apply {attachmentin.filename} to."
        # print(structureList)
        # answer = await ctx.bot.ui.getChoiceFromList(ctx, structureList, userPrompt)
        # Vuid = structureVuidList[answer]
        #
        #
        # x = 0
        # for iteration in blueprintData["blueprints"]:
        #     partName = blueprintDataSave["blueprints"][x]["id"]
        #     partString = blueprintDataSave["blueprints"][x]["data"]
        #     partString.replace("\\", "")
        #     partInfo = json.loads(partString)
        #     clonePartInfo = copy.deepcopy(partInfo)
        #     if partName == "Compartment" and partInfo["name"].lower() == "target":
        #
        #         #print("Found a target!")
        #         y = 0
        #         for iteration in blueprintData["blueprints"]:
        #
        #             partName = blueprintDataSave["blueprints"][x]["id"]
        #             partString = blueprintDataSave["blueprints"][x]["data"]
        #             partString.replace("\\", "")
        #             partInfo = json.loads(partString)
        #             clonePartInfo = copy.deepcopy(partInfo)
        #
        #             basePartPoints = partInfo["compartment"]["points"]
        #             basePartPointsLength = len(basePartPoints)
        #             basePartSharedPoints = partInfo["compartment"]["sharedPoints"]
        #             basePartThicknessMap = partInfo["compartment"]["thicknessMap"]
        #             basePartFaceMap = partInfo["compartment"]["faceMap"]
        #
        #             sourcePartName = blueprintDataSave["blueprints"][y]["id"]
        #             sourcePartString = blueprintDataSave["blueprints"][y]["data"]
        #             sourcePartString.replace("\\", "")
        #             sourcePartInfo = json.loads(sourcePartString)
        #
        #             if sourcePartName == "Compartment" and sourcePartInfo["name"].lower() == "source":
        #                 #print("Found a source!")
        #                 import math
        #                 sourcePartPosX = sourcePartInfo["pos"][0]
        #                 sourcePartPosY = sourcePartInfo["pos"][1]
        #                 sourcePartPosZ = sourcePartInfo["pos"][2]
        #                 sourcePartRotX = math.radians(sourcePartInfo["rot"][0])
        #                 sourcePartRotY = math.radians(sourcePartInfo["rot"][1])
        #                 sourcePartRotZ = math.radians(sourcePartInfo["rot"][2])
        #                 sourcePartPoints = sourcePartInfo["compartment"]["points"]
        #                 sourcePartPointsLength = len(sourcePartPoints)
        #                 sourcePartSharedPoints = sourcePartInfo["compartment"]["sharedPoints"]
        #                 sourcePartThicknessMap = sourcePartInfo["compartment"]["thicknessMap"]
        #                 sourcePartFaceMap = sourcePartInfo["compartment"]["faceMap"]
        #
        #                 # point positions (accounting for position + rotation)
        #                 pos = 0
        #                 # vector rotation
        #                 while pos < sourcePartPointsLength:
        #                     roundPoint = 6
        #                     vector = [sourcePartPoints[pos], sourcePartPoints[pos + 1], sourcePartPoints[pos + 2]]
        #                     # angles = [sourcePartRotZ, sourcePartRotY, -1*sourcePartRotX]
        #                     angles = [-1 * sourcePartRotX, -1 * sourcePartRotY, -1 * sourcePartRotZ]
        #
        #                     newVector = braveRotateVector(vector, angles)
        #
        #                     # newVector = rotateVector(vector, angles)
        #                     sourcePartPoints[pos] = round(newVector[0] + sourcePartPosX, roundPoint)
        #                     sourcePartPoints[pos + 1] = round(newVector[1] + sourcePartPosY, roundPoint)
        #                     sourcePartPoints[pos + 2] = round(newVector[2] + sourcePartPosZ, roundPoint)
        #                     pos += 3
        #
        #                 # shared point lists (adjusted to not overlap with current faces)
        #                 clonePartInfo["compartment"]["points"] = basePartPoints + sourcePartPoints
        #
        #                 for group in sourcePartSharedPoints:
        #                     pos = 0
        #                     while pos < len(group):
        #                         group[pos] = group[pos] + int(basePartPointsLength / 3)
        #                         pos += 1
        #                 clonePartInfo["compartment"]["sharedPoints"] = basePartSharedPoints + sourcePartSharedPoints
        #                 #print(sourcePartSharedPoints)
        #                 #print(basePartSharedPoints)
        #                 #print(clonePartInfo["compartment"]["sharedPoints"])
        #                 # thickness maps (simply merged, it's how it works)
        #                 clonePartInfo["compartment"]["thicknessMap"] = basePartThicknessMap + sourcePartThicknessMap
        #
        #                 # face map (adjusted to not overlap with current faces)
        #
        #                 for group in sourcePartFaceMap:
        #                     pos = 0
        #                     while pos < len(group):
        #                         group[pos] = group[pos] + int(basePartPointsLength / 3)
        #                         pos += 1
        #                     # print(group)
        #                 clonePartInfo["compartment"]["faceMap"] = basePartFaceMap + sourcePartFaceMap
        #
        #                 # save
        #                 data0 = json.dumps(clonePartInfo)
        #                 blueprintDataSave["blueprints"][x]["data"] = data0
        #             y += 1
        #     x += 1
        # import io
        # await ctx.send("Done!")
        # # data0 = json.dumps(blueprintData[0]["data"])
        # # data1 = json.dumps(blueprintData[1]["data"])
        # # data0.replace("\\", "")
        # # data1.replace("\\", "")
        # # blueprintData[0]["data"] = data0
        # # blueprintData[1]["data"] = data1
        #
        # # fileData[0]["data"] = blueprintData
        # return blueprintDataSave

    async def bakeGeometry200(ctx: commands.Context, attachment):
        blueprintData = json.loads(await attachment.read())
        blueprintDataSave = json.loads(await attachment.read())
        name = blueprintData["header"]["name"]
        version = blueprintData["header"]["gameVersion"]
        compartmentList = {}
        meshesOut = {}
        # add all compartments to a list that can be called back from later
        i = 0
        for component in blueprintData["blueprints"]:
            if component["type"] == "structure":

                if blueprintData["blueprints"][i]["blueprint"]["name"] is None:
                    blueprintData["blueprints"][i]["blueprint"]["name"] = "Hull"
                nameOut = blueprintData["blueprints"][i]["blueprint"]["name"]
                if nameOut in compartmentList:
                    blueprintData["blueprints"][i]["blueprint"]["name"] = f"{nameOut} (Vuid {i})"
                positionID = blueprintData["blueprints"][i]["id"]

                meshID = blueprintData["blueprints"][i]["blueprint"]["bodyMeshVuid"]
                compartmentList[positionID] = {"PositionID": positionID, "meshID": meshID}
                print(positionID)
                print("hiiiii")
                for object in blueprintData["objects"]:
                    if "structureBlueprintVuid" in object:
                        object["isbase"] = False
                        if object["structureBlueprintVuid"] == positionID:
                            compartmentList[positionID]["transform"] = object["transform"]
                            compartmentList[positionID]["isbase"] = False
                            if object["pvuid"] == -1 and "structureBlueprintVuid" in object:
                                compartmentList[positionID]["isbase"] = True
                                object["isbase"] = True
                            compartmentList[positionID]["flags"] = int(object["flags"])
                            compartmentList[positionID]["pvuid"] = int(object["pvuid"])
                            compartmentList[positionID]["vuid"] = int(object["vuid"])


                # usage of this is questionable
                # for object in blueprintData["objects"]:
                #     if "basketBlueprintVuid" in object:
                #         if object["compartmentBodyID"]["structureVuid"] == compartmentList[positionID]["vuid"]:
                #             compartmentList[positionID]["transform"] = numpy.add(object["transform"]["pos"],
                #                                                                  compartmentList[positionID][
                #                                                                      "transform"]["pos"]).tolist()
                #             compartmentList[positionID]["pvuid"] = int(object["pvuid"])
                #             compartmentList[positionID]["vuid"] = int(object["vuid"])

                # for object in blueprintData["objects"]:
                #     for compartment in compartmentList:
                #         if int(object["vuid"]) == int(compartment["pvuid"]):
                #             print("Hi!")
                #             positionID = compartment["positionID"]
                #             compartmentList[positionID]["transform"]["pos"] = numpy.add(object["transform"]["pos"], compartmentList[positionID]["transform"]["pos"])
                #             compartmentList[positionID]["transform"]["rot"] = numpy.add(object["transform"]["rot"], compartmentList[positionID]["transform"]["rot"])
                #             compartmentList[positionID]["transform"]["scale"] = numpy.multiply(object["transform"]["scale"], compartmentList[positionID]["transform"]["scale"])
            i += 1
        i = 0
        for object in blueprintData["objects"]:
            if "ringBlueprintVuid" in object:
                blueprintData["objects"][i]["isbase"] = True
            elif object["pvuid"] == -1 and "structureBlueprintVuid" in object:
                blueprintData["objects"][i]["isbase"] = True
            else:
                blueprintData["objects"][i]["isbase"] = True
            # if object["pvuid"] == -1 and "structureBlueprintVuid" in object:
            #     compartmentList[i]["isbase"] = True
            i += 1
        # i = 0
        compartmentListOriginal = compartmentList.copy()
        if len(str(compartmentListOriginal)) > 90000:
            await ctx.send("This tank is too big to process!")
            return
        # # apply structure offsets to have all compartments centered at [0,0,0] and save their meshes to the base vehicle
        for compartment in compartmentListOriginal:
            compartmentList = compartmentListOriginal.copy()
            # print(compartmentList)
            # print(compartment)
            relevantObjectID = compartmentList[compartment]["PositionID"]

            for object in blueprintData["objects"]:

                if "structureBlueprintVuid" in object:
                    if object["structureBlueprintVuid"] == relevantObjectID:
                        # this is the structure we need to relocate
                        # start by setting its base position to zero

                        compartmentList[relevantObjectID]["transform"]["pos"] = (compartmentListOriginal[relevantObjectID]["transform"]["pos"])
                        compartmentList[relevantObjectID]["transform"]["rot"] = (compartmentListOriginal[relevantObjectID]["transform"]["rot"])
                        compartmentList[relevantObjectID]["transform"]["scale"] = (compartmentListOriginal[relevantObjectID]["transform"]["scale"])
                        requireMirror = False


                        # parts need to be mirrored from here
                        # use flags of 7 = mirrored on hull
                        # 6 = mirrored on another addon
                        relevantBodyMeshID = compartmentList[relevantObjectID]["meshID"]
                        i = 0
                        for meshData in blueprintData["meshes"]:
                            if meshData["vuid"] == relevantBodyMeshID:
                                meshesOut[relevantObjectID] = copy.deepcopy(blueprintDataSave["meshes"][i])
                                meshesOut[relevantObjectID]["mirrored"] = False
                                newPoints = await blueprintFunctions.runMeshTranslation(ctx, meshesOut[relevantObjectID], object["transform"])
                                print(compartmentList[relevantObjectID])

                                meshesOut[relevantObjectID]["meshData"]["mesh"]["vertices"] = newPoints

                                # print(f"initial update for VUID{relevantBodyMeshID}!")
                                # for eee, iee in meshesOut.items():
                                #     print(iee)
                            i += 1

                        # for eee, meshData in meshesOut.items():
                        #     print(eee)
                        #     print(meshData["meshData"]["mesh"]["vertices"])
                        # print("--^--^--")

                        # objects with a pvuid of x are attached to a vuid of x.  Loop until the pvuid = -1
                        activeVuid = object["vuid"]
                        activePvuid = object["pvuid"]
                        #print(activeVuid)
                        while int(activePvuid) > -1:
                            for subobject in blueprintData["objects"]:
                                if subobject["vuid"] == activePvuid:
                                    # print(f"{activePvuid} is the active PVUID")
                                    relevantBodyMeshID = compartmentList[relevantObjectID]["meshID"]
                                    i = 0
                                    for eee, meshData in meshesOut.items():
                                        if eee == relevantObjectID:
                                            newPoints = await blueprintFunctions.runMeshTranslation(ctx, meshesOut[relevantObjectID], subobject["transform"])
                                            print(f"{len(newPoints)} +++ {compartmentList[relevantObjectID]['isbase']} +++ {meshesOut[relevantObjectID]['mirrored']}" )

                                            #mirror if running into a base --- compartmentList[relevantObjectID]["isbase"] == True and meshesOut[relevantObjectID]["mirrored"] == False
                                            if compartmentList[relevantObjectID]["flags"] == 6 or compartmentList[relevantObjectID]["flags"] == 7:
                                                if subobject["isbase"] == True and meshesOut[relevantObjectID]["mirrored"] == False:
                                                    print(f'''Starting a mirror!!\n{compartmentList[relevantObjectID]['flags']}\n{eee}''')
                                                    facesList = copy.deepcopy(meshesOut[relevantObjectID]["meshData"]["mesh"]["faces"])
                                                    netPartPointsLength = len(newPoints)
                                                    netPartPointCount = int(netPartPointsLength) / 3
                                                    print(object["transform"])
                                                    newPoints = copy.deepcopy(newPoints) + await blueprintFunctions.runMeshMirror(ctx, meshesOut[relevantObjectID], subobject["transform"])
                                                    print(newPoints)
                                                    for facein in meshesOut[relevantObjectID]["meshData"]["mesh"]["faces"]:
                                                        face = copy.deepcopy(facein)
                                                        i = 0
                                                        for facepoint in face["v"]:
                                                            face["v"][i] = int(int(face["v"][i]) + int(netPartPointCount))
                                                            # print(face["v"][i])
                                                            i += 1
                                                        facesList.append(face)
                                                    meshesOut[relevantObjectID]["meshData"]["mesh"]["vertices"] = newPoints
                                                    meshesOut[relevantObjectID]["meshData"]["mesh"]["faces"] = facesList
                                                    meshesOut[relevantObjectID]["mirrored"] = True
                                            else:
                                                meshesOut[relevantObjectID]["meshData"]["mesh"]["vertices"] = newPoints
                                        i += 1
                                    activeVuid = subobject["vuid"]
                                    activePvuid = subobject["pvuid"]





        # print(compartmentList)
        # copy all the meshes over to the hull
        verticesList = []
        facesList = []
        verticesOffset = 0
        for component in blueprintData["blueprints"]:
            if component["type"] == "structure":
                objectID = component["id"]
                relevantBodyMeshID = component["blueprint"]["bodyMeshVuid"]
                sourcePartInfo = compartmentList[objectID]["transform"]
                # print(meshesOut)
                for eee, meshData in meshesOut.items():
                    # print("Got data for #" + str(eee))
                    if meshData["vuid"] == relevantBodyMeshID:
                        # print("Using data for #" + str(eee))
                        # print("Hi!")

                        sourcePartPosX = sourcePartInfo["pos"][0]
                        sourcePartPosY = sourcePartInfo["pos"][1]
                        sourcePartPosZ = sourcePartInfo["pos"][2]
                        sourcePartRotX = math.radians(sourcePartInfo["rot"][0])
                        sourcePartRotY = math.radians(sourcePartInfo["rot"][1])
                        sourcePartRotZ = math.radians(sourcePartInfo["rot"][2])
                        sourcePartPoints = meshData["meshData"]["mesh"]["vertices"]
                        sourcePartPointsLength = len(sourcePartPoints)
                        netPartPointsLength = len(verticesList)
                        netPartPointCount = int(netPartPointsLength) / 3

                        # shared point lists (adjusted to not overlap with current faces)
                        verticesList = verticesList + sourcePartPoints
                        for facein in meshData["meshData"]["mesh"]["faces"]:
                            face = copy.deepcopy(facein)
                            i = 0
                            for facepoint in face["v"]:
                                face["v"][i] = int(int(face["v"][i]) + int(netPartPointCount))
                                # print(face["v"][i])
                                i += 1
                            facesList.append(face)
                        # print(verticesList)

        # print(verticesList)
        blueprintData["meshes"][0]["meshData"]["mesh"]["vertices"] = verticesList
        blueprintData["meshes"][0]["meshData"]["mesh"]["faces"] = facesList
        netPartPointsLength = len(verticesList)
        netPartPointCount = max(int(netPartPointsLength) / 3 - 1, 0)
        # print(f"There is {netPartPointsLength} vector elements and {netPartPointCount} points.")


        return blueprintData

    async def bakeGeometry127(ctx: commands.Context, attachment):
        blueprintData = json.loads(await attachment.read())
        blueprintDataSave = json.loads(await attachment.read())
        name = blueprintData["header"]["name"]
        version = blueprintData["header"]["gameVersion"]
        if "0.12" not in version:
            errorText = await self.bot.error.retrieveError(ctx)
            await ctx.send(await self.bot.error.retrieveCategorizedError(ctx, "blueprint"))
            await ctx.reply(f"{errorText}\n\nThis command does not support the Geometric Internals build yet.")

        x = 0
        for iteration in blueprintData["blueprints"]:
            partName = blueprintDataSave["blueprints"][x]["id"]
            partString = blueprintDataSave["blueprints"][x]["data"]
            partString.replace("\\", "")
            partInfo = json.loads(partString)
            clonePartInfo = copy.deepcopy(partInfo)
            if partName == "Compartment" and partInfo["name"].lower() == "target":

                #print("Found a target!")
                y = 0
                for iteration in blueprintData["blueprints"]:

                    partName = blueprintDataSave["blueprints"][x]["id"]
                    partString = blueprintDataSave["blueprints"][x]["data"]
                    partString.replace("\\", "")
                    partInfo = json.loads(partString)
                    clonePartInfo = copy.deepcopy(partInfo)

                    basePartPoints = partInfo["compartment"]["points"]
                    basePartPointsLength = len(basePartPoints)
                    basePartSharedPoints = partInfo["compartment"]["sharedPoints"]
                    basePartThicknessMap = partInfo["compartment"]["thicknessMap"]
                    basePartFaceMap = partInfo["compartment"]["faceMap"]

                    sourcePartName = blueprintDataSave["blueprints"][y]["id"]
                    sourcePartString = blueprintDataSave["blueprints"][y]["data"]
                    sourcePartString.replace("\\", "")
                    sourcePartInfo = json.loads(sourcePartString)

                    if sourcePartName == "Compartment" and sourcePartInfo["name"].lower() == "source":
                        #print("Found a source!")
                        import math
                        sourcePartPosX = sourcePartInfo["pos"][0]
                        sourcePartPosY = sourcePartInfo["pos"][1]
                        sourcePartPosZ = sourcePartInfo["pos"][2]
                        sourcePartRotX = math.radians(sourcePartInfo["rot"][0])
                        sourcePartRotY = math.radians(sourcePartInfo["rot"][1])
                        sourcePartRotZ = math.radians(sourcePartInfo["rot"][2])
                        sourcePartPoints = sourcePartInfo["compartment"]["points"]
                        sourcePartPointsLength = len(sourcePartPoints)
                        sourcePartSharedPoints = sourcePartInfo["compartment"]["sharedPoints"]
                        sourcePartThicknessMap = sourcePartInfo["compartment"]["thicknessMap"]
                        sourcePartFaceMap = sourcePartInfo["compartment"]["faceMap"]

                        # point positions (accounting for position + rotation)
                        pos = 0
                        # vector rotation
                        while pos < sourcePartPointsLength:
                            roundPoint = 6
                            vector = [sourcePartPoints[pos], sourcePartPoints[pos + 1], sourcePartPoints[pos + 2]]
                            # angles = [sourcePartRotZ, sourcePartRotY, -1*sourcePartRotX]
                            angles = [-1 * sourcePartRotX, -1 * sourcePartRotY, -1 * sourcePartRotZ]

                            newVector = braveRotateVector(vector, angles)

                            # newVector = rotateVector(vector, angles)
                            sourcePartPoints[pos] = round(newVector[0] + sourcePartPosX, roundPoint)
                            sourcePartPoints[pos + 1] = round(newVector[1] + sourcePartPosY, roundPoint)
                            sourcePartPoints[pos + 2] = round(newVector[2] + sourcePartPosZ, roundPoint)
                            pos += 3

                        # shared point lists (adjusted to not overlap with current faces)
                        clonePartInfo["compartment"]["points"] = basePartPoints + sourcePartPoints

                        for group in sourcePartSharedPoints:
                            pos = 0
                            while pos < len(group):
                                group[pos] = group[pos] + int(basePartPointsLength / 3)
                                pos += 1
                        clonePartInfo["compartment"]["sharedPoints"] = basePartSharedPoints + sourcePartSharedPoints
                        #print(sourcePartSharedPoints)
                        #print(basePartSharedPoints)
                        #print(clonePartInfo["compartment"]["sharedPoints"])
                        # thickness maps (simply merged, it's how it works)
                        clonePartInfo["compartment"]["thicknessMap"] = basePartThicknessMap + sourcePartThicknessMap

                        # face map (adjusted to not overlap with current faces)

                        for group in sourcePartFaceMap:
                            pos = 0
                            while pos < len(group):
                                group[pos] = group[pos] + int(basePartPointsLength / 3)
                                pos += 1
                            # print(group)
                        clonePartInfo["compartment"]["faceMap"] = basePartFaceMap + sourcePartFaceMap

                        # save
                        data0 = json.dumps(clonePartInfo)
                        blueprintDataSave["blueprints"][x]["data"] = data0
                    y += 1
            x += 1
        await ctx.send("Done!")

        return blueprintDataSave

    async def runMeshTranslation(ctx:commands.Context, meshData, sourcePartInfo):
        # print("Hi!")

        sourcePartPosX = sourcePartInfo["pos"][0]
        sourcePartPosY = sourcePartInfo["pos"][1]
        sourcePartPosZ = sourcePartInfo["pos"][2]
        sourcePartRotX = math.radians(sourcePartInfo["rot"][0])
        sourcePartRotY = math.radians(sourcePartInfo["rot"][1])
        sourcePartRotZ = math.radians(sourcePartInfo["rot"][2])
        sourcePartPoints = meshData["meshData"]["mesh"]["vertices"]
        sourcePartPointsLength = len(sourcePartPoints)

        # sourcePartSharedPoints = sourcePartInfo["compartment"]["sharedPoints"]
        # sourcePartThicknessMap = sourcePartInfo["compartment"]["thicknessMap"]
        # sourcePartFaceMap = sourcePartInfo["compartment"]["faceMap"]
        # point positions (accounting for position + rotation)
        pos = 0
        # vector rotation
        while pos < sourcePartPointsLength:
            roundPoint = 6
            vector = [sourcePartPoints[pos], sourcePartPoints[pos + 1], sourcePartPoints[pos + 2]]
            # angles = [sourcePartRotZ, sourcePartRotY, -1*sourcePartRotX]
            angles = [-1 * sourcePartRotX, -1 * sourcePartRotY, -1 * sourcePartRotZ]

            newVector = braveRotateVector(vector, angles)

            # newVector = rotateVector(vector, angles)
            sourcePartPoints[pos] = round(newVector[0] + sourcePartPosX, roundPoint)
            sourcePartPoints[pos + 1] = round(newVector[1] + sourcePartPosY, roundPoint)
            sourcePartPoints[pos + 2] = round(newVector[2] + sourcePartPosZ, roundPoint)
            pos += 3
        # shared point lists (adjusted to not overlap with current faces)
        return sourcePartPoints

    async def runMeshMirror(ctx:commands.Context, meshData, sourcePartInfo):
        # print("Hi!")

        sourcePartPosX = sourcePartInfo["pos"][0]
        sourcePartPosY = sourcePartInfo["pos"][1]
        sourcePartPosZ = sourcePartInfo["pos"][2]
        sourcePartRotX = math.radians(sourcePartInfo["rot"][0])
        sourcePartRotY = math.radians(sourcePartInfo["rot"][1])
        sourcePartRotZ = math.radians(sourcePartInfo["rot"][2])
        sourcePartPoints = meshData["meshData"]["mesh"]["vertices"]
        sourcePartPointsLength = len(sourcePartPoints)

        # sourcePartSharedPoints = sourcePartInfo["compartment"]["sharedPoints"]
        # sourcePartThicknessMap = sourcePartInfo["compartment"]["thicknessMap"]
        # sourcePartFaceMap = sourcePartInfo["compartment"]["faceMap"]
        # point positions (accounting for position + rotation)
        pos = 0
        # vector rotation
        while pos < sourcePartPointsLength:
            sourcePartPoints[pos] = -1*(sourcePartPoints[pos])
            pos += 3
        # shared point lists (adjusted to not overlap with current faces)
        return sourcePartPoints

    async def _get_world_transform(self, vuid: int, objects_by_vuid: dict, memo: dict) -> numpy.ndarray:
        """
        Calculates the final world matrix with the corrected ZYX rotation order and
        a standard LHS-to-RHS angle conversion.
        """
        if vuid in memo:
            return memo[vuid]

        if vuid == -1:
            return numpy.identity(4)

        obj = objects_by_vuid[vuid]
        pos = obj["transform"]["pos"]
        base_scale = numpy.array(obj["transform"]["scale"])
        rot_data = obj["transform"]["rot"]

        # 1. --- SCALE ---
        scale_3x3 = numpy.diag(base_scale)

        # 2. --- MIRROR ---
        flags = obj.get("flags")
        mirror_flags = {}
        if isinstance(flags, dict):
            mirror_flags = flags.get("mirror", {})

        mirror_vector = numpy.array([
            -1.0 if mirror_flags.get("x", False) else 1.0,
            -1.0 if mirror_flags.get("y", False) else 1.0,
            -1.0 if mirror_flags.get("z", False) else 1.0
        ])
        mirror_3x3 = numpy.diag(mirror_vector)

        # 3. --- ROTATE ---
        rot_matrix = numpy.identity(3)
        if len(rot_data) >= 3 and numpy.any(rot_data[:3]):
            # --- THE FINAL SYNTHESIS ---
            # Use the 'zyx' order that works for structural parts like the square.
            # Use a standard Left-Handed to Right-Handed conversion for the angles.
            euler_raw = rot_data[:3]
            euler_angles = [-euler_raw[0], -euler_raw[1], euler_raw[2]]
            rot_matrix = R.from_euler('zyx', euler_angles, degrees=True).as_matrix()
            # --- END SYNTHESIS ---

        # Combine in the R @ M @ S order
        mirror_scale_3x3 = numpy.dot(mirror_3x3, scale_3x3)
        transform_3x3 = numpy.dot(rot_matrix, mirror_scale_3x3)

        # 4. --- TRANSLATE ---
        local_matrix = numpy.identity(4)
        local_matrix[0:3, 0:3] = transform_3x3
        local_matrix[0:3, 3] = pos

        # Get parent's transform and apply it in the standard Parent -> Local order
        parent_vuid = int(obj["pvuid"])
        parent_world_transform = await self._get_world_transform(parent_vuid, objects_by_vuid, memo)
        world_transform = numpy.dot(parent_world_transform, local_matrix)

        memo[vuid] = world_transform
        return world_transform

    async def bakeGeometry210(self, attachment):
        blueprintData = json.loads(await attachment.read())

        objects_by_vuid = {int(obj["vuid"]): obj for obj in blueprintData["objects"]}
        meshes_by_vuid = {int(mesh["vuid"]): mesh for mesh in blueprintData["meshes"]}

        structures_to_process = []
        for bp in blueprintData["blueprints"]:
            if bp["type"] == "structure":
                for obj in objects_by_vuid.values():
                    if obj.get("structureBlueprintVuid") == bp["id"]:
                        structures_to_process.append({
                            "object_vuid": obj["vuid"],
                            "mesh_vuid": bp["blueprint"]["bodyMeshVuid"]
                        })
                        break

        transform_cache = {}
        all_processed_meshes = []

        for structure in structures_to_process:
            obj_vuid = structure["object_vuid"]
            mesh_vuid = structure["mesh_vuid"]

            if mesh_vuid not in meshes_by_vuid:
                continue

            # Calculate the single, final transformation matrix for this part
            world_transform = await self._get_world_transform(obj_vuid, objects_by_vuid, transform_cache)

            original_mesh = meshes_by_vuid[mesh_vuid]
            vertices_flat = original_mesh["meshData"]["mesh"]["vertices"]

            if not vertices_flat:
                continue

            vertices = numpy.array(vertices_flat).reshape(-1, 3)
            vertices_homogeneous = numpy.hstack([vertices, numpy.ones((vertices.shape[0], 1))])

            # Apply the final transform to all vertices at once
            transformed_vertices_homogeneous = numpy.dot(world_transform, vertices_homogeneous.T).T
            transformed_vertices = transformed_vertices_homogeneous[:, :3]

            # Check for mirrored faces to prevent them from rendering inside-out
            det = numpy.linalg.det(world_transform[0:3, 0:3])
            flip_faces = (det < 0)

            all_processed_meshes.append({
                "vertices": transformed_vertices.tolist(),
                "faces": original_mesh["meshData"]["mesh"]["faces"],
                "flip": flip_faces
            })

        # Combine all transformed meshes into the final result
        final_vertices = []
        final_faces = []
        vertex_offset = 0

        for mesh in all_processed_meshes:
            final_vertices.extend(mesh["vertices"])

            for face in mesh["faces"]:
                new_face = copy.deepcopy(face)
                face_indices = [v_idx + vertex_offset for v_idx in new_face["v"]]

                if mesh["flip"]:
                    new_face["v"] = [face_indices[0], face_indices[2], face_indices[1]]
                else:
                    new_face["v"] = face_indices
                final_faces.append(new_face)
            vertex_offset += len(mesh["vertices"])

        blueprintData["meshes"][0]["meshData"]["mesh"]["vertices"] = [coord for vertex in final_vertices for coord in
                                                                      vertex]
        blueprintData["meshes"][0]["meshData"]["mesh"]["faces"] = final_faces

        return blueprintData

    @commands.hybrid_command(name="getaddon", description="merge compartment geometry into itself.")
    async def getAddon(self, ctx: commands.Context):
        serverID = (ctx.guild.id)
        try:
            channel = int([dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
                error = await self.bot.error.retrieveCategorizedError(ctx, "blueprint")
                await ctx.send(f"{error}\n\nUtility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
                return
        if len(ctx.message.attachments) == 0:
            attachments = await textTools.getManyFilesResponse(ctx, "Upload the file(s) you wish to create addon structures out of.")
        else:
            attachments = ctx.message.attachments
        for attachment in attachments:
            blueprintData = json.loads(await attachment.read())
            structureList = ["All of them"]
            structureVuidList = {}
            compartmentData = {}
            compartmentNameData = {}
            tankName = blueprintData["header"]["name"]
            i = 0
            for component in blueprintData["blueprints"]:

                if component["type"] == "structure":
                    bmID = component["blueprint"]["bodyMeshVuid"]
                    compartmentNameData[int(bmID)] = component["blueprint"]["name"]
                    if blueprintData["blueprints"][i]["blueprint"]["name"] is None or len(blueprintData["blueprints"][i]["blueprint"]["name"]) < 1:
                        blueprintData["blueprints"][i]["blueprint"]["name"] = f"This might be your hull? ({i})"
                        if random.random() < 0.005:
                            blueprintData["blueprints"][i]["blueprint"]["name"] = "Sprocket Chan"
                    nameOut = blueprintData["blueprints"][i]["blueprint"]["name"]
                    if nameOut not in structureList:
                        print(nameOut)
                        structureList.append(nameOut)
                        structureVuidList[blueprintData["blueprints"][i]["blueprint"]["name"]] = int(component["blueprint"]["bodyMeshVuid"])
                i += 1

            userPrompt = "Pick the name of the compartment you wish to make an addon structure out of.  Note: unnamed structures are not listed"
            print(structureList)
            answer = await ctx.bot.ui.getChoiceFromList(ctx, structureList, userPrompt)

            # get info on grid snap
            gridSnap = 1
            userPrompt = "Specify your desired grid snap setting"
            gridSnapOptions = ['0mm (disables grid snap)', '1mm (default)']
            answer2 = await ctx.bot.ui.getChoiceFromList(ctx, gridSnapOptions, userPrompt)
            print(compartmentNameData)
            if answer == "All of them":
                i = 0
                for meshBase in blueprintData["meshes"]:
                    if compartmentNameData[meshBase["vuid"]] != "Unnamed Structure":
                        if blueprintData["meshes"][i]["meshData"]["format"] != "freeform":
                            await ctx.send(await self.bot.error.retrieveCategorizedError(ctx, "blueprint"))
                            await ctx.send(
                                "Error: generated compartments cannot be imported into.  Convert your generated compartments to freeform and try again.")
                            return
                        compartmentData = blueprintData["meshes"][i]["meshData"]

                        url = "https://raw.githubusercontent.com/SprocketTools/SprocketBot/main/startup_files/BlankAddonStructure.json"
                        response = requests.get(url)
                        if response.status_code == 200:
                            addonStructureData = json.loads(response.text)
                            addonStructureData['guid'] = f"9f8a9d20-eb45-482e-b149-{random.random() * 100000000000}"
                            addonStructureData['name'] = compartmentNameData[meshBase["vuid"]]
                            addonStructureData['components'][0]['info']['mesh'] = compartmentData

                            if answer2 == gridSnapOptions[0]:
                                gridSnap = 0
                            if answer2 == gridSnapOptions[1]:
                                gridSnap = 1
                            addonStructureData['components'][0]['info']['mesh']['gridSize'] = gridSnap
                            stringOut = json.dumps(addonStructureData, indent=4)
                            data = io.BytesIO(stringOut.encode())
                            await ctx.send(file=discord.File(data, f'{compartmentNameData[meshBase["vuid"]]}.json'))
                        else:
                            await ctx.send(await self.bot.error.retrieveCategorizedError(ctx, "blueprint"))
                            await ctx.send(
                                "I was unable to download the base .json file needed to create the compartment.  Maybe the GitHub servers are down or something.")
                        i += 1
                await ctx.send("Place these models into `C:\Program Files (x86)\Steam\steamapps\common\Sprocket\Sprocket_Data\StreamingAssets\Parts` and reload the game for it to appear.")

            else:
                Vuid = structureVuidList[answer]
                i = 0
                for meshBase in blueprintData["meshes"]:
                    if meshBase["vuid"] == Vuid:
                        if blueprintData["meshes"][i]["meshData"]["format"] != "freeform":
                            await ctx.send(await self.bot.error.retrieveCategorizedError(ctx, "blueprint"))
                            await ctx.send("Error: generated compartments cannot be imported into.  Convert your generated compartments to freeform and try again.")
                            return
                        compartmentData = blueprintData["meshes"][i]["meshData"]

                        url = "https://raw.githubusercontent.com/SprocketTools/SprocketBot/main/startup_files/BlankAddonStructure.json"
                        response = requests.get(url)
                        if response.status_code == 200:
                            addonStructureData = json.loads(response.text)
                            addonStructureData['guid'] = f"9f8a9d20-eb45-482e-b149-{random.random()*100000000000}"
                            addonStructureData['name'] = answer
                            addonStructureData['components'][0]['info']['mesh'] = compartmentData


                            if answer2 == gridSnapOptions[0]:
                                gridSnap = 0
                            if answer2 == gridSnapOptions[1]:
                                gridSnap = 1
                            addonStructureData['components'][0]['info']['mesh']['gridSize'] = gridSnap
                            await ctx.send("## Done!")
                            #message-bound copy
                            stringOut = json.dumps(addonStructureData, indent=4)
                            data = io.BytesIO(stringOut.encode())
                            fileOut = discord.File(data, f'{answer}.json')
                            await ctx.send(file=fileOut)
                            # DM-bound copy
                            stringOut = json.dumps(addonStructureData, indent=4)
                            data = io.BytesIO(stringOut.encode())
                            fileOut = discord.File(data, f'{answer}.json')
                            await ctx.author.send(content=f"addon structure {answer}", file=fileOut)
                            await ctx.send("Place this model into `C:\Program Files (x86)\Steam\steamapps\common\Sprocket\Sprocket_Data\StreamingAssets\Parts` and reload the game for it to appear.")
                        else:
                            await ctx.send(await self.bot.error.retrieveCategorizedError(ctx, "blueprint"))
                            await ctx.send("I was unable to download the base .json file needed to create the compartment.  Maybe the GitHub servers are down or something.")

                    i += 1

    @commands.command(name="transplant", description="Transplant a compartment onto another tank.")
    async def transplant(self, ctx: commands.Context):
        serverID = (ctx.guild.id)
        try:
            channel = int([dict(row) for row in await self.bot.sql.databaseFetch(
                f'SELECT * FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
            await ctx.send(await self.bot.error.retrieveCategorizedError(ctx, "blueprint"))
            await ctx.send(
                f"Utility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
            return
        sourceFile = await textTools.getFileResponse(ctx, "Upload the first .blueprint that contains your compartment.  Note: unnamed structures will not be listed, so make sure your source compartment has a unique name.")
        targetFile = await textTools.getFileResponse(ctx,"Upload the second .blueprint that you wish to modify.  Note: your target structure will not be listed if it does not have a unique name.")

        blueprintData = json.loads(await sourceFile.read())
        structureList = []
        structureVuidList = {}
        compartmentData = {}
        compartmentNameData = {}
        tankName = blueprintData["header"]["name"]
        i = 0

        # get data for the first compartment
        for component in blueprintData["blueprints"]:
            if component["type"] == "structure":
                bmID = component["blueprint"]["bodyMeshVuid"]
                compartmentNameData[int(bmID)] = component["blueprint"]["name"]
                if blueprintData["blueprints"][i]["blueprint"]["name"] is None or len(
                        blueprintData["blueprints"][i]["blueprint"]["name"]) < 1:
                    blueprintData["blueprints"][i]["blueprint"]["name"] = f"This might be your hull? ({i})"
                    if random.random() < 0.005:
                        blueprintData["blueprints"][i]["blueprint"]["name"] = "Sprocket Chan"
                nameOut = blueprintData["blueprints"][i]["blueprint"]["name"]
                if nameOut not in structureList:
                    print(nameOut)
                    structureList.append(nameOut)
                    structureVuidList[blueprintData["blueprints"][i]["blueprint"]["name"]] = int(component["blueprint"]["bodyMeshVuid"])
            i += 1

        userPrompt = "Pick the name of the source compartment.  Note: unnamed structures are not listed."
        print(structureList)
        sourceCompartmentAnswer = await ctx.bot.ui.getChoiceFromList(ctx, structureList, userPrompt)

        i = 0
        Vuid = structureVuidList[sourceCompartmentAnswer]
        for meshBase in blueprintData["meshes"]:
            if meshBase["vuid"] == Vuid:
                if blueprintData["meshes"][i]["meshData"]["format"] != "freeform":
                    await ctx.send(await self.bot.error.retrieveError(ctx))
                    await ctx.send(
                        "Error: generated compartments cannot be imported into.  Convert your generated compartments to freeform and try again.")
                    return
                compartmentData = blueprintData["meshes"][i]["meshData"]
            i += 1

        # get data for the second compartment
        blueprintData = json.loads(await targetFile.read())
        structureList = []
        structureVuidList = {}
        compartmentNameData = {}
        i = 0
        for component in blueprintData["blueprints"]:
            if component["type"] == "structure":
                bmID = component["blueprint"]["bodyMeshVuid"]
                compartmentNameData[int(bmID)] = component["blueprint"]["name"]
                if blueprintData["blueprints"][i]["blueprint"]["name"] is None or len(
                        blueprintData["blueprints"][i]["blueprint"]["name"]) < 1:
                    blueprintData["blueprints"][i]["blueprint"]["name"] = f"This might be your hull? ({i})"
                    if random.random() < 0.005:
                        blueprintData["blueprints"][i]["blueprint"]["name"] = "Sprocket Chan"
                nameOut = blueprintData["blueprints"][i]["blueprint"]["name"]
                if nameOut not in structureList:
                    print(nameOut)
                    structureList.append(nameOut)
                    structureVuidList[blueprintData["blueprints"][i]["blueprint"]["name"]] = int(component["blueprint"]["bodyMeshVuid"])
            i += 1

        userPrompt = "Pick the name of the target compartment.  Note: unnamed structures are not listed."
        print(structureList)
        targetCompartmentAnswer = await ctx.bot.ui.getChoiceFromList(ctx, structureList, userPrompt)

        # get info on grid snap
        gridSnap = 1
        userPrompt = "Specify your desired grid snap setting for the resultant compartment"
        gridSnapOptions = ['0mm (disables grid snap)', '1mm (default)']
        gridSnapAnswer = await ctx.bot.ui.getChoiceFromList(ctx, gridSnapOptions, userPrompt)
        print(compartmentNameData)

        Vuid = structureVuidList[targetCompartmentAnswer]

        i = 0
        for meshBase in blueprintData["meshes"]:
            if meshBase["vuid"] == Vuid:
                if blueprintData["meshes"][i]["meshData"]["format"] != "freeform":
                    await ctx.send(await self.bot.error.retrieveError(ctx))
                    await ctx.send(
                        "Error: generated compartments cannot be imported into.  Convert your generated compartments to freeform and try again.")
                    return
                blueprintData["meshes"][i]["meshData"] = compartmentData

                if gridSnapAnswer == gridSnapOptions[0]:
                    gridSnap = 0
                if gridSnapAnswer == gridSnapOptions[1]:
                    gridSnap = 1
                blueprintData["meshes"][i]["meshData"]['gridSize'] = gridSnap
                await ctx.send("## Done!")
                stringOut = json.dumps(blueprintData, indent=4)
                data = io.BytesIO(stringOut.encode())
                await ctx.send(file=discord.File(data, f'{tankName}-transplanted.blueprint'))
                await ctx.send("Place this model into `%userprofile%\Documents\My Games\Sprocket\Factions\Default\Blueprints\Vehicles` and load the new tank.")
            i += 1

    @commands.command(name="drawFrameV2", description="Renders a 3D wireframe GIF of a vehicle blueprint.")
    async def drawFrameV2(self, ctx: commands.Context):
        await ctx.send("Beginning processing now. This may take a while...")
        for attachment in ctx.message.attachments:
            try:
                # --- 1. Data Preparation ---
                blueprintData = json.loads(await attachment.read())
                name = blueprintData["header"]["name"]

                if "0.2" in blueprintData["header"]["gameVersion"]:
                    blueprintDataSave = await blueprintFunctions.bakeGeometry210(self, attachment)
                else:
                    await ctx.send("This command only supports v0.2+ blueprints for rendering.")
                    return

                meshData = blueprintDataSave["meshes"][0]["meshData"]["mesh"]
                verticesList = meshData["vertices"]
                faceList = meshData["faces"]

                # Convert flat vertex list to a NumPy array of [x, y, z] coordinates
                if not verticesList:
                    await ctx.send("Could not find any vertices to render.")
                    return
                vertices = numpy.array(verticesList).reshape(-1, 3)
                vertices = vertices[:, [0, 2, 1]]

                # --- 2. Setup for Rendering Loop ---
                images = []
                iframes = 8  # Increase frames for a smoother GIF

                # Pre-calculate the model's bounds to keep the camera framing consistent
                x_min, x_max = vertices[:, 0].min(), vertices[:, 0].max()
                y_min, y_max = vertices[:, 1].min(), vertices[:, 1].max()
                z_min, z_max = vertices[:, 2].min(), vertices[:, 2].max()

                # Find the center and the largest dimension to create a cubic plot area
                center = numpy.array(
                    [numpy.mean([x_min, x_max]), numpy.mean([y_min, y_max]), numpy.mean([z_min, z_max])])
                max_range = numpy.array(
                    [x_max - x_min, y_max - y_min, z_max - z_min]).max() / 2.0 * 1.1  # Add 10% padding

                # --- 3. Rendering Loop ---
                for i in range(iframes):
                    # Create a Matplotlib Figure and a 3D subplot
                    fig = plt.figure(figsize=(8, 8), dpi=200)  # Control image size and resolution
                    ax = fig.add_subplot(111, projection='3d')

                    # Create a list of polygons from the vertex and face data for the mesh
                    polygons = [vertices[face['v']] for face in faceList]

                    # Add the mesh to the plot using Poly3DCollection
                    mesh_collection = Poly3DCollection(
                        polygons,
                        edgecolors=(0.8, 1.0, 1.0),  # Light cyan edges
                        facecolors=(0.1, 0.2, 0.3, 0.5),  # Semi-transparent dark blue faces
                        linewidths=0.5
                    )
                    ax.add_collection3d(mesh_collection)

                    # Set the camera's viewing angle for this frame
                    azim = (360 / iframes) * i  # Azimuthal angle (horizontal rotation)
                    elev = 15  # Elevation angle (vertical tilt)
                    ax.view_init(elev=elev, azim=azim)

                    # Set the plot limits to be a cube centered on the object
                    ax.set_xlim(center[0] - max_range, center[0] + max_range)
                    ax.set_ylim(center[1] - max_range, center[1] + max_range)
                    ax.set_zlim(center[2] - max_range, center[2] + max_range)

                    # Set a dark background and hide the grid/axes for a clean look
                    ax.set_facecolor((0.05, 0.05, 0.1))
                    ax.axis('off')

                    # Render the current frame to an in-memory buffer
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, facecolor=ax.get_facecolor())
                    plt.close(fig)  # IMPORTANT: Close the figure to free up memory

                    buf.seek(0)
                    pil_img = Image.open(buf)
                    images.append(pil_img)

                # --- 4. GIF Compilation (your existing code) ---
                if not images:
                    await ctx.send("Failed to generate any frames.")
                    return

                gif_buffer = io.BytesIO()
                images[0].save(
                    gif_buffer,
                    format='GIF',
                    save_all=True,
                    append_images=images[1:],
                    duration=450,  # milliseconds per frame
                    loop=0
                )
                gif_buffer.seek(0)

                imageOut = discord.File(gif_buffer, filename=f'{name}_render.gif')
                await ctx.send(file=imageOut)

            except Exception as e:
                await ctx.send(f"An error occurred during rendering: `{e}`")
                import traceback
                traceback.print_exc()  # For debugging


    @commands.command(name="drawFrame", description="merge compartment geometry into itself.")
    async def drawFrame(self, ctx: commands.Context):
        await ctx.send("Beginning processing now.  WARNING: this may take awhile.")
        for attachment in ctx.message.attachments:
            imageXtop = 0
            imageYtop = 0
            images = []
            rotat = 0
            iframes = 16
            while rotat < iframes*2:
                blueprintData = json.loads(await attachment.read())
                name = blueprintData["header"]["name"]
                version = 0.127
                if "0.2" in blueprintData["header"]["gameVersion"]:
                    #await ctx.send("Detected a 0.2 blueprint.")
                    blueprintDataSave = await blueprintFunctions.bakeGeometry200(ctx, attachment)
                else:
                    return
                blueprintData = blueprintDataSave
                meshData = blueprintData["meshes"][0]["meshData"]["mesh"]
                verticesList = meshData["vertices"]
                faceList = meshData["faces"]
                verticesXlist = []
                verticesYlist = []
                verticesZlist = []

                rotationX = 0.2*math.sin(math.pi*2*rotat/(iframes))
                rotationY = math.pi/iframes*2*rotat
                rotationZ = -0.2*math.cos(math.pi*2*rotat/(iframes))

                # image settings
                imageScale = 500
                imagePadding = 250
                lineThickness = 6


                angles = [-1 * rotationX, -1 * rotationY, -1 * rotationZ]
                ## rotate all the vertices
                pos = 0
                while pos < len(verticesList):
                    roundPoint = 6
                    vector = [verticesList[pos], verticesList[pos + 1], verticesList[pos + 2]]
                    # angles = [sourcePartRotZ, sourcePartRotY, -1*sourcePartRotX]
                    if vector[0] < 1000 and vector[1] < 1000 and vector[2] < 1000:
                        newVector = braveRotateVector(vector, angles)

                        # newVector = rotateVector(vector, angles)
                        verticesList[pos] = round(newVector[0], roundPoint)
                        verticesXlist.append(newVector[0])
                        verticesList[pos + 1] = round(newVector[1], roundPoint)
                        verticesYlist.append(newVector[1])
                        verticesList[pos + 2] = round(newVector[2], roundPoint)
                        verticesZlist.append(newVector[2])

                    pos += 3

                # print(verticesList)

                # conversion from 3D to 2D
                imageXlist = verticesZlist
                imageYlist = verticesYlist

                # scale up the points
                i = 0
                while i < len(imageXlist):
                    imageXlist[i] = imageXlist[i]*imageScale
                    imageYlist[i] = imageYlist[i]*imageScale
                    i += 1

                # imageXbottom = min(imageXlist)
                # imageXtop = max(imageXlist)
                # imageYbottom = min(imageYlist)
                # imageYtop = max(imageYlist)
                if imageXtop == 0:
                    imageXbottom = min(imageXlist)
                    imageXtop = max(imageXlist)
                    imageYbottom = min(imageYlist)
                    imageYtop = max(imageYlist)
                # center the points
                i = 0
                while i < len(imageXlist):
                    imageXlist[i] = (imageXlist[i] - imageXbottom + imagePadding)
                    imageYlist[i] = (imageYlist[i] - imageYbottom + imagePadding)
                    i += 1



                # print(min(imageXlist))
                # print(min(imageYlist))
                # print(imageXlist)
                # print(imageYlist)


                imageX = imageXtop - imageXbottom + 2*imagePadding
                imageY = imageYtop - imageYbottom + 2*imagePadding
                # print(imageXtop)
                # print(imageYtop)

                # flip the points
                i = 0
                while i < len(imageXlist):
                    imageXlist[i] = imageX - imageXlist[i] - imagePadding/3
                    imageYlist[i] = imageY - imageYlist[i] - imagePadding/3
                    i += 1
                # create a list of lines to plug into an image program
                startingCoords = []
                endingCoords = []
                for face in faceList:
                    faceData = face["v"]
                    i = 0
                    while i < len(faceData):
                        startingCoords.append([imageXlist[faceData[i]], imageYlist[faceData[i]]])
                        endingCoords.append([imageXlist[faceData[(i + 1) % len(faceData)]], imageYlist[faceData[(i + 1) % len(faceData)]]])
                        i += 1


                # print(f"X top is {imageXtop}, bottom is {imageXbottom}.  Y top is {imageYtop}, bottom is {imageYbottom}")

                # initialize the image
                imageBase = numpy.zeros((int(imageY), int(imageX), 3), numpy.uint8)
                i = 0
                while i < len(startingCoords):
                    cv.line(imageBase, (round(startingCoords[i][0]), round(startingCoords[i][1])), (round(endingCoords[i][0]), round(endingCoords[i][1])), (100, 200, 255), lineThickness)
                    i += 1

                # send the image
                # bytes_io = io.BytesIO()
                imageBase = cv.resize(imageBase, (int(imageX), int(imageY)))
                img_rgb = cv.cvtColor(imageBase, cv.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)
                images.append(pil_img)


                # print(f"Frame {i} shape: {imageBase.shape}, dtype: {imageBase.dtype}")
                # img_encode = cv.imencode('.png', imageBase)[1]
                # # data_encode = numpy.array(img_encode)
                # # byte_encode = data_encode.tobytes()
                # # byteImage = io.BytesIO(byte_encode)
                # images.append(img_encode)
                rotat += 2

            # frames = [Image.open(image) for image in images]
            # frame_one = frames
            # for frame in images:
            #     img = Image.open(frame)
            #     images.append(img.convert('RGBA'))

            pil_frames = images

            # Save to in-memory BytesIO buffer
            gif_buffer = io.BytesIO()
            pil_frames[0].save(
                gif_buffer,
                format='GIF',
                save_all=True,
                append_images=pil_frames[1:],
                duration=750,  # milliseconds per frame
                loop=0
            )
            gif_buffer.seek(0)

            #cv.imwrite(f"{name}Edited.png", imageBase)
            #byteImage = io.BytesIO(byte_encode)
            imageOut = discord.File(gif_buffer, filename='image.gif')
            await ctx.send(file=imageOut)

            # bytes_io = io.BytesIO()
            # cv.imencode('.png', imageBase)[1].tofile(bytes_io)
            # file = discord.File(bytes_io, 'image_out.png')
            # await ctx.send(file=file)

            # byte_io = io.BytesIO()
            # imageBase.save(byte_io, format='PNG')
            # byte_io.seek(0)
            # file = discord.File(byte_io, filename=f'edited_image.png')
            # await ctx.send(file=file)

















            # stringOut = json.dumps(blueprintDataSave, indent=4)
            # data = io.BytesIO(stringOut.encode())
            # await ctx.send(file=discord.File(data, f'{name}(merged).blueprint'))

    async def getPowertrainStats(attachment):
        blueprintData = json.loads(await attachment.read())
        name = blueprintData["header"]["name"]
        tankName = blueprintData["header"]["name"]
        era = blueprintData["header"]["era"].lower()
        weight = float(blueprintData["header"]["mass"])/1000
        climbAngle = numpy.radians(45)
        gearCount = 8
        # eraBaseRPM is the ideal RPM when displacement is 1L/cyl
        eraPowerMod = 1
        flatnessScalar = 0.6
        eraResistance = 1
        eraBaseRPM = 4060
        sprocketDiameter = 0.6
        initialGear = 6.0
        finalGear = 0.5
        finalGearAdjustment = 1
        #dispPerCyl = 0
        if era == "midwar":
            eraPowerMod = 0.92
            eraResistance = 1.25
            eraBaseRPM = 3800
        if era == "earlywar":
            eraPowerMod = 0.72
            eraResistance = 1.5
            eraBaseRPM = 3100
        if era == "interwar":
            eraPowerMod = 0.586
            eraResistance = 3
            eraBaseRPM = 2700
            gearCount = 6
        if era == "wwi":
            eraPowerMod = 0.23
            eraResistance = 4
            eraBaseRPM = 1500
            gearCount = 3
            finalGearAdjustment = 0.95

        x = 0
        for iteration in blueprintData["blueprints"]:
            partName = blueprintData["blueprints"][x]["id"]
            partString = blueprintData["blueprints"][x]["data"]

            partString.replace("\\", "")
            partInfo = json.loads(partString)
            clonePartInfo = copy.deepcopy(partInfo)
            if partName == "ENG":
                name = partInfo["name"]
                displacement = round(float(partInfo["cylinders"]) * float(partInfo["cylinderDisplacement"]), 2)
                cylinders = int(partInfo["cylinders"])
                dispPerCyl = float(partInfo["cylinderDisplacement"])
                partInfo["targetMaxRPM"] = eraBaseRPM*(dispPerCyl**-0.3)
                maxRPM = int(partInfo["targetMaxRPM"])
            if partName == "TRK":
                sprocketDiameter = partInfo["wheels"][0]["diameter"]
                print(sprocketDiameter)
            x += 1
        idealRPM = eraBaseRPM*(dispPerCyl**-0.3)/1.01
        horsepower = 40*(dispPerCyl**0.7)*cylinders*eraPowerMod
        topSpeed = (13.33 * (horsepower ** 0.5) ) / ( (eraResistance ** 0.8) * ((weight) ** 0.5) )
        HPT = round(horsepower/weight, 2)
        configuration = {
            "HP": horsepower,
            "HPT": HPT,
            "topSpeed": topSpeed
        }
        return configuration


    async def drawCompartment(ctx: commands.Context, attachment):

        blueprintData = json.loads(await attachment.read())


    async def tunePowertrain200(ctx: commands.Context, attachment):
        if 1 > 0:
            await ctx.send("## This command has been retired for 0.2 tanks\nIt is recommended to use the [SprocketTools gear calculator](https://sprockettools.github.io/TopGearCalculator.html) instead.")
            return
        blueprintData = json.loads(await attachment.read())
        name = blueprintData["header"]["name"]
        tankName = blueprintData["header"]["name"]
        era = blueprintData["header"]["era"].lower()
        weight = float(blueprintData["header"]["mass"]) / 1000
        climbAngle = numpy.radians(60)
        gearCount = 8
        dispPerCyl = 1
        cylinders = 1
        # eraBaseRPM is the ideal RPM when displacement is 1L/cyl
        eraPowerMod = 1
        flatnessScalar = 0.8
        eraResistance = 0.7
        eraBaseRPM = 4000
        sprocketDiameter = 0.6
        initialGear = 6.0
        finalGear = 0.5
        finalGearAdjustment = 1
        # dispPerCyl = 0
        if era == "midwar":
            eraPowerMod = 0.92
            eraResistance = 1.25
            eraBaseRPM = 3800
            gearCount = 6
        if era == "earlywar":
            eraPowerMod = 0.72
            eraResistance = 1.5
            eraBaseRPM = 3100
            gearCount = 6
        if era == "interwar":
            eraPowerMod = 0.586
            eraResistance = 3
            eraBaseRPM = 2700
            gearCount = 4
        if era == "wwi":
            eraPowerMod = 0.23
            eraResistance = 4
            eraBaseRPM = 1500
            gearCount = 3
            finalGearAdjustment = 0.95

        Prompt = "What profile do you want to use?"
        optionList = ["Top speed", "Rough terrain", "Custom"]
        profileChoice = await ctx.bot.ui.getChoiceFromList(ctx, optionList, Prompt)

        if profileChoice == "Rough terrain":
            eraPowerMod = eraPowerMod * 0.8
            climbAngle = 1

        x = 0
        for partInfo in blueprintData["blueprints"]:
            validDiameter = False
            partID = partInfo["type"]
            if partID == "engine":
                cylinders = int(partInfo["blueprint"]["cylinders"])
                dispPerCyl = float(partInfo["blueprint"]["cylinderDisplacement"])
                partInfo["targetMaxRPM"] = eraBaseRPM * (dispPerCyl ** -0.3)
            if partID == "trackWheel" and validDiameter == False:
                validDiameter = True
                sprocketDiameter = partInfo["blueprint"]["diameter"]
            if partID == "transmission":
                gearCount = len(blueprintData["blueprints"][x]["blueprint"]["d"])
            x += 1

        if profileChoice == "Custom":
            try:
                gearCount = int(await textTools.getResponse(ctx, f"How many gears do you want to use?  For this vehicle era, it's recommended to use {gearCount} gears."))
            except Exception:
                await ctx.send("This number was invalid!  Using the recommended value...")

            climbAngle = numpy.radians(int(await textTools.getResponse(ctx, "Specify the desired climbing angle in degrees.  Note: bigger climbing angles also improve your neutral steer setting.  \nRecommended values are between 45 and 75.")))
            if climbAngle > 2 or climbAngle < 0.05:
                await ctx.send("This number was invalid!  Using the recommended value...")
                climbAngle = numpy.radians(60)



        # start the math
        idealRPM = eraBaseRPM * (dispPerCyl ** -0.3) / 1.01
        horsepower = 40 * (dispPerCyl ** 0.7) * cylinders * eraPowerMod
        topSpeed = (13.33 * (horsepower ** 0.5)) / ((eraResistance ** 0.8) * ((weight) ** 0.5))

        if profileChoice == "Custom":
            await ctx.send(f"Your vehicle's top speed is estimated to be {round(topSpeed, 1)}km/h.  Specify your intended top speed, or just say 'skip'.\n- A lower top speed will improve acceleration.")
            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            try:
                msg = await ctx.bot.wait_for('message', check=check, timeout=60.0)
                topSpeed = int(msg.content)
            except Exception:
                pass

            await ctx.send(f"[Advanced] What curve modifier do you wish to use?  Recommended values are between 0.5 and 1.5, while the default is 0.8.\n- A smaller number will improve acceleration near the final gear\n- A larger number will improve acceleration near the first gear")

            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            try:
                msg = await ctx.bot.wait_for('message', check=check, timeout=60.0)
                flatnessScalar = round(float(msg.content), 3)
            except Exception:
                pass

        Torque = 9.5492 * 746 * horsepower / idealRPM
        initialGear = (11 * ((sprocketDiameter / 2) * (weight * 1000) * 9.81 * climbAngle) / Torque) / 100
        finalGear = round(58 * numpy.pi * idealRPM * sprocketDiameter * finalGearAdjustment / (10000 * topSpeed), 3)
        print(topSpeed)
        import io
        await ctx.send(f"Your top speed should be about {round(topSpeed)} km/h. \nSet your upshift RPM to {int(idealRPM)}RPM and your maximum RPM to the highest setting available.\nEstimated max horsepower is {round(horsepower)}HP\n\nDownload the .blueprint attached below to get your updated transmission!")

        gearCountM1 = gearCount - 1
        idealFlatness = ((initialGear / finalGear) ** (1 / (gearCountM1)) - 1) * 100
        flatness = idealFlatness * flatnessScalar
        Bvalue = (initialGear / (finalGear * (1 + flatness / 100) ** (gearCountM1))) ** (
                    1 / (((gearCountM1) ** 2 + (gearCountM1)) / 2))
        transmissionGears = [initialGear]
        x = 1
        transmissionGears[0] = round(initialGear, 2)
        while x < gearCount:
            transmissionGears.append(
                round(float(transmissionGears[x - 1]) / ((1 + (flatness / 100)) * (Bvalue ** (gearCount - x))), 3))
            x += 1
        x = 0
        blueprintData["header"]["name"] = f'{tankName}-tuned'
        for partInfo in blueprintData["blueprints"]:
            partID = partInfo["id"]
            print(partID)
            if partID == 26:
                blueprintData["blueprints"][x]["blueprint"]["d"] = list(transmissionGears)
                blueprintData["blueprints"][x]["blueprint"]["r"] = list(transmissionGears[0:2])
            if partID == 12:
                blueprintData["blueprints"][x]["blueprint"]["targetMaxRPM"] = int(idealRPM)
                blueprintData["blueprints"][x]["blueprint"]["targetMinRPM"] = int(idealRPM/2)
            x += 1

        stringOut = json.dumps(blueprintData, indent=4)
        data = io.BytesIO(stringOut.encode())
        await ctx.send(file=discord.File(data, f'{tankName}-tuned.blueprint'))
    async def tunePowertrain127(ctx: commands.Context, attachment):
        blueprintData = json.loads(await attachment.read())
        name = blueprintData["header"]["name"]
        tankName = blueprintData["header"]["name"]
        era = blueprintData["header"]["era"].lower()
        weight = float(blueprintData["header"]["mass"]) / 1000
        climbAngle = numpy.radians(45)
        gearCount = 10
        # eraBaseRPM is the ideal RPM when displacement is 1L/cyl
        eraPowerMod = 1
        flatnessScalar = 0.6
        eraResistance = 1
        eraBaseRPM = 4000
        sprocketDiameter = 0.6
        initialGear = 6.0
        finalGear = 0.5
        finalGearAdjustment = 1
        # dispPerCyl = 0
        if era == "midwar":
            eraPowerMod = 0.92
            eraResistance = 1.25
            eraBaseRPM = 3800
            gearCount = 9
        if era == "earlywar":
            eraPowerMod = 0.72
            eraResistance = 1.5
            eraBaseRPM = 3100
            gearCount = 8
        if era == "interwar":
            eraPowerMod = 0.586
            eraResistance = 3
            eraBaseRPM = 2700
            gearCount = 6
        if era == "wwi":
            eraPowerMod = 0.23
            eraResistance = 4
            eraBaseRPM = 1500
            gearCount = 3
            finalGearAdjustment = 0.95

        x = 0
        for iteration in blueprintData["blueprints"]:
            partName = blueprintData["blueprints"][x]["id"]
            partString = blueprintData["blueprints"][x]["data"]

            partString.replace("\\", "")
            partInfo = json.loads(partString)
            clonePartInfo = copy.deepcopy(partInfo)
            if partName == "ENG":
                name = partInfo["name"]
                displacement = round(float(partInfo["cylinders"]) * float(partInfo["cylinderDisplacement"]), 2)
                cylinders = int(partInfo["cylinders"])
                dispPerCyl = float(partInfo["cylinderDisplacement"])
                partInfo["targetMaxRPM"] = eraBaseRPM * (dispPerCyl ** -0.3)
                maxRPM = int(partInfo["targetMaxRPM"])
            if partName == "TRK":
                sprocketDiameter = partInfo["wheels"][0]["diameter"]
                print(sprocketDiameter)

            x += 1
        idealRPM = eraBaseRPM * (dispPerCyl ** -0.3) / 1.01
        horsepower = 40 * (dispPerCyl ** 0.7) * cylinders * eraPowerMod
        topSpeed = (13.33 * (horsepower ** 0.5)) / ((eraResistance ** 0.8) * ((weight) ** 0.5))
        Torque = 9.5492 * 746 * horsepower / idealRPM
        initialGear = (11 * ((sprocketDiameter / 2) * (weight * 1000) * 9.81 * climbAngle) / Torque) / 100
        finalGear = round(58 * numpy.pi * idealRPM * sprocketDiameter * finalGearAdjustment / (10000 * topSpeed), 3)
        print(topSpeed)
        import io
        await ctx.send(f"Your top speed should be about {round(topSpeed)} km/h. \nSet your upshift RPM to {int(idealRPM)}RPM and your maximum RPM to the highest setting available.\nEstimated max horsepower is {round(horsepower)}HP\n\nDownload the .blueprint attached below to get your updated transmission!")

        gearCountM1 = gearCount - 1
        idealFlatness = ((initialGear / finalGear) ** (1 / (gearCountM1)) - 1) * 100
        flatness = idealFlatness * flatnessScalar
        Bvalue = (initialGear / (finalGear * (1 + flatness / 100) ** (gearCountM1))) ** (
                    1 / (((gearCountM1) ** 2 + (gearCountM1)) / 2))
        transmissionGears = [initialGear]
        x = 1
        transmissionGears[0] = round(initialGear, 2)
        while x < gearCount:
            transmissionGears.append(
                round(float(transmissionGears[x - 1]) / ((1 + (flatness / 100)) * (Bvalue ** (gearCount - x))), 3))
            x += 1
        x = 0
        for iteration in blueprintData["blueprints"]:
            partName = blueprintData["blueprints"][x]["id"]
            partString = blueprintData["blueprints"][x]["data"]
            partString.replace("\\", "")
            partInfo = json.loads(partString)
            clonePartInfo = copy.deepcopy(partInfo)
            if partName == "TSN":
                partInfo["d"] = list(transmissionGears)
                partInfo["r"] = list(transmissionGears)
            blueprintData["blueprints"][x]["data"] = json.dumps(partInfo)
            x += 1
        stringOut = json.dumps(blueprintData, indent=4)
        data = io.BytesIO(stringOut.encode())
        await ctx.send(file=discord.File(data, f'{tankName}-tuned.blueprint'))

    @commands.command(name="tunePowertrain", description="merge compartment geometry into itself.")
    async def tunePowertrain(self, ctx: commands.Context):
        if not ctx.message.attachments:
            await ctx.reply(
                "**-tunePowertrain** configures your engine's transmission to use the most optimal setup for your tank!\nTo use this command, attach one or more .blueprint files when running the **-tunePowertrain** command.\nNote: it is recommended to use twin transmissions on all vehicle builds, due to the tendency of Sprocket AI to have terrible clutch braking skills.\n# <:caatt:1151402846202376212>")

        serverID = (ctx.guild.id)
        try:
            channel = int([dict(row) for row in await self.bot.sql.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
                error = await self.bot.error.retrieveError(ctx)
                await ctx.send(f"{error}\n\nUtility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
                return

        for attachment in ctx.message.attachments:
            print(attachment.content_type)
            try:
                if "image" in attachment.content_type:
                    errorStr = await self.bot.error.retrieveError(ctx)
                    await ctx.reply(errorStr)
                    #await ctx.reply("Ah yes, I love eating random pictures instead of working with tank blueprints *like I was meant to do*! \n\n# <:caatt:1151402846202376212>")
                    return
            except Exception:
                pass
            blueprintData = json.loads(await attachment.read())
            version = 0.127
            if "0.2" in blueprintData["header"]["gameVersion"]:
                await ctx.send("Detected a 0.2 blueprint.  Beginning processing now.")
                await blueprintFunctions.tunePowertrain200(ctx, attachment)
            elif float(blueprintData["header"]["gameVersion"]) < 0.128:
                await ctx.send(f"Detected a legacy {blueprintData['header']['gameVersion']} blueprint.  Starting processing now.")
                await blueprintFunctions.tunePowertrain127(ctx, attachment)


    async def getBattleRating(config):
        armorBTRating = float(config["armorVolume"])*1000
        cannonBTRating = float(config["maxCaliber"])*float(config["maxPropellant"])
        mobilityBTRating = float(config["HPT"])*float(config["litersPerTon"])
        return armorBTRating, cannonBTRating, mobilityBTRating





    async def runBlueprintCheck(ctx: commands.Context, attachment, config):
        # importing data
        print(config)
        contestName = config["contestname"]
        era = config["era"]
        gameVersion = round(float(config["gameversion"]), 5)
        enforceGameVersion = config["enforcegameversion"]
        errorTolerance = config["errortolerance"]
        weightLimit = config["weightlimit"]
        crewMaxSpace = config["crewmaxspace"]
        crewMinSpace = config["crewminspace"]
        crewMin = config["crewmin"]
        crewMax = config["crewmax"]
        turretRadiusMin = config["turretradiusmin"]
        allowGCM = config["allowgcm"]
        GCMratioMin = config["gcmratiomin"]
        GCMtorqueMax = config["gcmtorquemax"]
        hullHeightMin = config["hullheightmin"]
        hullWidthMax = config["hullwidthmax"]
        torsionBarLengthMin = config["torsionbarlengthmin"]
        useDynamicTBlength = config["usedynamictblength"]
        allowHVSS = config["allowhvss"]
        beltWidthMin = config["beltwidthmin"]
        requireGroundPressure = config["requiregroundpressure"]
        groundPressureMax = config["groundpressuremax"]
        litersPerDisplacement = config["litersperdisplacement"]
        litersPerTon = config["litersperton"]
        caliberLimit = config["caliberlimit"]
        propellantLimit = config["propellantlimit"]
        boreLimit = config["borelimit"]
        shellLimit = config["shelllimit"]
        armorMin = config["armormin"]
        ATsafeMin = config["atsafemin"]
        armorMax = config["armormax"]

        # declaring initial variables and opening data
        report = ""
        blueprintData = json.loads(await attachment.read())
        errorCount = 0
        GCMcount = 0
        weight = float(blueprintData["header"]["mass"])/1000
        tankName = blueprintData["header"]["name"]
        tankName = await textTools.sanitize(tankName)
        tankEra = blueprintData["header"]["era"]
        overallTankWidth = 0
        maxArmorOverall = 0 # this gets increased over time
        crewCount = 0
        turretCount = 0
        displacement = 1
        fuelTankSize = 0.0
        gunCount = 0
        maxCaliber = 0
        maxPropellant = 0
        maxBore = 0
        maxShell = 0
        minArmor = 0
        armorVolume = 0.0
        crewReport = "Crew information: \n"
        suspensionType = "torsion bar"

        fileGameVersion = float(blueprintData["header"]["gameVersion"])
        if fileGameVersion != gameVersion and enforceGameVersion == True:
            #report = await textTools.addLine(report, )
            report = await textTools.addLine(report, f"This vehicle was made in {fileGameVersion}, while it is required to be in {fileGameVersion}.  Please update your game and then readjust your tank to fit the new version.")
            errorCount += 1
        if fileGameVersion != gameVersion and enforceGameVersion == False:
            report = await textTools.addLine(report, f"Warning! This vehicle was made in {fileGameVersion}, while it should be made in {gameVersion}.  Check with a {contestName} host or manager to ensure this is acceptable.")
        report = await textTools.addLine(report, "This tank was made in Sprocket version " + blueprintData["header"]["gameVersion"] + "\nVehicle weight: " + str(weight) + " tons.")
        if era.lower() != tankEra.lower():
            report = await textTools.addLine(report,f"This vehicle was made in the {tankEra} period, but needs to be sent as a {era} tank.  Please update your vehicle to use the proper era.")
            errorCount += 1
        if weight > weightLimit + 0.01:
            errorCount += 1
            report = await textTools.addLine(report,f"This vehicle is overweight!  Please reduce its weight to no more than {weightLimit}T and resend it.")

        x = 0
        for iteration in blueprintData["ext"]:
            partName = blueprintData["ext"][x]["REF"]
            partInfo = blueprintData["ext"][x]["DAT"]
            #partString.replace("\\", "")
            #partInfo = json.loads(partString)
            try:
                userLimit = json.loads(partInfo[1]["data"])
                thickness = userLimit["thickness"][0]
                #print(json.dumps(userLimit, indent=4))
                print(thickness)
                #except Exception:
                #pass
                if thickness > armorMax:
                    errorCount += 1
                    report = await textTools.addLine(report,f"This vehicle has mantlet face armor above the {armorMax}mm armor limit!  Please resend with a corrected version.")
                if thickness < minArmor:
                    minArmor = thickness
            except Exception:
                pass
            # print(partInfo)
            x += 1

        x = 0
        for iteration in blueprintData["blueprints"]:
            partName = blueprintData["blueprints"][x]["id"]
            partString = blueprintData["blueprints"][x]["data"]
            partString.replace("\\", "")
            partInfo = json.loads(partString)
            if partName == "CRW":
                crewSpot = 0
                for crew in partInfo["seats"]:
                    crewSpace = float(crew["spaceAlloc"])
                    if crewSpace > crewMaxSpace or crewSpace < crewMinSpace:
                        report = await textTools.addLine(report, f"This vehicle has crew outside of {contestName}'s limits, and cannot be accepted until this is fixed.")
                        errorCount += 1
                    crewCount += 1
                    crewSpot += 1
                    crewStats = f"Crew #{crewSpot}: {crew['spaceAlloc']}m of space, roles: {crew['roles']} \n"
                    crewReport = crewReport + crewStats
                if crewCount < crewMin:
                    report = await textTools.addLine(report,f"This vehicle needs to have at least {crewMin} crew members, but only has {crewCount} crew.")
                    errorCount += 1
                if crewCount > crewMax:
                    report = await textTools.addLine(report,f"This vehicle needs to have at most {crewMax} crew members, but it has {crewCount} crew.")
                    errorCount += 1
                print(crewReport)


            if partName == "CNN":
                gunCount += 1
                for cannon in partInfo["blueprints"]:
                    caliber = int(cannon["caliber"])
                    if caliber > maxCaliber:
                        maxCaliber = caliber
                    propellant = int(cannon["breechLength"])
                    if propellant > maxPropellant:
                        maxPropellant = propellant
                    calculatedShell = (3 * caliber) + propellant
                    calculatedBore = calculatedShell / 1000
                    errorCount += 1
                    for segment in partInfo["blueprints"][0]["segments"]:
                        calculatedBore += float(segment['len'])
                    if calculatedShell > shellLimit:
                        report = await textTools.addLine(report,
                            f"The \"{cannon['name']}\" is invalid!  This cannon uses a {calculatedShell}mm shell, while the limit for shell length is {shellLimit}mm.")
                    if calculatedBore > boreLimit:
                        report = await textTools.addLine(report,
                            f"The \"{cannon['name']}\" is invalid!  This cannon uses a {calculatedBore}m bore length, while the limit is {boreLimit}m.")
                    if propellant > propellantLimit:
                        report = await textTools.addLine(report,
                            f"The \"{cannon['name']}\" is invalid!  This cannon uses {propellant}mm of propellant, while the limit is {propellantLimit}mm.")
                    if caliber > caliberLimit:
                        report = await textTools.addLine(report,
                            f"The \"{cannon['name']}\" is invalid!  This cannon is {caliber}mm, while the caliber limit is {caliberLimit}mm.")
                    else:
                        report = await textTools.addLine(report,
                            f"\"{cannon['name']}\": {caliber}x{calculatedShell}mm with a {calculatedBore}m bore length.")
                        errorCount += -1
                    if calculatedBore > maxBore:
                        maxBore = calculatedBore
                    if calculatedShell > maxShell:
                        maxShell = calculatedShell

            if partName == "Compartment" and partInfo["name"] != "US Tanker Sitting Angled 1 (Zheifu Variant)":
                name = partInfo["name"]
                armorVolume += float(partInfo["armourVolume"])
                # displacement = float(partInfo["cylinders"])*float(partInfo["cylinderDisplacement"])
                # print(country)
                tooThinPlates = 0
                tooThickPlates = 0
                ATpronePlates = 0
                if partInfo["genID"] == "VSH":
                    width = float(partInfo["genData"]["shape"][1]) + 2 * float(partInfo["genData"]["shape"][6])
                    # print(str(width) + " aaaaaaaaaaaaaaaaaaaaa")
                    for thickness in partInfo["genData"]["armour"]:
                        # print(thickness)
                        if thickness < armorMin:
                            tooThinPlates += 1
                        if thickness > armorMax:
                            tooThickPlates += 1
                        if thickness > maxArmorOverall:
                            maxArmorOverall = thickness
                else:
                    # print(len(partInfo["compartment"]["points"]))
                    tooThinPlates = 0
                    tooThickPlates = 0
                    for thickness in partInfo["compartment"]["thicknessMap"]:
                        # print(thickness)
                        if thickness < armorMin:
                            tooThinPlates += 1
                        if thickness < ATsafeMin:
                            ATpronePlates += 1
                        if thickness > armorMax:
                            tooThickPlates += 1
                        if thickness > maxArmorOverall:
                            maxArmorOverall = thickness
                        if thickness < minArmor:
                            minArmor = thickness
                    xmin = 0
                    ymin = 0
                    zmin = 0
                    xmax = 0
                    ymax = 0
                    zmax = 0
                    min = [0, 0, 0]
                    max = [0, 0, 0]
                    if partInfo["ID"] == 0:
                        alternator = 0
                        for point in partInfo["compartment"]["points"]:
                            if alternator == 3:
                                alternator = 0
                            if point > max[alternator]:
                                max[alternator] = point
                            if point < min[alternator]:
                                min[alternator] = point
                            alternator += 1
                        # print(f"max {max[2]}   min {min[2]}")
                        height = max[1] - min[1]
                        width = max[0] - min[0]
                        hullLength = max[2] - min[2]
                        if width > overallTankWidth:
                            overallTankWidth = width
                        if height < hullHeightMin:
                            report = await textTools.addLine(report, f"{name} is {round(height, 2)} meters tall.  This won't fit any crew.")
                            errorCount += 1
                        if width > hullWidthMax:
                            report = await textTools.addLine(report,
                                f"{name} is {round(width, 2)} meters wide.  This is wider than the {hullWidthMax} meter limit.")
                            errorCount += 1
                    else:
                        ringArmor = partInfo["turret"]["ringArmour"]
                        basketVolume = partInfo["turret"]["basketVolume"]
                        torque = partInfo["turret"]["traverse"]["torque"]
                        ratio = partInfo["turret"]["traverse"]["ratio"]
                        ringRadius = float(partInfo["turret"]["radius"])
                        if ringRadius >= turretRadiusMin:
                            turretCount += 1
                        if ringRadius > overallTankWidth:
                            overallTankWidth = ringRadius
                        isGCM = False
                        if abs(int(partInfo["rot"][2])) > 20 and ringRadius >= turretRadiusMin:
                            isGCM = True
                            GCMcount += 1
                            if allowGCM == False:
                                report = await textTools.addLine(report, f"GCMs (including compartment \"{name}\") are not allowed in this contest.")
                                errorCount += 1
                            # custom mantlet checks
                            if torque > GCMtorqueMax:
                                errorCount += 1
                                report = await textTools.addLine(report, f"GCM \"{name}\" uses a torque setting above the {GCMtorqueMax}N limit!")
                            if ratio < GCMratioMin:
                                errorCount += 1
                                report = await textTools.addLine(report, f"GCM \"{name}\" has a traverse ratio below the required minimum ratio of {GCMtorqueMax}!")
                        if ringArmor < armorMin:
                            report = await textTools.addLine(report, f"{name}'s turret ring is below the 15mm armor requirement!")
                            errorCount += 1
                        if ringArmor < ATsafeMin:
                            ATpronePlates += 1
                        if ringArmor < minArmor:
                            minArmor = ringArmor
                        if ringArmor > maxArmorOverall:
                            maxArmorOverall = ringArmor
                        if basketVolume < 0 or basketVolume > 5:
                            report = await textTools.addLine(report,
                                f"{name} has been file edited and cannot be accepted.  Reason: turret volume is invalid.")
                            errorCount += 1
                        if float(ringRadius) <= turretRadiusMin and isGCM == False:
                            report = await textTools.addLine(report,
                                f"Warning: {name}'s turret ring is not wide enough to fit crew.  Increase the turret ring diameter if necessary.")
                        if ATpronePlates > 1:
                            report = await textTools.addLine(report, f"Warning: this vehicle is prone to infantry rifles.")


                if tooThickPlates > 0 or tooThinPlates > 0:
                    report = await textTools.addLine(report,
                        f"{name} has {tooThickPlates} armor plates exceeding the {armorMax}mm armor limit, and {tooThinPlates} armor plates below the minimum {armorMin}mm requirement.")
                    errorCount += 1

            if partName == "FLT":
                requiredFLT = round(displacement*litersPerDisplacement * (1 + (litersPerTon*weight)), 2)
                fuelTankSize = int(partInfo["L"])
                if partInfo["L"] < requiredFLT:
                    report = await textTools.addLine(report,f"Your internal fuel tank has {partInfo['L']}L of fuel, but needs {requiredFLT}L of fuel in order to perform adequately.")
                    errorCount += 1

            if partName == "TRK":
                separation = float(partInfo["separation"])
                trackWidthTot = 0.002 * float(partInfo["belt"]["x"])
                trackSystemWidth = separation + trackWidthTot + 0.2
                beltWidth = int(partInfo["belt"]["x"])
                sprocketIndex = 0
                idlerIndex = 1
                # Ground Pressure
                if partInfo["frontalTransmission"] == True:
                    sprocketIndex = 0
                    idlerIndex = 1

                trackSystemLength = float(partInfo["length"])
                sprocketForward = float(partInfo["wheels"][sprocketIndex]["zOffset"])
                idlerForward = float(partInfo["wheels"][idlerIndex]["zOffset"])
                roadwheelForward = float(partInfo["wheels"][2]["zOffset"])
                sprocketDiameter = float(partInfo["wheels"][sprocketIndex]["diameter"])
                idlerDiameter = float(partInfo["wheels"][idlerIndex]["diameter"])
                roadwheelDiameter = float(partInfo["wheels"][2]["diameter"])
                roadwheelSpacing = float(partInfo["roadSpacing"])
                if partInfo["frontalTransmission"] == True:
                    sprocketForward = -1*float(partInfo["wheels"][sprocketIndex]["zOffset"])
                    # await ctx.send("frontal transmission detected!")
                    #if sprocketForward > 0:
                    #    sprocketForward = 0
                else:
                    idlerForward = -1 * float(partInfo["wheels"][idlerIndex]["zOffset"])
                    # if idlerForward > 0:
                    #     idlerForward = 0

                Mgcl = trackSystemLength - idlerForward - sprocketForward - (idlerDiameter + sprocketDiameter)/2 - roadwheelDiameter - roadwheelForward
                if trackSystemLength > hullLength:
                    hullLength = trackSystemLength
                # await ctx.send(f"MGCL: {Mgcl}")
                roadwheelCount = ((Mgcl + roadwheelSpacing + roadwheelDiameter)/(roadwheelDiameter+roadwheelSpacing))
                # await ctx.send(f"Roadwheel Count: {roadwheelCount}")
                roadwheelCount = int(roadwheelCount)
                realContactLength = (roadwheelCount - 1)*(roadwheelDiameter+roadwheelSpacing)
                # await ctx.send(f"Real™️: {realContactLength}")
                surfaceAreaCM = (realContactLength * 100) * (beltWidth / 10) * 2
                groundPressure = weight*1000 / surfaceAreaCM
                # await ctx.send(f"Ground pressure: {groundPressure}kg/cm²")

                if groundPressure > groundPressureMax and requireGroundPressure == True:
                    report = await textTools.addLine(report, f"Your track ground pressure is {round(groundPressure, 2)}kg/cm², but cannot exceed {groundPressureMax}kg/cm².  Increase your track contact area with the ground, or lighten your vehicle to improve ground pressure.")
                    errorCount += 1

                print(partInfo["wheels"][1])
                if round(beltWidth, 3) < beltWidthMin:
                    report = await textTools.addLine(report,
                        f"Your track belt is {beltWidth}mm wide.  This is too narrow and will lead to bad off-road performance.  Increase your track width to at least {beltWidthMin}mm.")
                    errorCount += 1
                if round(trackSystemWidth, 3) > hullWidthMax:
                    report = await textTools.addLine(report,
                        f"Your track system is {round(trackSystemWidth, 2)} meters wide.  This exceeds the {hullWidthMax} meter limit.")
                    errorCount += 1
                if trackSystemWidth >= overallTankWidth:
                    overallTankWidth = round(trackSystemWidth, 3)
                try:
                    torsionBarLength = float(partInfo["suspensions"]["TBLength"])
                    if useDynamicTBlength == True:
                        torsionBarLengthMin = torsionBarLengthMin * separation
                    if round(torsionBarLength, 3) < torsionBarLengthMin:
                        report = await textTools.addLine(report, f"Your torsion bar is {torsionBarLength}m wide.  This is below the {torsionBarLengthMin} meter requirement.")
                        errorCount += 1

                except Exception:
                    suspensionType = "HVSS"
                    if allowHVSS == False:
                        report = await textTools.addLine(report, f"This vehicle uses HVSS suspension, which is not permitted in {contestName}")
                        errorCount += 1


            if partName == "FDR":
                separation = 2 * float(partInfo["f"][3])
                sectWidth = 2 * float(partInfo["f"][9])
                totalWidth = separation + sectWidth
                if totalWidth > round(hullWidthMax, 2):
                    report = await textTools.addLine(report,
                        f"Your fenders are {totalWidth} meters wide.  This is too wide - the maximum width is {hullWidthMax} meters.")
                    errorCount += 1
                if totalWidth > overallTankWidth:
                    overallTankWidth = totalWidth

            if partName == "ENG":
                name = partInfo["name"]
                displacement = round(float(partInfo["cylinders"]) * float(partInfo["cylinderDisplacement"]), 2)
                # print(country)
                engineLimit = 80
                if (float(engineLimit) + 0.01) < float(displacement):
                    report = await textTools.addLine(report,
                        f"Engine \"{name}\" displacement is invalid!  This engine is: {displacement} liters, while the limit is {engineLimit}.")
                    errorCount += 1
                else:
                    report = await textTools.addLine(report, f"Engine \"{name}\" has {displacement} liters of displacement.")



            x += 1

        litersPerTon = round(fuelTankSize/weight, 2)
        litersPerDisplacement = round(fuelTankSize / displacement, 2)

        blueprintDataOut = json.dumps(blueprintData, indent=4)

        if len(report) > 2000:
            reportLines = report.split("\n")
            reportLength = len(reportLines)
            reportSpot = 0
            reportBlock = ""
            await ctx.send(f"Your report was too long, at {len(report)} characters & {reportLength} lines.  Breaking it up into several lines.")
            while reportSpot < reportLength:
                if len(reportLines[reportSpot]) > 2000:
                    reportBlock = await textTools.addLine(reportBlock, "One section has been skipped due to exceeding the character limit.  Consider using shorter names for your compartments.")
                if len(reportLines[reportSpot]) + len(reportBlock) < 2000:
                    reportBlock = await textTools.addLine(reportBlock, reportLines[reportSpot])
                else:
                    await ctx.send(reportBlock)
                    reportBlock = ""
                reportSpot += 1
            await ctx.send(reportBlock)
        else:
            await ctx.send(report)

        # Writing to sample.json
        with open("tanktest.json", "w") as outfile:
            outfile.write(blueprintDataOut)
        valid = True
        if errorCount > errorTolerance:
            valid = False
        powertrainStats = await blueprintFunctions.getPowertrainStats(attachment)
        results = {
            "tankName": tankName,
            "tankWeight": weight,
            "errorCount": errorCount,
            "valid": valid,
            "tankWidth": overallTankWidth,
            "crewCount": crewCount,
            "turretCount": turretCount,
            "GCMratioMin": int(GCMratioMin),
            "armorVolume": armorVolume,
            "maxArmor": maxArmorOverall,
            "gameVersion": round(float(gameVersion), 5),
            "gameEra": era,
            "GCMcount": GCMcount,
            "hullHeight": height,
            "tankLength": hullLength,
            "torsionBarLength": torsionBarLength,
            "suspensionType": suspensionType,
            "beltWidth": beltWidth,
            "groundPressure": groundPressure,
            "HP": powertrainStats["HP"],
            "HPT": powertrainStats["HPT"],
            "litersPerDisplacement": litersPerDisplacement,
            "litersPerTon": litersPerTon,
            "topSpeed": powertrainStats["topSpeed"],
            "gunCount": gunCount,
            "maxCaliber": maxCaliber,
            "maxPropellant": maxPropellant,
            "maxBore": maxBore,
            "maxShell": maxShell,
            "minArmor": minArmor
            }
        return results

    async def runBlueprintCheck200(ctx: commands.Context, attachment, config):
        # importing data
        print(config)
        contestName = config["contestname"]
        era = config["era"]
        gameVersion = round(float(config["gameversion"]), 5)
        enforceGameVersion = config["enforcegameversion"]
        errorTolerance = config["errortolerance"]
        weightLimit = config["weightlimit"]
        crewMaxSpace = config["crewmaxspace"]
        crewMinSpace = config["crewminspace"]
        crewMin = config["crewmin"]
        crewMax = config["crewmax"]
        turretRadiusMin = config["turretradiusmin"]
        allowGCM = config["allowgcm"]
        GCMratioMin = config["gcmratiomin"]
        torqueMax = config["torquemax"]
        hullHeightMin = config["hullheightmin"]
        hullWidthMax = config["hullwidthmax"]
        torsionBarLengthMin = config["torsionbarlengthmin"]
        useDynamicTBlength = config["usedynamictblength"]
        allowHVSS = config["allowhvss"]
        beltWidthMin = config["beltwidthmin"]
        requireGroundPressure = config["requiregroundpressure"]
        groundPressureMax = config["groundpressuremax"]
        litersPerDisplacement = config["litersperdisplacement"]
        litersPerTon = config["litersperton"]
        caliberLimit = config["caliberlimit"]
        propellantLimit = config["propellantlimit"]
        boreLimit = config["borelimit"]
        shellLimit = config["shelllimit"]
        armorMin = config["armormin"]
        ATsafeMin = config["atsafemin"]
        armorMax = config["armormax"]

        # declaring initial variables and opening data
        report = ""

        blueprintData = json.loads(await attachment.read())
        errorCount = 0
        GCMcount = 0
        weight = float(blueprintData["header"]["mass"])/1000
        tankName = blueprintData["header"]["name"]
        tankName = await textTools.sanitize(tankName)
        tankEra = blueprintData["header"]["era"]
        overallTankWidth = 0
        maxArmorOverall = 0 # this gets increased over time
        crewCount = 0
        turretCount = 0
        displacement = 1
        fuelTankSize = 0.0
        gunCount = 0
        maxCaliber = 0
        maxPropellant = 0
        maxBore = 0
        maxShell = 0
        minArmor = 0
        armorVolume = 0.0
        startingLength = 5289
        wheelDiameter = 700
        wheelSpacing = 30
        groupSize = 2
        groupOffset = 1
        groupSpacing = 500
        fuelTankCatalog = {}
        crewReport = "Crew information: \n"
        suspensionType = "torsion bar"

        fileGameVersion = float(blueprintData["header"]["gameVersion"])
        if fileGameVersion != gameVersion and enforceGameVersion == True:
            #report = await textTools.addLine(report, )
            report = await textTools.addLine(report, f"This vehicle was made in {fileGameVersion}, while it is required to be in {fileGameVersion}.  Please update your game and then readjust your tank to fit the new version.")
            errorCount += 1
        if fileGameVersion != gameVersion and enforceGameVersion == False:
            report = await textTools.addLine(report, f"Warning! This vehicle was made in {fileGameVersion}, while it should be made in {gameVersion}.  Check with a {contestName} host or manager to ensure this is acceptable.")
        report = await textTools.addLine(report, "This tank was made in Sprocket version " + blueprintData["header"]["gameVersion"] + "\nVehicle weight: " + str(weight) + " tons.")
        if era.lower() != tankEra.lower():
            report = await textTools.addLine(report,f"This vehicle was made in the {tankEra} period, but needs to be sent as a {era} tank.  Please update your vehicle to use the proper era.")
            errorCount += 1
        if weight > weightLimit + 0.01:
            errorCount += 1
            report = await textTools.addLine(report,f"This vehicle is overweight!  Please reduce its weight to no more than {weightLimit}T and resend it.")

        # begin looping through all the parts
        x = 0
        for partData in blueprintData["blueprints"]:
            partID = partData["id"]
            partType = partData["type"]
            partInfo = partData["blueprint"]
            partName = partData["name"]

            if partType == "crewSeat":
                crewCount += 1

            if partType == "cannon":
                gunCount += 1
                caliber = int(partData["caliber"])
                if caliber > maxCaliber:
                    maxCaliber = caliber
                propellant = int(partData["breechLength"])
                if propellant > maxPropellant:
                    maxPropellant = propellant
                calculatedShell = (3 * caliber) + propellant
                calculatedBore = calculatedShell / 1000
                for segment in partInfo["blueprints"][0]["segments"]:
                    calculatedBore += float(segment['len'])
                if calculatedShell > shellLimit:
                    report = await textTools.addLine(report,f"The \"{partName}\" is invalid!  This cannon uses a {calculatedShell}mm shell, while the limit for shell length is {shellLimit}mm.")
                    errorCount += 1
                if calculatedBore > boreLimit:
                    report = await textTools.addLine(report,f"The \"{partName}\" is invalid!  This cannon uses a {calculatedBore}m bore length, while the limit is {boreLimit}m.")
                    errorCount += 1
                if propellant > propellantLimit:
                    report = await textTools.addLine(report,f"The \"{partName}\" is invalid!  This cannon uses {propellant}mm of propellant, while the limit is {propellantLimit}mm.")
                    errorCount += 1
                if caliber > caliberLimit:
                    report = await textTools.addLine(report,f"The \"{partName}\" is invalid!  This cannon is {caliber}mm, while the caliber limit is {caliberLimit}mm.")
                    errorCount += 1
                else:
                    report = await textTools.addLine(report,f"\"{partName}\": {caliber}x{calculatedShell}mm with a {calculatedBore}m bore length.")
                    errorCount += -1
                if calculatedBore > maxBore:
                    maxBore = calculatedBore
                if calculatedShell > maxShell:
                    maxShell = calculatedShell

            if partType == "structure":
                armorVolume += float(partInfo["armourVolume"])

            if partType == "motor":
                if int(partInfo["torque"]) > torqueMax:
                    errorCount += 1
                    report = await textTools.addLine(report,f"Turret \"{partName}\" uses a torque setting above the {torqueMax}N limit!")

            if partType == "fuelTank":
                fuelTankID = partID
                tankVolume = int(int(partInfo["x"])*int(partInfo["y"])*int(partInfo["z"])*0.000001)
                fuelTankCatalog[fuelTankID] = tankVolume

            if partType == "motor":
                if int(partInfo["ringThickness"]) > armorMax:
                    errorCount += 1
                    report = await textTools.addLine(report,f"You have a turret ring exceeding the armor limit of your vehicle.")

            if partType == "FLT":
                requiredFLT = round(displacement*litersPerDisplacement * (1 + (litersPerTon*weight)), 2)
                fuelTankSize = int(partInfo["L"])
                if partInfo["L"] < requiredFLT:
                    report = await textTools.addLine(report,f"Your internal fuel tank has {partInfo['L']}L of fuel, but needs {requiredFLT}L of fuel in order to perform adequately.")
                    errorCount += 1

            if partType == "TRK":
                separation = float(partInfo["separation"])
                trackWidthTot = 0.002 * float(partInfo["belt"]["x"])
                trackSystemWidth = separation + trackWidthTot + 0.2
                beltWidth = int(partInfo["belt"]["x"])
                sprocketIndex = 0
                idlerIndex = 1
                # Ground Pressure
                if partInfo["frontalTransmission"] == True:
                    sprocketIndex = 0
                    idlerIndex = 1

                trackSystemLength = float(partInfo["length"])
                sprocketForward = float(partInfo["wheels"][sprocketIndex]["zOffset"])
                idlerForward = float(partInfo["wheels"][idlerIndex]["zOffset"])
                roadwheelForward = float(partInfo["wheels"][2]["zOffset"])
                sprocketDiameter = float(partInfo["wheels"][sprocketIndex]["diameter"])
                idlerDiameter = float(partInfo["wheels"][idlerIndex]["diameter"])
                roadwheelDiameter = float(partInfo["wheels"][2]["diameter"])
                roadwheelSpacing = float(partInfo["roadSpacing"])
                if partInfo["frontalTransmission"] == True:
                    sprocketForward = -1*float(partInfo["wheels"][sprocketIndex]["zOffset"])
                    # await ctx.send("frontal transmission detected!")
                    #if sprocketForward > 0:
                    #    sprocketForward = 0
                else:
                    idlerForward = -1 * float(partInfo["wheels"][idlerIndex]["zOffset"])
                    # if idlerForward > 0:
                    #     idlerForward = 0

                Mgcl = trackSystemLength - idlerForward - sprocketForward - (idlerDiameter + sprocketDiameter)/2 - roadwheelDiameter - roadwheelForward
                if trackSystemLength > hullLength:
                    hullLength = trackSystemLength
                # await ctx.send(f"MGCL: {Mgcl}")
                roadwheelCount = ((Mgcl + roadwheelSpacing + roadwheelDiameter)/(roadwheelDiameter+roadwheelSpacing))
                # await ctx.send(f"Roadwheel Count: {roadwheelCount}")
                roadwheelCount = int(roadwheelCount)
                realContactLength = (roadwheelCount - 1)*(roadwheelDiameter+roadwheelSpacing)
                # await ctx.send(f"Real™️: {realContactLength}")
                surfaceAreaCM = (realContactLength * 100) * (beltWidth / 10) * 2
                groundPressure = weight*1000 / surfaceAreaCM
                # await ctx.send(f"Ground pressure: {groundPressure}kg/cm²")

                if groundPressure > groundPressureMax and requireGroundPressure == True:
                    report = await textTools.addLine(report, f"Your track ground pressure is {round(groundPressure, 2)}kg/cm², but cannot exceed {groundPressureMax}kg/cm².  Increase your track contact area with the ground, or lighten your vehicle to improve ground pressure.")
                    errorCount += 1

                print(partInfo["wheels"][1])
                if round(beltWidth, 3) < beltWidthMin:
                    report = await textTools.addLine(report,
                        f"Your track belt is {beltWidth}mm wide.  This is too narrow and will lead to bad off-road performance.  Increase your track width to at least {beltWidthMin}mm.")
                    errorCount += 1
                if round(trackSystemWidth, 3) > hullWidthMax:
                    report = await textTools.addLine(report,
                        f"Your track system is {round(trackSystemWidth, 2)} meters wide.  This exceeds the {hullWidthMax} meter limit.")
                    errorCount += 1
                if trackSystemWidth >= overallTankWidth:
                    overallTankWidth = round(trackSystemWidth, 3)
                try:
                    torsionBarLength = float(partInfo["suspensions"]["TBLength"])
                    if useDynamicTBlength == True:
                        torsionBarLengthMin = torsionBarLengthMin * separation
                    if round(torsionBarLength, 3) < torsionBarLengthMin:
                        report = await textTools.addLine(report, f"Your torsion bar is {torsionBarLength}m wide.  This is below the {torsionBarLengthMin} meter requirement.")
                        errorCount += 1

                except Exception:
                    suspensionType = "HVSS"
                    if allowHVSS == False:
                        report = await textTools.addLine(report, f"This vehicle uses HVSS suspension, which is not permitted in {contestName}")
                        errorCount += 1


            if partType == "AutoGenFenders":
                separation = 2 * float(partInfo["f"][3])
                sectWidth = 2 * float(partInfo["f"][9])
                totalWidth = separation + sectWidth
                if totalWidth > round(hullWidthMax, 2):
                    report = await textTools.addLine(report,
                        f"Your fenders are {totalWidth} meters wide.  This is too wide - the maximum width is {hullWidthMax} meters.")
                    errorCount += 1
                if totalWidth > overallTankWidth:
                    overallTankWidth = totalWidth

            if partType == "ENG":
                name = partInfo["name"]
                displacement = round(float(partInfo["cylinders"]) * float(partInfo["cylinderDisplacement"]), 2)
                # print(country)
                engineLimit = 80
                if (float(engineLimit) + 0.01) < float(displacement):
                    report = await textTools.addLine(report,
                        f"Engine \"{name}\" displacement is invalid!  This engine is: {displacement} liters, while the limit is {engineLimit}.")
                    errorCount += 1
                else:
                    report = await textTools.addLine(report, f"Engine \"{name}\" has {displacement} liters of displacement.")
            x += 1

        for objectData in blueprintData["objects"]:
            # add to the guel tank count
            pGuid = objectData["guid"]
            try:
                fuelTankID = objectData["fuelTankBlueprintVuid"]
                if pGuid == "5e8ab5c7-e9f1-4c64-a04a-29efc78b1918":
                    fuelTankSize += fuelTankCatalog[fuelTankID]
                if pGuid == "ecd3341c-f605-4816-946c-591eaa7e4f7d":
                    fuelTankSize += int(fuelTankCatalog[fuelTankID]*math.pi/4)
            except Exception:
                pass


        for partData in blueprintData["meshes"]:
            partType = partData["type"]
            partInfo = partData["blueprint"]
            partName = partData["name"]

            if partType == "Compartment":
                name = partInfo["name"]

                # displacement = float(partInfo["cylinders"])*float(partInfo["cylinderDisplacement"])
                # print(country)
                tooThinPlates = 0
                tooThickPlates = 0
                ATpronePlates = 0
                if partInfo["genID"] == "VSH":
                    width = float(partInfo["genData"]["shape"][1]) + 2 * float(partInfo["genData"]["shape"][6])
                    # print(str(width) + " aaaaaaaaaaaaaaaaaaaaa")
                    for thickness in partInfo["genData"]["armour"]:
                        # print(thickness)
                        if thickness < armorMin:
                            tooThinPlates += 1
                        if thickness > armorMax:
                            tooThickPlates += 1
                        if thickness > maxArmorOverall:
                            maxArmorOverall = thickness
                else:
                    # print(len(partInfo["compartment"]["points"]))
                    tooThinPlates = 0
                    tooThickPlates = 0
                    for thickness in partInfo["compartment"]["thicknessMap"]:
                        # print(thickness)
                        if thickness < armorMin:
                            tooThinPlates += 1
                        if thickness < ATsafeMin:
                            ATpronePlates += 1
                        if thickness > armorMax:
                            tooThickPlates += 1
                        if thickness > maxArmorOverall:
                            maxArmorOverall = thickness
                        if thickness < minArmor:
                            minArmor = thickness
                    xmin = 0
                    ymin = 0
                    zmin = 0
                    xmax = 0
                    ymax = 0
                    zmax = 0
                    min = [0, 0, 0]
                    max = [0, 0, 0]
                    if partInfo["ID"] == 0:
                        alternator = 0
                        for point in partInfo["compartment"]["points"]:
                            if alternator == 3:
                                alternator = 0
                            if point > max[alternator]:
                                max[alternator] = point
                            if point < min[alternator]:
                                min[alternator] = point
                            alternator += 1
                        # print(f"max {max[2]}   min {min[2]}")
                        height = max[1] - min[1]
                        width = max[0] - min[0]
                        hullLength = max[2] - min[2]
                        if width > overallTankWidth:
                            overallTankWidth = width
                        if height < hullHeightMin:
                            report = await textTools.addLine(report, f"{name} is {round(height, 2)} meters tall.  This won't fit any crew.")
                            errorCount += 1
                        if width > hullWidthMax:
                            report = await textTools.addLine(report,
                                f"{name} is {round(width, 2)} meters wide.  This is wider than the {hullWidthMax} meter limit.")
                            errorCount += 1
                    else:
                        ringArmor = partInfo["turret"]["ringArmour"]
                        basketVolume = partInfo["turret"]["basketVolume"]
                        torque = partInfo["turret"]["traverse"]["torque"]
                        ratio = partInfo["turret"]["traverse"]["ratio"]
                        ringRadius = float(partInfo["turret"]["radius"])
                        if ringRadius >= turretRadiusMin:
                            turretCount += 1
                        if ringRadius > overallTankWidth:
                            overallTankWidth = ringRadius
                        isGCM = False
                        if abs(int(partInfo["rot"][2])) > 20 and ringRadius >= turretRadiusMin:
                            isGCM = True
                            GCMcount += 1
                            if allowGCM == False:
                                report = await textTools.addLine(report, f"GCMs (including compartment \"{name}\") are not allowed in this contest.")
                                errorCount += 1
                            # custom mantlet checks
                            if torque > torqueMax:
                                errorCount += 1
                                report = await textTools.addLine(report, f"GCM \"{name}\" uses a torque setting above the {torqueMax}N limit!")
                            if ratio < GCMratioMin:
                                errorCount += 1
                                report = await textTools.addLine(report, f"GCM \"{name}\" has a traverse ratio below the required minimum ratio of {torqueMax}!")
                        if ringArmor < armorMin:
                            report = await textTools.addLine(report, f"{name}'s turret ring is below the 15mm armor requirement!")
                            errorCount += 1
                        if ringArmor < ATsafeMin:
                            ATpronePlates += 1
                        if ringArmor < minArmor:
                            minArmor = ringArmor
                        if ringArmor > maxArmorOverall:
                            maxArmorOverall = ringArmor
                        if basketVolume < 0 or basketVolume > 5:
                            report = await textTools.addLine(report,
                                f"{name} has been file edited and cannot be accepted.  Reason: turret volume is invalid.")
                            errorCount += 1
                        if float(ringRadius) <= turretRadiusMin and isGCM == False:
                            report = await textTools.addLine(report,
                                f"Warning: {name}'s turret ring is not wide enough to fit crew.  Increase the turret ring diameter if necessary.")
                        if ATpronePlates > 1:
                            report = await textTools.addLine(report, f"Warning: this vehicle is prone to infantry rifles.")


                if tooThickPlates > 0 or tooThinPlates > 0:
                    report = await textTools.addLine(report,
                        f"{name} has {tooThickPlates} armor plates exceeding the {armorMax}mm armor limit, and {tooThinPlates} armor plates below the minimum {armorMin}mm requirement.")
                    errorCount += 1



        # start finalizing data
        if crewCount < crewMin:
            report = await textTools.addLine(report,f"This vehicle needs to have at least {crewMin} crew members, but only has {crewCount} crew.")
            errorCount += 1
        if crewCount > crewMax:
            report = await textTools.addLine(report,f"This vehicle needs to have at most {crewMax} crew members, but it has {crewCount} crew.")
            errorCount += 1

        # calculate contact length for ground pressure (all values in mm)
        maxLength = startingLength + wheelSpacing + groupSpacing - wheelDiameter
        wheel = 1
        currentLength = -1 * wheelSpacing
        wheelGroupPos = groupOffset
        finalLength = 0
        while currentLength <= maxLength:
            finalLength = currentLength
            currentLength += wheelDiameter + wheelSpacing
            wheel += 1
            wheelGroupPos += 1
            if wheelGroupPos == groupSize:
                currentLength += groupSpacing
                wheelGroupPos -= groupSize
        groundContactLength = finalLength + wheelSpacing

        litersPerTon = round(fuelTankSize/weight, 2)
        litersPerDisplacement = round(fuelTankSize / displacement, 2)

        blueprintDataOut = json.dumps(blueprintData, indent=4)

        if len(report) > 2000:
            reportLines = report.split("\n")
            reportLength = len(reportLines)
            reportSpot = 0
            reportBlock = ""
            await ctx.send(f"Your report was too long, at {len(report)} characters & {reportLength} lines.  Breaking it up into several lines.")
            while reportSpot < reportLength:
                if len(reportLines[reportSpot]) > 2000:
                    reportBlock = await textTools.addLine(reportBlock, "One section has been skipped due to exceeding the character limit.  Consider using shorter names for your compartments.")
                if len(reportLines[reportSpot]) + len(reportBlock) < 2000:
                    reportBlock = await textTools.addLine(reportBlock, reportLines[reportSpot])
                else:
                    await ctx.send(reportBlock)
                    reportBlock = ""
                reportSpot += 1
            await ctx.send(reportBlock)
        else:
            await ctx.send(report)

        # Writing to sample.json
        with open("tanktest.json", "w") as outfile:
            outfile.write(blueprintDataOut)
        valid = True
        if errorCount > errorTolerance:
            valid = False
        powertrainStats = await blueprintFunctions.getPowertrainStats(attachment)
        results = {
            "tankName": tankName,
            "tankWeight": weight,
            "errorCount": errorCount,
            "valid": valid,
            "tankWidth": overallTankWidth,
            "crewCount": crewCount,
            "turretCount": turretCount,
            "GCMratioMin": int(GCMratioMin),
            "armorVolume": armorVolume,
            "maxArmor": maxArmorOverall,
            "gameVersion": round(float(gameVersion), 5),
            "gameEra": era,
            "GCMcount": GCMcount,
            "hullHeight": height,
            "tankLength": hullLength,
            "torsionBarLength": torsionBarLength,
            "suspensionType": suspensionType,
            "beltWidth": beltWidth,
            "groundPressure": groundPressure,
            "HP": powertrainStats["HP"],
            "HPT": powertrainStats["HPT"],
            "litersPerDisplacement": litersPerDisplacement,
            "litersPerTon": litersPerTon,
            "topSpeed": powertrainStats["topSpeed"],
            "gunCount": gunCount,
            "maxCaliber": maxCaliber,
            "maxPropellant": maxPropellant,
            "maxBore": maxBore,
            "maxShell": maxShell,
            "minArmor": minArmor
            }
        return results

    @commands.command(name="importMesh", description="Sorry Argore")
    async def importMesh(self, ctx:commands.Context):
        await ctx.send("Upload the .blueprint you wish to import into.  Note: you can only import to freeform compartments.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msgBP = await ctx.bot.wait_for('message', check=check, timeout=200.0)
        except Exception:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            await ctx.send("Gonna need a blueprint file next time.")
            return

        await ctx.send(content="Upload the meshes you wish to import.  They must be a .obj file with no faces exceeding 4 points.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=240.0)
        except Exception:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            return

        armorThickness = 1
        await ctx.send(content=f"Specify the desired armor thickness to use on everything (in mm)")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg2 = await ctx.bot.wait_for('message', check=check, timeout=240.0)
            armorThickness = int(msg2.content)
        except Exception:
            await ctx.send(await self.bot.error.retrieveError(ctx))
            await ctx.send("This number was invalid!  Using the recommended value...")
            return

        for attachmentBP in msgBP.attachments:
            blueprintData = json.loads(await attachmentBP.read())
            structureList = []
            structureVuidList = {}
            tankName = blueprintData["header"]["name"]
            string = "0.2.3"
            blueprintData["header"]["gameVersion"] = "0.2.3"
            for attachmentin in msg.attachments:
                try:
                    attachment = await attachmentin.read()
                    print(attachment)
                    dataList = str(attachment).split("\\n")
                    print(dataList)
                    print(dataList[0])
                    structureList = []
                    verticesList = []
                    thicknessList = []
                    facesList = []

                    for data in dataList:
                        if data[0:2] == "v ":
                            points = data.split(" ")[1:4]
                            points[0] = -1*float(points[0])
                            for point in points:
                                verticesList.append(round(float(point), 5))
                        if data[0:2] == "f ":
                            faceDataIn = data.split(" ")[1:]
                            faceSet = []
                            for face in faceDataIn:
                                point = int(face.split("/")[0]) - 1
                                faceSet.append(point)
                            thicknessSet = [armorThickness] * len(faceSet)
                            # if len(faceSet) > 4:
                            #     await ctx.send(await self.bot.error.retrieveError(ctx))
                            #     await ctx.send("### Your model is not triangulated properly!\n Open your mesh in Blender and apply a **Triangulate** modifier, using these settings.  Export it as a .obj file, then run the command again.")
                            #     await ctx.send("https://raw.githubusercontent.com/SprocketTools/SprocketBot/main/blender-settings.png")
                            #     return
                            facesList.append(faceSet)
                            thicknessList.append(thicknessSet)
                    pointsK = [16777215, 16777215, 0, -16777215, -16777215, 0]
                    for point in pointsK:
                        verticesList.append(round(float(point), 5))
                    print(verticesList)
                    print(facesList)
                    print(thicknessList)

                    ftList = []
                    for i in range(len(facesList)):
                        data = {}
                        data["v"] = facesList[i]
                        data["t"] = thicknessList[i]
                        ftList.append(data)
                    dupeStatus = False
                    i = 0
                    for component in blueprintData["blueprints"]:
                        if component["type"] == "structure":
                            if blueprintData["blueprints"][i]["blueprint"]["name"] is None:
                                blueprintData["blueprints"][i]["blueprint"]["name"] = "Hull"
                            if blueprintData["blueprints"][i]["blueprint"]["description"] is None:
                                blueprintData["blueprints"][i]["blueprint"]["description"] = "null"
                        try:
                            if blueprintData["blueprints"][i]["blueprint"]["name"] is None:
                                blueprintData["blueprints"][i]["blueprint"]["name"] = "null"
                            if blueprintData["blueprints"][i]["blueprint"]["description"] is None:
                                blueprintData["blueprints"][i]["blueprint"]["description"] = "null"
                        except Exception:
                            pass
                        print(component)
                        if component["type"] == "structure":
                            nameOut = blueprintData["blueprints"][i]["blueprint"]["name"]
                            if nameOut in structureList and dupeStatus == False:
                                await ctx.send(await self.bot.error.retrieveError(ctx))
                                await ctx.send(f"Note: you have multiple compartments named {nameOut}.  To make things easier for yourself later, it's recommended to through your blueprint and give your compartments unique names.")
                                dupeStatus = True
                                nameOut = f"{nameOut} (Vuid {i})"
                            structureList.append(nameOut)
                            structureVuidList[blueprintData["blueprints"][i]["blueprint"]["name"]] = int(component["blueprint"]["bodyMeshVuid"])
                        i += 1

                    userPrompt = f"Pick the name of the compartment you wish to apply {attachmentin.filename} to."
                    print(structureList)
                    answer = await ctx.bot.ui.getChoiceFromList(ctx, structureList, userPrompt)
                    Vuid = structureVuidList[answer]
                    i = 0
                    for meshBase in blueprintData["meshes"]:
                        if meshBase["vuid"] == Vuid:
                            if blueprintData["meshes"][i]["meshData"]["format"] != "freeform":
                                await ctx.send(await self.bot.error.retrieveError(ctx))
                                await ctx.send("Generated compartments cannot be imported into.  Convert your generated compartments to freeform and try again.")
                                return
                            blueprintData["meshes"][i]["meshData"]["mesh"]["vertices"] = verticesList
                            blueprintData["meshes"][i]["meshData"]["mesh"]["faces"] = ftList
                        i += 1
                except Exception as error:
                    await ctx.send(await self.bot.error.retrieveError(ctx))
                    await ctx.send(f"## The mesh import failed!  \n\n### Reason: \n{error}")
                    return

            await ctx.send("## Done!")
            stringOut = json.dumps(blueprintData, indent=4)
            data = io.BytesIO(stringOut.encode())
            await ctx.send(file=discord.File(data, f'{tankName}-tuned.blueprint'))
            await ctx.send("### Note:\nWhen opening the model, make sure to select all of your faces and invert them, so that the geometry displays the correct way.")





    @commands.command(name="setupDatabase2", description="Wipe literally everything.")
    async def cog5(self, ctx):
        await ctx.send(content="Hello!")

def braveRotateVector(vector, rot):
    import numpy as np
    rotX = rot[0]
    rotY = rot[1]
    rotZ = rot[2]
    # Define the rotation matrices for each plane
    matrixX = np.array([[1, 0, 0],
                        [0, np.cos(rotX), -np.sin(rotX)],
                        [0, np.sin(rotX), np.cos(rotX)]])

    matrixY = np.array([[np.cos(rotY), 0, np.sin(rotY)],
                        [0, 1, 0],
                        [-np.sin(rotY), 0, np.cos(rotY)]])

    matrixZ = np.array([[np.cos(rotZ), -np.sin(rotZ), 0],
                        [np.sin(rotZ), np.cos(rotZ), 0],
                        [0, 0, 1]])

    # Define the original vector
    # vector = np.array([1, 2, 3])

    # Rotate the vector around the XY plane
    # vector_xy = np.dot(vector, matrixX)

    # Rotate the vector around the YZ plane
    # vector_yz = np.dot(vector_xy, matrixY)

    # Rotate the vector around the XZ plane
    # vector_xz = np.dot(vector_yz, matrixZ)

    # Z comes before X
    # Y is not in the middle

    vector_xz = np.dot(vector, matrixZ)

    vector_xy = np.dot(vector_xz, matrixX)
    vector_yz = np.dot(vector_xy, matrixY)

    # Print the final rotated vector
    return vector_yz

async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(blueprintFunctions(bot))