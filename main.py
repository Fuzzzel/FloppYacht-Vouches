import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
import logging
from flask import Flask, jsonify, render_template
import threading
from dotenv import load_dotenv

# Nastavení logování pro výpis informací do konzole
logging.basicConfig(level=logging.INFO)

load_dotenv()

# Flask aplikace
app = Flask(__name__)

# Cesta k databázi
DB_PATH = "vouches.json"

# Načtení databáze
def load_vouches():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump([], f)
    with open(DB_PATH, "r") as f:
        return json.load(f)

# Uložení databáze
def save_vouches(vouches):
    with open(DB_PATH, "w") as f:
        json.dump(vouches, f, indent=4)

@app.route("/")
def home():
    vouches = load_vouches()
    return render_template("index.html", vouches=vouches)

@app.route("/api/vouches")
def api_vouches():
    return jsonify(load_vouches())

# Discord bot
intents = discord.Intents.default()  # Používá výchozí záměry
intents.message_content = True
bot = commands.Bot(command_prefix="+", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Bot připojen k Discordu jako {bot.user}")
    print(f"Bot připojen k Discordu jako {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        message = await ctx.send(f"*Wrong use of command, this is correct -->* `+rep @user message`")
        await asyncio.sleep(3)
        await message.delete()
    else:
        message = await ctx.send("Došlo k chybě. Zkontroluj příkaz a zkus to znovu.")
        await asyncio.sleep(3)
        await message.delete()

# Příkaz /vouch
@bot.command(name="rep")
async def vouch(ctx, mention, *, message: str):
    user = ctx.author
    vouches = load_vouches()

    # Získání avatar URL
    avatar_url = user.avatar.url if user.avatar else "https://cdn-icons-png.flaticon.com/512/2111/2111370.png"

    new_vouch = {
        "id": len(vouches) + 1,
        "message": message,
        "user": user.name,
        "user_id": user.id,
        "avatar_url": str(avatar_url),  # Ujistíme se, že URL je převedeno na řetězec
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    vouches.append(new_vouch)

    # Řazení od nejnovějšího vouchu
    vouches.sort(key=lambda x: x["id"], reverse=True)
    save_vouches(vouches)

    message = await ctx.send(f"`Vouch submited!` <:peeposummertime:1328082701617725572> ")
    await ctx.message.add_reaction("✅")
    await asyncio.sleep(3)
    await message.delete()

def run_flask():
    app.run(debug=True, use_reloader=False)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

def run_bot():
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    discord_thread = threading.Thread(target=run_bot)

    flask_thread.start()
    discord_thread.start()

    flask_thread.join()
    discord_thread.join()

    run_bot()
