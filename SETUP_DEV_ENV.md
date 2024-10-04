# Running your own Sprocket Bot on your PC

Sprocket Bot is a complex project, involving many Python libraries, custom functions, and a SQL server.  This guide will help explain the steps needed to have your own environment up and running.

Currently the "official" Sprocket Bot is hosted on a Raspberry Pi 4B with 8GB of RAM - albeit it seems to only use less than 400MB for the entire bot, SQL server, and operating system.  Any PC that is viewing this webpage should have the specs needed to run the bot.

Note: this guide assumes that you understand the fundamentals of Python.  

## Necessary software
- Python 3.11+
- PostgreSQL 16
- Github
- Development IDE (I use PyCharm, VScodium should also work)

## Set up the PostgreSQL server

This is going to be the hardest step, so it's best to get this done with first.  Download and install PostgreSQL 16 from [here](https://www.postgresql.org/download/).  Take note of the port and passwords that you set - you'll need them later in this install guide.  In this example, I'll use the default port of 5432.
Open pgAdmin 4 and click "new server."  In the popup window, add the following information.
- General tab - Name: "Local server" or similar
- Connection tab - Host name/address: `localhost`
- Connection tab - Port: the port you defined when installing PostgreSQL (default was 5432)
- Connection tab - Password: the password you defined when installing PostgreSQL
- Connection tab - Save password?: enable

Click "save" and you should then be connected to the PostgreSQL server.
Now, you will need to create a database for the bot.  Under the "Servers" menu, right click on your SQL server and click `create --> Database`.  In the popup window, set the database name to `sprocketbotdevelopment` and click "Save".  Your SQL server should be all ready to go!

Note: the PostgreSQL server will launch automatically when starting the computer.  You won't have to worry about having to launch it in the future.  

## Establish a Discord bot profile

Follow the instructions linked [here](https://discordpy.readthedocs.io/en/stable/discord.html), saving the token for later.  Once you have the bot invited to a Discord server, copy its user ID and save that later.  You will need this when creating your configuration.ini file.

## Clone the SprocketBot repository

Next, use the Github CMD or Github Desktop app to clone the SprocketBot repository to your PC (it's the same repository that this setup file is in).

## Clone the SprocketTools repository

Sprocket Bot pushes updates to the SprocketTools.github.io website.  In order to relicate this, you will need to make a copy of the repository and obtain an SSH access key.  If you wish to not use or modify the website features, set the `updateGithub` variable in your config file to "N", as it will allow the bot to run without a Github access key.

## Create the configuration.ini file

In the `C:\SprocketBot` folder, create a file named `configuration.ini`.  Copy the code chunk below and replace the missing data bits with your information. 
```ini
[SECURITY]
user = postgres
password = ~~ password to your PostgreSQL server ~~
host = localhost
port = 5432

[settings.development]
Token = ~~ Insert your bot token here ~~
clientID = ~~ Place the User ID of your bot here ~~
OSseparator = \\
database = sprocketbotdevelopment

[settings.official]
Token = ~~ If you plan to host the bot on a dedicated server, insert that token here. ~~
clientID = ~~ Place the User ID of your bot here ~~
OSseparator = /
database = sprocketbot

[settings]
ownerID = place your Discord user ID here
updateGithub = N
githubPAT = if you have a clone of the SprocketTools repository, place your SSH access token here
```

## Set up the development IDE

Install either PyCharm (easiest) or VScodium.  You will then want to open the SprocketBot repository folder in your IDE.
You will need to install the following list of Python packages to operate the bot:
- discord.py
- asyncpg
- nest-asyncio
- pillow
- requests
- yt-dlp
- discord-ext-music
- gitpython

## Run the bot

Run the `main.py` file to launch the bot.  If everything was set up correctly, you should log into Discord after several seconds and be able to run commands!
Note: several commands will need to be ran through Discord to fully set up the database:
- `?setupCampaignDatabase` - this allows you to run most of the campaign functions
- `?resetServerConfig` - allows for setting up your server's settings
- `?resetHelpConfig` - This is used by the ?SprocketHelp command
- `?resetContests` and `?resetContestCategories` are used for running Sprocket contests
- `?resetErrorConfig` - used for setting up your list of errors.  Alot of the bot depends on this list not being empty.
- `?resetImageCatalog` - used for establishing a Github catalog

After setting these up, make sure to run `-addError` a couple times to ensure you get proper error responses.


## Hosting the bot

Your general procedure for self-hosting Sprocket Bot is similar to what's covered in this guide, you'll just need to ensure that additional procedures are made for autostarting the bot, and update the configuration file to point to the correct values.  Also ensure that the database setup is correct, as you'll likely need a separate database for the bot.

## Coding the bot

Refer to [here](https://github.com/SprocketTools/SprocketBot/blob/main/CODING_INTRO.md) to get started.