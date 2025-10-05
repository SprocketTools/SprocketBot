# Running your own Sprocket Bot on a Raspberry PI

Sprocket Bot is designed to run on a Raspberry Pi, so if you want to run your own instance of it on your Pi, this guide should be able to help.

Note: this guide assumes you are already connected to a Raspberry Pi terminal through SSH and have FTP access to its files. 

## Download repository & code

`sudo apt install git`

`sudo apt install ffmpeg`

`sudo mkdir Github`

`cd Github`

`sudo git clone https://github.com/SprocketTools/SprocketBot`

`sudo chown username:username -R /home/radiopi/Github/SprocketBot`
- replace username with the username of your Pi.  Default is "pi"

## Set up your configuration files (FTP browser recommended)

Make a new folder in your user's directory called `configuration.ini`.  In the file, add this:

```
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
```
Switch out the uppercase items with your appropriate values.  
- The `geminiapis` list can be as long as you want it - the bot splits the tokens into a list during bootup and switches between them to extend free tier ratelimits.  Make sure the tokens come from different Google accounts.
- The `database` can be changed, but you'll need to remember this for later.

Now make a folder called `bots` inside your user's directory.  Inside this folder, add a new .ini file called `bot_1.ini`.  Inside the file, add this:
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
Several of these variables are part of legacy systems I haven't removed, so leave them if you don't know what they do.

## Set up the PostgreSQL server

Download and install PostgreSQL:

Take note of the port and passwords that you set - you'll need them later in this install guide.  In this example, I'll use the default port of 5432.
Open pgAdmin 4 and click "new server."  In the popup window, add the following information.
- General tab - Name: "Local server" or similar
- Connection tab - Host name/address: `localhost`
- Connection tab - Port: the port you defined when installing PostgreSQL (default was 5432)
- Connection tab - Password: the password you defined when installing PostgreSQL
- Connection tab - Save password?: enable

Click "save" and you should then be connected to the PostgreSQL server.

Now allow for remote connections:

`sudo nano /etc/postgresql/<version>/main/postgresql.conf`

Uncomment `listen_addresses = 'localhost'`  and change it to `listen_addresses = '*'`, then save.

`sudo nano /etc/postgresql/<version>/main/pg_hba.conf`

Under "IPv4 local connections", add this line:
`host    all             all             192.168.0.0/24        md5`

Under "# "local" is for Unix domain socket connections only" change "peer" to "md5"

then save.

`sudo systemctl restart postgresql`


Now try to configure your PostgreSQL connection:

`sudo -i -u postgres`

`psql`
```
CREATE USER POSTGRES_USERNAME WITH PASSWORD 'POSTGRES_PASSWORD';
    CREATE DATABASE botdatabase OWNER POSTGRES_USERNAME;
```


Now try connecting to your server via pgAdmin 4 using the information above.  If you are successful, then it's safe to move on.

## Set up Python packages

`cd Github`

`cd SprocketBot`

`python -m venv env`

`source env/bin/activate`

`pip install pipreqs`

`pipreqs --force ./`

`pip install -r requirements.txt`

catch missing dependencies:

`pip install opencv-python-headless discord-ext-music pygame `



Now test the bot:

`python launcher.py`


## Setup databases

There's alot, sorry.

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

Extra commands:
- run `-setup` in your own server
- run several `-addError` commands to insert jokes into the database.  These are required for alot of stuff to work.

## Automate starting the bot

`sudo nano /etc/systemd/system/sprocketbot.service`

Add this:

```
[Unit]
Description=Sprocket Bot Launcher Service
After=network-online.target

[Service]
Type=simple
User=[username]
WorkingDirectory=/home/[username]/Github/SprocketBot
ExecStart=/home/[username]/Github/SprocketBot/env/bin/python /home/[username]/Github/SprocketBot/launcher.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`sudo systemctl daemon-reload`

`sudo systemctl enable sprocketbot.service`

`sudo systemctl start sprocketbot.service`
