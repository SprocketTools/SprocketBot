# Sprocket Bot
### The best Discord Utility bot for improving your Sprocket Tank Design experience!
This bot's primary utility is to run the Zheifu campaign, while also incorporating several tools and utilities for manipulating vehicle blueprints.

Invite Sprocket Bot to your Discord server [here](https://discord.com/api/oauth2/authorize?client_id=1137847253114040330&permissions=68169452355409&scope=bot%20applications.commands)!

The big thing:
## Setting up your own contests

Setting up contests is fairly straightforward.  You will need:
- A "contest info" .json file
- One or more "contest category" .json files
- A private channel that you can make threads in 
- A public channel that users can use to run the `-submitTank` command with 

Contests can have multiple categories, and you can re-register contests and categories under the same name (if you originally created it).  Be warned that saving over existing items you made before will clear everything except the .blueprint files of previous entries.



Two configuration .json file examples are included above.  The first one, `contestInfoTemplate.json` is used to establish a contest:
```
{
	"contestName": "Contest Name Goes Here",                << The name of your contest
	"description": "A short description of the contest",    << Needs to be under 1000 characters
	"rulesLink": "place a URL here",                        << Should be a link to Google Docs
	"startTimeStamp": 2234779200,                           << use https://r.3v.fi/discord-timestamps/ to get the timestamp number 
	"endTimeStamp": 2235845200                              << use https://r.3v.fi/discord-timestamps/ to get the timestamp number 
}
```
Use the `-registerContest` command to register a contest, attaching the appropriate .json file while doing so.  Sprocket Bot will create a thread to log entries to.


The second one, `contestCategoryTemplate.json` is used to establish a category for a contest:
```
{
        "categoryName": "Contest Name Goes Here",		<< The name of your category
        "era": "earlywar",					<< This must match the name of the target contest
        "gameVersion": 0.127,					<< The game version you are analyzing entries with
        "weightLimit": 28,					<< The weight limit of a tank in metric tons
        "enforceGameVersion": "True",				<< Set to "True" or "False" to determine whether multiple game versions are allowed
        "errorTolerance": 1,					<< The amount of violations a tank can have before it is denied
        "crewMaxSpace": 1.0,					<< Limit on amount of space a crew member may have (in-game limit is 1.0)
        "crewMinSpace": 0.8,					<< Minimum requirement for crew size (in-game limit is 0.6)
        "crewMin": 3,						<< Minimum required amount of crew
        "crewMax": 6,						<< Maximum allowed amount of crew (in-game limit is 16)
        "turretRadiusMin": 0.8,					<< Required minimum turret radius (NOT Diameter)
        "allowGCM": "True",					<< Allow "Geometric Custom Mantlets" A.K.A. GCMs A.K.A. sideways turrets.  *See note 1
        "GCMratioMin": 65,					<< Minimum traverse ratio of GCMs 
        "GCMtorqueMax": 150,					<< Maximum torque allowed for GCMs
        "hullHeightMin": 0.98,					<< Minimum height requirement for hulls.  Drivers are usually 1 meter tall when sitting
        "hullWidthMax": 2.85,					<< Maximum hull width in meters.  Accounts for geometry, tracks, and pre-made fenders
        "torsionBarLengthMin": 0.5,				<< Minimum length for torsion bars.
        "useDynamicTBLength": "True",				<< *See note 2
        "allowHVSS": "False",					<< *See note 3
        "beltWidthMin": 100,					<< Belt width requirement in millimeters
        "requireGroundPressure": "True",			<< If enabled, checks for ground pressure
        "groundPressureMax": 1.0,				<< Ground pressure requirement
        "litersPerDisplacement": 28,				<< Minimum liters of internal fuel required per liter of engine displacement
        "litersPerTon": 1,					<< Minimum liters of internal fuel required per metric ton of vehicle weight
	"minEDPT": 0.25,					<< Minimum engine displacement required per metric ton of vehicle weight
        "caliberLimit": 128,					<< Gun caliber upper limit.  In-game limit is 250mm
        "propellantLimit": 600,					<< Propellant length limit in millimeters
        "boreLimit": 4,						<< Limit on cannon bore length (shell length + barrel length)
        "shellLimit": 1200,					<< Limit on shell length (caliber*3 + propellant)
        "armorMin": 8,						<< Minimum armor thickness requirement.  Checks all compartments and turret rings.
        "ATsafeMin": 15,					<< *See note 4
        "armorMax": 250						<< Upper armor limit.   In-game limit is 500mm (you can type numbers past the slider limit)
    }
```
Use the `-registerContestCategory` command to register a contest category, attaching the appropriate .json file while doing so.  Sprocket Bot will ask you for the contest you wish to register it to.

To allow or disable entries, run the `-toggleContestEntries` command.  This will change whether participants (note: from all servers Sprocket Bot is in) to submit a tank to the contest.

Anyone can submit a tank using the `-submitTank` command - attach the .blueprint file when running the command.  The participant will be prompted for information about their vehicle before and after running the blueprint checks.  Once all checks clear, the vehicle .blueprint will be saved to Sprocket Bot's storage, and the entry will be logged in the appropriate thread and in the contest data file.



### Notes:
- "Geometric Custom Mantlets" are detected when a turret radius is below the set minimum radius, and the turret is rotated more than 20 degrees
- If "dynamic torsion bars" is set to `True`, then the `torsionBarLengthMin` is multiplied by the track separation instead.  In cases like this, `torsionBarLengthMin` should not exceed a value of 0.9
- HVSS is not guaranteed to be accurate when calculating ground pressure
- The "ATsafeMin" is a soft armor requirement that simply flashes a warning whenever the thinnest armor plate is below this value.  Use it mainly for bonus points, otherwise set the value to zero.



## Contributing Code
Sprocket Bot is written purely in Python.  The attached .json files are usable as examples, and do not reflect the current campaign level.  It is recommended to use Github to download and update the files, opening main.py with PyCharm.

## Warnings
Sprocket bot is an **in-development** utility bot, developed by a college student during their free time.  I say "utility" because its capabilities are changing quite rapidly, and is nowhere near the end result I want it to be in.  As a result, 100% reliability in its services is not guaranteed.  
- Granting Sprocket Bot administrator priveledges is not recommended.  It currently has no code that allows it to delete *anything* outsize Zheifu, but ask me about this in DMs on Discord.
- I cannot keep the bot's entire source code public once administrative utilities and/or vehicle rating formulas are added.

## Requirements
My responsibility for how contest hosts run their contests is extremely limited.  
Contest hosts may run whatever contests they'd like to with Sprocket Bot, except in the following circumstances:  
- The contest(s) violate Discord's TOS in rather blatant ways 
- The contest(s) cause excessive strain on the server or break it (which I would be impressed to actually see, no contest ever ran in Sprocket Official's history would have managed to do this *except the Ambushed! challenge*)

This doesn't mean I won't help to ensure the contests are set up as intended though.  Should issues like these arise, please contact me through Discord for fastest response.

### Contributors
Overlord,
Azomer

### Bug Hunters
0bihoernchen,
Hackstar,
Everyone in the **Zheifu Testing** server who has helped test the bot during development

### Code Contributors
*Be the first to put your name here!*
