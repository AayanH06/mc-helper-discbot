import discord
from discord.ext import commands
from mcstatus import JavaServer as MinecraftServer
from mcrcon import MCRcon
from dotenv import load_dotenv
import os
import asyncio
from wakeonlan import send_magic_packet
import time
import subprocess
import psutil
import requests

#basic setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.dm_messages = True
intents.dm_reactions = True
bot = commands.Bot(command_prefix = 'mc!', intents = intents)

pending_whitelist = {}

#config details
MC_PORT = 25565
RCON_PORT = 25575
#lol u thought u would see these
#didnt want these to be public 
load_dotenv()
MC_HOST = os.getenv("MC_HOST")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
TRUSTED_GUILD_ID = int(os.getenv("TRUSTED_GUILD_ID") or 0)
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID") or 0)
BOT_OWNER_USERNAME = str(os.getenv("BOT_OWNER_USERNAME"))
TARGET_MAC = str(os.getenv("TARGET_MAC"))
TOKEN = str(os.getenv("MC_LAUNCH_TOKEN"))

@bot.event
async def on_ready():
    print("first we mine... then we craft... let's minecraft!")
    print("--------------------------------------------------")
    bot.loop.create_task(update_presence())

async def update_presence():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            server = MinecraftServer(MC_HOST, MC_PORT)
            status = server.status()
            version = status.version.name
            players = status.players.online
            msg = f"with {players} players on {MC_HOST}"
        except:
            msg = "Server Offline"

        await bot.change_presence(activity=discord.Game(name=msg))
        await asyncio.sleep(60)  # update every 60 seconds

@bot.command()
async def info(ctx):
    server = MinecraftServer(MC_HOST,25565)
    try:
        status = server.status()
        embed = discord.Embed(title=f"{MC_HOST}", color=discord.Color.green())
        embed.add_field(name="Version", value=status.version.name, inline=True)
        embed.add_field(name="Players", value=f"{status.players.online}/{status.players.max}", inline=True)
        embed.add_field(name="MOTD", value=status.description, inline=False)
        await ctx.send(embed=embed)
    except:
        await ctx.send("Minecraft server is offline or unreachable.")
#\u2705
@bot.command()
async def whitelist(ctx, username: str = None):
    if username is None:
        await ctx.send("Please enter your in-game name.")
        return

    owner = await bot.fetch_user(BOT_OWNER_ID)

    # DM the owner for confirmation
    if not ctx.guild or ctx.guild.id != TRUSTED_GUILD_ID:
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

    # you are from approved server
    try:
        print("PLEASE WORK")
        with MCRcon(MC_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
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
        with MCRcon(MC_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
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

@bot.command()
async def myid(ctx):
    await ctx.send(f"Your Discord ID: `{ctx.author.id}`")

"""def is_pc_online(ip):
    return os.system(f"ping -n 1 {ip}" if os.name == "nt" else f"ping -c 1 {ip}") == 0

@bot.command()
async def start(ctx):
    await ctx.send("Sending Wake-on-LAN packet...")
    send_magic_packet(TARGET_MAC)

    await ctx.send("Waiting for PC to boot...")
    for _ in range(30):  # ~90 seconds max (3s x 30)
        if is_pc_online(MC_HOST):
            await ctx.send("PC is online. Launching server...")
            break
        time.sleep(3)
    else:
        await ctx.send("Timeout: PC did not come online.")
        return

    try:
        response = requests.post(
            f"http://{MC_HOST}:5001/start-server",
            json={"token": TOKEN},
            timeout=10
        )
        if response.ok:
            await ctx.send("Minecraft server launch triggered.")
        else:
            await ctx.send(f"Launch failed: {response.status_code} - {response.text}")
    except Exception as e:
        await ctx.send(f"Could not contact the server: `{e}`")"""


bot.run(DISCORD_TOKEN) 

