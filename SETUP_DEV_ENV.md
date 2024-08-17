# Running your own Sprocket Bot on your PC

Sprocket Bot is a complex project, involving many Python libraries, custom functions, and a SQL server.  This guide will help explain the steps needed to have your own environment up and running.

Currently the "official" Sprocket Bot is hosted on a Raspberry Pi 4B with 8GB of RAM - albeit it seems to only use less than 1GB of that.  Any PC that is viewing this webpage should have the specs needed to run the bot.

Note: this guide is not 100% complete.  Experience with Python is recommended.

## Necessary software
- Python 3.11
- PostgreSQL 16
- Github
- Development IDE (I use PyCharm, VScodium should also work)

## Set up the PostgreSQL server

This is going to be the hardest step, so it's best to get this done with first.  Download PostgreSQL from [here](https://www.postgresql.org/download/) - take note of the port and passwords that you set.  
Open pgAdmin 4 and click "new server."  In the popup window, add the following information.
- General - Name: "Local server" or similar
- Connection - Host name/address: `localhost`
- Connection - Port: the port you defined when installing PostgreSQL (default was 2022)
- Connection - Password: the password you defined when installing PostgreSQL
- Connection - Save password?: enable

Click "save" and you should then be connected to the PostgreSQL server.
Now, you will need to create a database for the bot.  Under the "Servers" menu, right click on your SQL server and click `create --> Database`.  In the popup window, set the database name to `sprocketbotdevelopment` and click "Save".  Your SQL server should be all ready to go!

Note: the PostgreSQL server will launch automatically when starting the computer.  You won't have to worry about having to launch it in the future.  

## Establish a Discord bot profile

Follow the instructions linked [here](https://discordpy.readthedocs.io/en/stable/discord.html)
Once you have the bot invited to a Discord server, copy its user ID.  You will need this when creating your configuration.ini file.

## Clone the SprocketBot repository

Next, use the Github CMD or Github Desktop app to clone the SprocketBot repository to your PC.  This is the folder you will open with your IDE later.

## Clone the SprocketTools repository

Sprocket Bot pushes updates to the SprocketTools.github.io website.  In order to relicate this, you will need to make a copy of the repository and obtain an SSH access key.  If you wish to not use or modify the website features, set the `updateGithub` variable in your config file to "N", as it will allow the bot to run without a Github access key.

## Create the configuration.ini file

In the `C:\SprocketBot` folder, create a file named `configuration.ini`.  Copy the code chunk below and replace the missing data bits with your information. 
```
[SECURITY]
user = postgres
password = ~~ password to your PostgreSQL server ~~
host = localhost
port = 2022

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
updateGithub = Y
githubPAT = if you have a clone of the SprocketTools repository, place your SSH access token here
```

## Set up the development IDE

Install either PyCharm (easiest) or VScodium.  You will then want to open the SprocketBot repository folder in your IDE and install all the missing Python libraries.

## Run the bot

Run the `main.py` file to launch the bot.  If everything was set up correctly, you should log into Discord after several seconds and be able to run commands!
Note: several commands will need to be ran through Discord to fully set up the database.


