import discord
from discord.ext import tasks, commands
import requests
import os
from keep_alive import keep_alive

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
FACEIT_API_KEY = os.getenv("FACEIT_API_KEY")
ORGANIZER_ID = os.getenv("ORGANIZER_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def get_tournaments():
    url = f"https://open.faceit.com/data/v4/organizers/{ORGANIZER_ID}/championships"
    headers = {
        "Authorization": f"Bearer {FACEIT_API_KEY}"
    }
    params = {
        "limit": 5,
        "offset": 0
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        print(f"Błąd API: {response.status_code} {response.text}")
        return []

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    fetch_tournaments.start()

@tasks.loop(minutes=10)
async def fetch_tournaments():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Nie znaleziono kanału.")
        return

    tournaments = get_tournaments()
    if tournaments:
        for t in tournaments:
            embed = discord.Embed(
                title=t.get("name", "Brak nazwy"),
                url=t.get("faceit_url", ""),
                description=t.get("description", "Brak opisu"),
                color=discord.Color.orange()
            )
            embed.add_field(name="Gra", value=t.get("game", "Brak danych"))
            embed.add_field(name="Status", value=t.get("status", "Brak danych"))
            embed.add_field(name="Start", value=t.get("started_at", "Brak danych"))
            await channel.send(embed=embed)
    else:
        await channel.send("Brak nowych turniejów lub błąd API.")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
