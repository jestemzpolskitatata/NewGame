import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests
import os
from flask import Flask
from threading import Thread

# === KEEP ALIVE ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# === KONFIGURACJA ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID")
GUILD_ID = int(os.getenv("GUILD_ID")
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID")
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID")
FACEIT_API_KEY = os.getenv("FACEIT_API_KEY")
ORGANIZER_ID = "599b0f48-50be-46f2-a80e-068148dbf6c0"

# === BOT ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# === LICZNIK TICKETÓW ===
def get_next_ticket_number():
    try:
        with open("ticket_counter.txt", "r") as f:
            number = int(f.read().strip())
    except:
        number = 0
    number += 1
    with open("ticket_counter.txt", "w") as f:
        f.write(str(number))
    # Formatowanie numerka
    if number <= 999:
        return f"{number:03d}"
    else:
        return f"0{number}"

# === POBIERANIE TURNIEJÓW FACEIT ===
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
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} komend.")
    except Exception as e:
        print(e)
    fetch_tournaments.start()

# === WYSYŁANIE TURNIEJÓW CO 10 MIN ===
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

# === PANEL TICKETÓW ===
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Contact support", style=discord.ButtonStyle.blurple, custom_id="contact_support")
    async def contact_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        staff_role = guild.get_role(STAFF_ROLE_ID)
        ticket_number = get_next_ticket_number()
        channel_name = f"ticket#{ticket_number}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        category = guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None
        channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category,
            reason=f"Ticket created by {user}"
        )

        await channel.send(
            f"{user.mention} Twój ticket został utworzony! {staff_role.mention} pomoże Ci wkrótce."
        )
        await interaction.response.send_message(
            f"Stworzono kanał: {channel.mention}", ephemeral=True
        )

# === KOMENDA /ticket-channel DLA ADMINA ===
@bot.tree.command(
    name="ticket-channel",
    description="Wyślij panel do tworzenia ticketów (tylko dla adminów)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_channel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Support",
        description="Please use the button below if you wish to open a ticket!",
        color=discord.Color.orange()
    )
    embed.set_footer(text="CSCL | Support")
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Panel ticketów wysłany!", ephemeral=True)

@ticket_channel.error
async def ticket_channel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "Nie masz uprawnień administratora do tej komendy.", ephemeral=True
        )

# === START ===
if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
