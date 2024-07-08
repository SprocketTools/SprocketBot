Scam bots follow a very predictable pattern.  They flood as many channels as possible with the same messages, containing a link, questionable words, and often times a ping.  As a result, detecting these bots and discerning them from normal users involves looking for these patterns.  Sprocket Bot contains a fairly robust system to detect scams and delete them on its own.  

## How it works
Sprocket Bot scans messages and look for whether the message triggers two flags: if the message contains very unusual material, such as "$50" or "e-womans", and if it contains a scam link, such as "sc.link".  If a message contains both, the associated account gets a flag.  When a user accumulates enough flags to reach a server's threshold, Sprocket Bot will mark the account as a scam bot, then perform an action based upon the server's configuration.  
To ensure that false positives are avoided, flags on an account are removed the instant it sends a non-flagged message.  Additionally, users are sent a direct message if they are one flag short of being marked as a scam bot.  

## Setting up Sprocket Bot to automatically delete scams
To set up this tool, run through the -setup command.  While running the setup command, you will be asked for the following settings:
- How many consecutive scam messages do you want an account to send before Sprocket Bot considers it as hacked?
- What action do you want Sprocket Bot to take, if any?
 - If set to "kick," the bot will also delete messages sent by the user in the previous 10 minutes.  
- What do you want Sprocket Bot to ping when it detects a hacked account?

### Notes:
This tool will not work properly if other bots or automated systems will punish users before Sprocket Bot detects the accounts.  For example, if another bot will time out a user for sending two links in 1 second, then the bot won't kick them from the server.
All messages and actions flagged by the bot are logged to an internal debug channel, so that I can ensure false positives are being avoided.   These logs do not show what server the action originates from.

Updated on July 8th, 2024

