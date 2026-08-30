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

TOKEN = "MTU0M2M0ODQ5Mzk0OTg3MDEyMA.GRp-M2.pptC2PG4YHDQ1X1fhsTyAsQHUU_9jVXqh5tZ4"
OWNER_ID = 1531322045638508736
LOG_CHANNEL_ID = 1543646909686878259

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

SETTINGS_FILE = "protect_settings.json"
VERIFIED_FILE = "verified_users.json"
WARNINGS_FILE = "warnings.json"

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"auto_verify": True, "anti_raid": True, "max_joins": 5, "time_window": 60, "captcha": True}, f, indent=2)

if not os.path.exists(VERIFIED_FILE):
    with open(VERIFIED_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(WARNINGS_FILE):
    with open(WARNINGS_FILE, "w") as f:
        json.dump({}, f)

def load_settings():
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def load_verified():
    with open(VERIFIED_FILE, "r") as f:
        return json.load(f)

def save_verified(verified):
    with open(VERIFIED_FILE, "w") as f:
        json.dump(verified, f, indent=2)

def load_warnings():
    with open(WARNINGS_FILE, "r") as f:
        return json.load(f)

def save_warnings(warnings):
    with open(WARNINGS_FILE, "w") as f:
        json.dump(warnings, f, indent=2)

async def log_to_channel(title, description):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        return
    embed = discord.Embed(title=title, description=description[:4000], color=0x2b2d31, timestamp=datetime.utcnow())
    embed.set_footer(text="Protect Bot")
    await channel.send(embed=embed)

join_times = {}

@bot.event
async def on_member_join(member):
    settings = load_settings()
    if not settings["anti_raid"]:
        return
    now = time.time()
    for user_id, times in list(join_times.items()):
        join_times[user_id] = [t for t in times if now - t < 300]
        if not join_times[user_id]:
            del join_times[user_id]
    if member.id not in join_times:
        join_times[member.id] = []
    join_times[member.id].append(now)
    recent_joins = len(join_times.get(member.id, []))
    if recent_joins > settings["max_joins"]:
        try:
            await member.ban(reason=f"Anti-raid: {recent_joins} joines")
            await log_to_channel("Anti-raid", f"{member.mention} ({member.id}) banni")
        except:
            pass
        return
    if settings["auto_verify"]:
        verified = load_verified()
        if member.id not in verified:
            verified.append(member.id)
            save_verified(verified)
            role = discord.utils.get(member.guild.roles, name="Membre")
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass
            await log_to_channel("Auto-verify", f"{member.mention} ({member.id}) auto-verifie")
    if settings["captcha"]:
        await send_captcha(member)

captcha_cache = {}

async def send_captcha(member):
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    result = num1 + num2
    embed = discord.Embed(title="Verification", description=f"Bienvenue {member.mention}!\n\n{num1} + {num2} = ?\n\nTu as 60 secondes.", color=0x2b2d31)
    try:
        await member.send(embed=embed)
        captcha_cache[member.id] = {"result": result, "time": time.time()}
    except:
        pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.author.id in captcha_cache:
        data = captcha_cache[message.author.id]
        if time.time() - data["time"] > 60:
            del captcha_cache[message.author.id]
            await message.channel.send(f"{message.author.mention} Temps ecoule. Tape /verify.")
            return
        if message.content.isdigit() and int(message.content) == data["result"]:
            del captcha_cache[message.author.id]
            verified = load_verified()
            if message.author.id not in verified:
                verified.append(message.author.id)
                save_verified(verified)
                role = discord.utils.get(message.guild.roles, name="Membre")
                if role:
                    await message.author.add_roles(role)
                await message.channel.send(f"{message.author.mention} Verifie !")
                await log_to_channel("Captcha", f"{message.author.mention} ({message.author.id}) a passe le captcha")
        else:
            await message.channel.send(f"{message.author.mention} Mauvaise reponse.")
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="Protect Actif"), status=discord.Status.online)
    print(f"Protect Bot connecte sur {len(bot.guilds)} serveurs")

@bot.tree.command(name="verify", description="Reessayer la verification")
async def verify(interaction: discord.Interaction):
    if interaction.user.id in captcha_cache:
        await interaction.response.send_message("Verification deja en cours.", ephemeral=True)
        return
    await send_captcha(interaction.user)
    await interaction.response.send_message("Verification envoyee en MP.", ephemeral=True)

