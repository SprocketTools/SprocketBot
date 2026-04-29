## Intro

Scam bots, despite their seeming inconsistencies and rapidly changing scams, follow a very predictable pattern.  The channel spam bots prepare a simple message and send it into as many channels as possible.  Sometimes they include a link, message, or image attachment, but it's always the same between the channels.  As a result, detecting these bots and discerning them from normal users involves looking for these patterns.  Sprocket Bot contains a fairly robust system to detect scams, delete them on its own, and verify users before kicking them.  

DM scams are similarly easy to detect and prevent; countermeasures are already implemented in some servers and will be implemented globally soon.

## How it works
Sprocket Bot scans messages and look for whether all messages match these three conditions: 
- The message matches the prior message sent by the account
- The message was sent to a different channel than the prior message
- The message was sent within 8 seconds of the previous message
If a message matches these 3 conditions, the associated user gets a flag.  Failing any of these 3 conditions reset's the user's flag count to 0.  Once a user accumulates enough flags to match the Discord server's threshold (typically 3 to 5), the account will be considered a scam bot, and Sprocket Bot will perform an action based on the server's configuration.  

## Setting up Sprocket Bot to automatically delete scams
To set up this tool, run the `-settings` command.  You have the ability to configure:
- How many consecutive scam messages do you want an account to send before Sprocket Bot considers it as hacked?
	- Setting to 3 is recommended; higher numbers increase the chance Sprocket Bot will miss a scam
- What action do you want Sprocket Bot to take, if any?
	- Kicking the user is recommended 
- What do you want Sprocket Bot to ping when it detects a hacked account?
	- This is useful if you don't want the bot to auto-kick users

## False flag prevention
Sprocket Bot has logged 2 or 3 "false kicks" over its initial 2 years of preventing scams, and another 2 false kicks against people acting like scam bots.  A small number compared to the 400+ hacked account kicks logged in the same period, but enough that safety fallbacks have been implemented to prevent these from occuring:
- Users will receive a DM if they are one flag short of being marked as a scam bot.
- If a user is considered a scam bot, their recent messages will be deleted and the user will be timed out.  They will then receive a DM with instructions on how to prove themselves as human, and be given about 5 minutes to verify.

## Notes
- This tool will not work properly if other bots or automated systems will block links or timeout users behave similarly to scams.  This includes Automod or other Discord bots.  
- Any message that receives a flag is logged internally to help improve the accuracy of the scam detection systems.



## Last updated on April 29th, 2026

