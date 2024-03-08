## Setting up your own contests with Sprocket Bot

Setting up contests is fairly straightforward.  You will need:
- A "contest info" .json file
- One or more "contest category" .json files
- A private channel that you can make threads in 
- A public channel that users can use to run the `-submitTank` command with 

Contests can have multiple categories, and you can re-register contests and categories under the same name (if you originally created it).  Be warned that saving over existing items you made before will clear everything except the .blueprint files of previous entries.

Two configuration .json file examples are included in the `Contest Configuration Examples` folder.  The first one, `Contest Config.json` is used to establish a contest.

Use the `-registerContest` command to register a contest, attaching the appropriate .json file while doing so.  Sprocket Bot will create a thread to log entries to.

The second one, `contestCategoryConfigExampleV2.json` is used to establish a category for a contest.  Use the `-registerCategory` command to register a contest category, attaching the appropriate .json file while doing so.  Sprocket Bot will ask you for the contest you wish to register it to.

To allow or disable entries, run the `-toggleContestEntries` command.  This will change whether participants (note: from all servers Sprocket Bot is in) to submit a tank to the contest.

Anyone can submit a tank using the `-submitTank` command - attach the .blueprint file when running the command.  The participant will be prompted for information about their vehicle before and after running the blueprint checks.  Once all checks clear, the vehicle .blueprint will be saved to Sprocket Bot's storage, and the entry will be logged in the appropriate thread and in the contest data file.

### Notes:
- "Geometric Custom Mantlets" are detected when a turret radius is below the set minimum radius, and the turret is rotated more than 20 degrees
- If "dynamic torsion bars" is set to `True`, then the `torsionBarLengthMin` is multiplied by the track separation instead.  In cases like this, `torsionBarLengthMin` should not exceed a value of 0.9
- HVSS is not guaranteed to be accurate when calculating ground pressure
- The "ATsafeMin" is a soft armor requirement that simply flashes a warning whenever the thinnest armor plate is below this value.  Use it mainly for bonus points, otherwise set the value to zero.

## Requirements
My responsibility for how contest hosts run their contests is extremely limited.  
Contest hosts may run whatever contests they'd like to with Sprocket Bot, except in the following circumstances:  
- The contest(s) violate Discord's TOS in rather blatant ways 
- The contest(s) cause excessive strain on the server or break it (which I would be impressed to actually see, no contest ever ran in Sprocket Official's history would have managed to do this *except the Ambushed! challenge*)

This doesn't mean I won't help to ensure the contests are set up as intended though.  Should issues like these arise, please contact me through Discord for fastest response.


