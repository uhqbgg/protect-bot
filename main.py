# main.py
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import time
import json
import os
from datetime import datetime, timedelta
import random

TOKEN = "MTU0MzM0ODQ5Mzk0OTg3MDEyMA.GpxKdY.VJNGfLpG-KXais7DWXYO2pcC5mWaxH5T1kpi4w"
OWNER_ID = 1531322045638508736
LOG_CHANNEL_ID = 1543646909686878259

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="Protect Actif"), status=discord.Status.online)
    print(f"Bot connecté sur {len(bot.guilds)} serveurs")

@bot.tree.command(name="ping", description="Test")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong !")

if __name__ == "__main__":
    bot.run(TOKEN)
