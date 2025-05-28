import discord
from discord.ext import commands
from mcstatus import JavaServer as MinecraftServer
from mcrcon import MCRcon
from dotenv import load_dotenv
import os
import asyncio

#basic setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = 'mc!', intents = intents)

#config details
MC_PORT = 25565
RCON_PORT = 25575
#lol u thought u would see these
load_dotenv()
MC_HOST = os.getenv("MC_HOST")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

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
            msg = f"🌍 {players} players on {version}"
        except:
            msg = "❌ Server Offline"

        await bot.change_presence(activity=discord.Game(name=msg))
        await asyncio.sleep(60)  # update every 60 seconds

@bot.command()
async def info(ctx):
    server = MinecraftServer("mc.aayan.us",25565)
    try:
        status = server.status()
        embed = discord.Embed(title="mc.aayan.us", color=discord.Color.green())
        embed.add_field(name="Version", value=status.version.name, inline=True)
        embed.add_field(name="Players", value=f"{status.players.online}/{status.players.max}", inline=True)
        embed.add_field(name="MOTD", value=status.description, inline=False)
        await ctx.send(embed=embed)
    except:
        await ctx.send("❌ Minecraft server is offline or unreachable.")

@bot.command()
async def whitelist(ctx, username):
    if username is None:
        await ctx.send("❌Please enter your in-game name.")
    try:
        with MCRcon(MC_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(f"whitelist add {username}")
        await ctx.send(f"✅ Whitelisted `{username}`.\nServer says: `{response}`")
    except:
        await ctx.send("❌ Failed to connect to RCON or run command.")

#@bot.command()
#async def start(ctx):

bot.run(DISCORD_TOKEN)  