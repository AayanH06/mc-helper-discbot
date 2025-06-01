import discord
from discord.ext import commands
from mcstatus import JavaServer as MinecraftServer
from mcrcon import MCRcon
from dotenv import load_dotenv
import os
import asyncio
from wakeonlan import send_magic_packet
import requests
import json
import socket

#basic setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.dm_messages = True
intents.dm_reactions = True
intents.members = True
bot = commands.Bot(command_prefix = 'mc!', intents = intents)
bot.remove_command("help")

#config details
MC_PORT = 25565
RCON_PORT = 25575
#lol u thought u would see these
#didnt want these to be public 
load_dotenv()
MC_DOMAIN = os.getenv("MC_DOMAIN")
MC_IP = os.getenv("SERVER_IP")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
TRUSTED_GUILD_ID = int(os.getenv("TRUSTED_GUILD_ID") or 0)
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID") or 0)
BOT_OWNER_USERNAME = str(os.getenv("BOT_OWNER_USERNAME"))
TARGET_MAC = str(os.getenv("TARGET_MAC"))
TOKEN = str(os.getenv("MC_LAUNCH_TOKEN"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

pending_whitelist = {}
TRUSTED_USERS = "trusted_users.json"
START_STOP = "wants_dm.json"
adminIDs = [BOT_OWNER_ID]

server_was_online = False
last_seen_active = None

@bot.event
async def on_ready():
    print("first we mine... then we craft... let's minecraft!")
    print("--------------------------------------------------")

    try:
        owner = await bot.fetch_user(BOT_OWNER_ID)
        await owner.send("The bot has been restarted and is now online.")
    except Exception as e:
        print(f"Failed to DM bot owner: {e}")

    global server_was_online
    try:
        server = MinecraftServer(MC_DOMAIN, MC_PORT)
        server.status()
        server_was_online = True
    except:
        server_was_online = False

    bot.loop.create_task(update_presence())
    bot.loop.create_task(server_status_task())
    bot.loop.create_task(auto_shutdown_check())

async def update_presence():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            server = MinecraftServer(MC_DOMAIN, MC_PORT)
            status = server.status()
            version = status.version.name
            players = status.players.online
            msg = f"with {players} person on {MC_DOMAIN}"
        except:
            msg = "Server Offline. Try `mc!start`"

        await bot.change_presence(activity=discord.Game(name=msg))
        await asyncio.sleep(60)  # update every 60 seconds

async def server_status_task():
    global server_was_online
    await bot.wait_until_ready()

    while not bot.is_closed():
        try:
            server = MinecraftServer("mc.aayan.us", 25565)
            status = server.status()

            if not server_was_online:
                try:
                    with open(START_STOP, 'r') as f:
                        data = json.load(f)
                        user_ids = data.get("wants_dm",[])
                except FileNotFoundError:
                    print("START_STOP file not found.")
                    user_ids = []
                
                for user_id in user_ids:
                    try:
                        user = await bot.fetch_user(user_id)
                        embed = discord.Embed(
                            title="Server Status",
                            description=f"`{MC_DOMAIN}` is now online!",
                            color=discord.Color.green()
                        )
                        embed.set_footer(text="Use mc!doDM to toggle off.")
                        await user.send(embed=embed)
                    except Exception as e:
                        print("Failed to notifed list that server has started.")
                print("Notified list that server has started.")

                server_was_online = True

        except Exception:
            if server_was_online:
                for user_id in user_ids:
                    try:
                        user = await bot.fetch_user(user_id)
                        embed = discord.Embed(
                            title="Server Status",
                            description=f"`{MC_DOMAIN}` is now offline.",
                            color=discord.Color.red()
                        )
                        embed.set_footer(text="Use mc!doDM to toggle off.")
                        await user.send(embed=embed)
                    except Exception as e:
                        print("Failed to notifed list that server has stopped.")
                print("Notified list that server has stopped.")
            server_was_online = False

        await asyncio.sleep(60)  # check every 60 seconds

async def auto_shutdown_check():
    global last_seen_active
    server = MinecraftServer(MC_DOMAIN,25565)

    while True:
        try:
            status = server.status()
            player_count = status.players.online

            if player_count > 0:
                last_seen_active = asyncio.get_running_loop().time()
                print(f"Players online: {player_count}. Resetting timer.")
            else:
                if last_seen_active is None:
                    last_seen_active = asyncio.get_running_loop().time()

                inactive_time = asyncio.get_running_loop().time() - last_seen_active
                print(f"No players. Inactive for {inactive_time:.0f} seconds.")

                if inactive_time >= 3600:
                    print("Server inactive for 1 hour. Shutting down.")
                    with MCRcon(MC_DOMAIN, RCON_PASSWORD, port=RCON_PORT) as mcr:
                        mcr.command(f"say Server is detected as inactive for 1 hour. run mc!start and contact @{BOT_OWNER_USERNAME} if this is a mistake. Shutting down in 15 seconds.")
                        await asyncio.sleep(15)
                        response = mcr.command("stop")
                    break  # optional: exit loop if server shuts down

        except Exception as e:
            print(f"Error checking server status: {e}")

        await asyncio.sleep(600)

@bot.command(help='Fetches the MOTD, playercount, version, and thumbnail')
async def info(ctx):
    print(f"{ctx.author} ran: info")
    server = MinecraftServer(MC_DOMAIN,25565)

    image = discord.File("server-icon.png", filename = "server-icon.png")

    try:
        status = server.status()
        players = status.players.sample

        embed = discord.Embed(title=f"{MC_DOMAIN}", 
                              color=discord.Color.green()
                              )
        embed.add_field(name="Version", value=status.version.name, inline=True)
        embed.add_field(name="Players:", value=f"{status.players.online}/{status.players.max}", inline=True)
        embed.add_field(name="MOTD", value=status.description, inline=False)
        embed.set_thumbnail(url="attachment://server-icon.png")

        row = []
        if players:
           for i, player in enumerate(players, 1):
               avatar_url = f"https://minotar.net/avatar/{player.name}/64"
               row.append(f"[{player.name}]({avatar_url})")
               if i % 3 == 0 or i == len(players):
                   embed.add_field(name="\u200bPlayers Connected:", value=" | ".join(row), inline=False)
                   row = []
        else:
            embed.add_field(name="No players online", value="Invite your friends!", inline=False)

        await ctx.send(embed=embed, file=image)
    except:
        embed = discord.Embed(title=f"{MC_DOMAIN}", 
                            color=discord.Color.red()
                            )
        embed.add_field(name="\u200b", value="Run mc!start to start crafting!", inline=False)
        embed.set_thumbnail(url="attachment://server-icon.png")

        await ctx.send(embed=embed, file=image)
#\u2705

def load_trusted_users_file():
    try:
        with open(TRUSTED_USERS, 'r') as trusted_file:
            data = json.load(trusted_file)
            return set(data.get("trusted_users", []))
    except FileNotFoundError:
        return set()

def isInGuild(user_id: int, guild_id: int) -> bool:
    guild = bot.get_guild(guild_id)
    if not guild:
        return False
    else:
        return guild.get_member(user_id) is not None

def isTrusted(ctx) -> bool:
    return isInGuild(ctx.author.id, TRUSTED_GUILD_ID) or ctx.author.id in load_trusted_users_file()

@bot.command(help='ADMIN ONLY: Trusts a user to run commands such as `mc!start` or `mc!stop`. Removes admin verification of whitelist requests.')
@commands.is_owner()
async def trust(ctx, user: discord.User):
        print(f"{ctx.author} ran: trust")
        trusted = load_trusted_users_file()
        if user.id not in trusted:
            trusted.add(user.id)
            with open(TRUSTED_USERS, 'w') as trusted_file:
                json.dump({"trusted_users": list(trusted)}, trusted_file, indent=2)
            await ctx.send(f"{user.name} is now a trusted user.")
        else:
            await ctx.send(f"{user.name} is already a trusted user.")

@bot.command(help='ADMIN ONLY: Untrusts a user from the above.')
@commands.is_owner()
async def untrust(ctx, user: discord.User):
    print(f"{ctx.author} ran: untrust")
    trusted = load_trusted_users_file()
    if user.id in trusted:
        trusted.remove(user.id)
        with open(TRUSTED_USERS, "w") as f:
            json.dump({"trusted_users": list(trusted)}, f, indent=2)
        await ctx.send(f"{user.name} is no longer a trusted user.")
    else:
        await ctx.send(f"{user.name} was not a trusted user.")

@bot.command(help='Whitelists user, limited to one IGN per person.')
async def whitelist(ctx, username: str = None):
    #must add in 1 whitelist per user, store discord ID and IGN together
    print(f"{ctx.author} ran: whitelist")
    if username is None:
        await ctx.send("Please enter your in-game name.")
        return
    owner = await bot.fetch_user(BOT_OWNER_ID)

    # DM the owner for confirmation
    if not isTrusted(ctx):
        try:
            dm_msg = await owner.send(
                f"Whitelist request for `{username}` from `{ctx.author}`.\n"
                "React to approve within 24 hours."
            )
            await dm_msg.add_reaction("\u2705")
            pending_whitelist[dm_msg.id] = {
                "username" : username,
                "channel_id" : ctx.channel.id,
                "requester_id" : ctx.author.id
            }  #store pending whitelist and auxillary information
            await ctx.send("Whitelist request sent for approval.")
            return  #stop here, wait for approval via on_raw_reaction_add
        except discord.Forbidden:
            await ctx.send("Could not DM the bot owner. Approval failed.")
            return

    # you are a trusted user (member of trusted guild or manually approved using mc!trust)
    try:
        print("PLEASE WORK") #i put this in for debugging but im gonna keep it b/c it's silly
        with MCRcon(MC_DOMAIN, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(f"whitelist add {username}")
        await ctx.send(f"`{username}` has been whitelisted.")
        await owner.send(f"`{username}` has been whitelisted.")
    except Exception as e:
        await ctx.send(f"Whitelist failed.\n`{e}`")
        await owner.send(f"Error while whitelisting `{username}`:\n`{e}`")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id != BOT_OWNER_ID or payload.emoji.name != "\u2705":
        return

    entry = pending_whitelist.get(payload.message_id)
    if not entry:
        print(f"[SKIP] Unknown message ID: {payload.message_id}")
        return

    username = entry["username"]
    channel_id = entry["channel_id"]
    requester_id = entry["requester_id"]

    try:
        with MCRcon(MC_DOMAIN, RCON_PASSWORD, port=RCON_PORT) as mcr:
            mcr.command(f"whitelist add {username}")

        user = await bot.fetch_user(payload.user_id)
        await user.send(f"`{username}` has been whitelisted.")

        channel = await bot.fetch_channel(channel_id)
        requester = await bot.fetch_user(requester_id)
        # Only send in channel if it's a text channel or thread, otherwise DM the requester
        if isinstance(channel, (discord.TextChannel, discord.Thread)):
            await channel.send(f"{requester.mention} has been whitelisted as `{username}` ✅")
        else:
            await requester.send(f"You have been whitelisted as `{username}` ✅")

        print(f"[APPROVED] {username} whitelisted by owner.")
    except Exception as e:
        await user.send(f"Error while whitelisting `{username}`:\n`{e}`")
    finally:
        del pending_whitelist[payload.message_id]

@bot.command(help='Fetches user ID')
async def myid(ctx):
    print(f"{ctx.author} ran: myid")
    await ctx.send(f"Your Discord ID: `{ctx.author.id}`")

def is_pc_online(host: str, port: int, timeout=3) -> bool:
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except:
        return False

@bot.command(help='Requests server start. Will return error if server PC is shut off.')
async def start(ctx):
    
    if isTrusted(ctx):
        print(f"{ctx.author} ran: start")    
        server = MinecraftServer(MC_DOMAIN, MC_PORT)

        if is_pc_online(MC_IP, 5001):
            print(f"{MC_DOMAIN} is active, checking if server is online")

            try:
                # If status() succeeds, then request is redundant
                server.status()
                await ctx.send("Server is already online. No need to start a new instance.")
                return
            except:
                print("Server not responding to mcstatus. Proceeding to launch...")

            #checks local http server w/ token
            try:
                response = requests.post(
                    f"http://{MC_IP}:5001/start-server",
                    json={"token": TOKEN},
                    timeout=10
                )
                if response.ok:
                    await ctx.send("Minecraft server launch triggered. Please wait ~2 minutes.")
                else:
                    await ctx.send(f"Launch failed: {response.status_code} - {response.text}")
            except Exception as e:
                await ctx.send(f"Could not contact the server starter API:\n`{e}`")
        else:
            print(f"{MC_DOMAIN} is inactive, server cannot be started.")
            await ctx.send(f"{MC_DOMAIN} appears offline and cannot be started. Contact @{BOT_OWNER_USERNAME}.")
    else:
        print(f"{ctx.author} ran: start but is not authorized.") 
        await ctx.send(f"You are not authorized to perform this command. Contact @{BOT_OWNER_USERNAME}")

@bot.command(help='Requests server stop.')
async def stop(ctx):
    
    if isTrusted(ctx):    
        server = MinecraftServer(MC_DOMAIN, MC_PORT)
        try:
            print(f"{ctx.author} ran: stop")
            status = server.status()
            with MCRcon(MC_DOMAIN, RCON_PASSWORD, port=RCON_PORT) as mcr:
                response = mcr.command("stop")
            await ctx.send(f"Stopping server {MC_DOMAIN}")
        except:
            print(f"{MC_DOMAIN} is already offline.")
            await ctx.send(f"{MC_DOMAIN} is already offline.")
    else:
        print(f"{ctx.author} ran: stop but is not authorized.")
        await ctx.send(f"You are not authorized to perform this command. Contact @{BOT_OWNER_USERNAME}")

def load_startstop_file():
    try:
        with open(START_STOP, 'r') as start_stop:
            data = json.load(start_stop)
            return set(data.get("wants_dm", []))
    except FileNotFoundError:
        return set()

@bot.command(aliases=["dodm","dm", "toggleDM", "notify"], help='Toggles DMs from bot regarding the server starting/stopping.')
async def doDM(ctx):
    print(f"{ctx.author} ran: doDM")
    user_id = ctx.author.id

    wants_startstop = load_startstop_file()
    
    if user_id not in wants_startstop:
        wants_startstop.add(user_id)
        action = "added to"
        response = "You have been added to the DM list. Re-run command to toggle off."
    else:
        wants_startstop.remove(user_id)
        action = "removed from"
        response = "You have been removed from the DM list. Re-run command to toggle on."

    with open(START_STOP, 'w') as f:
        json.dump({"wants_dm": list(wants_startstop)}, f, indent=2)
        print(f"{ctx.author} has been {action} the DM list.")
        await ctx.send(response)


@bot.command(help='List of commands.')
async def help(ctx):
    embed = discord.Embed(
        title="Bot Commands",
        description="\u200b",
        color=discord.Color.blurple()
    )
    for command in bot.commands:
        if not command.hidden:
            embed.add_field(
                name=f"mc!{command.name}",
                value=command.help or "No description.",
                inline=False
            )
    await ctx.send(embed=embed)

@bot.command(name='sudo',help='ADMIN ONLY: accesses RCON')
@commands.is_owner()
async def sudo(ctx, *, command:str):
    if not command.strip():
        await ctx.send("RCON command cannot be empty.")
        return
    
    print(f"{ctx.author} ran: sudo {command}")
    server = MinecraftServer(MC_DOMAIN, MC_PORT)

    try:
        status = server.status()
        with MCRcon(MC_DOMAIN, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(f"{command}")
            await ctx.send(response)
    except:
        print("Sudo failed: server offline")
        await ctx.send("Sudo failed: server offline")

bot.run(DISCORD_TOKEN) 

