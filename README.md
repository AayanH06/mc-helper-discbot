# mc_helper_discbot
MC Server Discord Bot (Hosted privately on my RPI)

started a 1.21.1 MC server with my friends on 5/27/25 and have had many prior. thought this would be a good project for my github and also would be practical and completely self hosted. a lot of MC discord bots are limited and aren't updated very often.

this bot is NOT made to work fresh off the install. you will have to configure a '.env' file to fill in some values that i neglected to hardcode for simplicity and privacy's sake.

please reach out to me on linkedin (linked.aayan.us) if you have any questions about this bot.

# MC Helper Discord Bot - Setup Instructions

This guide explains how to run the Minecraft helper Discord bot locally.

## Prerequisites

1. **Most recent Python** installation
2. **Git** installed
3. A **Discord Bot Token**
4. Access to a **Discord server** where the bot can be invited and used
5. (Optional) A Minecraft server with RCON enabled

## Steps

### 1. Clone the Repository
Open a terminal or command prompt and run:
git clone https://github.com/AayanH06/mc-helper-discbot.git
cd mc-helper-discbot

### 2. Create and Activate a Virtual Environment (Recommended)
       I literally could not download my dependencies/libraries 
       without this. someone lmk if there is a workaround

On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

On Windows:
I reccomend adding your python library to PATH, there are guides online that walk you through this.

### 3. Install Dependencies
Install everything that is being imported at the top of main.py by using the command 'pip install ______'

### 4. Set Up Environment Variables
Create a `.env` file in the root directory and add:

DISCORD_TOKEN= 
RCON_PASSWORD=
MC_HOST=
TRUSTED_GUILD_ID=
BOT_OWNER_ID=
BOT_OWNER_USERNAME=
TARGET_MAC=
SERVER_DIR=
SERVER_JAR=
MC_LAUNCH_TOKEN=
CHANNEL_ID=


### 5. Run the Bot
python main.py

You should see a confirmation message that the bot is online.

If you installed your python dependencies in a virtual environemnt (i.e. venv), you must also launch the bot within that environment each time

### 6. Invite the Bot to Your Server
Use this URL format (replace `YOUR_CLIENT_ID`):

https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=8

Get `YOUR_CLIENT_ID` from your bot's application page under "OAuth2 > General".

### 7. Testing the Bot
Use commands like:
mc!whitelist your_mc_username

The bot will DM the owner and await approval via reaction.
  
## Notes

- Ensure RCON is enabled in your `server.properties`:
  enable-rcon=true
  rcon.password=your_password

- If you encounter permission errors, check the bot’s role and permissions in your Discord server.

****I CANNOT STRESS THIS ENOUGH****
if you fork this, please commit with .env inside of .gitignore before actually uploading .env to the folder. the whole point of not hardcoding those values is to prevent some goofy people online from exploiting your personal data. happy crafting!

The flask script is for two devices to communicate with eachother over a single network. In my case, I have my MC server on my desktop and the discord bot on a RPI.
I reccomend going to 'Task Scheduler' on windows and setting the flask script to run after each login. 
