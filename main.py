import datetime
# import asyncio
utc = datetime.timezone.utc

# If no tzinfo is given then UTC is assumed.
from pathlib import Path
import os
import platform
import discord
import json
import copy
from discord.ext import tasks, commands
from discord.ui import View
import random
import time
from random import random

description = '''A list of all available commands.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Determines whether this is the live version of the bot or the testing version.

# development settings (running on Windows/PyCharm)
if platform.system() == "Windows":
    SECRETSpath = "C:\\SprocketBot\\tokenSecrets.json"
    fileObject = open(SECRETSpath, "r")
    jsonContent = fileObject.read()
    with open(SECRETSpath, "r") as fileObject:
        secretsList = json.loads(fileObject.read())
    COUNTRIESpath = "countries.json"
    CONFIGpath = "config.json"
    TANKSpath = "tanksInfo.json"
    INVENTORYpath = "tanksInventory.json"
    MANUFACTURINGpath = "tanksAssembly.json"
    OPERATORSpath = "companyOperators.json"
    RESEARCHpath = "research-in-progress.json"
    BLIMPpath = "blimpsInfo.json"
    FUNFACTSpath = "fun-facts.json"
    PRODUCTIONpath = "productionPaths.json"
    CONSOLELOGpath = "log.txt"
    CONTESTSpath = "contestInfo.json"
    client_id = '1139195875994910740'
    token = secretsList[1] # testing bot token
    channel_id = '1152377925916688484'
    TANKrepository = "\\tankCatalog\\"
    OSslashLine = "\\"
    prefix = "?"

else:
    # default settings (running on Rasbian)
    directory = "/home/mumblepi/sprocket_bot/"
    SECRETSpath = "/home/mumblepi/tokenSecrets.json"
    fileObject = open(SECRETSpath, "r")
    jsonContent = fileObject.read()
    with open(SECRETSpath, "r") as fileObject:
        secretsList = json.loads(fileObject.read())
    COUNTRIESpath = directory + "countries.json"
    TANKSpath = directory + "tanksInfo.json"
    CONFIGpath = directory + "config.json"
    INVENTORYpath = directory + "tanksInventory.json"
    MANUFACTURINGpath = directory + "tanksAssembly.json"
    OPERATORSpath = directory + "companyOperators.json"
    RESEARCHpath = directory + "research-in-progress.json"
    BLIMPpath = directory + "blimpsInfo.json"
    PRODUCTIONpath = directory + "productionPaths.json"
    FUNFACTSpath = directory + "fun-facts.json"
    CONSOLELOGpath = directory + "log.txt"
    CONTESTSpath = directory + "contestInfo.json"
    client_id = "1137847253114040330"
    token = secretsList[0] # official bot token
    channel_id = '1142053482371756062'
    TANKrepository = directory + "tankCatalog/"
    OSslashLine = "/"
    prefix = "-"

bot = commands.Bot(command_prefix=prefix, description=description, intents=intents, help_command=None)

# opens the JSON file and establishes settings
fileObject = open(COUNTRIESpath, "r")
jsonContent = fileObject.read()
with open(COUNTRIESpath, "r") as fileObject:
    variablesList = json.loads(fileObject.read())
    variablesListOriginal = copy.deepcopy(variablesList)

fileObject = open(OPERATORSpath, "r")
jsonContent = fileObject.read()
with open(OPERATORSpath, "r") as fileObject:
    operatorsList = json.loads(fileObject.read())
    operatorsListOriginal = copy.deepcopy(operatorsList)

fileObject = open(MANUFACTURINGpath, "r")
jsonContent = fileObject.read()
with open(MANUFACTURINGpath, "r") as fileObject:
    manufacturingList = json.loads(fileObject.read())
    manufacturingListOriginal = copy.deepcopy(manufacturingList)

fileObject = open(TANKSpath, "r")
jsonContent = fileObject.read()
with open(TANKSpath, "r") as fileObject:
    tanksList = json.loads(fileObject.read())
    tanksListOriginal = copy.deepcopy(tanksList)

fileObject = open(FUNFACTSpath, "r")
jsonContent = fileObject.read()
with open(FUNFACTSpath, "r") as fileObject:
    funfactsList = json.loads(fileObject.read())
    funfactsListOriginal = copy.deepcopy(funfactsList)

fileObject = open(INVENTORYpath, "r")
jsonContent = fileObject.read()
with open(INVENTORYpath, "r") as fileObject:
    inventoryList = json.loads(fileObject.read())
    inventoryListOriginal = copy.deepcopy(inventoryList)

fileObject = open(RESEARCHpath, "r")
jsonContent = fileObject.read()
with open(RESEARCHpath, "r") as fileObject:
    researchList = json.loads(fileObject.read())
    researchListOriginal = copy.deepcopy(researchList)
    print(researchList)

fileObject = open(CONFIGpath, "r")
jsonContent = fileObject.read()
with open(CONFIGpath, "r") as fileObject:
    settingsList = json.loads(fileObject.read())
    settingsListOriginal = copy.deepcopy(settingsList)

fileObject = open(BLIMPpath, "r")
jsonContent = fileObject.read()
with open(BLIMPpath, "r") as fileObject:
    blimpList = json.loads(fileObject.read())
    blimpListOriginal = copy.deepcopy(settingsList)

fileObject = open(PRODUCTIONpath, "r")
jsonContent = fileObject.read()
with open(PRODUCTIONpath, "r") as fileObject:
    productionList = json.loads(fileObject.read())
    productionListOriginal = copy.deepcopy(settingsList)

fileObject = open(CONTESTSpath, "r")
jsonContent = fileObject.read()
with open(CONTESTSpath, "r") as fileObject:
    contestsList = json.loads(fileObject.read())
    contestsListOriginal = copy.deepcopy(settingsList)

time = [
    datetime.time(hour=23, minute=58, tzinfo=utc)
]

times = [
    datetime.time(hour=0, tzinfo=utc),
    datetime.time(hour=3, minute=30, tzinfo=utc),
    datetime.time(hour=7, tzinfo=utc),
    datetime.time(hour=10, minute=30, tzinfo=utc),
    datetime.time(hour=14, tzinfo=utc),
    datetime.time(hour=17, minute=30, tzinfo=utc),
    datetime.time(hour=21, tzinfo=utc)
]

backuptime = [
    datetime.time(hour=0, minute=5, tzinfo=utc),
    datetime.time(hour=1, minute=5, tzinfo=utc),
    datetime.time(hour=2, minute=5, tzinfo=utc),
    datetime.time(hour=3, minute=5, tzinfo=utc),
    datetime.time(hour=4, minute=5, tzinfo=utc),
    datetime.time(hour=5, minute=5, tzinfo=utc),
    datetime.time(hour=6, minute=5, tzinfo=utc),
    datetime.time(hour=7, minute=5, tzinfo=utc),
    datetime.time(hour=8, minute=5, tzinfo=utc),
    datetime.time(hour=9, minute=5, tzinfo=utc),
    datetime.time(hour=10, minute=5, tzinfo=utc),
    datetime.time(hour=11, minute=5, tzinfo=utc),
    datetime.time(hour=12, minute=5, tzinfo=utc),
    datetime.time(hour=13, minute=3, tzinfo=utc),
    datetime.time(hour=14, minute=4, tzinfo=utc),
    datetime.time(hour=15, minute=3, tzinfo=utc),
    datetime.time(hour=16, minute=5, tzinfo=utc),
    datetime.time(hour=17, minute=5, tzinfo=utc),
    datetime.time(hour=18, minute=5, tzinfo=utc),
    datetime.time(hour=19, minute=5, tzinfo=utc),
    datetime.time(hour=20, minute=5, tzinfo=utc),
    datetime.time(hour=21, minute=5, tzinfo=utc),
    datetime.time(hour=22, minute=5, tzinfo=utc),
    datetime.time(hour=23, minute=5, tzinfo=utc),
    datetime.time(hour=23, minute=57, tzinfo=utc)
]

# load modifiers
costPerTon = int(settingsList["costPerTon"])
fundsToAdvanceLevel = int(settingsList["fundsToAdvanceLevel"])
countryScalar = int(settingsList["countryResearchCostScalar"])
productionRate = settingsList["productionRate"]
maxLevel = int(settingsList["maxLevel"])
costToAddProduction = int(settingsList["costToAddProduction"])
cannonWeights = settingsList["cannonWeights"].items()
print(cannonWeights)
# x = 20
# i = 0
# while i < 25:
#     x += (10+(10*i))
#     print(f"    \"{i}\": \"{x}\",")
#     i += 1

# Arrays for using with tech levels
cannonWeights = [120, 198, 276, 355, 433, 511, 590, 668, 746, 825, 903, 981, 1060, 1138, 1216, 1295, 1373, 1451, 1530, 1608, 1686, 1765, 1843, 1921, 2000]
# propellantLengths = [200, 215, 240, 270, 300, 340, 385, 500, 600, 750, 950, 1200, 1200, 1200, 1200, 1200, 1200, 1200, 1200, 1200, 1200, 1200, 1200, 1200, 1200]
shellLengths = [350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350, 1350, 1400, 1450, 1500, 1550]
boreLengths = [2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.6, 5.8, 6.0, 6.2, 6.4, 6.6, 6.8, 7.0]
netDisplacement = [3.6, 4.2, 4.8, 5.6, 7.0, 8.5, 10.5, 14, 17, 20, 22, 24.5, 28, 32, 36, 40, 45, 50, 55, 60, 65, 70, 74, 77, 80]
weightLimit = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135]
armorThickness = [50, 57, 65, 73, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 225, 230, 235, 240, 245, 250]
GCMtorque = [200, 275, 350, 425, 500, 575, 650, 725, 800, 875, 950, 1025, 1100, 1175, 1250, 1325, 1400, 1475, 1550, 1625, 1700, 1775, 1850, 1925, 2000]
GCMratio = [75, 73, 71, 69, 67, 65, 63, 61, 59, 57, 55, 53, 51, 49, 47, 45, 43, 41, 39, 37, 35, 33, 31, 29, 25]
railwayGauges = ["narrow", "standard", "wide"]
railwayGaugeLimits = [2.6, 3.2, 3.6]
upgradeRailwayCostScalar = 120
railwayResearchRate = 0.25 # time in Zheifu weeks
# howitzerLength = [0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
# howitzerWeights = [150, 248, 345, 444, 541, 639, 738, 919, 1026, 1134, 1242, 1349, 1458, 1565, 1672, 1781, 2060, 2177, 2295, 2412, 2529, 2648, 2765, 2882, 3000]
contractorsChat = 1145273573708140595
blimpLogChat = 1155266268895641680
tankLogChat = 1156854471767367680
factoryRepairSpeed = 0.08
blimpCapacity = 80
tonsPerDay = 2.5
gunCount = 34
baseTechValue = 0
taxableCitizensPortion = 0.1
costToBuyFactory = 5000000
researchSpeed = 0.725
companyWeeksToResearch = 0.51
strategyCost = 50000
advanceTime = True
themes = ["Steampunk or Interwar", "Interwar through Early WWII", "Early WWII", "Middle of WWII", "Closing of WWII", "Postwar", "Early Cold War"]
themeCount = len(themes)
focusSchools = ["madurai", "vazarin", "naramon", "unairu", "zenurik"]

industryNames = ["Amogus", "Exponential", "Epic Failure", "Kerbal", "Vatican", "Howard Jones", "", "Overcharge", "TM™", "Cursed", "The Funny:tm:", "Microsoft", "404", "Entrati", "Miracle", "Overlord", "Overpressure", "Tactical Ballistics", "Astroneer's", "Orokin Bioengineering", "The Definitely Legitimate", "Adolf's Art School &", "Suspicious", "Sus Amogus", "Zeus' Potato Slingshot", "Golfing Paradise", "Flork", "Otto's Inflatable"]
industryCount = len(industryNames)

industryTypes = ["Research Group", "Labs", "inc.", "Research Conglomerate", "University", "College", "Elementary School", "Preschool", "Laboratories", "Research", "Scopolamine Lab"]
industryTypeCount = len(industryTypes)

blimpSpeed = 150

async def advanceDay():
    print("Hi!")
    selectedKeys = list()
    channel = bot.get_channel(int(channel_id))
    funFactRandom = round(((len(funfactsList)-1)*random()))
    await channel.send("### A new day has began in the wonderful lands of Zheifu! \n Fun fact: " + funfactsList[str(funFactRandom)])
    print("This should run at whatever time you set it to run at!")

    # for manufacturingID, tankInfo in manufacturingList.items():
    #     tankName = tankInfo["name"]
    #     country = tankInfo["country"]
    #     tankInfo["progress"] = float(tankInfo["progress"]) + float(tankInfo["rate"])
    #     if float(tankInfo["progress"]) > 0.995:
    #         inventoryList[country][tankName]["stored"] = float(inventoryList[country][tankName]["stored"]) + 1
    #         countryChannel = bot.get_channel(int(variablesList[country][0]["channel"]))
    #         if variablesList[country][0]["autoBuild"] == "false":
    #             selectedKeys.append(manufacturingID)
    #             variablesList[country][0]["unspentTonnage"] = float(variablesList[country][0]["unspentTonnage"]) + float(inventoryList[country][tankName]["weight"])
    #             # await countryChannel.send(f"A {tankName} has finished assembly!")
    #         if variablesList[country][0]["autoBuild"] == "true":
    #             tankInfo["progress"] = 0
    #             variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - int(tankInfo["cost"])
    #             # await countryChannel.send(f"A {tankName} has finished assembly!  Auto Build is enabled for {country}, so another {tankName} is now being built.")
    #         print(tankName)
    #
    # for key in selectedKeys:
    #     if key in manufacturingList:
    #         del manufacturingList[key]

    for country, countryInfo in variablesList.items():
        costScale = 1
        if countryInfo[0]["type"] == "country":
            costScale = 10
        if int(countryInfo[0]["money"]) < 0 and countryInfo[0]["type"] == "country":
            countryInfo[0]["populationHappiness"] = int(countryInfo[0]["populationHappiness"]) - 2

        if countryInfo[0]["focus"] == "research":
            countryInfo[0]["money"] = int(countryInfo[0]["money"]) - strategyCost*costScale
        if countryInfo[0]["focus"] == "building":
            countryInfo[0]["money"] = int(countryInfo[0]["money"]) - strategyCost*costScale

    researchListEdit = [0]
    researchListEdit = dict(researchList)
    # print(researchList)
    # print(researchListEdit)
    for country, researchType in researchListEdit.items():
        # print(researchType)
        deletionKeys = list()
        focus = variablesList[country][0]["focus"]
        focusedResearchBoost = 1
        if focus == "research":
            focusedResearchBoost = 1.5
        if focus == "building":
            focusedResearchBoost = 0.5
        researchNerf = 1
        if variablesList[country][0]["type"] == "country":

            if int(variablesList[country][0]["populationHappiness"]) < 50:
                researchNerf = researchNerf * (int(variablesList[country][0]["populationHappiness"]) / 50)

        for type, info in researchType.items():
            type = type.lower()
            # print(info)
            # researchList[country][type]["progress"] = float(info["progress"]) + researchSpeed*float(info["rate"])/7
            print(info["progress"])
            info["progress"] = float(info["progress"]) + (researchSpeed * focusedResearchBoost * researchNerf * float(info["rate"]) / 7)
            print(info["progress"])
            print("intended rate of advance:" + str(researchSpeed * float(info["rate"]) / 7))
            if float(info["progress"]) > 0.995:
                variablesList[country][0][type+"Tech"] = int(variablesList[country][0][type+"Tech"]) + 1
                if variablesList[country][0]["autoResearch"] == "true":
                    info["progress"] = 0
                    if variablesList[country][0]["type"] == "country":
                        variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - int(fundsToAdvanceLevel*countryScalar)
                    else:
                        variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - int(fundsToAdvanceLevel)
                    countryChannel = bot.get_channel(int(variablesList[country][0]["channel"]))
                    try:
                        await countryChannel.send(country + " has finished researching and retooling for " + type + " upgrades!  Progress has been launched to begin the next upgrade.")
                    except Exception:
                        pass
                if variablesList[country][0]["autoResearch"] == "false":
                    countryChannel = bot.get_channel(int(variablesList[country][0]["channel"]))
                    try:
                        await countryChannel.send(country + " has finished researching and retooling for " + type + " upgrades!")
                    except Exception:
                        pass
                    deletionKeys.append(type)
        for key in deletionKeys:
            del researchList[country][key]

    # researchList = researchListEdit.copy()


    # print(researchList)
    # print("\n")

    #blimps
    selectedBlimps = list()
    for blimpName, blimpInfo in blimpList.items():
        print(blimpInfo)
        if blimpInfo['status'] == 'active':
            blimpInfo['miles_travelled'] = int(blimpInfo['miles_travelled']) + blimpSpeed
            blimpCountry = blimpInfo['origin']
            channel = bot.get_channel(variablesList[blimpCountry][0]["channel"])
            if int(blimpInfo['miles_travelled']) >= int(blimpInfo['travel_goal']):
                riskLevel = int(blimpInfo['riskLevel'])
                blimpRoll = 100*random()
                tankName = blimpInfo['stowage']
                if blimpRoll < riskLevel: # cargo failed
                    await channel.send(f"{blimpName} lost its cargo when trying to land!  While the ship is repairable, its cargo is irrecoverable.")
                    blimpInfo['status'] = 'returning'
                elif blimpRoll < 2*riskLevel: #return failed
                    await channel.send(f"{blimpName} was destroyed shortly after delivering its tanks!  While the ship is irrecoverable, the tanks it was carrying are still able to fight.")
                    inventoryList[blimpCountry][tankName]['stored'] = int(inventoryList[blimpCountry][tankName]['stored']) + int(blimpInfo['count'])
                elif blimpRoll < 3*riskLevel: # ship was destroyed
                    await channel.send(f"{blimpName} was destroyed while en route to its destination!")
                else: # success
                    await channel.send(f"{blimpName} was able to successfully deploy its cargo and is now en route back home.")
                    inventoryList[blimpCountry][blimpInfo['stowage']]['stored'] = int(inventoryList[blimpCountry][tankName]['stored']) + int(blimpInfo['count'])
                    blimpInfo['status'] = 'returning'

        if blimpInfo['status'] == 'returning':
            blimpInfo['miles_travelled'] = int(blimpInfo['miles_travelled']) - blimpSpeed
            if int(blimpInfo['miles_travelled']) < 2:
                blimpCountry = blimpInfo['origin']
                channel = bot.get_channel(variablesList[blimpCountry][0]["channel"])
                blimpInfo['stowage'] = "empty"
                blimpInfo['count'] = 0
                blimpInfo['miles_travelled'] = 0
                blimpInfo['travel_goal'] = 5000
                blimpInfo['status'] = "idle"
                blimpInfo['riskLevel'] = 0
                await channel.send(f"{blimpName} has made it home safely, and is now ready to transport additional tanks.")

    # Production Lines 2.0


    for country, productionLines in productionList.items():
        focus = variablesList[country][0]["focus"]
        focusedResearchBoost = 1
        focusedBuildingBoost = 1
        if focus == "research":
            focusedBuildingBoost = 0.5
        if focus == "building":
            focusedBuildingBoost = 1.5
        for productionLine, lineInfo in productionLines.items():
            if lineInfo["status"] == "under construction":
                lineInfo["factoryHealth"] = float(lineInfo["factoryHealth"]) + factoryRepairSpeed*focusedBuildingBoost
                # If the factory is fully assembled, begin construction:
                if float(lineInfo["factoryHealth"]) > 0.99:
                    lineInfo["factoryHealth"] = 1
                    lineInfo["status"] = "idle"
                    # If a tank is queued, set the factory to begin assembly of it:
                    if lineInfo["nextTank"] != "":
                        lineInfo["status"] = "building"
                        lineInfo["currentTank"] = lineInfo["nextTank"]
                        lineInfo["currentTankWeight"] = lineInfo["nextTankWeight"]
                        lineInfo["currentTankProgress"] = 0

            # perform this action if a tank is being built
            if lineInfo["status"] == "building":
                tankName = lineInfo["currentTank"]
                nextTankName = lineInfo["nextTank"]
                # print(tankName + "  aa")
                productionRateVal = await getProductionRate(tankName)
                if variablesList[country][0]["type"] == "country":
                    if int(variablesList[country][0]["populationHappiness"]) < 50:
                        productionRateVal = productionRateVal * (int(variablesList[country][0]["populationHappiness"])/50)
                try:
                    timeScalar = float(tanksList[tankName]["buildTimeScalar"])
                except Exception:
                    timeScalar = 1.0
                lineInfo["currentTankProgress"] = float(lineInfo["currentTankProgress"]) + productionRateVal*focusedBuildingBoost*timeScalar
                if float(lineInfo["currentTankProgress"]) > 0.995:
                    inventoryList[country][tankName]["stored"] = float(inventoryList[country][tankName]["stored"]) + 1
                    tankCountry = tanksList[tankName]["origin"]
                    tons = tanksList[tankName]["weight"]
                    cost = 50000
                    if country == tankCountry:
                        cost = round(pow((float(tons) * costPerTon), 1.1))
                    if country != tankCountry and variablesList[tankCountry][0]["type"] == "company" and inventoryList[country][tankName]["type"] == "foreign":
                        cost = round(pow((float(tons) * costPerTon), 1.1)) + int(tanksList[tankName]["licenseFee"])
                        variablesList[tankCountry][0]["money"] = int(variablesList[tankCountry][0]["money"]) + int(tanksList[tankName]["licenseFee"])
                    if tankName == "2.5T Transport Truck":
                        cost = -50000
                    if tankName == "7.5T Flatbed Transporter":
                        cost = -150000
                    lineInfo["currentTank"] = lineInfo["nextTank"]
                    lineInfo["currentTankWeight"] = lineInfo["nextTankWeight"]
                    lineInfo["currentTankProgress"] = 0
                    if lineInfo["currentTank"] == "":
                        lineInfo["status"] = "idle"
                    else:
                        lineInfo["status"] = "building"
                        tons = tanksList[tankName]["weight"]
                        tankCountry = tanksList[tankName]["origin"]
                        # if country == tankCountry:
                        #     cost = round(pow((float(tons) * costPerTon), 1.1))
                        # if country != tankCountry and variablesList[tankCountry][0]["type"] == "company" and inventoryList[country][tankName]["type"] == "foreign":
                        #     cost = round(pow((float(tons) * costPerTon), 1.1)) + int(tanksList[tankName]["licenseFee"])
                        #     variablesList[tankCountry][0]["money"] = int(variablesList[tankCountry][0]["money"]) + int(tanksList[tankName]["licenseFee"])
                        if tankName == "2.5T Transport Truck":
                            cost = -50000
                        if tankName == "7.5T Flatbed Transporter":
                            cost = -150000
                        # variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - cost
                    countryChannel = bot.get_channel(int(variablesList[country][0]["channel"]))
                    await countryChannel.send(f"A {tankName} has finished assembly!  Auto Build is enabled for {country}, so another {tankName} is now being built.")
                    # print(tankName)

async def advanceWeek():
    from datetime import datetime
    selectedKeys = list()
    channel = bot.get_channel(int(channel_id))

    for country, countryInfo in variablesList.items():
        if variablesList[country][0]["type"] == "country":
            # variable definition
            taxRate = int(variablesList[country][0]["taxRate"])*0.01
            population = int(variablesList[country][0]["populationCount"])
            income = int(variablesList[country][0]["averageIncome"])
            happiness = int(variablesList[country][0]["populationHappiness"])
            totalIncome = int(variablesList[country][0]["populationCount"])*int(variablesList[country][0]["averageIncome"])*taxableCitizensPortion
            armyCut = int(totalIncome * int(variablesList[country][0]["taxRate"])*int(variablesList[country][0]["taxPercentToArmy"])/(100*100))
            variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) + armyCut

            if taxRate <= 0.19:
                variablesList[country][0]["averageIncome"] = income + (0.25/(taxRate+0.08))
                variablesList[country][0]["populationHappiness"] = happiness + (0.24/(taxRate+0.09))

            if float(variablesList[country][0]["averageIncome"]) > 110:
                variablesList[country][0]["averageIncome"] = 110

            if float(variablesList[country][0]["populationHappiness"]) > 100:
                variablesList[country][0]["populationHappiness"] = 100

            if taxRate >= 0.26:
                variablesList[country][0]["averageIncome"] = income - ((taxRate+0.05)/0.25)
                variablesList[country][0]["populationHappiness"] = happiness - ((taxRate - 0.25)*1.5)

    await channel.send("## Finances have been updated for all countries.")


@tasks.loop(time=times)
async def daily_cycle():
    if advanceTime == True:
        await advanceDay()

@tasks.loop(time=time)
async def weekly_cycle():
    if advanceTime == True:
        await advanceWeek()

@tasks.loop(time=backuptime)
async def backup_cycle():
    await backupFiles()
async def async_initialisation():
    daily_cycle.start()
    weekly_cycle.start()
    backup_cycle.start()
    print("hi!!!")

bot.setup_hook = async_initialisation

@bot.event
async def on_ready():
    channel = bot.get_channel(1152377925916688484)
    await channel.send("I am now online!")

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def The(ctx):
    message = ctx.message
    url = message.jump_url
    # msg = await ctx.fetch_message(id=ctx.message_id)
    await ctx.send(url)
    view = Confirm()
    # link = 'https://discordapp.com/channels/guild_id/channel_id/message_id'.split('/')
    # message = await ctx.bot.get_guild(int(link[-3])).get_channel(int(link[-2])).fetch_message(int(link[-1]))

    # await ctx.send(ctx.jump_url)
    await ctx.reply(view=view)
    await ctx.send("testing")

class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Amogus', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # await interaction.response.send_message('Confirming', ephemeral=True)
        await interaction.response.send_message("Why.")
        print("Hi!")
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Sus', style=discord.ButtonStyle.grey, custom_id='lol')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Ew.')
        self.value = False
        self.stop()
    @discord.ui.button(label='SusL', style=discord.ButtonStyle.grey)
    async def cancela(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Ew.')
        self.value = False
        self.stop()
    @discord.ui.button(label='SusA', style=discord.ButtonStyle.grey)
    async def cancelaa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Ew.')
        self.value = False
        self.stop()
    @discord.ui.button(label='SusAA', style=discord.ButtonStyle.grey)
    async def cancelaaa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Ew.')
        self.value = False
        self.stop()
    @discord.ui.button(label='SusAAAA', style=discord.ButtonStyle.grey)
    async def cancelaaaa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Ew.')
        self.value = False
        self.stop()
    @discord.ui.button(label='Susaa', style=discord.ButtonStyle.grey)
    async def cancesl(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Ew.')
        self.value = False
        self.stop()
    @discord.ui.button(label='fgkmdfkjghbnfdkjnbg', style=discord.ButtonStyle.grey)
    async def cancelf(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Ew.')
        self.value = False
        self.stop()
    @discord.ui.button(label='Sussy', style=discord.ButtonStyle.grey)
    async def cancsdel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Ew.')
        self.value = False
        self.stop()

class Dropdown(discord.ui.Select):
    def __init__(self, country):

        self.country = country
        # Set the options that will be presented inside the dropdown
        options = [
        ]
        print(country)
        for tank, tankInfo in tanksList.items():
            print(tank)
            if(tankInfo["origin"] == country):
                options.append(discord.SelectOption(label=tank, description=(f"weight: {tankInfo['weight']} tons"), emoji='🟩'))

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Choose a tank...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        await interaction.response.send_message(f'You selected the {self.values[0]}')

class DropdownView(discord.ui.View):
    def __init__(self, country):
        super().__init__()
        self.country = country
        # Adds the dropdown to our view object.
        self.add_item(Dropdown(country))

@bot.command()
async def The_Funny(ctx):
    await ctx.send(file=discord.File('The Funny Sound Effect.mp3'))

@bot.command()
async def upgradeRailways(ctx):
    country = await getUserCountry(ctx)
    if variablesList[country][0]["type"] == "company":
        await ctx.send("https://tenor.com/view/you-dont-have-to-do-this-kyle-south-park-dont-do-it-please-stop-gif-21229609")
        await ctx.send("You are a company that does not maintain rail lines.")
        return

    gauge = railwayGauges[variablesList[country][0]["railGauge"]]
    if variablesList[country][0]["railGauge"] == "wide":
        await ctx.send("Your railways cannot be upgraded further!  Enjoy the sense of achievement from spending insane amounts of your money just to build a pancake tank.")
        return
    await ctx.send(f"You currently have {variablesList[country][0]['railGauge']}-gauge railways supporting tanks up to {gauge} meters wide.  ")



@bot.command()
async def tankTesting(ctx):
    """Sends a message with our dropdown containing colours"""
    country = await getUserCountry(ctx)
    print(country + "            AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    # Create the view containing our dropdown
    view = DropdownView(country)

    # Sending a message containing our view
    await ctx.send('Pick a tank from the list:', view=view)

@bot.command()
async def reset (ctx, countryReset: str):
    channel = bot.get_channel(1142053482371756062)
    await channel.send(variablesList[countryReset][0]["displayName"] + " was doing too good, so they've been reset to how things were when the contest started.")
    print("This should run at whatever time you set it to run at!")
    deleteKeys = list()
    for tankName, tankInfo in manufacturingList.items():
        if tankInfo["country"] == countryReset:
            deleteKeys.append(tankName)
    for key in deleteKeys:
        if key in manufacturingList:
            del manufacturingList[key]

    deleteKeys = list()
    for tankName, tankInfo in tanksList.items():
        if tankInfo["country"] == countryReset:
            deleteKeys.append(tankName)
    for key in deleteKeys:
        if key in tanksList:
            del tanksList[key]

    variablesList[countryReset] = variablesListOriginal[countryReset]

@bot.command()
async def reloadEverything (ctx):
    fileObject = open(COUNTRIESpath, "r")
    jsonContent = fileObject.read()
    with open(COUNTRIESpath, "r") as fileObject:
        variablesList = json.loads(fileObject.read())
        variablesListOriginal = copy.deepcopy(variablesList)

    fileObject = open(OPERATORSpath, "r")
    jsonContent = fileObject.read()
    with open(OPERATORSpath, "r") as fileObject:
        operatorsList = json.loads(fileObject.read())
        operatorsListOriginal = copy.deepcopy(operatorsList)

    fileObject = open(MANUFACTURINGpath, "r")
    jsonContent = fileObject.read()
    with open(MANUFACTURINGpath, "r") as fileObject:
        manufacturingList = json.loads(fileObject.read())
        manufacturingListOriginal = copy.deepcopy(manufacturingList)

    fileObject = open(TANKSpath, "r")
    jsonContent = fileObject.read()
    with open(TANKSpath, "r") as fileObject:
        tanksList = json.loads(fileObject.read())
        tanksListOriginal = copy.deepcopy(tanksList)

    fileObject = open(FUNFACTSpath, "r")
    jsonContent = fileObject.read()
    with open(FUNFACTSpath, "r") as fileObject:
        funfactsList = json.loads(fileObject.read())
        funfactsListOriginal = copy.deepcopy(funfactsList)

    fileObject = open(INVENTORYpath, "r")
    jsonContent = fileObject.read()
    with open(INVENTORYpath, "r") as fileObject:
        inventoryList = json.loads(fileObject.read())
        inventoryListOriginal = copy.deepcopy(inventoryList)

    fileObject = open(BLIMPpath, "r")
    jsonContent = fileObject.read()
    with open(BLIMPpath, "r") as fileObject:
        blimpList = json.loads(fileObject.read())
        blimpListOriginal = copy.deepcopy(inventoryList)



    await ctx.send("Configs reloaded!")


@bot.command()
@commands.has_role("Campaign Manager")
async def deleteTank (ctx, tankDelete: str):
    deleteKeys = list()
    for tankName, tankInfo in manufacturingList.items():
        if tankInfo["name"] == tankDelete:
            print(tankName)
            country = tankInfo["country"]
            variablesList[country][0]["unspentTonnage"] = float(variablesList[country][0]["unspentTonnage"]) + float(tanksList[tankInfo["name"]]["weight"])
            deleteKeys.append(tankName)
    for key in deleteKeys:
        if key in manufacturingList:
            del manufacturingList[key]
    print("A")
    deleteKeys = list()
    for tankName, tankInfo in tanksList.items():
        if tankName == tankDelete:
            deleteKeys.append(tankName)
    for key in deleteKeys:
        if key in deleteKeys:
            del tanksList[tankDelete]
    print("B")
    deleteKeys = list()
    for country, tankCatalog in inventoryList.items():
        for tankName, tankInfo in tankCatalog.items():
            if tankName == tankDelete:
                deleteKeys.append(tankName)
        for key in deleteKeys:
            if key in inventoryList[country]:
                del inventoryList[country][tankDelete]


    await ctx.send("I have wiped the " + tankDelete + " from inventory.")
    await ctx.send("Note that no refunds were issued, " + ctx.channel.name + " just took them out on a parade tour and auctioned them off at the local for-charity event. \n  Take note that this probably shouldn't be ran for company tanks, once someone has already purchased them.")

@bot.command()
async def stopProduction (ctx, *, tankDelete):
    country = await getUserCountry(ctx)
    userCountry = country
    count = 0
    deleteKeys = list()
    for tankName, tankInfo in manufacturingList.items():
        if tankInfo["name"] == tankDelete and tankInfo["country"] == userCountry:
            # print(tankName)
            country = tankInfo["country"]
            variablesList[country][0]["unspentTonnage"] = float(variablesList[country][0]["unspentTonnage"]) + float(tanksList[tankInfo["name"]]["weight"])
            deleteKeys.append(tankName)
            # print(tankName)
    for key in deleteKeys:
        if key in manufacturingList and manufacturingList[key]["country"] == userCountry:
            del manufacturingList[key]
            count += 1
    await ctx.send(f"{count}x {tankDelete} have been cancelled and removed from the factory line.")









@bot.command()
async def decommissionTank (ctx, *, tankDelete):
    country = await getUserCountry(ctx)
    userCountry = country
    print(country)
    try:
        cost = tanksList[tankDelete]["cost"]
        count = int(inventoryList[country][tankDelete]["stored"]) + int(inventoryList[country][tankDelete]["deployed"]) + int(inventoryList[country][tankDelete]["deployedAbroad"])
    except Exception:
        await ctx.send("Tank name is invalid!")
        return

    deleteKeys = list()
    for tankName, tankInfo in manufacturingList.items():
        if tankInfo["name"] == tankDelete and tankInfo["country"] == userCountry:
            print(tankName)
            country = tankInfo["country"]
            variablesList[country][0]["unspentTonnage"] = float(variablesList[country][0]["unspentTonnage"]) + float(tanksList[tankInfo["name"]]["weight"])
            deleteKeys.append(tankName)
    for key in deleteKeys:
        if key in manufacturingList:
            del manufacturingList[key]
    print("A")
    print("B")
    deleteKeys = list()
    for country, tankCatalog in inventoryList.items():
        for tankName, tankInfo in tankCatalog.items():
            if tankName == tankDelete and country == userCountry:
                deleteKeys.append(tankName)
        for key in deleteKeys:
            if key in inventoryList[country] and country == userCountry:
                del inventoryList[country][tankDelete]
    variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) + (cost*count)
    await ctx.send(f"{count}x {tankDelete} have been successfully decommissioned!  ฿{cost*count} of funding has been earned from their sale.")







@bot.command()
async def deployTank(ctx, tankCount: int, *, tankName):
    """Adds two numbers together."""
    # try:
    country = await getUserCountry(ctx)
    # except Exception:
    #     await ctx.send("You're not a country!  You can't deploy tanks to fight!")
    #     return
    try:
        inStorage = inventoryList[country][tankName]["stored"]
        if int(inStorage) >= int(tankCount):
            inventoryList[country][tankName]["stored"] = int(inStorage) - int(tankCount)
            inventoryList[country][tankName]["deployed"] = int(inventoryList[country][tankName]["deployed"]) + int(tankCount)
            await ctx.send("Successfully deployed " + str(tankCount) + "x " + tankName + "!")
        else:
            await ctx.send("\"The commander said to deploy " + str(tankCount) + " of these... wait, where did they go?\" \n \n Make sure you actually have sufficient tanks in storage before trying to deploy them.")

    except KeyError as ke:

        try:
            testVal = variablesList[country][0]["intelSize"]
            country = ctx.channel.name
            print(testVal)
            await ctx.send("This tank doesn't exist in your inventory!")
        except Exception:
            await ctx.send("I'd be interested to watch an actual company-on-country war take place, but my precepts dictate I cannot allow a company to deploy vehicles to a standing army.")

@bot.command()
@commands.has_role('Campaign Manager')
async def addTonnage(ctx, money: int, *, country):
    """Adds two numbers together."""
    countryDisplay = variablesList[country][0]["displayName"]
    # variablesList[country][0]["money"] = variablesList[country][0]["money"] + money
    variablesList[country][0]["unspentTonnage"] = float(variablesList[country][0]["unspentTonnage"]) + float(money)
    await ctx.send("You added {0} to {1}\'s factory capacity.".format(str(money), countryDisplay))
    await ctx.send("Their total available tonnage is now " + str(variablesList[country][0]["unspentTonnage"]) + " tons.")

@bot.command()
@commands.has_role('Campaign Manager')
async def addMoney(ctx, money: int, *, country):
    """Adds two numbers together."""
    countryDisplay = variablesList[country][0]["displayName"]
    variablesList[country][0]["money"] = variablesList[country][0]["money"] + money
    # variablesList[country][0]["unspentTonnage"] = float(variablesList[country][0]["unspentTonnage"]) + float(money)
    await ctx.send("You added {0} to {1}\'s money supply.".format(str(money), countryDisplay))
    await ctx.send("Their total cash is now ฿" + str(variablesList[country][0]["money"]))

@bot.command()
async def friendlyResearchReset(ctx):
    for country, countryInfo in variablesList.items():
        try:
            for researchItem, info in researchList[country].items():
                variablesList[country][0][f"{researchItem}Tech"] = int(variablesList[country][0][f"{researchItem}Tech"]) + 1
            researchList[country] = {}
            print(f"Reset {country}!")
        except Exception:
            print(f"Unable to reset {country}.")

@bot.command()
async def resetAllCountries(ctx):
    for country, countryInfo in variablesList.items():
        researchList[country] = {}
        if countryInfo[0]["type"] == "country":
            countryInfo[0]["money"] = 18000000 + int(int(countryInfo[0]["populationCount"])/100)
            countryInfo[0]["populationHappiness"] = 55
            countryInfo[0]["averageIncome"] = 60
            countryInfo[0]["taxRate"] = 10
            countryInfo[0]["railwayTech"] = 0
        if countryInfo[0]["type"] == "company":
            countryInfo[0]["money"] = 3000000
        countryInfo[0]["engineTech"] = baseTechValue
        countryInfo[0]["cannonTech"] = baseTechValue
        countryInfo[0]["armorTech"] = baseTechValue
        countryInfo[0]["suspensionTech"] = baseTechValue
        countryInfo[0]["autoBuild"] = "false"
        countryInfo[0]["autoResearch"] = "false"
        countryInfo[0]["focus"] = "none"
    await ctx.send(f"You have successfully reset all faction parameters!")

@bot.command()
async def registerCompany(ctx, *, companyName):
    """Adds two numbers together."""
    channel = bot.get_channel(int(contractorsChat))
    thread = await channel.create_thread(
        name=companyName,
        type=discord.ChannelType.public_thread
    )
    countryDict = {companyName: [{'displayName': companyName, 'type': "company", 'channel': thread.id, "contractors": 0, "money": 3000000, "idealTonnage": "50", "currentTonnage": "50", "unspentTonnage": "50", "engineTech": baseTechValue, "cannonTech": baseTechValue, "armorTech": baseTechValue, "suspensionTech": baseTechValue, "engineResearchFunding": 22000, "cannonResearchFunding": 22000, "armorResearchFunding": 22000, "autoBuild": "false", "autoResearch": "false", "focus": "none"}]}
    productionList[companyName] = {}
    productionList[companyName]["Production Line 1"] = {'status': 'under construction', 'factoryHealth': '0', 'currentTank': '', 'currentTankWeight': 0, 'currentTankProgress': 0, 'nextTank': '', 'nextTankWeight': 0}
    productionList[companyName]["Production Line 2"] = {'status': 'under construction', 'factoryHealth': '0', 'currentTank': '', 'currentTankWeight': 0, 'currentTankProgress': 0, 'nextTank': '', 'nextTankWeight': 0}
    variablesList.update(countryDict)
    inventoryDict = {companyName: {}}
    inventoryList.update(inventoryDict)
    operatorsList[str(ctx.author.id)] = companyName
    await ctx.send(f"You have successfully founded {companyName}!  You can find its specific thread here: <#{str(thread.id)}>")

@bot.command()
async def establishCompany(ctx, *, companyName):
    """Adds two numbers together."""
    channel = bot.get_channel(int(contractorsChat))
    thread = await channel.create_thread(
        name=companyName,
        type=discord.ChannelType.private_thread
    )
    if companyName in variablesList:
        await ctx.send("This company already exists!")
        return
    countryDict = {companyName: [{'displayName': companyName, 'type': "company", 'channel': thread.id, "contractors": 0, "money": 3000000, "idealTonnage": "50", "currentTonnage": "50", "unspentTonnage": "50", "engineTech": baseTechValue, "cannonTech": baseTechValue, "armorTech": baseTechValue, "suspensionTech": baseTechValue, "engineResearchFunding": 22000, "cannonResearchFunding": 22000, "armorResearchFunding": 22000, "autoBuild": "false", "autoResearch": "false", "focus": "none"}]}
    productionList[companyName] = {}
    productionList[companyName]["Production Line 1"] = {'status': 'under construction', 'factoryHealth': '0', 'currentTank': '', 'currentTankWeight': 0, 'currentTankProgress': 0, 'nextTank': '', 'nextTankWeight': 0}
    productionList[companyName]["Production Line 2"] = {'status': 'under construction', 'factoryHealth': '0', 'currentTank': '', 'currentTankWeight': 0, 'currentTankProgress': 0, 'nextTank': '', 'nextTankWeight': 0}
    variablesList.update(countryDict)
    inventoryDict = {companyName: {}}
    inventoryList.update(inventoryDict)
    operatorsList[str(ctx.author.id)] = companyName
    await thread.send(f"<@{ctx.author.id}>You are now the CEO of {companyName}!  This is your private thread, where you can conduct operations and receive updates.\n Start by running the `-companyStats` command to see your technology limits!")

@bot.command()
async def setUpdateChannel(ctx, *, country=None):
    if country is None:
        country = await getUserCountry(ctx)
    channel = ctx.channel.id
    variablesList[country][0]["channel"] = channel
    await ctx.send(f"{country} will now receive updates in <#{channel}>!")

@bot.command()
@commands.has_role('Campaign Manager')
async def restartServer(ctx):
    await ctx.send("Include a backup?  Yes/No")
    import asyncio
    def check(m: discord.Message):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=3000.0)
        resp = msg.content.lower()
        if resp == "no":
            await ctx.send("Shutting down now.")
            import os
            os.system("systemctl reboot -i")
        elif resp == "yes":
            await backupFiles()
            await ctx.send("Backup successful.  Restarting now.")
            import os
            os.system("systemctl reboot -i")
        else:
            await ctx.send("Cancelled.")
    except asyncio.TimeoutError:
        await ctx.send("Operation cancelled.")
        return

@bot.command()
@commands.has_role('Campaign Administrator')
async def startNewWeek(ctx):
    await advanceWeek()

@bot.command()
async def setTaxRate(ctx, rate: int):
    country = ctx.channel.name
    if rate < 401 and rate > -6:
        variablesList[country][0]["taxRate"] = rate
        await ctx.send(f"Taxation rate updated to {rate}%")
    elif rate > 400:
        await ctx.send(f"*Knew I could trust you. Take this, there's a present in there for the mucking Taxmen. Why don't you deliver it to them?*\n\nYou'd probably cause more issues than solve by setting a tax rate this high.")

@bot.command()
@commands.has_role('Campaign Administrator')
async def startNewDay(ctx):
    await advanceDay()

@bot.command()
@commands.has_role('Campaign Administrator')
async def theMidnightBell(ctx):
    await advanceDay()
    await advanceWeek()

@bot.command()
@commands.has_role('Campaign Administrator')
async def resetTankCount(ctx):
    for faction, factionInfo in inventoryList.items():
        for tankName, tankInfo in factionInfo.items():
            tankInfo["stored"] = 0
            tankInfo["deployed"] = 0
            tankInfo["deployedAbroad"] = 0
    await backupFiles()
    await ctx.send("Success!  Files have been backed up.")

def getRailGauge(input: str):
    if input == "narrow":
        return 2.4
    if input == "standard":
        return 2.8
    if input == "enlarged":
        return 3.2
    if input == "wide":
        return 3.6

@bot.command()
@commands.has_role('Campaign Administrator')
async def resetFactoryConfig(ctx):
    for faction, factionInfo in variablesList.items():
        i = 1
        if variablesList[faction][0]["type"] == "country":
            count = 8
        if variablesList[faction][0]["type"] == "company":
            count = 2
        productionList[faction] = {}
        while i <= count:
            productionList[faction][f"Line {i}"] = {'status': 'under construction', 'factoryHealth': '0', 'currentTank': '', 'currentTankWeight': 0, 'currentTankProgress': 0, 'nextTank': '', 'nextTankWeight': 0}
            i+=1
    await backupFiles()
    await ctx.send("Success!  Files have been backed up.")

@bot.command()
@commands.has_role('Campaign Administrator')
async def giveBonusFactory(ctx):
    for faction, factionInfo in variablesList.items():
        if variablesList[faction][0]["type"] == "company":
            productionList[faction][f"R4E2 Bonus Line"] = {'status': 'idle', 'factoryHealth': '100', 'currentTank': '', 'currentTankWeight': 0, 'currentTankProgress': 0, 'nextTank': '', 'nextTankWeight': 0}
    await backupFiles()
    await ctx.send("Success!  Files have been backed up. \n# Warning: only run this one time!")

@bot.command()
async def setAutoBuild(ctx, state: str):
    user_id = ctx.author.id
    try:
        country = operatorsList[str(user_id)]
    except Exception:
        country = ctx.channel.name
    if state == "true" :
        variablesList[country][0]["autoBuild"] = state
        await ctx.send("Continuous building is now active!  Tanks will build repeatedly, drawing funding and production as needed.")
    elif state == "false":
        variablesList[country][0]["autoBuild"] = state
        await ctx.send("Continuous building has been stopped!  Existing tanks will finish building, but new ones won't continue  being built.")

@bot.command()
async def setAutoResearch(ctx, state: str):
    user_id = ctx.author.id
    try:
        country = operatorsList[str(user_id)]
    except Exception:
        country = ctx.channel.name
    if state == "true" :
        variablesList[country][0]["autoResearch"] = state
        await ctx.send(f"Continuous research is now active!  Research will continue to fund itself.")
    elif state == "false":
        variablesList[country][0]["autoResearch"] = state
        await ctx.send(f"Continuous research has been stopped!  Existing research will finish, but no longer repeat.")

@bot.command()
@commands.has_role('Campaign Manager')
async def addProduction(ctx, money: int):
    """Adds two numbers together."""
    country = ctx.channel.name
    countryDisplay = variablesList[country][0]["displayName"]
    # variablesList[country][0]["money"] = variablesList[country][0]["money"] + money
    variablesList[country][0]["unspentTonnage"] = float(variablesList[country][0]["unspentTonnage"]) + float(money)
    await ctx.send("You added {0} to {1}\'s factory capacity.".format(str(money), countryDisplay))
    await ctx.send("Their total available tonnage is now " + str(variablesList[country][0]["unspentTonnage"]) + " tons.")



@bot.command()
async def countryStats(ctx):

    country = ctx.channel.name
    if variablesList[country][0]["type"] == "country":
        embed = discord.Embed(title=variablesList[country][0]["displayName"], description=variablesList[country][0]["description"], color=discord.Color.random())
        embed.add_field(name="Land size", value="{:,}".format(int(variablesList[country][0]["land"])) + "mi", inline=False)
        embed.add_field(name="Money in storage", value="฿" + ("{:,}".format(int(variablesList[country][0]["money"]))), inline=False)
        embed.add_field(name="Population size", value=str(round(int(variablesList[country][0]["populationCount"])/1000000, 2)) + "M", inline=False)
        embed.add_field(name="Populace happiness", value=(str(int(variablesList[country][0]["populationHappiness"]))) + "%", inline=False)
        embed.add_field(name="Average worker's income", value= "฿" + str(int(100*int(variablesList[country][0]["averageIncome"]))/100), inline=False)
        embed.add_field(name="Taxation rate", value=(str(variablesList[country][0]["taxRate"])) + "%", inline=False)
        embed.add_field(name="Army funding percent", value=(str(variablesList[country][0]["taxPercentToArmy"])) + "%", inline=False)
        embed.add_field(name="Railway Gauge", value=railwayGauges[variablesList[country][0]["railwayTech"]], inline=False)
        await ctx.send(embed=embed)

@bot.command()
async def companyStats(ctx):
    print(operatorsList)
    user_id = ctx.author.id
    print(user_id)
    try:
        country = operatorsList[str(ctx.author.id)]
    except Exception:
        await ctx.send("You aren't part of a company yet!")
        print(str(user_id))
        return
    gunOutput = round(float(gunCount) * float(variablesList[country][0]["cannonTech"]) / 100)

    cannonLevel = int(variablesList[country][0]["cannonTech"])
    mobilityLevel = int(variablesList[country][0]["engineTech"])
    armorLevel = int(variablesList[country][0]["armorTech"])
    suspensionLevel = int(variablesList[country][0]["suspensionTech"])
    AmongUsJoke = "Suspension"
    if random() < 0.01:
        AmongUsJoke = "Sus pension"

    embed = discord.Embed(title=variablesList[country][0]["displayName"], description="These are your company stats and technological limits!", color=discord.Color.random())
    embed.add_field(name="Money in storage", value="฿" + ("{:,}".format(int(variablesList[country][0]["money"]))), inline=False)
    embed.add_field(name="Shell length", value=str(shellLengths[cannonLevel]) + "mm", inline=False)
    embed.add_field(name="Bore length", value=str(boreLengths[cannonLevel]) + "m", inline=False)
    embed.add_field(name=AmongUsJoke + " carrying capacity", value=str(weightLimit[suspensionLevel]) + " tons", inline=False)
    embed.add_field(name="Net engine displacement", value=str(netDisplacement[mobilityLevel]) + " liters", inline=False)
    embed.add_field(name="Riveted Armor thickness", value=str(int(0.6 * armorThickness[armorLevel])) + "mm", inline=False)
    embed.add_field(name="Welded Armor thickness", value=str(int(0.9 * armorThickness[armorLevel])) + "mm", inline=False)
    embed.add_field(name="Cast Armor thickness", value=str(armorThickness[armorLevel]) + "mm", inline=False)
    embed.add_field(name="Custom mantlet (GCM) torque limit", value=str(GCMtorque[mobilityLevel]) + "mm", inline=False)
    embed.add_field(name="Minimum GCM traverse ratio", value=str(GCMratio[mobilityLevel]), inline=False)
    embed.add_field(name="Arma Aspectus", value=str(themes[int(suspensionLevel*themeCount/maxLevel)]), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def countryTech(ctx):
    country = ctx.channel.name
    cannonLevel = int(variablesList[country][0]["cannonTech"])
    mobilityLevel = int(variablesList[country][0]["engineTech"])
    armorLevel = int(variablesList[country][0]["armorTech"])
    suspensionLevel = int(variablesList[country][0]["suspensionTech"])
    railwayLevel = int(variablesList[country][0]["railwayTech"])
    AmongUsJoke = "Suspension"
    if random() < 0.01:
        AmongUsJoke = "Sus pension"
    print(cannonWeights[cannonLevel])
    embed = discord.Embed(title=variablesList[country][0]["displayName"] + "'s Technology", description="These are the technological limits of your country.  Consider investing more into R&D to accelerate development of newer technology!", color=discord.Color.random())
    embed.add_field(name="Shell length", value=str(shellLengths[cannonLevel]) + "mm", inline=False)
    embed.add_field(name="Bore length", value=str(boreLengths[cannonLevel]) + "m", inline=False)
    embed.add_field(name=AmongUsJoke + " carrying capacity", value=str(weightLimit[suspensionLevel]) + " tons", inline=False)
    embed.add_field(name="Net engine displacement", value=str(netDisplacement[mobilityLevel]) + " liters", inline=False)
    embed.add_field(name="Riveted Armor thickness", value=str(0.6*int(armorThickness[armorLevel])) + "mm", inline=False)
    embed.add_field(name="Welded Armor thickness", value=str(0.9*int(armorThickness[armorLevel])) + "mm", inline=False)
    embed.add_field(name="Cast Armor thickness", value=str(armorThickness[armorLevel]) + "mm", inline=False)
    embed.add_field(name="Railway transport width", value=str(railwayGaugeLimits[railwayLevel]) + "m", inline=False)
    embed.add_field(name="Custom mantlet (GCM) torque limit", value=str(GCMtorque[mobilityLevel]) + "mm", inline=False)
    embed.add_field(name="Minimum GCM traverse ratio", value=str(GCMratio[mobilityLevel]), inline=False)
    embed.add_field(name="Arma Aspectus", value=str(themes[int(suspensionLevel*themeCount/maxLevel)]), inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role('Campaign Manager')
async def backupConfig(ctx):
    await backupFiles()
    await ctx.send("Configuration backed up successfully!")

async def backupFiles():
    json_output = json.dumps(variablesList, indent=4)
    with open(COUNTRIESpath, "w") as outfile:
        outfile.write(json_output)
    json_output = json.dumps(inventoryList, indent=4)
    with open(INVENTORYpath, "w") as outfile:
        outfile.write(json_output)
    json_output = json.dumps(manufacturingList, indent=4)
    with open(MANUFACTURINGpath, "w") as outfile:
        outfile.write(json_output)
    json_output = json.dumps(tanksList, indent=4)
    with open(TANKSpath, "w") as outfile:
        outfile.write(json_output)
    json_output = json.dumps(operatorsList, indent=4)
    with open(OPERATORSpath, "w") as outfile:
        outfile.write(json_output)
    json_output = json.dumps(blimpList, indent=4)
    with open(BLIMPpath, "w") as outfile:
        outfile.write(json_output)
    json_output = json.dumps(researchList, indent=4)
    with open(RESEARCHpath, "w") as outfile:
        outfile.write(json_output)
    json_output = json.dumps(productionList, indent=4)
    with open(PRODUCTIONpath, "w") as outfile:
        outfile.write(json_output)
    json_output = json.dumps(contestsList, indent=4)
    with open(CONTESTSpath, "w") as outfile:
        outfile.write(json_output)
    channel = bot.get_channel(1152377925916688484)
    await channel.send("Progress has been saved.  See below for the appropriate .json files:")
    from discord import File
    await channel.send(file=File(COUNTRIESpath), content="Country stats")
    await channel.send(file=File(INVENTORYpath), content="Tank inventory")
    await channel.send(file=File(TANKSpath), content="List of tanks")
    await channel.send(file=File(OPERATORSpath), content="Company operators")
    await channel.send(file=File(BLIMPpath), content="Blimp catalogs")
    await channel.send(file=File(RESEARCHpath), content="Research in progress")
    await channel.send(file=File(PRODUCTIONpath), content="All factory lines")
    await channel.send(f"Testing")

@bot.command()
async def registerTankReallyLegacy(ctx, name: str, weight: float, licenseFee: int, importFee: int, buyoutFee: int, *, country):
    costVal = round(pow((float(weight) * 1000), 1.1))

    try:
        print(variablesList[country][0]["type"])
    except Exception:
        await ctx.send("Country name is invalid!")
        return



    originType = variablesList[country][0]["type"]
    tanksList[name] = {'origin': country, 'originType': originType, 'weight': weight, 'cost': costVal, 'licenseFee': licenseFee, 'importFee': importFee, 'buyoutFee': buyoutFee}
    inventoryList[country][name] = {'weight': weight, 'type': "local", 'stored': 0, 'deployed': 0, 'deployedAbroad': 0}

    await ctx.send("Registered the " + name + " as a tank manufactured by " + variablesList[country][0]["displayName"] + "!")
    json_output = json.dumps(tanksList, indent=4)

    # Writing to sample.json
    with open("tanks.json", "w") as outfile:
        outfile.write(json_output)

@bot.command()
async def registerContractor(ctx, name: discord.User, *, company):
    ID = name.id
    operatorsList[str(ID)] = company
    print(ID)
    print(company)
    await ctx.send("Successfully registered " + str(name) + " as a contractor of " + company + "!")
    companyMemberCount = 0
    for userName, userCompany in operatorsList.items():
        if userCompany == company:
            companyMemberCount += 1
    await ctx.send(company + " now has " + str(companyMemberCount) + " contractors!")
    variablesList[company][0]["contractors"] = companyMemberCount

@bot.command()
async def removeContractor(ctx, name: discord.User, *, company):
    ID = name.id

    del operatorsList[str(ID)]
    await ctx.send("Successfully removed " + str(name) + " from " + company + "!")
    variablesList[company][0]["contractors"] = int(variablesList[company][0]["contractors"]) - 1

@bot.command()
async def leaveCompany(ctx):
    ID = ctx.author.id

    del operatorsList[str(ID)]
    await ctx.send("You are no longer part of a company.")

# @bot.command()
# async def buildTank(ctx, *, tankName):
#     import time
#     user_id = ctx.author.id
#     millisec = time.time_ns() // 1000000
#     country = await getUserCountry(ctx)
#     print(country)
#     # A: Tank is local, and exists
#     # B: Tank is company-owned, and exists
#     # C: Tank does not exist
#
#     try:
#         tons = tanksList[tankName]["weight"]
#         tankCountry = tanksList[tankName]["origin"]
#
#     except KeyError as ke:
#         await ctx.send("\"Paradox. You behold an absence. Describe it.\"")
#         await ctx.send("The " + str(ke) + " simply doesn't exist.  Maybe it's still in development, or there was a typo in the name. \n Use `-listTanks` to see what tanks you have available to build!")
#         return
#
#     if country == tankCountry:
#         cost = round(pow((float(tons) * costPerTon), 1.1))
#     if country != tankCountry and variablesList[tankCountry][0]["type"] == "company":
#         cost = round(pow((float(tons) * costPerTon), 1.1)) + int(tanksList[tankName]["licenseFee"])
#         variablesList[tankCountry][0]["money"] = int(variablesList[tankCountry][0]["money"]) + int(tanksList[tankName]["licenseFee"])
#
#     rateVal = float(float(productionRate) / float(tons))
#
#     rateVal = 0.34
#
#     tonnageLeft =  float(variablesList[country][0]["unspentTonnage"])
#
#     #registers the tank into the system, if necessary:
#     try:
#         print(inventoryList[country][tankName])
#     except Exception:
#         inventoryList[country][tankName] = {'weight': tanksList[tankName]["weight"], 'type': "foreign", 'stored': 0, 'deployed': 0, 'deployedAbroad': 0}
#         print("Tank added to registry.")
#
#
#     if float(tonnageLeft) < float(tons):
#         await ctx.send("Your factories do not have enough capacity to build a " + tankName + "!")
#
#     elif float(tonnageLeft) >= float(tons):
#         variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - cost
#         variablesList[country][0]["unspentTonnage"] = float(variablesList[country][0]["unspentTonnage"]) - float(tons)
#         manufacturingList[millisec] = {'name': tankName, 'country': country, 'cost': cost, 'progress': 0, 'rate': rateVal}
#         json_output = json.dumps(manufacturingList, indent=4)
#         days = round(1.0 / rateVal)
#         # Writing to sample.json
#         with open("tanks-in-progress.json", "w") as outfile:
#             outfile.write(json_output)
#         await ctx.send("You have successfully ordered a " + tankName + "! \n Cost: ฿" + str(cost) + "\n Production time: " + str(days) + " days")
#         if variablesList[tankCountry][0]["type"] == "company":
#             channel = bot.get_channel(variablesList[tankCountry][0]["channel"])
#             await channel.send(f"{country} has paid licensing fees to build a {tankName}!")
#     else:
#         await ctx.send("This tank is unavailable in your inventory!")

@bot.command()
async def message(ctx, *, country):
    import asyncio
    try:
        channelToSend = variablesList[country][0]["channel"]
    except Exception:
        await ctx.send("Country is invalid.")
        return
    countryOrigin = await getUserCountry(ctx)
    await ctx.send("Type your message here, and include any attachments that you wish to send.  Note that your message will have the country of origin attached.")
    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=1800.0)
    except asyncio.TimeoutError:
        await ctx.reply("The command to send a message to {country} has timed out.")
        return
    else:
        message = msg.content

    channel = bot.get_channel(channelToSend)
    await ctx.send("Message is en route.")
    await channel.send(f"## Message from {variablesList[countryOrigin][0]['displayName']}:\n{message}", allowed_mentions=discord.AllowedMentions(roles=False, users=True, everyone=False))
    for attachment in msg.attachments:
        file = await attachment.to_file()
        await channel.send(file=file, content="")
@bot.command()
@commands.has_role('Moderator')
async def troll(ctx, channelin: str, *, message):
    import re
    channelin = int(re.sub(r'[^0-9]', '', channelin))
    print(channelin)
    channel = bot.get_channel(channelin)
    await ctx.send("Message is en route.")
    await channel.send(message)
    for attachment in ctx.message.attachments:
        file = await attachment.to_file()
        await channel.send(file=file, content="")

@bot.command()
async def postContract(ctx, *, message):
    channel = bot.get_channel(1145273680214110329)
    countryOrigin = ctx.channel.name
    await ctx.send("Your contract is now available for companies to try and complete.")
    await channel.send(f"## {countryOrigin} has expressed interest in a new tank design!  Their desired specifications are as follows:\n{message}", allowed_mentions=discord.AllowedMentions(roles=False, users=True, everyone=False))

@bot.command()
async def buildBlimp(ctx, *, blimpName):
    import random
    NameInput = int(round(industryCount * random.random())) - 1
    TypeInput = int(round(industryTypeCount*random.random())) - 1
    country = await getUserCountry(ctx)
    if country == "invalid_country":
        await ctx.send("It appears you aren't part of a country, or are running this command in the wrong channel.")
        return
    variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - 5000000
    blimpList[blimpName] = {'origin': country, 'stowage': 'empty', 'count': 0, 'miles_travelled': 0, 'RNGpoint': 600, 'travel_goal': 1200, 'risk_factor': 0, 'status': 'idle'}
    await ctx.send(f"You have successfully purchased a blimp named {blimpName} from {industryNames[NameInput]} {industryTypes[TypeInput]}!\nCost: ฿{5000000}\n")
    # idle = inactive, # loaded = awaiting distance needed, active = travelling to front, returning = blimp survived travels and is returning

class BlimpDropdown(discord.ui.Select):
    country_var = ""
    def __init__(self, country, tankName, tankCount):

        self.country = country
        self.tankName = tankName
        self.tankCount = tankCount
        print(country + " -----------------------------------<------------")
        # Set the options that will be presented inside the dropdown
        blimpCost = 5000000
        options = []
        for balloon, balloonInfo in blimpList.items():
            if balloonInfo["origin"] == country and balloonInfo["stowage"] == "empty":
                options.append(discord.SelectOption(label=balloon, description=("cost: ฿{:,}").format(fundsToAdvanceLevel), emoji='🎈', value=balloon))

        print(country)
        country_var = country
        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Choose a blimp to fill with tanks.', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        import random
        country = self.country
        tankName = self.tankName
        tankCount = self.tankCount
        blimpName = self.values[0]
        blimpChannel = bot.get_channel(int(blimpLogChat))
        inventoryList[country][tankName]["stored"] = int(inventoryList[country][tankName]["stored"]) - tankCount
        blimpList[blimpName]["stowage"] = tankName
        blimpList[blimpName]["count"] = tankCount
        blimpList[blimpName]["count"] = tankCount
        blimpList[blimpName]["status"] = "loaded"
        await blimpChannel.send(f"{variablesList[country][0]['displayName']}'s {blimpName} is waiting for navigation data!  Cargo: {tankCount}x {tankName}")
        await interaction.response.send_message(f"{blimpName} is loaded!  Overlord will get with you to figure out where you want the blimp to go.")

class BlimpDropdownView(discord.ui.View):
    def __init__(self, country, tankName, tankCount):
        super().__init__()
        self.country = country
        self.tankName = tankName
        self.tankCount = tankCount
        # Adds the dropdown to our view object.
        self.add_item(BlimpDropdown(country, tankName, tankCount))

@bot.command()
async def loadBlimp(ctx, tankName: str):
    country = await getUserCountry(ctx)
    if country == "invalid_country":
        await ctx.send("This is not a valid country or company!")
        return
    tankCount = int(blimpCapacity / float(tanksList[tankName]["weight"]))
    if tankCount > inventoryList[country][tankName]["stored"]:
        tankCount = int(inventoryList[country][tankName]["stored"])
    await ctx.send(f"Select a blimp below to load with vehicles.  You can store {tankCount}x {tankName} in a blimp.")
    view = BlimpDropdownView(country, tankName, tankCount)
    await ctx.send(view=view)

@bot.command()
async def activateBlimp(ctx):
    import asyncio
    blimpName = ""
    riskChance = 0
    miles = 0
    await ctx.send("Name the blimp to activate.")
    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send("Operation cancelled.")
        return
    else:
        blimpName = msg.content
        try:
            asdfghjkl = blimpList[blimpName]
        except Exception:
            await ctx.send("Blimp name isn't valid!  Make sure capitalization is correct.")
            return

    await ctx.send("Specify how many miles it will take to reach the destination.")
    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send("Operation cancelled.")
        return
    else:
        miles = int(50*(int(msg.content)/50))

    await ctx.send("Specify the risk factor on a scale of 0 to 10.")
    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send("Operation cancelled.")
        return
    else:
        riskChance = int(msg.content)

    blimpList[blimpName]['status'] = "active"
    blimpList[blimpName]['riskLevel'] = riskChance
    blimpList[blimpName]['travel_goal'] = miles
    await ctx.send(f"Successfully activated {blimpName}!")


@bot.command()
async def listFactions(ctx):
    description = "These names are all compatible with bot commands. \n\n"
    for countryName, countryInfo in variablesList.items():
        description = description.__add__(f"{countryName}\n")
    embed = discord.Embed(title="List of all countries and companies", description=description,color=discord.Color.random())
    await ctx.send(embed=embed)



@bot.command()
async def buyoutTank(ctx, tankName: str):
    user_id = ctx.author.id
    # millisec = time.time_ns() // 1000000
    country = await getUserCountry(ctx)
    print(country)

    # A: Tank is local, and exists
    # B: Tank is company-owned, and exists
    # C: Tank does not exist


    try:
        tons = tanksList[tankName]["weight"]
        tankCountry = tanksList[tankName]["origin"]
        if country == tankCountry:
            buyoutPrice = tanksList[tankName]["buyoutFee"]
    except KeyError as ke:
        await ctx.send("\"I feel like something's missing here!\"")
        await ctx.send("The " + str(ke) + " simply doesn't exist.  Maybe it's still in development, or there was a typo in the name. \n Use `-listTanks` to see what tanks you have available to build!")
        return
    #registers the tank into the system, if necessary:

    try:
        print(inventoryList[country][tankName])
    except Exception:
        inventoryList[country][tankName] = {'weight': tanksList[tankName]["weight"], 'type': "foreign", 'stored': 0, 'deployed': 0, 'deployedAbroad': 0}
        print("Tank added to registry.")

    if inventoryList[country][tankName]["type"] == "local":
        await ctx.send("Why are you trying to buy the rights to your own tank?")
        return
    else:
        variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - int(tanksList[tankName]["buyoutFee"])
        variablesList[tankCountry][0]["money"] = int(variablesList[tankCountry][0]["money"]) + int(tanksList[tankName]["buyoutFee"])
        inventoryList[country][tankName]["type"] = "local"
        await ctx.send("You have successfully purchased the rights to the " + tankName + "!  \nYou are now free to produce and modify this tank however you want.")
        channel = bot.get_channel(variablesList[tankCountry][0]["channel"])
        await channel.send(f"{country} has purchased the manufacturing rights to the {tankName}!  They are now able to build and modify this vehicle as they wish.")
        print("Hi!")

@bot.command()
@commands.has_role('Campaign Manager')
async def donate(ctx):
    userCountry = await getUserCountry(ctx)
    recipientCountry = ""
    import asyncio

    if variablesList[userCountry][0]["type"] == "company":
        await ctx.reply("Donations from companies are not permitted to prevent abuse of Zheifu's financial systems.")
        return

    valid = 0
    await ctx.send("Who are you planning to send this donation to?")
    while valid <= 2:

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await bot.wait_for('message', check=check, timeout=120.0)
            try:
                recipientCountry = msg.content
                channelToSend = variablesList[recipientCountry][0]["channel"]
                valid = 7
            except Exception:
                valid += 1
                await ctx.reply("Invalid faction.  Please try again.")

        except asyncio.TimeoutError:
            await ctx.reply("The command has timed out.")
            return

        if valid == 3:
            await ctx.reply("Operation cancelled.")
            return

    valid = 0
    await ctx.send("How much are you planning to send?  Enter a number (or zero to cancel)")
    while valid <= 2:

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await bot.wait_for('message', check=check, timeout=120.0)
            try:
                number = int(msg.content)
                valid = 7
                if number < 0:
                    number = msg*1/0
            except Exception:
                valid += 1
                await ctx.reply("Invalid number.  Please try again.")

        except asyncio.TimeoutError:
            await ctx.reply("The command has timed out.")
            return

        if valid == 3:
            await ctx.reply("Operation cancelled.")
            return

    if number == 0:
        await ctx.reply("Operation cancelled.")
        return

    if int(variablesList[userCountry][0]["money"])/8 < number:
        await ctx.reply(f"You're trying to donate quite alot of money there.  I am going to recommend not donating more than ฿{round(int(variablesList[userCountry][0]['money'])/10)} so that you don't break the bank.")
        return

    await ctx.send("Type your attached message here.  Note that the country of origin will be attached.")
    def check(m: discord.Message):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=1800.0)
    except asyncio.TimeoutError:
        await ctx.reply("The command has timed out.")
        return
    else:
        message = msg.content

    channelToSend = variablesList[recipientCountry][0]["channel"]
    channel = bot.get_channel(channelToSend)
    variablesList[userCountry][0]["money"] = int(variablesList[userCountry][0]["money"]) - number
    variablesList[recipientCountry][0]["money"] = int(variablesList[recipientCountry][0]["money"]) + number
    await ctx.reply(f"Donation of ฿{number} to {recipientCountry} is now underway!")
    await channel.send(f"## You have received a donation of ฿{number} from {variablesList[userCountry][0]['displayName']}!\nThey have attached the following message: \n\n{message}", allowed_mentions=discord.AllowedMentions(roles=False, users=True, everyone=False))


@bot.command()
async def importTank(ctx, tankName: str):
    user_id = ctx.author.id
    # millisec = time.time_ns() // 1000000
    country = await getUserCountry(ctx)
    print(country)

    # A: Tank is local, and exists
    # B: Tank is company-owned, and exists
    # C: Tank does not exist


    try:
        tons = tanksList[tankName]["weight"]
        tankCountry = tanksList[tankName]["origin"]
        if country == tankCountry:
            importPrice = tanksList[tankName]["importFee"]
    except KeyError as ke:
        await ctx.send("\"I feel like something's missing here!\"")
        await ctx.send("The " + str(ke) + " simply doesn't exist.  Maybe it's still in development, or there was a typo in the name. \n Use `-listTanks` to see what tanks you have available to build!")
        return
    #registers the tank into the system, if necessary:

    try:
        print(inventoryList[country][tankName])
    except Exception:
        inventoryList[country][tankName] = {'weight': tanksList[tankName]["weight"], 'type': "foreign", 'stored': 0, 'deployed': 0, 'deployedAbroad': 0}
        print("Tank added to registry.")

    # if inventoryList[country][tankName]["type"] == "local":
    #     await ctx.send("Why are you trying to import your own tank?")
    #     return
    if int(inventoryList[tankCountry][tankName]["stored"]) < 1:
        await ctx.send(variablesList[tankCountry][0]["displayName"] + " doesn't have any of these tanks in storage!  You'll have to ask them to build some for you...")
    else:
        print(country)
        print(tankCountry)
        variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - int(tanksList[tankName]["importFee"])
        variablesList[tankCountry][0]["money"] = int(variablesList[tankCountry][0]["money"]) + int(tanksList[tankName]["importFee"])
        inventoryList[country][tankName]["stored"] = int(inventoryList[country][tankName]["stored"]) + 1
        inventoryList[tankCountry][tankName]["stored"] = int(inventoryList[tankCountry][tankName]["stored"]) - 1
        await ctx.send("You have successfully imported a " + str(tankName) + "! \n Cost: ฿" + str(tanksList[tankName]["importFee"]))
        channel = bot.get_channel(variablesList[country][0]["channel"])
        await channel.send(f"A {tankName} has been imported by {country}!")

        print("Hi!")

@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')

@bot.command()
@commands.has_role('Campaign Manager')
async def toggleTime(ctx):
    global advanceTime
    advanceTime = not advanceTime
    await ctx.send(f"Time advancing is now set to {advanceTime}")

@bot.command()
async def listProduction(ctx):
    country = await getUserCountry(ctx)
    embed = discord.Embed(title=f"{variablesList[country][0]['displayName']}'s factory lines",
                          description="This is a short list of all your factory lines. \nFor more details on a specific line, use `-factoryDetails <factory name>`",
                          color=discord.Color.random())
    for lineName, lineInfo in productionList[country].items():
        print(lineName)
        if lineInfo["status"] == "building":
            embed.add_field(name=lineName, value=f"Building a {lineInfo['currentTank']} ({int(lineInfo['currentTankProgress']*100)}%) \n ", inline=False)
        elif lineInfo["status"] == "idle":
            embed.add_field(name=lineName, value=f"Idle", inline=False)
        else:
            embed.add_field(name=lineName, value=f"Under construction ({int(lineInfo['factoryHealth'] * 100)}%) \n ", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def factoryDetails(ctx, *, factoryName):
    country = await getUserCountry(ctx)
    try:
        factoryInfo = productionList[country][factoryName]
    except Exception:
        await ctx.reply("This factory does not exist!  Check your factory name and try again.")
        return
    embed = discord.Embed(title=f"{factoryName}",
                          description="This is a detailed information about your factory.",
                          color=discord.Color.random())
    embed.add_field(name="Status", value=factoryInfo['status'], inline=False)
    embed.add_field(name="Factory condition", value=str(float(factoryInfo['factoryHealth'])*100) + "%", inline=False)
    if productionList[country][factoryName]["status"] == "building":
        embed.add_field(name="Tank in construction", value=factoryInfo['currentTank'], inline=False)
        embed.add_field(name="Tank assembly progress", value=str(round(100*float(factoryInfo['currentTankProgress']), 4)) + "%", inline=False)
        embed.add_field(name="Next tank", value=factoryInfo['nextTank'], inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def activateFactory(ctx, *, factoryName):
    country = await getUserCountry(ctx)
    try:
        factoryInfo = productionList[country][factoryName]
    except Exception:
        await ctx.reply("This factory does not exist!  Check your factory name and try again.")
        return
    if productionList[country][factoryName]["status"] != "under construction" and productionList[country][factoryName]["currentTank"] != "":
        productionList[country][factoryName]["status"] = "building"
        await ctx.reply(f"{factoryName} is now building the {productionList[country][factoryName]['currentTank']}!")
    else:
        await ctx.reply(f"{factoryName} does not have a tank set to start building!")

@bot.command()
async def deactivateFactory(ctx, *, factoryName):
    country = await getUserCountry(ctx)
    try:
        factoryInfo = productionList[country][factoryName]
    except Exception:
        await ctx.reply("This factory does not exist!  Check your factory name and try again.")
        return
    if productionList[country][factoryName]["status"] != "under construction":
        productionList[country][factoryName]["status"] = "idle"
        await ctx.reply(f"{factoryName} has now stopped!")

@bot.command()
async def buildFactory(ctx, *, factoryName):
    import random
    NameInput = int(round(industryCount * random.random())) - 1
    TypeInput = int(round(industryTypeCount*random.random())) - 1
    country = await getUserCountry(ctx)
    if country == "invalid_country":
        await ctx.send("It appears you aren't part of a country, or are running this command in the wrong channel.")
        return
    for sampleName, sampleInfo in productionList[country].items():
        if sampleInfo["status"] == "under construction":
            await ctx.send(f"You are already constructing {sampleName}.  To avoid stretching out your construction workers, wait until {sampleName} finishes assembly before building a new one.")
            return
    try:
        existingName = productionList[country][factoryName]
        await ctx.send(f"{factoryName} already exists!  Choose a different name for your factory.")
        return
    except Exception:
        variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - costToBuyFactory
        productionList[country][factoryName] = {'status': 'under construction', 'factoryHealth': '0', 'currentTank': '', 'currentTankWeight': 0, 'currentTankProgress': 0, 'nextTank': '', 'nextTankWeight': 0}
        await ctx.send(f"You have successfully paid {industryNames[NameInput]} {industryTypes[TypeInput]} to construct a new factory line titled {factoryName}!\nCost: ฿{costToBuyFactory}\n")

@bot.command()
@commands.has_role('Campaign Manager')
async def redeem(ctx):
    import asyncio
    await ctx.send("Name the country receiving the freebie.")
    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=1800.0)
        country = msg.content
        variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) + 2500000
        await ctx.send(f"Success!  Now enter the name of the production line that {country} will receive.")
    except asyncio.TimeoutError:
        await ctx.reply(f"This country is invalid.")
        return

    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=1800.0)
        name = msg.content
        productionList[country][name] =  {'status': 'idle', 'factoryHealth': '100', 'currentTank': '', 'currentTankWeight': 0, 'currentTankProgress': 0, 'nextTank': '', 'nextTankWeight': 0}
        await ctx.send(f"**Done!**  {country} has been granted: \nA new production line named \"{name}\"\n฿2500000 in funds \n\nThanks for participating in the Round 3 survey!  See you on the battlefield!")
    except asyncio.TimeoutError:
        await ctx.reply(f"{country} is invalid.")
        return

@bot.command()
@commands.has_role('Campaign Manager')
async def help(ctx):
    await ctx.send("Please refer to <#1167422233141067816> for information on using Sprocket Bot.")

@bot.command()
@commands.has_role('Campaign Manager')
async def setFocusAll(ctx):
    for country in variablesList:
        variablesList[country][0]["focus"] = "none"
    await ctx.reply("Complete!")

@bot.command()
async def setFocus(ctx):
    import asyncio
    country = await getUserCountry(ctx)
    stratCost = strategyCost
    if variablesList[country][0]["focus"] == "country":
        stratCost = stratCost*10
    await ctx.send(f"You can change your country's main focus to be either research or building!  Warning: using a focused strategy costs {stratCost} per day, so think carefully before using it. \n- **Research** halves your manufacturing speed to improve research\n- **Building** halves your research speed to improve building speed\n- **None** is the same as normal \n\nReply with your desired main focus.  Current focus: {variablesList[country][0]['focus']}")
    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=500.0)
        focus_input = msg.content
        if focus_input.lower() in focusSchools:
            await ctx.reply("https://tenor.com/view/warframe-bnp-mirage-nekros-illegal-gif-20541385")
            return
        if focus_input.lower() == "building":
            variablesList[country][0]["focus"] = "building"
            await ctx.reply("You are now focusing your country's efforts towards building tanks!")
        if focus_input.lower() == "research":
            variablesList[country][0]["focus"] = "research"
            await ctx.reply("You are now focusing your country's efforts towards researching new technology!")
        if focus_input.lower() == "none":
            variablesList[country][0]["focus"] = "none"
            await ctx.reply("Focused efforts have been halted.")
    except Exception:
        await ctx.reply(f"Invalid reply.  Operation cancelled.")
        return




@bot.command()
async def configureFactory(ctx, *, factoryName):
    import random, asyncio
    NameInput = int(round(industryCount * random.random())) - 1
    TypeInput = int(round(industryTypeCount*random.random())) - 1
    specialStatus = False
    country = await getUserCountry(ctx)
    try:
        print(productionList[country][factoryName]['status'])
    except Exception:
        await ctx.reply("It appears that your factory does not exist.  Try again.")
        return
    await ctx.send(f"Name the tank you wish to build in {factoryName}.  Or, reply with \"none\" to stop future production of vehicles.")
    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=1800.0)
    except asyncio.TimeoutError:
        await ctx.reply(f"The command to send a message to {country} has timed out.")
        return
    try:
        tankName = msg.content
        if tankName == "none":
            productionList[country][factoryName]['nextTank'] = ""
            await ctx.send(f"{factoryName} will no longer build new vehicles automatically.")
            return
        if tankName == "7.5T Flatbed Transporter" or tankName == "2.5T Transport Truck":
            if variablesList[country][0]["type"] == "company":
                specialStatus = True
        if specialStatus == False:
            tankWeight = int(tanksList[tankName]["weight"])
    except Exception:
        await ctx.send(f"The {msg.content} doesn't exist!  Make sure the name is spelled correctly.")
        return
    if tanksList[tankName]["status"] != "approved" and specialStatus == False:
        await ctx.send(f"The {msg.content} is not approved for production.  Status: {tanksList[tankName]['status']}")
        return
    try:
        print(inventoryList[country][tankName])
    except Exception:
        if tanksList[tankName]["originType"] == "company":
            inventoryList[country][tankName] = {'weight': tanksList[tankName]["weight"], 'type': "foreign", 'stored': 0, 'deployed': 0, 'deployedAbroad': 0}
        elif specialStatus == False:
            await ctx.send(f"The {msg.content} doesn't exist in your inventory, but this name is already in use.")
            return

    try:
        # update for if a tank
        if productionList[country][factoryName]['status'] != "under construction":
            productionList[country][factoryName]['status'] = "building"
        productionList[country][factoryName]['nextTank'] = tankName
        if tankName == "2.5T Transport Truck":
            productionList[country][factoryName]['nextTankWeight'] = 2.5
        elif tankName == "7.5T Flatbed Transporter":
            productionList[country][factoryName]['nextTankWeight'] = 7.5
        else:
            productionList[country][factoryName]['nextTankWeight'] = tankWeight
        if productionList[country][factoryName]['currentTank'] == "":
            productionList[country][factoryName]['currentTank'] = productionList[country][factoryName]['nextTank']
            if tankName == "2.5T Transport Truck":
                productionList[country][factoryName]['currentTankWeight'] = 2.5
            elif tankName == "7.5T Flatbed Transporter":
                productionList[country][factoryName]['currentTankWeight'] = 7.5
            else:
                productionList[country][factoryName]['currentTankWeight'] = productionList[country][factoryName]['nextTankWeight']
            tons = tanksList[tankName]["weight"]
            tankCountry = tanksList[tankName]["origin"]
            # if country == tankCountry:
            #     cost = round(pow((float(tons) * costPerTon), 1.1))
            # if country != tankCountry and variablesList[tankCountry][0]["type"] == "company":
            #     cost = round(pow((float(tons) * costPerTon), 1.1)) + int(tanksList[tankName]["licenseFee"])
            #     variablesList[tankCountry][0]["money"] = int(variablesList[tankCountry][0]["money"]) + int(tanksList[tankName]["licenseFee"])
            # variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - cost
    except Exception:
        await ctx.send(f"\"Hans \nbring Flammenwerfer\" \n\nSome inexplicable error tripped the command.  Probably best to ping the bot developer on this.")
    await ctx.send(f"{factoryName} is now set to build the {tankName}!")

@bot.command()
async def configureIndustry(ctx):
    import random, asyncio
    NameInput = int(round(industryCount * random.random())) - 1
    TypeInput = int(round(industryTypeCount*random.random())) - 1
    specialStatus = False
    country = await getUserCountry(ctx)
    await ctx.send(f"Name the tank you wish to build.  Or, reply with \"none\" to stop future production of vehicles.")
    def check(m: discord.Message): return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=1800.0)
    except asyncio.TimeoutError:
        await ctx.reply(f"The command to send a message to {country} has timed out.")
        return
    try:
        tankName = msg.content
        if tankName == "none":
            for factoryName in productionList[country]:
                productionList[country][factoryName]['nextTank'] = ""
                await ctx.send(f"Everything will no longer build new vehicles automatically.")
            return
        if tankName == "7.5T Flatbed Transporter" or tankName == "2.5T Transport Truck":
            if variablesList[country][0]["type"] == "company":
                specialStatus = True
        if specialStatus == False:
            tankWeight = int(tanksList[tankName]["weight"])
    except Exception:
        await ctx.send(f"The {msg.content} doesn't exist!  Make sure the name is spelled correctly.")
        return
    if tanksList[tankName]["status"] != "approved" and specialStatus == False:
        await ctx.send(f"The {msg.content} is not approved for production.  Status: {tanksList[tankName]['status']}")
        return
    try:
        print(inventoryList[country][tankName])
    except Exception:
        if tanksList[tankName]["originType"] == "company":
            inventoryList[country][tankName] = {'weight': tanksList[tankName]["weight"], 'type': "foreign", 'stored': 0, 'deployed': 0, 'deployedAbroad': 0}
        elif specialStatus == False:
            await ctx.send(f"The {msg.content} doesn't exist in your inventory, but this name is already in use.")
            return
    for factoryName in productionList[country]:
        try:
            # update for if a tank
            if productionList[country][factoryName]['status'] != "under construction":
                productionList[country][factoryName]['status'] = "building"
            productionList[country][factoryName]['nextTank'] = tankName
            if tankName == "2.5T Transport Truck":
                productionList[country][factoryName]['nextTankWeight'] = 2.5
            elif tankName == "7.5T Flatbed Transporter":
                productionList[country][factoryName]['nextTankWeight'] = 7.5
            else:
                productionList[country][factoryName]['nextTankWeight'] = tankWeight
            if productionList[country][factoryName]['currentTank'] == "":
                productionList[country][factoryName]['currentTank'] = productionList[country][factoryName]['nextTank']
                if tankName == "2.5T Transport Truck":
                    productionList[country][factoryName]['currentTankWeight'] = 2.5
                elif tankName == "7.5T Flatbed Transporter":
                    productionList[country][factoryName]['currentTankWeight'] = 7.5
                else:
                    productionList[country][factoryName]['currentTankWeight'] = productionList[country][factoryName]['nextTankWeight']
                tons = tanksList[tankName]["weight"]
                tankCountry = tanksList[tankName]["origin"]
                # if country == tankCountry:
                #     cost = round(pow((float(tons) * costPerTon), 1.1))
                # if country != tankCountry and variablesList[tankCountry][0]["type"] == "company":
                #     cost = round(pow((float(tons) * costPerTon), 1.1)) + int(tanksList[tankName]["licenseFee"])
                #     variablesList[tankCountry][0]["money"] = int(variablesList[tankCountry][0]["money"]) + int(tanksList[tankName]["licenseFee"])
                # variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - cost
        except Exception:
            await ctx.send(f"\"Hans \nbring Flammenwerfer\" \n\nSome inexplicable error tripped the command.  Probably best to ping the bot developer on this.")
    await ctx.send(f"Everything is now set to build the {tankName}!")

@bot.command()
async def flipGeometry(ctx):
    country = await getUserCountry(ctx)

    # received if else statement from stackoverflow: https://stackoverflow.com/questions/65169339/download-csv-file-sent-by-user-discord-py
    for attachment in ctx.message.attachments:

        fileData = json.loads(await attachment.read())
        bigString = json.dumps(fileData)
        bigString.replace("\\", "")
        blueprintData = json.loads(bigString)
        blueprintData[0]["data"] = json.loads(blueprintData[0]["data"])
        blueprintData[1]["data"] = json.loads(blueprintData[1]["data"])
        print(blueprintData[0]["data"])
        name = ""
        if blueprintData[0]["id"] != "Compartment":
            await ctx.send("This isn't a valid compartment .blueprint!  Make sure you are uploading the .blueprint file of just the compartment, located in `%userprofile%\Documents\My Games\Sprocket\Factions\Default\Blueprints\Compartments`")
            return
        else:
            name = blueprintData[0]["data"]["name"]
            await ctx.send(f"Initializing...\n{name} successfully parsed!")

        x_state = True
        y_state = False
        z_state = False
        alternator = 0
        x = 0
        print(blueprintData[0]["data"]["compartment"]["points"])
        for point in blueprintData[0]["data"]["compartment"]["points"]:
            print(point)
            if alternator == 3:
                alternator = 0
            if alternator == 0 and x_state == True:
                blueprintData[0]["data"]["compartment"]["points"][x] = point-(2*point)
            if alternator == 1 and y_state == True:
                blueprintData[0]["data"]["compartment"]["points"][x] = point-(2*point)
            if alternator == 2 and z_state == True:
                blueprintData[0]["data"]["compartment"]["points"][x] = point-(2*point)
            x += 1
            alternator += 1
        print(blueprintData[0]["data"]["compartment"]["points"])
        from discord import File
        import io
        await ctx.send("Done!")
        data0 = json.dumps(blueprintData[0]["data"])
        data1 = json.dumps(blueprintData[1]["data"])
        data0.replace("\\", "")
        data1.replace("\\", "")
        blueprintData[0]["data"] = data0
        blueprintData[1]["data"] = data1


        # fileData[0]["data"] = blueprintData
        stringOut = json.dumps(blueprintData, indent=4)
        data = io.BytesIO(stringOut.encode())
        await ctx.send(file=discord.File(data, f'{name}.blueprint'))

@bot.command()
async def bakeGeometry(ctx):
    import asyncio
    country = await getUserCountry(ctx)


    # received if else statement from stackoverflow: https://stackoverflow.com/questions/65169339/download-csv-file-sent-by-user-discord-py
    for attachment in ctx.message.attachments:

        blueprintData = json.loads(await attachment.read())
        blueprintDataSave = json.loads(await attachment.read())
        name = blueprintData["header"]["name"]
        x = 0
        for iteration in blueprintData["blueprints"]:
            partName = blueprintData["blueprints"][x]["id"]
            partString = blueprintData["blueprints"][x]["data"]
            partString.replace("\\", "")
            partInfo = json.loads(partString)
            clonePartInfo = copy.deepcopy(partInfo)
            if partName == "Compartment" and partInfo["name"] == "target":
                basePartPoints = partInfo["compartment"]["points"]
                basePartPointsLength = len(basePartPoints)
                basePartSharedPoints = partInfo["compartment"]["sharedPoints"]
                basePartThicknessMap = partInfo["compartment"]["thicknessMap"]
                basePartFaceMap = partInfo["compartment"]["faceMap"]

                print("Found a target!")
                y = 0
                for iteration in blueprintData["blueprints"]:
                    sourcePartName = blueprintData["blueprints"][y]["id"]
                    sourcePartString = blueprintData["blueprints"][y]["data"]
                    sourcePartString.replace("\\", "")
                    sourcePartInfo = json.loads(sourcePartString)

                    if sourcePartName == "Compartment" and sourcePartInfo["name"] == "source":
                        print("Found a source!")
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
                            #angles = [sourcePartRotZ, sourcePartRotY, -1*sourcePartRotX]
                            angles = [-1*sourcePartRotX, -1*sourcePartRotY, -1*sourcePartRotZ]

                            newVector = braveRotateVector(vector, angles)

                            #newVector = rotateVector(vector, angles)
                            sourcePartPoints[pos] = round(newVector[0] + sourcePartPosX, roundPoint)
                            sourcePartPoints[pos + 1] = round(newVector[1] + sourcePartPosY, roundPoint)
                            sourcePartPoints[pos + 2] = round(newVector[2] + sourcePartPosZ, roundPoint)
                            pos += 3

                        # shared point lists (adjusted to not overlap with current faces)
                        clonePartInfo["compartment"]["points"] = basePartPoints + sourcePartPoints

                        for group in sourcePartSharedPoints:
                            pos = 0
                            while pos < len(group):
                                group[pos] = group[pos] + int(basePartPointsLength/3)
                                pos += 1
                        clonePartInfo["compartment"]["sharedPoints"] = basePartSharedPoints + sourcePartSharedPoints
                        print(sourcePartSharedPoints)
                        print(basePartSharedPoints)
                        print(clonePartInfo["compartment"]["sharedPoints"])
                        #thickness maps (simply merged, it's how it works)
                        clonePartInfo["compartment"]["thicknessMap"] = basePartThicknessMap + sourcePartThicknessMap

                        # face map (adjusted to not overlap with current faces)

                        for group in sourcePartFaceMap:
                            pos = 0
                            while pos < len(group):
                                group[pos] = group[pos] + int(basePartPointsLength/3)
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
        # data0 = json.dumps(blueprintData[0]["data"])
        # data1 = json.dumps(blueprintData[1]["data"])
        # data0.replace("\\", "")
        # data1.replace("\\", "")
        # blueprintData[0]["data"] = data0
        # blueprintData[1]["data"] = data1


        # fileData[0]["data"] = blueprintData
        stringOut = json.dumps(blueprintDataSave, indent=4)
        data = io.BytesIO(stringOut.encode())
        await ctx.send(file=discord.File(data, f'{name}(merged).blueprint'))


@bot.command()
async def flipGeometry2(ctx):
    import asyncio
    for attachment in ctx.message.attachments:
        fileData = json.loads(await attachment.read())
        bigString = json.dumps(fileData)
        bigString.replace("\\", "")
        blueprintData = json.loads(bigString)
        blueprintData[0]["data"] = json.loads(blueprintData[0]["data"])
        blueprintData[1]["data"] = json.loads(blueprintData[1]["data"])
        print(blueprintData[0]["data"])
        name = ""
        if blueprintData[0]["id"] != "Compartment":
            await ctx.send("This isn't a valid compartment .blueprint!  Make sure you are uploading the .blueprint file of just the compartment, located in `%userprofile%\Documents\My Games\Sprocket\Factions\Default\Blueprints\Compartments`")
            return
        else:
            name = blueprintData[0]["data"]["name"]
            await ctx.send(f"Initializing...\n{name} successfully parsed!")
        roundVal = 0
        await ctx.send("Specify the amount of digits to use when round \nBigger numbers mean more chances to fix floating-point errors, while smaller numbers better preserve the original geometry shape. \n `5` is recommended for most cases.")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await bot.wait_for('message', check=check, timeout=90.0)
            roundVal = int(msg.content)
        except asyncio.TimeoutError:
            await ctx.send("Operation cancelled.")
            return


        x = 0
        for point in blueprintData[0]["data"]["compartment"]["points"]:
            blueprintData[0]["data"]["compartment"]["points"][x] = round(point, roundVal)
            x += 1
        import io
        await ctx.send("Done!")
        data0 = json.dumps(blueprintData[0]["data"])
        data1 = json.dumps(blueprintData[1]["data"])
        data0.replace("\\", "")
        data1.replace("\\", "")
        blueprintData[0]["data"] = data0
        blueprintData[1]["data"] = data1


        # fileData[0]["data"] = blueprintData
        stringOut = json.dumps(blueprintData, indent=4)
        data = io.BytesIO(stringOut.encode())
        await ctx.send(file=discord.File(data, f'{name}.blueprint'))

#yes, it was stolen from the internet.

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

def googleRotateVector(vector, rotations):
    import numpy as np
    for rotation in rotations:
        vector = np.dot(rotation, vector)
    return vector

# Example usage:

def rotateVector(vector, angles):
    print(angles)
    import math
    x = vector[0]
    y = vector[1]
    z = vector[2]

    # yz plane
    ny = y * math.cos(angles[0]) - z * math.sin(angles[0])
    nz = y * math.sin(angles[0]) + z * math.cos(angles[0])

    y = ny
    z = nz

    #xy plane
    nx = x * math.cos(angles[2]) - y * math.sin(angles[2])
    ny = x * math.sin(angles[2]) + y * math.cos(angles[2])

    x = nx
    y = ny
    z = nz

    # xz plane
    nz = z * math.cos(angles[1]) + x * math.sin(angles[1])
    nx = z * math.sin(angles[1]) - x * math.cos(angles[1])

    # combined
    # x = vector[0] * math.cos(angles[0]) - vector[1] * math.sin(angles[0]) + vector[0] * math.cos(angles[1]) - vector[2] * math.sin(angles[1])
    # y = vector[0] * math.sin(angles[0]) + vector[1] * math.cos(angles[0]) + vector[1] * math.sin(angles[2]) + vector[2] * math.cos(angles[2])
    # z = vector[0] * math.sin(angles[1]) + vector[2] * math.cos(angles[1]) + vector[1] * math.sin(angles[2]) + vector[2] * math.cos(angles[2])

    return [nx, ny, nz]


@bot.command()
async def flipGeometry3(ctx):

    # received if else statement from stackoverflow: https://stackoverflow.com/questions/65169339/download-csv-file-sent-by-user-discord-py
    for attachment in ctx.message.attachments:

        fileData = json.loads(await attachment.read())
        bigString = json.dumps(fileData)
        bigString.replace("\\", "")
        blueprintData = json.loads(bigString)
        blueprintData[0]["data"] = json.loads(blueprintData[0]["data"])
        blueprintData[1]["data"] = json.loads(blueprintData[1]["data"])
        print(blueprintData[0]["data"])
        name = ""
        if blueprintData[0]["id"] != "Compartment":
            await ctx.send("This isn't a valid compartment .blueprint!  Make sure you are uploading the .blueprint file of just the compartment, located in `%userprofile%\Documents\My Games\Sprocket\Factions\Default\Blueprints\Compartments`")
            return
        else:
            name = blueprintData[0]["data"]["name"]
            await ctx.send(f"Initializing...\n{name} successfully parsed!")

        x_state = True
        y_state = False
        z_state = False
        alternator = 0
        x = 0
        print(blueprintData[0]["data"]["compartment"]["points"])
        for point in blueprintData[0]["data"]["compartment"]["points"]:
            print(point)
            if alternator == 3:
                alternator = 0
            if alternator == 0 and x_state == True:
                blueprintData[0]["data"]["compartment"]["points"][x] = point-(2*point)
            if alternator == 1 and y_state == True:
                blueprintData[0]["data"]["compartment"]["points"][x] = point-(2*point)
            if alternator == 2 and z_state == True:
                blueprintData[0]["data"]["compartment"]["points"][x] = point-(2*point)
            x += 1
            alternator += 1
        print(blueprintData[0]["data"]["compartment"]["points"])
        from discord import File
        import io
        await ctx.send("Done!")
        data0 = json.dumps(blueprintData[0]["data"])
        data1 = json.dumps(blueprintData[1]["data"])
        data0.replace("\\", "")
        data1.replace("\\", "")
        blueprintData[0]["data"] = data0
        blueprintData[1]["data"] = data1


        # fileData[0]["data"] = blueprintData
        stringOut = json.dumps(blueprintData, indent=4)
        data = io.BytesIO(stringOut.encode())
        await ctx.send(file=discord.File(data, f'{name}.blueprint'))

@bot.command()
async def tankInfo(ctx, *, tankName):
    try:
        print(tanksList[tankName])
    except KeyError:
        await ctx.send("This tank doesn't exist!  Use the `-listTanks` command to see what you have available, or take a look at tanks that contractors have for sale!")
        return

    country = await getUserCountry(ctx)
    costVal = round(pow((float(tanksList[tankName]["weight"]) * costPerTon), 1.1))
    print(country)
    if tanksList[tankName]["originType"] == country and tanksList[tankName]["origin"] != country:
        await ctx.send("This isn't your tank!  You're only allowed to get information on your own vehicles or company-designed tanks.")
    else:
        embed = discord.Embed(title="Stat page: " + tankName, description="A " + tanksList[tankName]["originType"] + "-built tank", color=discord.Color.random())
        embed.add_field(name="Origin", value=tanksList[tankName]["origin"], inline=False)
        embed.add_field(name="Weight", value=str(tanksList[tankName]["weight"]) + "T", inline=False)
        embed.add_field(name="Cost to build", value="฿" + str(costVal), inline=False)
        if variablesList[country][0]["type"] == "company":
            embed.add_field(name="Amount in storage", value=inventoryList[country][tankName]["stored"], inline=False)
        if country == ctx.channel.name:
            try:
                embed.add_field(name="Amount in storage", value=inventoryList[country][tankName]["stored"], inline=False)
                embed.add_field(name="Amount deployed to nearby fronts", value=inventoryList[country][tankName]["deployed"], inline=False)
                embed.add_field(name="Amount deployed to faraway fronts", value=inventoryList[country][tankName]["deployedAbroad"], inline=False)
            except KeyError:
                embed.add_field(name="Amount in storage", value="None, you haven't purchased any of these tanks yet!", inline=False)
        if tanksList[tankName]["licenseFee"] != "0" and tanksList[tankName]["buyoutFee"] != "0":
            embed.add_field(name="Licensing fee", value="฿" + str(tanksList[tankName]["licenseFee"]), inline=False)
            embed.add_field(name="Cost to buy vehicle rights", value="฿" + str(tanksList[tankName]["buyoutFee"]), inline=False)
        await ctx.send(embed=embed)

async def getUserCountry(ctx):
    user_id = ctx.author.id

    ainakikoRole = discord.utils.get(ctx.message.guild.roles, name="aina-kiko")
    argunshireRole = discord.utils.get(ctx.message.guild.roles, name="argunshire")
    austrondianRole = discord.utils.get(ctx.message.guild.roles, name="austrondian")
    bugoslaviaRole = discord.utils.get(ctx.message.guild.roles, name="bugoslavia")
    ghaniaRole = discord.utils.get(ctx.message.guild.roles, name="ghania")
    illustravitRole = discord.utils.get(ctx.message.guild.roles, name="illustravit")
    landepunktRole = discord.utils.get(ctx.message.guild.roles, name="landepunkt")
    nunatuniqRole = discord.utils.get(ctx.message.guild.roles, name="nunatuniq")
    posterianRole = discord.utils.get(ctx.message.guild.roles, name="posterian")
    shoishoRole = discord.utils.get(ctx.message.guild.roles, name="shoisho")
    independentRole = discord.utils.get(ctx.message.guild.roles, name="independent")

    if ainakikoRole in ctx.message.author.roles:
        return "aina-kiko"
    if argunshireRole in ctx.message.author.roles:
        return "argunshire"
    if austrondianRole in ctx.message.author.roles:
        return "austrondian"
    if bugoslaviaRole in ctx.message.author.roles:
        return "bugoslavia"
    if ghaniaRole in ctx.message.author.roles:
        return "ghania"
    if illustravitRole in ctx.message.author.roles:
        return "illustravit"
    if landepunktRole in ctx.message.author.roles:
        return "landepunkt"
    if nunatuniqRole in ctx.message.author.roles:
        return "nunatuniq"
    if posterianRole in ctx.message.author.roles:
        return "posterian"
    if shoishoRole in ctx.message.author.roles:
        return "shoisho"
    if independentRole in ctx.message.author.roles:
        try:
            return operatorsList[str(user_id)]
        except Exception:
            return "invalid_country"

@bot.command()
async def listProductionLegacy(ctx):
    country = await getUserCountry(ctx)
    if country == "invalid_country":
        await ctx.send("This is not a valid country or company!")

    embed = discord.Embed(title=str(variablesList[country][0]["displayName"]) + "'s Tanks in Production",
                          description="This is all tanks you currently have in production.  \n You currently have ฿" + str(variablesList[country][0]["money"]) + " in funds, and " + str(variablesList[country][0]["unspentTonnage"]) + "T in available production.",
                          color=discord.Color.random())
    for tankName, tankInfo in manufacturingList.items():
        if tankInfo["country"] == country:
            embed.add_field(name=tankInfo["name"], value="progress: " + str(round(100*float(tankInfo["progress"]))) + "%",
                            inline=False)
    await ctx.send(embed=embed)


async def getProductionRate(tankName: str):
    weight = float(tanksList[tankName]["weight"])
    return tonsPerDay/weight

@bot.command()
async def setBaseTechnology(ctx, orgValue: int):
    value = orgValue - 1
    baseTechValue = value
    x = 0
    for country in variablesList:
        if int(variablesList[country][0]["suspensionTech"]) < value:
            variablesList[country][0]["suspensionTech"] = value
            x += 1
        if int(variablesList[country][0]["cannonTech"]) < value:
            variablesList[country][0]["cannonTech"] = value
            x += 1
        if int(variablesList[country][0]["armorTech"]) < value:
            variablesList[country][0]["armorTech"] = value
            x += 1
        if int(variablesList[country][0]["engineTech"]) < value:
            variablesList[country][0]["engineTech"] = value
            x += 1
    await ctx.send(f"Updated {x} research sections to the base level of {orgValue} (registered as {value} in the bot)")


@bot.command()
async def listTanksLegacy(ctx):
    user_id = ctx.author.id
    try:
        country = operatorsList[str(user_id)]
    except Exception:
        print("test")
        country = ctx.channel.name
    print(country)
    embed = discord.Embed(title=str(variablesList[country][0]["displayName"]) + "'s Tank Designs",
                          description="These are all the tanks you have available to produce. \n You currently have ฿" + str(variablesList[country][0]["money"]) + " in funds, and " + str(variablesList[country][0]["unspentTonnage"]) + "T in available production.",
                          color=discord.Color.random())
    countryTanksInfo = inventoryList[country]
    print(countryTanksInfo)
    for tankName, tankInfo in inventoryList[country].items():
        print(tankInfo)
        embed.add_field(name=tankName, value="weight: " + str(tankInfo["weight"]) + " tons \n In storage: " + str(tankInfo["stored"]) + "\n Deployed: " + str(tankInfo["deployed"]),inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role('Campaign Manager')
async def listDeployment(ctx, country: str):

    embed = discord.Embed(title=str(variablesList[country][0]["displayName"]) + "'s Deployments",
                          description="These are all the tanks deployed by " + country + ". \n They currently have ฿" + str(variablesList[country][0]["money"]) + " in funds, and " + str(variablesList[country][0]["unspentTonnage"]) + "T in available production.",
                          color=discord.Color.random())
    countryTanksInfo = inventoryList[country]
    print(countryTanksInfo)
    for tankName, tankInfo in inventoryList[country].items():
        print(tankInfo)
        if int(tankInfo["deployed"]) > 0:
            embed.add_field(name=tankName, value="Deployed: " + str(tankInfo["deployed"]),inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def listTanks(ctx):
    user_id = ctx.author.id
    try:
        country = operatorsList[str(user_id)]
    except Exception:
        print("test")
        country = ctx.channel.name
    print(country)
    description = ""
    appendation = ""
    for tankName, tankInfo in inventoryList[country].items():
        print(tankName)
        appendation = f" ** {tankName} ** \n weight: {tankInfo['weight']} tons \n In storage: {tankInfo['stored']} \n Deployed: {tankInfo['deployed']} \n \n"
        description = description.__add__(appendation)
        print(appendation)

    embed = discord.Embed(title=str(variablesList[country][0]["displayName"]) + "'s Tank Designs",
                          description=description,
                          color=discord.Color.random())
    countryTanksInfo = inventoryList[country]
    print(countryTanksInfo)
    await ctx.send(embed=embed)

@bot.command()
async def listBlimps(ctx):
    country = await getUserCountry(ctx)
    print(country)
    description = ""
    appendation = ""
    for blimpName, blimpInfo in blimpList.items():
        if blimpInfo["origin"] == country:
            appendation = f" ** {blimpName} ** \n Distance from launch point: {blimpInfo['miles_travelled']} miles \n Length of route: {blimpInfo['RNGpoint']} \n Cargo: {blimpInfo['count']}x {blimpInfo['stowage']} \n \n"
            description = description.__add__(appendation)

    embed = discord.Embed(title=str(variablesList[country][0]["displayName"]) + "'s Blimps",
                          description=description,
                          color=discord.Color.random())
    countryTanksInfo = inventoryList[country]
    print(countryTanksInfo)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role('Campaign Manager')
async def approveTank(ctx, tankName: str):
    try:
        tanksList[tankName]["status"] = "approved"
        await ctx.send("Registered the " + tankName + "!")
    except Exception:
        await ctx.send("This tank doesn't exist!")
        return

@bot.command()
async def registerTankLegacy(ctx):
    name = "invalid"
    weight = -1
    errors = 0
    country = await getUserCountry(ctx)
    for attachment in ctx.message.attachments:

        fileData = (await attachment.read())
        # print(fileData)
        blueprintData = json.loads(await attachment.read())
        weight = float(blueprintData["header"]["mass"])/1000
        cost = round(pow((weight * costPerTon), 1.1))
        name = blueprintData["header"]["name"]
        await ctx.send("This tank was made in Sprocket version " + blueprintData["header"]["gameVersion"] + "\nVehicle weight: " + str(weight) + " tons. \nVehicle cost: ฿" + str(cost) )

        x = 0
        for iteration in blueprintData["blueprints"]:
            partName = blueprintData["blueprints"][x]["id"]
            partString = blueprintData["blueprints"][x]["data"]
            partString.replace("\\", "")
            partInfo = json.loads(partString)
            if partName == "CRW":
                for crew in partInfo["seats"]:
                    print(crew["spaceAlloc"])
                    if float(crew["spaceAlloc"]) > 1.001:
                        await ctx.send("This vehicle was file edited to have stronger crew and cannot be accepted until this is fixed.")
                        errors += 1
            if partName == "CNN":
                for cannon in partInfo["blueprints"]:
                    caliber = int(cannon["caliber"])
                    propellant = int(cannon["breechLength"])
                    cannonTechLevel = variablesList[country][0]["cannonTech"]
                    # propLimit = propellantLengths[cannonTechLevel]
                    boreLimit = float(boreLengths[cannonTechLevel])
                    shellLimit = float(shellLengths[cannonTechLevel])
                    calculatedShell = (3*caliber) + propellant
                    calculatedBore = calculatedShell/1000
                    errors += 1
                    for segment in partInfo["blueprints"][0]["segments"]:
                        calculatedBore += float(segment['len'])
                    if calculatedShell > shellLimit:
                        await ctx.send(f"The \"{cannon['name']}\" is invalid!  This cannon uses {calculatedShell}mm shells, while the limit is {shellLimit}mm.")
                    if calculatedBore > boreLimit:
                        await ctx.send(f"The \"{cannon['name']}\" is invalid!  This cannon uses a {calculatedBore}m bore length, while the limit is {boreLimit}m.")
                    else:
                        await ctx.send(f"\"{cannon['name']}\": {caliber}x{calculatedShell}mm with a {calculatedBore}m bore length.")
                        errors += -1

            if partName == "Compartment" and partInfo["name"] != "US Tanker Sitting Angled 1 (Zheifu Variant)":
                name = partInfo["name"]
                # displacement = float(partInfo["cylinders"])*float(partInfo["cylinderDisplacement"])
                # print(country)

                armorTechLevel = variablesList[country][0]["armorTech"]
                armorLimit = armorThickness[armorTechLevel]
                tooThinPlates = 0
                tooThickPlates = 0
                if partInfo["genID"] == "VSH":
                    width = float(partInfo["genData"]["shape"][1]) + 2*float(partInfo["genData"]["shape"][6])
                    print(str(width) + " aaaaaaaaaaaaaaaaaaaaa")
                    for thickness in partInfo["genData"]["armour"]:
                        # print(thickness)
                        if thickness > armorLimit:
                            tooThickPlates += 1
                        if thickness < 15:
                            tooThinPlates += 1
                else:
                    # print(len(partInfo["compartment"]["points"]))
                    tooThinPlates = 0
                    tooThickPlates = 0
                    for thickness in partInfo["compartment"]["thicknessMap"]:
                        # print(thickness)
                        if thickness > armorLimit:
                            tooThickPlates += 1
                        if thickness < 15:
                            tooThinPlates += 1
                    xmin = 0
                    ymin = 0
                    zmin = 0
                    xmax = 0
                    ymax = 0
                    zmax = 0
                    min = [0,0,0]
                    max = [0,0,0]
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
                        if height < 0.99999:
                            await ctx.send(f"{name} is {round(height, 2)} meters tall.  This won't fit any crew.")
                            errors += 1
                        if variablesList[country][0]["type"] == "country":
                            widthLimit = railwayGaugeLimits[int(variablesList[country][0]["railwayTech"])]
                            if width > widthLimit:
                                await ctx.send(f"{name} is {round(width, 2)} meters wide.  Warning: this is too wide for your railways, which can only support hulls up to {widthLimit} wide.")
                    else:
                        basketVolume = partInfo["turret"]["ringArmour"]


                        ringArmor = partInfo["turret"]["ringArmour"]
                        torque = partInfo["turret"]["traverse"]["torque"]
                        ratio = partInfo["turret"]["traverse"]["ratio"]
                        torqueLevel = variablesList[country][0]["engineTech"]
                        print(torqueLevel)
                        torqueLimit = GCMtorque[torqueLevel]
                        ratioLimit = GCMratio[torqueLevel]
                        if abs(int(partInfo["rot"][2])) > 20:
                            # custom mantlet checks
                            if torque > torqueLimit:
                                errors += 1
                                await ctx.send(f"GCM \"{name}\" uses a torque setting above the {torqueLimit}N limit!")
                            if ratio < ratioLimit:
                                errors += 1
                                await ctx.send(f"GCM \"{name}\" has a traverse ratio below the required minimum ratio of {ratioLimit}!")
                        if ringArmor < 15:
                            await ctx.send(f"{name}'s turret ring is below the 15mm armor requirement!")
                            errors += 1




                if tooThickPlates > 0 or tooThinPlates > 0:
                    await ctx.send(f"{name} has {tooThickPlates} armor plates exceeding the armor limit, and {tooThinPlates} armor plates below the minimum 15mm requirement.")
                    errors += 1
                # if (float(engineLimit) + 0.01) < float(displacement):
                #     await ctx.send(f"Engine \"{name}\" displacement is invalid!  This engine is: {displacement} liters, while the limit is {engineLimit}.")
                # else:
                #     await ctx.send(f"Engine \"{name}\" displacement: {displacement} liters")

            if partName == "ENG":
                name = partInfo["name"]
                displacement = float(partInfo["cylinders"])*float(partInfo["cylinderDisplacement"])
                # print(country)
                engineTechLevel = variablesList[country][0]["engineTech"]
                engineLimit = netDisplacement[engineTechLevel]
                if (float(engineLimit) + 0.01) < float(displacement):
                    await ctx.send(f"Engine \"{name}\" displacement is invalid!  This engine is: {displacement} liters, while the limit is {engineLimit}.")
                    errors += 1
                else:
                    await ctx.send(f"Engine \"{name}\" displacement: {displacement} liters")

            x += 1

        costVal = round(pow((float(weight) * 1000), 1.1))

        try:
            print(variablesList[country][0]["type"])
        except Exception:
            await ctx.send("Country name is invalid!")
            return

        # What to do if the process for checking is successful
        name = blueprintData["header"]["name"]
        if errors == 0:
            import asyncio
            licenseFee = 0
            importFee = 0
            buyoutFee = 0
            if variablesList[country][0]["type"] == "company":
                await ctx.send("**Approved!**  Since you are a company, answer the following questions about selling this tank.  \nAvoid using commas and periods in your answer, as any non-number answers will cancel the operation.\n \n### How much you want to charge other countries when they build your tank?")
                def check(m: discord.Message):
                    return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                try:
                    msg = await bot.wait_for('message', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    await ctx.send("Operation cancelled.")
                    return
                else:
                    try:
                        licenseFee = int(msg.content)
                    except Exception:
                        await ctx.send("This isn't a number!  \nOperation cancelled.")
                        return

                await ctx.send("### How much you want to sell built models of this tank for?  \nThis value needs to be greater than the cost to build it.")
                def check(m: discord.Message):
                    return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                try:
                    msg = await bot.wait_for('message', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    await ctx.send("Operation cancelled.")
                    return
                else:
                    try:
                        importFee = int(msg.content)
                    except Exception:
                        await ctx.send("This isn't a number!  \nOperation cancelled.")
                        return

                await ctx.send("### How much you want to charge other countries to purchase the blueprints of your vehicle?  \nThis removes all licensing fees for that country and allows them to design their own versions of it.")
                def check(m: discord.Message):
                    return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                try:
                    msg = await bot.wait_for('message', check=check, timeout=90.0)
                except asyncio.TimeoutError:
                    await ctx.send("Operation cancelled.")
                    return
                else:
                    try:
                        buyoutFee = int(msg.content)
                    except Exception:
                        await ctx.send("This isn't a number!  \nOperation cancelled.")
                        return

            await ctx.send("## Attach the specified photos of your vehicle here.  \n**Picture 1** needs to be a well-lit picture of the tank's front and side.\n**Picture 2** needs to be a well-lit picture of the tank's rear and side.\n**Picture 3** needs to be a front view of the tank using the \"Internals\" overlay.\nAn example of what we are looking for can be found [here](<https://media.discordapp.net/attachments/970048246191894558/1170154647110037534/Photo_Submission_Requirements_V2.png?ex=65580270&is=65458d70&hm=cee3cb20a4ad6bf5ada6eb91869b35b9818b081e1ece31cc5b7c811093b8cf0b&=&width=1201&height=675>)")

            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            try:
                msg = await bot.wait_for('message', check=check, timeout=5000.0)
            except asyncio.TimeoutError:
                await ctx.send("Operation cancelled.")
                return

            editedBlueprintData = await attachNumberDecals(blueprintData)
            name = blueprintData["header"]["name"]
            await ctx.send("The " + name + " has been sent off for inspection!")
            json_output = json.dumps(editedBlueprintData, indent=4)
            file_location = TANKrepository
            from pathlib import Path
            Path(file_location).mkdir(parents=True, exist_ok=True)
            with open(str(file_location + "/" + str(name) + ".blueprint"), "w") as outfile:
                outfile.write(json_output)
            print(type(blueprintData))
            originType = variablesList[country][0]["type"]
            inventoryList[country][name] = {'weight': weight, 'type': "local", 'stored': 0, 'deployed': 0, 'deployedAbroad': 0}
            tanksList[name] = {'origin': country, 'originType': originType, 'status': 'undetermined', 'weight': weight, 'width': width, 'cost': costVal, 'licenseFee': licenseFee, 'importFee': importFee, 'buyoutFee': buyoutFee}
            msg = ctx.message
            url = msg.jump_url
            chnl = bot.get_channel(int(tankLogChat))
            await chnl.send(f"--------------------------------------------\n {country} is looking to register a new tank design! \nName: {name} \nLicensing fee: {licenseFee} \nImport fee: {importFee} \nBuyout fee: {buyoutFee} \n## Vehicle blueprint: [here]({url})")
            view = approveTankToggle(name)
            await chnl.send(view=view)

        else:
            await ctx.send("The " + name + " needs fixes to the problems listed above before it can be registered.")



class approveTankToggle(discord.ui.View):
    def __init__(self, tankName):
        super().__init__(timeout=None)
        self.value = None
        self.tankName = tankName

        # When the confirm button is pressed, set the inner value to `True` and
        # stop the View from listening to more input.
        # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Approve Tank', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        tankName = self.tankName
        button.disabled = True
        await interaction.response.edit_message(view=self, content=f"The {tankName} has been approved!")
        # await interaction.response.send_message('Confirming', ephemeral=True)
        tanksList[tankName]["status"] = "approved"
        # await interaction.response.send_message(f"The {tankName} has been approved!")
        country = tanksList[tankName]["origin"]
        channel = bot.get_channel(int(variablesList[country][0]["channel"]))
        await channel.send(f"### The {tankName} has passed inspection!  It is now available for production.")
        print("Hi!")
        self.value = True
        self.stop()

        # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Deny Tank', style=discord.ButtonStyle.red, custom_id='lol')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        tankName = self.tankName
        await interaction.response.edit_message(view=self, content=f"The {tankName} has been denied.  Please inform the submitter as to why it was denied, if you have not already.")
        tanksList[tankName]["status"] = "denied"
        country = tanksList[tankName]["origin"]
        channel = bot.get_channel(int(variablesList[country][0]["channel"]))
        await channel.send(f"### The {tankName} failed inspection.  Await information from the inspector as to why it was not approved for production.")
        self.value = False
        self.stop()

    async def callback(self, interaction: discord.Interaction):
        print("Hello!")

@bot.command()
async def registerTank(ctx):
    name = "invalid"
    weight = -1
    errors = 0
    country = await getUserCountry(ctx)
    for attachment in ctx.message.attachments:
        configuration = await getZheifuBlueprintCheckerConfig(ctx)
        results = await runBlueprintCheck(ctx, attachment, configuration)

        name = results["tankName"]
        weight = results["tankWeight"]
        valid = results["valid"]
        crewReport = results["crewReport"]
        crewCount = results["crewCount"]
        maxVehicleArmor = float(results["maxArmor"])
        tankWidth = results["tankWidth"]
        costVal = round(pow((float(weight) * 1000), 1.1))

        try:
            print(variablesList[country][0]["type"])
        except Exception:
            await ctx.send("Country name is invalid!")
            return

        # What to do if the process for checking is successful

        if valid == True:
            import asyncio

            # initial variable setup
            allowWeld = False
            allowRivet = False
            licenseFee = 0
            importFee = 0
            buyoutFee = 0
            maxLegalArmor = float(configuration["armorMax"])
            armorRatio = maxVehicleArmor/maxLegalArmor
            print(armorRatio)
            timeScalar = 1

            if variablesList[country][0]["type"] == "company":
                await ctx.send("**Approved!**  Since you are a company, answer the following questions about selling this tank.  \nAvoid using commas and periods in your answer, as any non-number answers will cancel the operation.\n \n### How much you want to charge other countries when they build your tank?")
                def check(m: discord.Message):
                    return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                try:
                    msg = await bot.wait_for('message', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    await ctx.send("Operation cancelled.")
                    return
                else:
                    try:
                        licenseFee = int(msg.content)
                    except Exception:
                        await ctx.send("This isn't a number!  \nOperation cancelled.")
                        return

                await ctx.send("### How much you want to sell built models of this tank for?  \nThis value needs to be greater than the cost to build it.")
                def check(m: discord.Message):
                    return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                try:
                    msg = await bot.wait_for('message', check=check, timeout=60.0)
                except asyncio.TimeoutError:
                    await ctx.send("Operation cancelled.")
                    return
                else:
                    try:
                        importFee = int(msg.content)
                    except Exception:
                        await ctx.send("This isn't a number!  \nOperation cancelled.")
                        return

                await ctx.send("### How much you want to charge other countries to purchase the blueprints of your vehicle?  \nThis removes all licensing fees for that country and allows them to design their own versions of it.")
                def check(m: discord.Message):
                    return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                try:
                    msg = await bot.wait_for('message', check=check, timeout=90.0)
                except asyncio.TimeoutError:
                    await ctx.send("Operation cancelled.")
                    return
                else:
                    try:
                        buyoutFee = int(msg.content)
                    except Exception:
                        await ctx.send("This isn't a number!  \nOperation cancelled.")
                        return
            append = "casted"

            if armorRatio <= 0.9:
                allowWeld = True
                append = "welded, casted"
            if armorRatio <= 0.6:
                allowRivet = True
                append = "riveted, welded, casted"
            await ctx.send(f"What construction type is your vehicle meant to be?  Valid options: {append}.")
            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            try:
                msg = await bot.wait_for('message', check=check, timeout=300.0)
            except asyncio.TimeoutError:
                await ctx.reply("Operation cancelled.")
                return
            else:
                type = str(msg.content).lower()
                if type == "riveted" and allowRivet == True:
                    await ctx.send("Construction type set.")
                    timeScalar = 1.3
                elif type == "welded" and allowWeld == True:
                    await ctx.send("Construction type set.")
                    timeScalar = 1
                elif type == "casted":
                    await ctx.send("Construction type set.")
                    timeScalar = 0.7
                else:
                    if allowRivet == True:
                        await ctx.send("Invalid input, assuming vehicle is riveted.")
                        timeScalar = 1.3
                        type = "riveted"
                    elif allowWeld == True:
                        await ctx.send("Invalid input, assuming vehicle is welded.")
                        timeScalar = 1
                        type = "welded"
                    else:
                        await ctx.send("Invalid input, assuming vehicle is casted.")
                        timeScalar = 0.7
                        type = "casted"

            await ctx.send("## Attach the specified photos of your vehicle here.  \n**Picture 1** needs to be a well-lit picture of the tank's front and side.\n**Picture 2** needs to be a well-lit picture of the tank's rear and side.\n**Picture 3** needs to be a front view of the tank using the \"Internals\" overlay **while looking at the ammunition rack editor.**\n**Picture 4** needs to be a top+side view of the tank using the \"Internals\" overlay **while looking at the ammunition rack editor.**\n### Note: at least one of your screenshots needs to include the full page and Sprocket UI.")

            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            try:
                msg = await bot.wait_for('message', check=check, timeout=5000.0)
            except asyncio.TimeoutError:
                await ctx.send("Operation cancelled.")
                return

            blueprintData = json.loads(await attachment.read())

            editedBlueprintData = await attachNumberDecals(blueprintData)
            await ctx.send("The " + name + " has been sent off for inspection!")
            json_output = json.dumps(editedBlueprintData, indent=4)
            file_location = TANKrepository
            from pathlib import Path
            Path(file_location).mkdir(parents=True, exist_ok=True)
            with open(str(file_location + "/" + str(name) + ".blueprint"), "w") as outfile:
                outfile.write(json_output)
            originType = variablesList[country][0]["type"]
            inventoryList[country][name] = {'weight': weight, 'type': "local", 'stored': 0, 'deployed': 0, 'deployedAbroad': 0}
            tanksList[name] = {'origin': country, 'originType': originType, 'status': 'undetermined', 'weight': weight, 'width': tankWidth, 'cost': costVal, 'buildTimeScalar': timeScalar, 'licenseFee': licenseFee, 'importFee': importFee, 'buyoutFee': buyoutFee}
            msg = ctx.message
            url = msg.jump_url
            chnl = bot.get_channel(int(tankLogChat))
            if variablesList[country][0]["type"] == "company":
                await chnl.send(f"### {country} (company) is looking to register a new tank design! \nName: {name} \nLicensing fee: {licenseFee} \nImport fee: {importFee} \nBuyout fee: {buyoutFee} \nConstruction type: {type} \nCrew count: {crewCount} \n{crewReport} \n## Vehicle blueprint: [here]({url})")
            else:
                await chnl.send(f"### {country} is looking to register a new tank design! \nName: {name} \nConstruction type: {type} \nCrew count: {crewCount} \n{crewReport} \n## Vehicle blueprint: [here]({url})")
            view = approveTankToggle(name)
            await chnl.send(view=view)
            await chnl.send(f"** ** \n\n\n** **")
        else:
            await ctx.send("The " + name + " needs fixes to the problems listed above before it can be registered.")

async def addLine(inputOne: str, inputTwo: str):
    return f"{inputOne}\n{inputTwo}"

async def getZheifuBlueprintCheckerConfig(ctx):
    country = await getUserCountry(ctx)
    cannonLevel = int(variablesList[country][0]["cannonTech"])
    mobilityLevel = int(variablesList[country][0]["engineTech"])
    armorLevel = int(variablesList[country][0]["armorTech"])
    suspensionLevel = int(variablesList[country][0]["suspensionTech"])
    try:
        railwayLevel = int(variablesList[country][0]["railwayTech"])
    except Exception:
        railwayLevel = 2

    # data fed into the blueprint checker

    contestName = "Zheifu"
    era = "Latewar"
    errorTolerance = 0
    gameVersion = 0.127
    enforceGameVersion = False

    # crew
    crewMaxSpace = 1.0
    crewMinSpace = 0.6
    crewMin = 1
    crewMax = 16

    # compartments
    turretRadiusMin = 0.5
    GCMratioMin = variablesList[country][0]["armorTech"]
    GCMtorqueMax = GCMtorque[mobilityLevel]
    hullHeightMin = 0.995
    hullWidthMax = railwayGaugeLimits[railwayLevel]
    allowGCM = True

    # cannons
    caliberLimit = 250
    propellantLimit = 1200
    boreLimit = float(boreLengths[cannonLevel])
    shellLimit = float(shellLengths[cannonLevel])

    # tracks
    beltWidthMin = 50
    requireGroundPressure = True
    groundPressureMax = 1.0

    # fuel
    litersPerDisplacement = 20
    litersPerTon = 0.01
    minEDPT = 0.01

    # suspension
    maxWeight = weightLimit[suspensionLevel]
    torsionBarLengthMin = 0.5
    useDynamicTBLength = True
    allowHVSS = False

    # armor
    armorMin = 15
    ATsafeMin = 14
    armorMax = armorThickness[armorLevel]

    configuration = {
        "contestName": contestName,
        "era": era,
        "gameVersion": gameVersion,
        "weightLimit": maxWeight,
        "enforceGameVersion": enforceGameVersion,
        "errorTolerance": errorTolerance,
        "crewMaxSpace": crewMaxSpace,
        "crewMinSpace": crewMinSpace,
        "crewMin": crewMin,
        "crewMax": crewMax,
        "turretRadiusMin": turretRadiusMin,
        "allowGCM": allowGCM,
        "GCMratioMin": GCMratioMin,
        "GCMtorqueMax": GCMtorqueMax,
        "hullHeightMin": hullHeightMin,
        "hullWidthMax": hullWidthMax,
        "torsionBarLengthMin": torsionBarLengthMin,
        "useDynamicTBLength": useDynamicTBLength,
        "allowHVSS": allowHVSS,
        "beltWidthMin": beltWidthMin,
        "requireGroundPressure": requireGroundPressure,
        "groundPressureMax": groundPressureMax,
        "litersPerDisplacement": litersPerDisplacement,
        "litersPerTon": litersPerTon,
        "minEDPT": minEDPT,
        "caliberLimit": caliberLimit,
        "propellantLimit": propellantLimit,
        "boreLimit": boreLimit,
        "shellLimit": shellLimit,
        "armorMin": armorMin,
        "ATsafeMin": ATsafeMin,
        "armorMax": armorMax
    }
    return configuration


@bot.command()
async def verifyTank(ctx):
    for attachment in ctx.message.attachments:
        configuration = await getZheifuBlueprintCheckerConfig(ctx)
        await runBlueprintCheck(ctx, attachment, configuration)

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
        minEDPT = config["minEDPT"]
        litersPerTon = config["litersPerTon"]
        caliberLimit = config["caliberLimit"]
        propellantLimit = config["propellantLimit"]
        boreLimit = config["boreLimit"]
        shellLimit = config["shellLimit"]
        armorMin = config["armorMin"]
        ATsafeMin = config["ATsafeMin"]
        armorMax = config["armorMax"]


        # declaring initial variables and opening data
        country = await getUserCountry(ctx)
        report = ""
        blueprintData = json.loads(await attachment.read())
        errorCount = 0
        weight = float(blueprintData["header"]["mass"])/1000
        cost = round(pow((weight * costPerTon), 1.1))
        tankName = blueprintData["header"]["name"]
        tankEra = blueprintData["header"]["era"]
        overallTankWidth = 0
        maxArmorOverall = 15 # this gets increased over time
        crewCount = 0
        turretCount = 0
        displacement = 1
        crewReport = "Crew information: \n"

        fileGameVersion = float(blueprintData["header"]["gameVersion"])
        if fileGameVersion != gameVersion and enforceGameVersion == True:
            #report = await addLine(report, )
            report = await addLine(report, f"This vehicle was made in {fileGameVersion}, while it is required to be in {fileGameVersion}.  Please update your game and then readjust your tank to fit the new version.")
            errorCount += 1
        if fileGameVersion != gameVersion and enforceGameVersion == False:
            report = await addLine(report, f"Warning! This vehicle was made in {fileGameVersion}, while it should be made in {gameVersion}.  Check with a {contestName} host or manager to ensure this is acceptable.")
        report = await addLine(report, "This tank was made in Sprocket version " + blueprintData["header"]["gameVersion"] + "\nVehicle weight: " + str(weight) + " tons. \nVehicle cost: ฿" + str(cost) )
        if era.lower() != tankEra.lower():
            report = await addLine(report,f"This vehicle was made in the {tankEra} period, but needs to be sent as a {era} tank.  Please update your vehicle to use the proper era.")
            errorCount += 1
        if weight > weightLimit + 0.01:
            errorCount += 1
            report = await addLine(report,f"This vehicle is overweight!  Please reduce its weight to no more than {weightLimit}T and resend it.")

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
                    report = await addLine(report,f"This vehicle has mantlet face armor above the {armorMax}mm armor limit!  Please resend with a corrected version.")
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
                        report = await addLine(report, f"This vehicle has crew outside of {contestName}'s limits, and cannot be accepted until this is fixed.")
                        errorCount += 1
                    crewCount += 1
                    crewSpot += 1
                    crewStats = f"Crew #{crewSpot}: {crew['spaceAlloc']}m of space, roles: {crew['roles']} \n"
                    crewReport = crewReport + crewStats
                if crewCount < crewMin:
                    report = await addLine(report,f"This vehicle needs to have at least {crewMin} crew members, but only has {crewCount} crew.")
                    errorCount += 1
                if crewCount > crewMax:
                    report = await addLine(report,f"This vehicle needs to have at most {crewMax} crew members, but it has {crewCount} crew.")
                    errorCount += 1
                print(crewReport)


            if partName == "CNN":
                for cannon in partInfo["blueprints"]:
                    caliber = int(cannon["caliber"])
                    propellant = int(cannon["breechLength"])
                    calculatedShell = (3 * caliber) + propellant
                    calculatedBore = calculatedShell / 1000
                    errorCount += 1
                    for segment in partInfo["blueprints"][0]["segments"]:
                        calculatedBore += float(segment['len'])
                    if calculatedShell > shellLimit:
                        report = await addLine(report,
                            f"The \"{cannon['name']}\" is invalid!  This cannon uses a {calculatedShell}mm shell, while the limit for shell length is {shellLimit}mm.")
                    if calculatedBore > boreLimit:
                        report = await addLine(report,
                            f"The \"{cannon['name']}\" is invalid!  This cannon uses a {calculatedBore}m bore length, while the limit is {boreLimit}m.")
                    if propellant > propellantLimit:
                        report = await addLine(report,
                            f"The \"{cannon['name']}\" is invalid!  This cannon uses {propellant}mm of propellant, while the limit is {propellantLimit}mm.")
                    if caliber > caliberLimit:
                        report = await addLine(report,
                            f"The \"{cannon['name']}\" is invalid!  This cannon is {caliber}mm, while the caliber limit is {caliberLimit}mm.")
                    else:
                        report = await addLine(report,
                            f"\"{cannon['name']}\": {caliber}x{calculatedShell}mm with a {calculatedBore}m bore length.")
                        errorCount += -1

            if partName == "Compartment" and partInfo["name"] != "US Tanker Sitting Angled 1 (Zheifu Variant)":
                name = partInfo["name"]
                # displacement = float(partInfo["cylinders"])*float(partInfo["cylinderDisplacement"])
                # print(country)
                tooThinPlates = 0
                tooThickPlates = 0
                ATpronePlates = 0
                if partInfo["genID"] == "VSH":
                    width = float(partInfo["genData"]["shape"][1]) + 2 * float(partInfo["genData"]["shape"][6])
                    print(str(width) + " aaaaaaaaaaaaaaaaaaaaa")
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
                            report = await addLine(report, f"{name} is {round(height, 2)} meters tall.  This won't fit any crew.")
                            errorCount += 1
                        if width > hullWidthMax:
                            report = await addLine(report,
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
                            if allowGCM == False:
                                report = await addLine(report, f"GCMs (including compartment \"{name}\") are not allowed in this contest.")
                                errorCount += 1
                            # custom mantlet checks
                            if torque > GCMtorqueMax:
                                errorCount += 1
                                report = await addLine(report, f"GCM \"{name}\" uses a torque setting above the {GCMtorqueMax}N limit!")
                            if ratio < GCMratioMin:
                                errorCount += 1
                                report = await addLine(report, f"GCM \"{name}\" has a traverse ratio below the required minimum ratio of {GCMtorqueMax}!")
                        if ringArmor < armorMin:
                            report = await addLine(report, f"{name}'s turret ring is below the 15mm armor requirement!")
                            errorCount += 1
                        if ringArmor < ATsafeMin:
                            ATpronePlates += 1
                        if ringArmor > maxArmorOverall:
                            maxArmorOverall = ringArmor
                        if basketVolume < 0 or basketVolume > 5:
                            report = await addLine(report,
                                f"{name} has been file edited and cannot be accepted.  Reason: turret volume is invalid.")
                            errorCount += 1
                        if float(ringRadius) <= turretRadiusMin:
                            report = await addLine(report,
                                f"Warning: {name}'s turret ring is not wide enough to support crew.  Unless this is a cosmetic compartment or custom mentlet, please increase the turret ring diameter.")
                        if ATpronePlates > 1:
                            report = await addLine(report, f"Warning: this vehicle is prone to infantry rifles!  Make sure you are OK with this for your submission.")


                if tooThickPlates > 0 or tooThinPlates > 0:
                    report = await addLine(report,
                        f"{name} has {tooThickPlates} armor plates exceeding the {armorMax}mm armor limit, and {tooThinPlates} armor plates below the minimum 15mm requirement.")
                    errorCount += 1

            if partName == "FLT":
                requiredFLT = round(displacement*litersPerDisplacement * (1 + (litersPerTon*weight)), 2)
                if int(partInfo["L"]) < requiredFLT:
                    report = await addLine(report,f"Your internal fuel tank has {int(partInfo['L'])}L of fuel, but needs {requiredFLT}L of fuel in order to perform adequately.")
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
                    report = await addLine(report, f"Your track ground pressure is {round(groundPressure, 2)}kg/cm², but cannot exceed {groundPressureMax}kg/cm².  Increase your track contact area with the ground, or lighten your vehicle to improve ground pressure.")
                    errorCount += 1

                print(partInfo["wheels"][1])
                if beltWidth < beltWidthMin:
                    report = await addLine(report,
                        f"Your tack belt is {beltWidth}mm wide.  This is too narrow and will lead to bad off-road performance.  Increase your track width to at least {beltWidthMin}mm.")
                    errorCount += 1
                if trackSystemWidth > hullWidthMax:
                    report = await addLine(report,
                        f"Your tack system is {round(trackSystemWidth, 2)} meters wide.  This is too wide for your railways, which can only support vehicles up to {hullWidthMax} meters wide.")
                    errorCount += 1
                if trackSystemWidth > overallTankWidth:
                    overallTankWidth = trackSystemWidth
                try:
                    torsionBarLength = float(partInfo["suspensions"]["TBLength"])
                    if useDynamicTBlength == True:
                        torsionBarLengthMin = torsionBarLengthMin * separation
                    if torsionBarLength < torsionBarLengthMin:
                        report = await addLine(report, f"Your torsion bar is {torsionBarLength}m wide.  This is too short and will lead to bad off-road performance.  Increase your torsion bar length to at least {torsionBarLengthMin}m.")
                        errorCount += 1

                except Exception:
                    if allowHVSS == False:
                        report = await addLine(report, f"This vehicle uses HVSS suspension, which is not permitted in {contestName}")
                        errorCount += 1


            if partName == "FDR":
                separation = 2 * float(partInfo["f"][3])
                sectWidth = 2 * float(partInfo["f"][9])
                totalWidth = separation + sectWidth
                if totalWidth > hullWidthMax:
                    report = await addLine(report,
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
                    report = await addLine(report,
                        f"Engine \"{name}\" displacement is invalid!  This engine is: {displacement} liters, while the limit is {engineLimit}.")
                    errorCount += 1
                else:
                    report = await addLine(report, f"Engine \"{name}\" has {displacement} liters of displacement.")
                if (displacement/weight) < minEDPT:
                    report = await addLine(report, f"Engine \"{name}\" has a {round((displacement/weight), 2)} engine displacement per tonnage ratio.  This is too low - the minimum requirement is {minEDPT}.")
                    errorCount += 1
            x += 1

        # print out minimum engine tech required
        # for currentValue in netDisplacement:
        #     if displacement >= currentValue:
        #         # print(currentValue)
        #         engineTech += 1
        # for currentValue in netDisplacement:
        #     if displacement >= currentValue:
        #         # print(currentValue)
        #         engineTech += 1
        # print(engineTech)

        blueprintDataOut = json.dumps(blueprintData, indent=4)

        if len(report) > 2000:
            reportLines = report.split("\n")
            reportLength = len(reportLines)
            reportSpot = 0
            reportBlock = ""
            await ctx.send(f"Your report was too long, at {len(report)} characters & {reportLength} lines.  Breaking it up into several lines.")
            while reportSpot < reportLength:
                if len(reportLines[reportSpot]) > 2000:
                    reportBlock = await addLine(reportBlock, "One section has been skipped due to exceeding the character limit.  Consider using shorter names for your compartments.")
                if len(reportLines[reportSpot]) + len(reportBlock) < 2000:
                    reportBlock = await addLine(reportBlock, reportLines[reportSpot])
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
                }

        return results



@bot.command()
async def fundResearch(ctx, type: str):
    import random
    user_id = ctx.author.id
    country = await getUserCountry(ctx)
    if variablesList[country][0]["type"] == "company":
        upgradeCost = fundsToAdvanceLevel
        researchRate = 26/float(variablesList[country][0]["idealTonnage"])
    elif variablesList[country][0]["type"] == "country":
        upgradeCost = fundsToAdvanceLevel*countryScalar
        researchRate = 37750000 / (int(variablesList[country][0]["populationCount"])) + 0.2
    else:
        await ctx.send("That's odd, I can't get your country or company!")
        return
    typeName = type.lower()
    NameInput = int(round(industryCount * random.random())) - 1
    TypeInput = int(round(industryTypeCount*random.random())) - 1

    try:
        print(researchList[country])
    except Exception:
        researchList[country] = {}

    try:
        print(researchList[country][typeName])
        await ctx.send(
            "You've already funded re-tooling to new technology!")
    except Exception:

        if float(variablesList[country][0][typeName+"Tech"]) > maxLevel:
            await ctx.send(f"Well this is a bit odd... you've hit the maximum {typeName} technology level feasible in this campaign!")

        elif float(variablesList[country][0]["money"]) < upgradeCost:
            await ctx.send("You don't have enough money to fund development!  You only have ฿" + str(variablesList[country][0]["money"]) + " available.")



        else:
            if typeName == "armor" or typeName == "cannon" or typeName == "engine" or typeName == "suspension":
                variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - upgradeCost
                researchList[country][type] = {'progress': 0, 'rate': researchRate}
                print("Research started.")
                await ctx.send(f"You have successfully funded development at {industryNames[NameInput]} {industryTypes[TypeInput]}!\nCost: ฿{upgradeCost}\nTime to completion: {round(1/researchRate)} (Zheifu) weeks.")

            else:
                await ctx.send("Invalid research category. \nSpend your funds in either the `cannon`, `engine`, or `armor` categories!")

@bot.command()
async def researchProgress(ctx):
    country = await getUserCountry(ctx)
    if country == "invalid_country":
        await ctx.send("This is not a valid country or company!")

    embed = discord.Embed(title=str(variablesList[country][0]["displayName"]) + "'s Research",
                          description="This is how your research is coming along.  \n You currently have ฿" + str(variablesList[country][0]["money"]) + " in funds",
                          color=discord.Color.random())
    countryResearch = researchList[country]
    print("Hi! >>> " + str(countryResearch))
    for researchType, researchInfo in countryResearch.items():
        embed.add_field(name=researchType, value="progress: " + str(round(100*(0.0001+float(researchInfo["progress"])))) + "%",
                            inline=False)
    await ctx.send(embed=embed)



@bot.command()
@commands.has_role('Campaign Manager')
async def forceTechLevel(ctx, country: str, value: int):
    value = value - 1
    variablesList[country][0]["armorTech"] = value
    variablesList[country][0]["engineTech"] = value
    variablesList[country][0]["cannonTech"] = value
    variablesList[country][0]["suspensionTech"] = value
    await ctx.send("Overrides complete.")
    if value < 0 or value > 24:
        await ctx.send("Note: this value is invalid and will probably break the bot.  Valid levels are between 1 and 25.")

class Dropdown(discord.ui.Select):
    country_var = ""
    def __init__(self, country):

        self.country = country
        # Set the options that will be presented inside the dropdown
        blimpCost = 5000000
        researchPrice = int(fundsToAdvanceLevel)
        if variablesList[country][0]["type"] == "country":
            researchPrice = fundsToAdvanceLevel*countryScalar

        options = [
            discord.SelectOption(label="Fund thicker armor research", description=("cost: ฿{:,}").format(researchPrice), emoji='🔩', value="armor"),
            discord.SelectOption(label="Develop bigger cannons", description=("cost: ฿{:,}").format(researchPrice), emoji='🧨', value="cannon"),
            discord.SelectOption(label="Design stronger engines", description=("cost: ฿{:,}").format(researchPrice), emoji='💥', value="engine"),
            # discord.SelectOption(label="Start construction of a new transport blimp", description=("cost: ฿{:,}").format(blimpCost), emoji='🎈', value="transport"),
            discord.SelectOption(label="Research stronger tank suspension", description=("cost: ฿{:,}").format(researchPrice), emoji='⚙️', value="suspension"),
        ]
        if variablesList[country][0]["type"] == "country" and int(variablesList[country][0]["railwayTech"]) != len(railwayGauges) - 1:
            landSize = int(variablesList[country][0]["land"])
            options.append(discord.SelectOption(label="Upgrade your railways to a wider gauge", description=("cost: ฿{:,}").format(landSize*upgradeRailwayCostScalar), emoji='🚂', value="railway"))
        print(country)
        country_var = country
        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Click here to open the list of upgrades.', min_values=1, max_values=1, options=options)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("This is not yours.", ephemeral=True)
        else:
            return True

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        import random
        country = self.country
        typeName = self.values[0]

        if variablesList[country][0]["type"] == "company":
            upgradeCost = fundsToAdvanceLevel
            researchRate = companyWeeksToResearch
        elif variablesList[country][0]["type"] == "country":
            upgradeCost = fundsToAdvanceLevel * countryScalar
            researchRate = 37500000 / int(variablesList[country][0]["populationCount"]) + 0.1666
        else:
            await interaction.response.send_message("That's odd, I can't get your country or company!")
            return
        # typeName = type.lower()
        NameInput = int(round(industryCount * random.random())) - 1
        TypeInput = int(round(industryTypeCount * random.random())) - 1

        try:
            print(researchList[country][typeName])
            await interaction.response.send_message(
                "You've already funded re-tooling to new technology!")
        except Exception:

            if float(variablesList[country][0][typeName + "Tech"]) > maxLevel:
                await interaction.response.send_message(
                    f"Well this is a bit odd... you've hit the maximum {typeName} technology level feasible in this campaign!")
                return

            elif float(variablesList[country][0]["money"]) < upgradeCost:
                await interaction.response.send_message("You don't have enough money to fund development!  You only have ฿" + str(
                    variablesList[country][0]["money"]) + " available.")
                return



            else:
                if typeName == "armor" or typeName == "cannon" or typeName == "engine" or typeName == "suspension":
                    variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - upgradeCost
                    researchList[country][typeName] = {'progress': 0, 'rate': researchRate}
                    print("Research started.")
                    await interaction.response.send_message(
                        f"You have successfully funded development at {industryNames[NameInput]} {industryTypes[TypeInput]}!\nCost: ฿{upgradeCost}\nTime to completion: {round(1 / researchRate)} (Zheifu) weeks.")
                elif typeName == "transport":
                    variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - upgradeCost
                    researchList[country][typeName] = {'progress': 0, 'rate': 1}
                    await interaction.response.send_message(
                        f"You have successfully purchased a blimp from {industryNames[NameInput]} {industryTypes[TypeInput]}!\nCost: ฿{5000000}\nTime to delivery: {round(1 / 1)} (Zheifu) weeks.")
                elif typeName == "railway":
                    variablesList[country][0]["money"] = int(variablesList[country][0]["money"]) - int(variablesList[country][0]["land"])*upgradeRailwayCostScalar
                    researchList[country][typeName] = {'progress': 0, 'rate': railwayResearchRate}
                    await interaction.response.send_message(f"You have successfully initialized an upgrade to your country's railway networks! \nCost: ฿{int(variablesList[country][0]['land'])*upgradeRailwayCostScalar}\nTime to completion: {round(1 / railwayResearchRate)} (Zheifu) weeks.")
                else:
                    await interaction.response.send_message("Invalid research category. \nSpend your funds in either the `cannon`, `engine`, or `armor` categories!")



        # await interaction.response.send_message(f'You selected the {self.values[0]}')






class DropdownView(discord.ui.View):
    def __init__(self, country):
        super().__init__()
        self.country = country
        # Adds the dropdown to our view object.
        self.add_item(Dropdown(country))

@bot.command()
async def upgrades(ctx):
    country = await getUserCountry(ctx)
    if country == "invalid_country":
        await ctx.send("This is not a valid country or company!")
    try:
        embed = discord.Embed(title=str(variablesList[country][0]["displayName"]) + "'s Upgrades",
                              description="This is how your research and equipment upgrades are coming along.  \n You currently have ฿" + str(variablesList[country][0]["money"]) + " in funds",
                              color=discord.Color.random())
        countryResearch = researchList[country]
        print("Hi! >>> " + str(countryResearch))
        for researchType, researchInfo in countryResearch.items():
            embed.add_field(name=researchType, value="progress: " + str(round(100*(0.0001+float(researchInfo["progress"])))) + "%",
                                inline=False)
        await ctx.send(embed=embed)
    except Exception:
        appendThing = {country: {}}
        researchList[country] = {}
        await ctx.send("You don't have any research active yet!")
    """Sends a message with our dropdown containing colours"""
    # Create the view containing our dropdown
    view = DropdownView(country)

    # Sending a message containing our view
    await ctx.send(f'if you want to start research or upgrades for something, select it below!  \nOr, configure whether upgrade auto-funding is active (current state: {variablesList[country][0]["autoResearch"]})', view=view)
    view = AutoResearchToggle(country)
    await ctx.send(view=view)

class AutoResearchToggle(discord.ui.View):
    def __init__(self, country):
        super().__init__()
        self.value = None
        self.country = country

        # When the confirm button is pressed, set the inner value to `True` and
        # stop the View from listening to more input.
        # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Enable upgrade auto-funding', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        country = self.country
        # await interaction.response.send_message('Confirming', ephemeral=True)
        variablesList[country][0]["autoResearch"] = "true"
        await interaction.response.send_message("You will now automatically fund upgrades for new technology and equipment.")
        print("Hi!")
        self.value = True
        self.stop()

        # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Disable upgrade auto-funding', style=discord.ButtonStyle.grey, custom_id='lol')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        country = self.country
        variablesList[country][0]["autoResearch"] = "false"
        await interaction.response.send_message('You will no longer automatically fund upgrades for new technology and equipment.')
        self.value = False
        self.stop()

    async def callback(self, interaction: discord.Interaction):
        print("Hi!")


@bot.command()
@commands.has_role('Campaign Administrator')
async def Hey(ctx, *, extra):
    await ctx.send("Crash the server?  On it.")
    exit(1)

async def attachNumberDecals(blueprintData: dict):
    weight = float(blueprintData["header"]["mass"])/1000
    cost = round(pow((weight * costPerTon), 1.1))
    name = blueprintData["header"]["name"]

    index = len(tanksList)
    x = 0
    ref = str(index)
    x = 1
    for val in ref:
        decal = {
          "REF": "356f883c9f9bc9344aa34cd4f646d36e",
          'CID': 0,
          "T": [
            -0,
            -0.1,
            x,
            90.0,
            270.0,
            0.0,
            0.5,
            0.5,
            0.5,
            90.0
          ],
          "DAT": [
            {
              "id": "decal",
              "data": "{\"ID\":" + str(101005905 - (2*x)) + "}",
              "metaData": ""
            },
            {
              "id": "asset",
              "data": "{\"Data\":\"https://sprockettools.github.io/numbers/DINWhite" + val + ".png\",\"Type\":2}",
              "metaData": ""
            }
          ]
        }
        x += -0.5
        blueprintData["ext"].append(decal)
    return blueprintData

async def getContestName(ctx):
    import asyncio
    await ctx.send("Beginning processing now.")
    contestName = ""
    contestHostID = ctx.author.id
    contestListText = ""
    for contestTitle, contestInfo in contestsList["contests"].items():
        print(contestInfo)
        if contestInfo["contestHost"] == contestHostID:
            contestListText = contestListText + f"\n{contestTitle}"
    await ctx.send(f"What contest are you adding categories to? Currently you are managing the following contests: {contestListText}")
    def check(m: discord.Message):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=300.0)
        contestName = str(msg.content)
    except asyncio.TimeoutError:
        await ctx.reply("Operation cancelled.")
        return
    if contestsList["contests"][contestName]["contestHost"] != contestHostID:
        await ctx.reply("This isn't your contest!")
        return
    else:
        return contestName

@bot.command()
@commands.has_role('event organizer')
async def toggleEntries(ctx):
    contestName = await getContestName(ctx)
    contestsList["contests"][contestName]["acceptEntries"] = not contestsList["contests"][contestName]["acceptEntries"]
    await ctx.reply(f"{contestName}'s submission processing is now set to {contestsList['contests'][contestName]['acceptEntries']}!")

@bot.command()
@commands.has_role('event organizer')
async def registerContest(ctx):
    await ctx.send("Beginning processing now.")
    contestHostID = ctx.author.id
    for attachment in ctx.message.attachments:
        fileData = json.loads(await attachment.read())
        contestName = fileData["contestName"]
        submitDirectory = TANKrepository + f"{contestName}"
        Path(submitDirectory).mkdir(parents=True, exist_ok=True)
        contestsList["contests"][contestName] = fileData
        contestsList["contests"][contestName]["categories"] = {}
        contestsList["contests"][contestName]["submissions"] = {}
        contestsList["contests"][contestName]["contestHost"] = contestHostID
        contestsList["contests"][contestName]["acceptEntries"] = "false"

        # create logging channel
        channel = bot.get_channel(ctx.channel.id)
        thread = await channel.create_thread(
            name=contestName,
            type=discord.ChannelType.private_thread
        )
        contestsList["loggingChannel"][contestName] = thread.id

        # await backupFiles()
        await thread.send(f"<@{contestHostID}>, the {contestName} is now registered!  Submissions are turned off for now - enable them once you are ready.  Once you do enable submissions, they will be logged here.")


@bot.command()
@commands.has_role('event organizer')
async def registerContestCategory(ctx):
    import asyncio
    await ctx.send("Beginning processing now.")
    contestName = ""
    contestHostID = ctx.author.id
    contestListText = ""
    for contestTitle, contestInfo in contestsList["contests"].items():
        print(contestInfo)
        if contestInfo["contestHost"] == contestHostID:
            contestListText = contestListText + f"\n{contestTitle}"
    await ctx.send(f"What contest are you adding categories to? Currently you are managing the following contests: {contestListText}")
    def check(m: discord.Message):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for('message', check=check, timeout=300.0)
    except asyncio.TimeoutError:
        await ctx.reply("Operation cancelled.")
        return
    else:
        contestName = str(msg.content)
    if contestsList["contests"][contestName]["contestHost"] != contestHostID:
        await ctx.reply("This isn't your contest!")
        return
    channel = bot.get_channel(ctx.channel.id)
    for attachment in ctx.message.attachments:
        fileData = json.loads(await attachment.read())
        categoryName = fileData["categoryName"]
        # contestsList["contests"][contestName] = fileData
        contestsList["contests"][contestName]["categories"][categoryName] = fileData
        contestsList["contests"][contestName]["categories"][categoryName]["hostChannel"] = ctx.channel.id
        contestsList["contests"][contestName]["categories"][categoryName]["submissions"] = {}
        contestsList["contests"][contestName]["categories"][categoryName]["contestName"] = contestName

        submitDirectory = TANKrepository + contestName + OSslashLine + categoryName
        Path(submitDirectory).mkdir(parents=True, exist_ok=True)
        # await backupFiles()
        await ctx.send(f"The category \"{categoryName}\" is now registered!")

@bot.command()
async def submit(ctx):
    import asyncio
    name = "invalid"
    weight = -1
    errors = 0
    contestName = ""
    contestListText = ""
    for contestTitle, contestInfo in contestsList["contests"].items():
        if contestInfo["acceptEntries"] == True:
            contestListText = contestListText + f"\n{contestTitle}"
    for attachment in ctx.message.attachments:
        await ctx.send(f"What contest are you submitting the {attachment.filename} to? The following contests are currently available: {contestListText}")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await bot.wait_for('message', check=check, timeout=300.0)
            contestName = msg.content
            try:
                if contestsList["contests"][contestName]["acceptEntries"] != True:
                    await ctx.reply(f"This contest has closed entries.  its ending date was <t:{contestsList[contestName]['endTimeStamp']}:R>")
                    return
            except Exception:
                await ctx.reply("This contest does not exist.  Please make sure you spelled the contest's name correctly.")

        except asyncio.TimeoutError:
            await ctx.reply("Operation cancelled.")
            return


        categoryListText = ""
        for categoryTitle, categoryInfo in contestsList["contests"][contestName]["categories"].items():
            categoryListText = categoryListText + f"\n{categoryTitle}"

        await ctx.send(f"What category are you submitting the {attachment.filename} to? You can pick from the following categories: {categoryListText}")
        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        try:
            msg = await bot.wait_for('message', check=check, timeout=300.0)
            categoryName = msg.content
            try:
                configuration = contestsList["contests"][contestName]["categories"][categoryName]
            except Exception:
                await ctx.reply("This category does not exist.  Please make sure you spelled the contest's name correctly.")
                return

        except asyncio.TimeoutError:
            await ctx.reply("Operation cancelled.")
            return

        results = await runBlueprintCheck(ctx, attachment, configuration)
        await ctx.reply("Blueprint processing complete.")
        name = results["tankName"]
        weight = results["tankWeight"]
        valid = results["valid"]
        crewReport = results["crewReport"]
        crewCount = results["crewCount"]
        maxVehicleArmor = float(results["maxArmor"])
        tankWidth = results["tankWidth"]
        results["tankOwner"] = ctx.author.id
        if valid == True:
            await ctx.send(f"## Attach the specified photos of the {name} here.  \n**Picture 1** needs to be a well-lit picture of the tank's front and side.\n**Picture 2** needs to be a well-lit picture of the tank's rear and side.\n**Picture 3** needs to be a front view of the tank using the \"Internals\" overlay **while looking at the ammunition rack editor.**\n**Picture 4** needs to be a top+side view of the tank using the \"Internals\" overlay **while looking at the ammunition rack editor.**\n### Note: at least one of your screenshots needs to include the full page and Sprocket UI.")

            def check(m: discord.Message):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            try:
                msg = await bot.wait_for('message', check=check, timeout=5000.0)
            except asyncio.TimeoutError:
                await ctx.send("Operation cancelled.")
                return

            blueprintData = json.loads(await attachment.read())

            await ctx.send(f"The {name} has been submitted!  Thanks for participating in the {contestName}!")
            json_output = json.dumps(blueprintData, indent=4)
            file_location = f"{TANKrepository}{OSslashLine}{contestName}"
            from pathlib import Path
            Path(file_location).mkdir(parents=True, exist_ok=True)
            with open(str(file_location + "/" + str(name) + ".blueprint"), "w") as outfile:
                outfile.write(json_output)

            msg = ctx.message
            url = msg.jump_url
            chnl = bot.get_channel(int(contestsList["loggingChannel"][contestName]))
            await chnl.send(f"### You have a new entry into the {contestName}! \nName: {name} \nConstruction type: {type} \nCrew count: {crewCount} \n{crewReport} \n## Vehicle blueprint: [here]({url})")
            await chnl.send(f"** ** \n\n** **")
        else:
            await ctx.send("The " + name + " needs fixes to the problems listed above before it can be registered.")


bot.run(token)

