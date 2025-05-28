import discord
from discord.ext import commands
from mcstatus import JavaServer as MinecraftServer
from mcrcon import MCRcon
from dotenv import load_dotenv
import os

#lol u thought u would see these
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

#basic setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = 'mc!', intents = intents)

#config details
MC_HOST = "mc.aayan.us"
MC_PORT = 25565
RCON_PORT = 25575

@bot.event
async def on_ready():
    print("first we mine... then we craft... let's minecraft!")
    print("--------------------------------------------------")

@bot.command()
async def info(ctx):
    server = MinecraftServer("mc.aayan.us",25565)
    try:
        status = server.status()
        embed = discord.Embed(title="Minecraft Server Info", color=discord.Color.green())
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

bot.run(DISCORD_TOKEN)