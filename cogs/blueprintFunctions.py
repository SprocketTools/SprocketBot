import discord, json, numpy, copy
from discord.ext import commands
from discord import app_commands
from cogs.textTools import textTools
class blueprintFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    async def getPowertrainStats(self, attachment):
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
    async def runBlueprintCheck(ctx, attachment, config):
        # importing data
        contestName = config["contestName"]
        era = config["era"]
        gameVersion = config["gameVersion"]
        enforceGameVersion = config["enforceGameVersion"]
        errorTolerance = config["errorTolerance"]
        weightLimit = config["weightLimit"]
        crewMaxSpace = config["crewMaxSpace"]
        crewMinSpace = config["crewMinSpace"]
        crewMin = config["crewMin"]
        crewMax = config["crewMax"]
        turretRadiusMin = config["turretRadiusMin"]
        allowGCM = config["allowGCM"]
        GCMratioMin = config["GCMratioMin"]
        GCMtorqueMax = config["GCMtorqueMax"]
        hullHeightMin = config["hullHeightMin"]
        hullWidthMax = config["hullWidthMax"]
        torsionBarLengthMin = config["torsionBarLengthMin"]
        useDynamicTBlength = config["useDynamicTBLength"]
        allowHVSS = config["allowHVSS"]
        beltWidthMin = config["beltWidthMin"]
        requireGroundPressure = config["requireGroundPressure"]
        groundPressureMax = config["groundPressureMax"]
        litersPerDisplacement = config["litersPerDisplacement"]
        litersPerTon = config["litersPerTon"]
        caliberLimit = config["caliberLimit"]
        propellantLimit = config["propellantLimit"]
        boreLimit = config["boreLimit"]
        shellLimit = config["shellLimit"]
        armorMin = config["armorMin"]
        ATsafeMin = config["ATsafeMin"]
        armorMax = config["armorMax"]

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
        fuelTankSize = 0
        gunCount = 0
        maxCaliber = 0
        maxPropellant = 0
        maxBore = 0
        maxShell = 0
        minArmor = 0
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
                                f"{name} is {round(width, 2)} meters wide.  This is too wide for your railways, which can only support hulls up to {hullWidthMax} wide.")
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
                        if abs(int(partInfo["rot"][2])) > 20 and ringRadius >= turretRadiusMin:
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
                        if float(ringRadius) <= turretRadiusMin:
                            report = await textTools.addLine(report,
                                f"Warning: {name}'s turret ring is not wide enough to support crew.  Unless this is a cosmetic compartment or custom mentlet, please increase the turret ring diameter.")
                        if ATpronePlates > 1:
                            report = await textTools.addLine(report, f"Warning: this vehicle is prone to infantry rifles!  Make sure you are OK with this for your submission.")


                if tooThickPlates > 0 or tooThinPlates > 0:
                    report = await textTools.addLine(report,
                        f"{name} has {tooThickPlates} armor plates exceeding the {armorMax}mm armor limit, and {tooThinPlates} armor plates below the minimum {armorMin}mm requirement.")
                    errorCount += 1

            if partName == "FLT":
                requiredFLT = round(displacement*litersPerDisplacement * (1 + (litersPerTon*weight)), 2)
                fuelTankSize = [partInfo["L"]]
                if int(partInfo["L"]) < requiredFLT:
                    report = await textTools.addLine(report,f"Your internal fuel tank has {int(partInfo['L'])}L of fuel, but needs {requiredFLT}L of fuel in order to perform adequately.")
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
                        f"Your tack belt is {beltWidth}mm wide.  This is too narrow and will lead to bad off-road performance.  Increase your track width to at least {beltWidthMin}mm.")
                    errorCount += 1
                if round(trackSystemWidth, 3) > hullWidthMax:
                    report = await textTools.addLine(report,
                        f"Your tack system is {round(trackSystemWidth, 2)} meters wide.  This is too wide for your railways, which can only support vehicles up to {hullWidthMax} meters wide.")
                    errorCount += 1
                if trackSystemWidth >= overallTankWidth:
                    overallTankWidth = round(trackSystemWidth, 3)
                try:
                    torsionBarLength = float(partInfo["suspensions"]["TBLength"])
                    if useDynamicTBlength == True:
                        torsionBarLengthMin = torsionBarLengthMin * separation
                    if round(torsionBarLength, 3) < torsionBarLengthMin:
                        report = await textTools.addLine(report, f"Your torsion bar is {torsionBarLength}m wide.  This is too short and will lead to bad off-road performance.  Increase your torsion bar length to at least {torsionBarLengthMin}m.")
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
            "crewReport": crewReport,
            "turretCount": turretCount,
            "GCMratioMin": GCMratioMin,
            "maxArmor": maxArmorOverall,
            "gameVersion": gameVersion,
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

    @commands.command(name="setupDatabase2", description="Wipe literally everything.")
    async def cog5(self, ctx):
        await ctx.send(content="Hello!")

async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(blueprintFunctions(bot))