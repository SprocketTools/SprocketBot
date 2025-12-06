# Running your own Sprocket Bot on your PC

Note: this guide is a bit out of date.

Sprocket Bot is a complex project, involving many Python libraries, custom functions, and a SQL server.  This guide will help explain the steps needed to have your own environment up and running.

Currently the "official" Sprocket Bot is hosted on a Raspberry Pi 4B with 8GB of RAM - albeit it seems to only use less than 400MB for the entire bot, SQL server, and operating system.  Any PC that is viewing this webpage should have the specs needed to run the bot.

Note: this guide assumes that you understand the fundamentals of Python.  

## Necessary software
- Python 3.11+
- PostgreSQL 16+
- Github
- Development IDE (I use PyCharm, VScodium should also work)

## Set up the PostgreSQL server

This is going to be the hardest step, so it's best to get this done with first.  Download and install PostgreSQL 16 (or higher) from [here](https://www.postgresql.org/download/).  Take note of the port and passwords that you set - you'll need them later in this install guide.  In this example, I'll use the default port of 5432.

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

## Create the configuration files

Create and enter the `C:\SprocketBot` folder.  From here, create a file named `configuration.ini`.  Copy the code chunk below and replace the missing data bits with your information. 
```ini
[SECURITY]
user = POSTGRES_USERNAME
password = POSTGRES_PASSWORD
host = /var/run/postgresql
port = 5432
database = botdatabase

[settings]
lastupdated = 0
ownerid = YOUR_DISCORD_USER_ID
geminiapis = GEMINI_API_1,GEMINI_API_2,GEMINI_API_3...
githubpat = GITHUB_PERSONAL_TOKEN
spotify_client_id = SPOTIFY_CLIENT_ID
spotify_client_secret = SPOTIFY_CLIENT_SECRET
bot_status_webhook = PLACE_A_WEBHOOK_URL_HERE
```
You can leave the "Spotify client ID" and "secret" out of your configuration file if you don't have Spotify premium - this is mainly used to make an automatic music player.

In the `C:\SprocketBot\Bots` folder, create a file with your name of choice, such as `dev.ini`.  Copy the code chunk below and replace the missing data bits with your information. 

```
[botinfo]
token = YOUR_BOT_TOKEN
prefix = -
master = true
updategithub = false
mode = official
flavor = normal
clientid = YOUR_BOT_USER_ID
sqldatabase = botdatabase
```
If you place multiple of these files in the `bots` directory, multiple bot instances will launch when you run `launcher.py`.

## Set up the development IDE

Install either PyCharm (best choice) or VScodium.  You will then want to open the SprocketBot repository folder in your IDE.  Locate this folder in `Documents\Github\SprocketBot` if you used Github Desktop.
Use the attached requirements.txt file to install the necessary packages (although it probably won't install them all).

## Run the bot

Run the `launcher.py` file to launch the bot.  If everything was set up correctly, you should log into Discord after several seconds and be able to run commands!

## Setup databases

Several commands will need to be ran on the bot through Discord to fully set up the database.  There's alot, sorry.

`-resetServerConfig`

`-setupmoderationdatabase`

`-setupCampaignDatabase`

`-setupTransactionDatabase`

`-resetContests`

`-resetContestCategories`

`-resetContestEntries`

`-setup_observatory_log`

`-setupStarboardDatabase`

`-resetErrorConfig`

`-setupclickup`

`-resetImageCatalog`

`-resetRoleColorDatabase`

`-setupTimedMessageDatabase`

`-resetHelpConfig`

`-resetCodeConfigs`

After setting these up, make sure to run `-addError` a couple times to ensure you get proper error responses later on.


## Hosting the bot

Your general procedure for self-hosting Sprocket Bot is similar to what's covered in this guide, you'll just need to ensure that additional procedures are made for autostarting the bot, and update the configuration file to point to the correct values.  Also ensure that the database setup is correct, as you'll likely need a separate database for the bot.

## Coding the bot

To add your own code to Sprocket Bot, refer to [this documentation](https://github.com/SprocketTools/SprocketBot/blob/main/CODING_INTRO.md) to get started.