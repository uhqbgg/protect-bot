import discord

TOKEN = "MTUOMzM0ODQ5MzK0OTg3MDEyMA.GRp-M2.pptC2PG4YHDQ1X1fhsTyAsSQHUU_9jVXqh5tZ4"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")

bot.run(TOKEN)
