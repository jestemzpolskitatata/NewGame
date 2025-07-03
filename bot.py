import discord
from discord.ext import tasks, commands
import requests

from keep_alive import keep_alive

FACEIT_API_KEY = 'a6f20d43-f934-4e5c-b348-42cf6e732dda'
ORGANIZER_ID = '599b0f48-50be-46f2-a80e-068148dbf6c0'
DISCORD_TOKEN = 'MTM5MDA3OTE5NzY0MDM5Mjg1NQ.Gk29JH.zXxZFBUDHU1eeRwbN1mPc_hv1YibE8YIXZcVbQ'  
CHANNEL_ID = 1389255740014727420           

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
