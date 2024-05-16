import discord, json, math, numpy, copy, io
from discord.ext import commands
import cv2 as cv
from discord import app_commands

import main
from cogs.textTools import textTools
from PIL import Image, ImageChops
from cogs.SQLfunctions import SQLfunctions
from cogs.discordUIfunctions import discordUIfunctions
class blueprintFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="bakeGeometry", description="merge compartment geometry into itself.")
    async def bakeGeometry(self, ctx: commands.Context):
        import asyncio
        # country = await getUserCountry(ctx)
        serverID = (ctx.guild.id)
        try:
            channel = int([dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel and ctx.author.id != main.ownerID:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
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
        #             await ctx.send(await textTools.retrieveError(ctx))
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
        # answer = await discordUIfunctions.getChoiceFromList(ctx, structureList, userPrompt)
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
        # i = 0
        # # apply offsets to have all compartments centered at [0,0,0]

        print(compartmentList)
        # copy all the meshes over to the hull
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
                        netPartPointCount = int(netPartPointsLength) / 3
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
                                # print(face["v"][i])
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

    async def bakeGeometry127(ctx: commands.Context, attachment):
        blueprintData = json.loads(await attachment.read())
        blueprintDataSave = json.loads(await attachment.read())
        name = blueprintData["header"]["name"]
        version = blueprintData["header"]["gameVersion"]
        if "0.12" not in version:
            errorText = await textTools.retrieveError(ctx)
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
        import io
        await ctx.send("Done!")

        return blueprintDataSave

    @commands.command(name="drawFrame", description="merge compartment geometry into itself.")
    async def drawFrame(self, ctx: commands.Context):
        import asyncio

        for attachment in ctx.message.attachments:
            blueprintData = json.loads(await attachment.read())
            name = blueprintData["header"]["name"]
            version = 0.127
            if "0.2" in blueprintData["header"]["gameVersion"]:
                await ctx.send("Detected a 0.2 blueprint.")
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

            rotationX = 0.00
            rotationY = -0.2
            rotationZ = 0.1

            # image settings
            imageScale = 500
            imagePadding = 100
            lineThickness = 10


            angles = [-1 * rotationX, -1 * rotationY, -1 * rotationZ]
            ## rotate all the vertices
            pos = 0
            while pos < len(verticesList):
                roundPoint = 6
                vector = [verticesList[pos], verticesList[pos + 1], verticesList[pos + 2]]
                # angles = [sourcePartRotZ, sourcePartRotY, -1*sourcePartRotX]

                newVector = braveRotateVector(vector, angles)

                # newVector = rotateVector(vector, angles)
                verticesList[pos] = round(newVector[0], roundPoint)
                verticesXlist.append(newVector[0])
                verticesList[pos + 1] = round(newVector[1], roundPoint)
                verticesYlist.append(newVector[1])
                verticesList[pos + 2] = round(newVector[2], roundPoint)
                verticesZlist.append(newVector[2])

                pos += 3

            print(verticesList)

            # conversion from 3D to 2D
            imageXlist = verticesZlist
            imageYlist = verticesYlist

            # scale up the points
            i = 0
            while i < len(imageXlist):
                imageXlist[i] = imageXlist[i]*imageScale
                imageYlist[i] = imageYlist[i]*imageScale
                i += 1

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

            imageXbottom = min(imageXlist)
            imageXtop = max(imageXlist)
            imageYbottom = min(imageYlist)
            imageYtop = max(imageYlist)

            print(min(imageXlist))
            print(min(imageYlist))
            print(imageXlist)
            print(imageYlist)

            imageX = imageXtop - imageXbottom + 2*imagePadding
            imageY = imageYtop - imageYbottom + 2*imagePadding
            print(imageX)
            print(imageY)

            # flip the points
            i = 0
            while i < len(imageXlist):
                imageXlist[i] = imageX - imageXlist[i]
                imageYlist[i] = imageY - imageYlist[i]
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


            print(f"X top is {imageXtop}, bottom is {imageXbottom}.  Y top is {imageYtop}, bottom is {imageYbottom}")

            # initialize the image
            imageBase = numpy.zeros((int(imageY), int(imageX), 3), numpy.uint8)
            i = 0
            while i < len(startingCoords):
                cv.line(imageBase, (round(startingCoords[i][0]), round(startingCoords[i][1])), (round(endingCoords[i][0]), round(endingCoords[i][1])), (100, 200, 255), lineThickness)
                i += 1

            # send the image
            # bytes_io = io.BytesIO()
            img_encode = cv.imencode('.png', imageBase)[1]
            data_encode = numpy.array(img_encode)
            byte_encode = data_encode.tobytes()
            byteImage = io.BytesIO(byte_encode)
            imageOut = discord.File(byteImage, filename='image.png')
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
















            stringOut = json.dumps(blueprintDataSave, indent=4)
            data = io.BytesIO(stringOut.encode())
            await ctx.send(file=discord.File(data, f'{name}(merged).blueprint'))

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



        await ctx.send(f" How many gears do you want to use?  For this vehicle era, it's recommended to use {gearCount} gears.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=200.0)
            gearCount = int(msg.content)
        except Exception:
            await ctx.send("This number was invalid!  Using the recommended value...")

        await ctx.send(f"Specify the desired climbing angle in degrees.  Note: bigger climbing angles also improve your neutral steer setting.  \nRecommended values are between 45 and 75.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=200.0)
            climbAngle = numpy.radians(int(msg.content))
            if int(msg.content) > 90 or int(msg.content) < 1:
                await ctx.send("This number was invalid!  Using the recommended value...")
                climbAngle = numpy.radians(60)

        except Exception:
            await ctx.send("This number was invalid!  Using the recommended value...")

        x = 0
        for partInfo in blueprintData["blueprints"]:
            partID = partInfo["id"]
            if partID == 12:
                cylinders = int(partInfo["blueprint"]["cylinders"])
                dispPerCyl = float(partInfo["blueprint"]["cylinderDisplacement"])
                partInfo["targetMaxRPM"] = eraBaseRPM * (dispPerCyl ** -0.3)
            if partID == 72:
                sprocketDiameter = partInfo["blueprint"]["diameter"]
                print(sprocketDiameter)
            x += 1
        print(cylinders)
        print(dispPerCyl)

        idealRPM = eraBaseRPM * (dispPerCyl ** -0.3) / 1.01
        horsepower = 40 * (dispPerCyl ** 0.7) * cylinders * eraPowerMod
        topSpeed = (13.33 * (horsepower ** 0.5)) / ((eraResistance ** 0.8) * ((weight) ** 0.5))

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
        import asyncio
        if not ctx.message.attachments:
            await ctx.reply(
                "**-tunePowertrain** configures your engine's transmission to use the most optimal setup for your tank!\nTo use this command, attach one or more .blueprint files when running the **-tunePowertrain** command.\nNote: it is recommended to use twin transmissions on all vehicle builds, due to the tendency of Sprocket AI to have terrible clutch braking skills.\n# <:caatt:1151402846202376212>")

        serverID = (ctx.guild.id)
        try:
            channel = int([dict(row) for row in await SQLfunctions.databaseFetch(f'SELECT * FROM serverconfig WHERE serverid = {serverID}')][0]['commandschannelid'])
            if ctx.channel.id != channel:
                await ctx.send(f"Utility commands are restricted to <#{channel}>")
                return
        except Exception:
                error = await textTools.retrieveError(ctx)
                await ctx.send(f"{error}\n\nUtility commands are restricted to the server's bot commands channel, but the server owner has not set a channel yet!  Ask them to run the `-setup` command in one of their private channels.")
                return

        for attachment in ctx.message.attachments:
            print(attachment.content_type)
            try:
                if "image" in attachment.content_type:
                    errorStr = await textTools.retrieveError(ctx)
                    await ctx.reply(errorStr)
                    #await ctx.reply("Ah yes, I love eating random pictures instead of working with tank blueprints *like I was meant to do*! \n\n# <:caatt:1151402846202376212>")
                    return
            except Exception:
                pass
            blueprintData = json.loads(await attachment.read())
            version = 0.127
            if "0.2" in blueprintData["header"]["gameVersion"]:
                await ctx.send("Detected a 0.2 blueprint.")
                await blueprintFunctions.tunePowertrain200(ctx, attachment)
            elif float(blueprintData["header"]["gameVersion"]) < 0.128:
                await ctx.send(f"Detected a legacy {blueprintData['header']['gameVersion']} blueprint.")
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

        # x = 0
        # for iteration in blueprintData["ext"]:
        #     partName = blueprintData["ext"][x]["REF"]
        #     partInfo = blueprintData["ext"][x]["DAT"]
        #     #partString.replace("\\", "")
        #     #partInfo = json.loads(partString)
        #     try:
        #         userLimit = json.loads(partInfo[1]["data"])
        #         thickness = userLimit["thickness"][0]
        #         #print(json.dumps(userLimit, indent=4))
        #         print(thickness)
        #         #except Exception:
        #         #pass
        #         if thickness > armorMax:
        #             errorCount += 1
        #             report = await textTools.addLine(report,f"This vehicle has mantlet face armor above the {armorMax}mm armor limit!  Please resend with a corrected version.")
        #         if thickness < minArmor:
        #             minArmor = thickness
        #     except Exception:
        #         pass
        #     # print(partInfo)
        #     x += 1

        x = 0
        for partData in blueprintData["blueprints"]:
            partType = partData["type"]
            partString = blueprintData["blueprints"][x]["data"]
            partString.replace("\\", "")
            partInfo = json.loads(partString)
            if partType == "crewSeat":
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

            partName = ""
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

            if partName == "Compartment":
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

    @commands.command(name="importMesh", description="Sorry Argore")
    async def importMesh(self, ctx:commands.Context):
        await ctx.send("Upload the .blueprint you wish to import into.  Note: you can only import to freeform compartments.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msgBP = await ctx.bot.wait_for('message', check=check, timeout=200.0)
        except Exception:
            await ctx.send(await textTools.retrieveError(ctx))
            await ctx.send("Gonna need a blueprint file next time.")
            return

        await ctx.send(content="Upload the meshes you wish to import.  They must be a .obj file with no faces exceeding 4 points.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await ctx.bot.wait_for('message', check=check, timeout=240.0)
        except Exception:
            await ctx.send(await textTools.retrieveError(ctx))
            return

        armorThickness = 1
        await ctx.send(content=f"Specify the desired armor thickness to use on everything (in mm)")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg2 = await ctx.bot.wait_for('message', check=check, timeout=240.0)
            armorThickness = int(msg2.content)
        except Exception:
            await ctx.send(await textTools.retrieveError(ctx))
            await ctx.send("This number was invalid!  Using the recommended value...")
            return

        for attachmentBP in msgBP.attachments:
            blueprintData = json.loads(await attachmentBP.read())
            structureList = []
            structureVuidList = {}
            tankName = blueprintData["header"]["name"]

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
                            if len(faceSet) > 4:
                                await ctx.send(await textTools.retrieveError(ctx))
                                await ctx.send("### Your model is not triangulated properly!\n Open your mesh in Blender and apply a **Triangulate** modifier, using these settings.  Export it as a .obj file, then run the command again.")
                                await ctx.send("https://raw.githubusercontent.com/SprocketTools/SprocketBot/main/blender-settings.png")
                                return
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
                                await ctx.send(await textTools.retrieveError(ctx))
                                await ctx.send(f"Note: you have multiple compartments named {nameOut}.  To make things easier for yourself later, it's recommended to through your blueprint and give your compartments unique names.")
                                dupeStatus = True
                                nameOut = f"{nameOut} (Vuid {i})"
                            structureList.append(nameOut)
                            structureVuidList[blueprintData["blueprints"][i]["blueprint"]["name"]] = int(component["blueprint"]["bodyMeshVuid"])
                        i += 1

                    userPrompt = f"Pick the name of the compartment you wish to apply {attachmentin.filename} to."
                    print(structureList)
                    answer = await discordUIfunctions.getChoiceFromList(ctx, structureList, userPrompt)
                    Vuid = structureVuidList[answer]
                    i = 0
                    for meshBase in blueprintData["meshes"]:
                        if meshBase["vuid"] == Vuid:
                            if blueprintData["meshes"][i]["meshData"]["format"] != "freeform":
                                await ctx.send(await textTools.retrieveError(ctx))
                                await ctx.send("Generated compartments cannot be imported into.  Convert your generated compartments to freeform and try again.")
                                return
                            blueprintData["meshes"][i]["meshData"]["mesh"]["vertices"] = verticesList
                            blueprintData["meshes"][i]["meshData"]["mesh"]["faces"] = ftList
                        i += 1
                except Exception as error:
                    await ctx.send(await textTools.retrieveError(ctx))
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