# Sprocket Bot
### The best Discord bot for improving your Sprocket Tank Design experience!
This bot's primary utility is to run the Zheifu campaign, while also incorporating several tools and utilities for manipulating vehicle blueprints.

Invite Sprocket Bot to your Discord server [here](https://discord.com/api/oauth2/authorize?client_id=1137847253114040330&permissions=68169452355409&scope=bot%20applications.commands)

## Setting up your own contests
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


## Contributing Code
Sprocket Bot is written purely in Python.  The attached .json files are usable as examples, and do not reflect the current campaign level.  It is recommended to use Github to download and update the files, opening main.py with PyCharm.