@bot.tree.command(name="ban", description="[ADMIN] Bannir")
@app_commands.describe(membre="L'utilisateur", raison="Raison")
async def ban_cmd(interaction: discord.Interaction, membre: discord.Member, raison: str = "Non specifie"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    await membre.ban(reason=raison)
    await interaction.response.send_message(f"{membre.mention} banni")
    await log_to_channel("Ban", f"{membre.mention} ({membre.id}) banni")

@bot.tree.command(name="kick", description="[ADMIN] Expulser")
@app_commands.describe(membre="L'utilisateur", raison="Raison")
async def kick_cmd(interaction: discord.Interaction, membre: discord.Member, raison: str = "Non specifie"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    await membre.kick(reason=raison)
    await interaction.response.send_message(f"{membre.mention} expulse")
    await log_to_channel("Kick", f"{membre.mention} ({membre.id}) kick")

@bot.tree.command(name="warn", description="[ADMIN] Avertir")
@app_commands.describe(membre="L'utilisateur", raison="Raison")
async def warn_cmd(interaction: discord.Interaction, membre: discord.Member, raison: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    warnings = load_warnings()
    user_id = str(membre.id)
    if user_id not in warnings:
        warnings[user_id] = []
    warnings[user_id].append({"raison": raison, "date": datetime.utcnow().isoformat(), "admin": interaction.user.name})
    save_warnings(warnings)
    await interaction.response.send_message(f"{membre.mention} averti ({len(warnings[user_id])})")
    await log_to_channel("Warn", f"{membre.mention} ({membre.id}) averti\nRaison: {raison}")

@bot.tree.command(name="warnings", description="[ADMIN] Voir les avertissements")
@app_commands.describe(membre="L'utilisateur")
async def warnings_cmd(interaction: discord.Interaction, membre: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    warnings = load_warnings()
    user_warnings = warnings.get(str(membre.id), [])
    if not user_warnings:
        await interaction.response.send_message(f"{membre.mention} aucun avertissement.", ephemeral=True)
        return
    embed = discord.Embed(title=f"Avertissements de {membre.name}", color=0x2b2d31)
    for i, w in enumerate(user_warnings[-10:], 1):
        embed.add_field(name=f"#{i}", value=f"Raison: {w['raison']}\nDate: {w['date'][:16]}\nAdmin: {w['admin']}", inline=False)
    embed.set_footer(text=f"Total: {len(user_warnings)}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="clear_warnings", description="[ADMIN] Effacer les avertissements")
@app_commands.describe(membre="L'utilisateur")
async def clear_warnings_cmd(interaction: discord.Interaction, membre: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    warnings = load_warnings()
    if str(membre.id) in warnings:
        del warnings[str(membre.id)]
        save_warnings(warnings)
        await interaction.response.send_message(f"Avertissements de {membre.mention} effaces.")
        await log_to_channel("Clear Warnings", f"{membre.mention} ({membre.id}) reinitialise")
    else:
        await interaction.response.send_message(f"{membre.mention} aucun avertissement.", ephemeral=True)

@bot.tree.command(name="settings", description="[ADMIN] Configurer")
@app_commands.describe(auto_verify="true/false", anti_raid="true/false", max_joins="nombre", time_window="secondes", captcha="true/false")
async def settings_cmd(interaction: discord.Interaction, auto_verify: str = None, anti_raid: str = None, max_joins: int = None, time_window: int = None, captcha: str = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    settings = load_settings()
    if auto_verify is not None:
        settings["auto_verify"] = auto_verify.lower() == "true"
    if anti_raid is not None:
        settings["anti_raid"] = anti_raid.lower() == "true"
    if max_joins is not None:
        settings["max_joins"] = max_joins
    if time_window is not None:
        settings["time_window"] = time_window
    if captcha is not None:
        settings["captcha"] = captcha.lower() == "true"
    save_settings(settings)
    embed = discord.Embed(title="Configuration", color=0x2b2d31)
    embed.add_field(name="Auto-verify", value="Oui" if settings["auto_verify"] else "Non", inline=True)
    embed.add_field(name="Anti-raid", value="Oui" if settings["anti_raid"] else "Non", inline=True)
    embed.add_field(name="Captcha", value="Oui" if settings["captcha"] else "Non", inline=True)
    embed.add_field(name="Max joins", value=str(settings["max_joins"]), inline=True)
    embed.add_field(name="Time window", value=f"{settings['time_window']}s", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_to_channel("Settings", f"Configuration modifiee")

@bot.tree.command(name="stats", description="[ADMIN] Statistiques")
async def stats_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    guild = interaction.guild
    verified = load_verified()
    warnings = load_warnings()
    embed = discord.Embed(title=f"Statistiques - {guild.name}", color=0x2b2d31)
    embed.add_field(name="Membres", value=f"{guild.member_count}", inline=True)
    embed.add_field(name="Bots", value=f"{len([m for m in guild.members if m.bot])}", inline=True)
    embed.add_field(name="Humains", value=f"{guild.member_count - len([m for m in guild.members if m.bot])}", inline=True)
    embed.add_field(name="Verifies", value=f"{len(verified)}", inline=True)
    embed.add_field(name="Avertissements", value=f"{sum(len(w) for w in warnings.values())}", inline=True)
    embed.add_field(name="Salons", value=f"{len(guild.channels)}", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="unban", description="[ADMIN] Debannir")
@app_commands.describe(user_id="ID de l'utilisateur")
async def unban_cmd(interaction: discord.Interaction, user_id: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"{user.mention} debanni.")
        await log_to_channel("Unban", f"{user.mention} ({user_id}) debanni")
    except Exception as e:
        await interaction.response.send_message(f"Erreur: {e}", ephemeral=True)

@bot.tree.command(name="clear", description="[ADMIN] Supprimer des messages")
@app_commands.describe(amount="Nombre (1-100)")
async def clear_cmd(interaction: discord.Interaction, amount: int = 10):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Entre 1 et 100.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount + 1)
    await interaction.followup.send(f"{len(deleted)-1} messages supprimes.", ephemeral=True)

@bot.tree.command(name="info", description="[ADMIN] Infos sur un membre")
@app_commands.describe(membre="L'utilisateur")
async def info_cmd(interaction: discord.Interaction, membre: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    warnings = load_warnings()
    user_warnings = warnings.get(str(membre.id), [])
    verified = load_verified()
    embed = discord.Embed(title=f"Informations - {membre.name}", color=0x2b2d31)
    embed.set_thumbnail(url=membre.display_avatar.url)
    embed.add_field(name="ID", value=membre.id, inline=True)
    embed.add_field(name="Compte cree", value=membre.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
    embed.add_field(name="Arrive", value=membre.joined_at.strftime("%d/%m/%Y %H:%M") if membre.joined_at else "Inconnu", inline=True)
    embed.add_field(name="Verifie", value="Oui" if membre.id in verified else "Non", inline=True)
    embed.add_field(name="Avertissements", value=len(user_warnings), inline=True)
    embed.add_field(name="Roles", value=", ".join([r.name for r in membre.roles if r.name != "@everyone"])[:500] or "Aucun", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="massban", description="[ADMIN] Bannir plusieurs")
@app_commands.describe(ids="IDs separes par des virgules", raison="Raison")
async def massban_cmd(interaction: discord.Interaction, ids: str, raison: str = "Non specifie"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    user_ids = [id.strip() for id in ids.split(",") if id.strip().isdigit()]
    if not user_ids:
        await interaction.response.send_message("IDs invalides.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    success = 0
    failed = 0
    for user_id in user_ids:
        try:
            user = await bot.fetch_user(int(user_id))
            await interaction.guild.ban(user, reason=raison)
            success += 1
        except:
            failed += 1
    await interaction.followup.send(f"{success} bannis, {failed} echoues.")
    await log_to_channel("Mass Ban", f"{success} utilisateurs bannis")

@bot.tree.command(name="lockdown", description="[ADMIN] Verrouiller/Deverrouiller")
@app_commands.describe(channel="Le salon", lock="True = verrouiller, False = deverrouiller")
async def lockdown_cmd(interaction: discord.Interaction, channel: discord.TextChannel, lock: bool):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin uniquement.", ephemeral=True)
        return
    overwrite = channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False if lock else None
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    status = "verrouille" if lock else "deverrouille"
    await interaction.response.send_message(f"Salon {channel.mention} {status}.")
    await log_to_channel("Lockdown", f"Salon {channel.name} {status}")

if __name__ == "__main__":
    bot.run(TOKEN)
