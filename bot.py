import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import random
from flask import Flask
from threading import Thread
from time import sleep

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

seen_chapters = []
user_channel_ids = {}
CHANNELS_FILE = "channels.json"

# Load channel registrations
if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        user_channel_ids = json.load(f)
else:
    user_channel_ids = {}

def save_channels():
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_channel_ids, f, indent=2)

def generate_manga_url(title):
    url_slug = title.lower()
    url_slug = re.sub(r'[^\w\s-]', '', url_slug)
    url_slug = re.sub(r'[-\s]+', '-', url_slug)
    url_slug = url_slug.strip('-')
    return f"https://olympustaff.com/series/{url_slug}"

PHRASES = [
    "🔥 فصل جديد متاح للقراءة",
    "⚡ إصدار حصري جديد",
    "🎯 أحدث فصل نزل الآن",
    "🌟 مغامرة جديدة تنتظرك",
    "💎 فصل مميز متاح حصرياً",
    "🚀 إصدار جديد من المانجا",
    "✨ لحظة انتظرتها طويلاً"
]

NOTIFICATION_TITLES = [
    "📚 إصدار جديد من",
    "🎭 الفصل الجديد من",
    "🗡️ أحدث فصل من",
    "⭐ قراءة ممتعة من",
    "🔖 استمتع بقراءة"
]

def load_seen():
    try:
        with open("last_seen.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_seen():
    try:
        with open("last_seen.json", "w", encoding="utf-8") as f:
            json.dump(seen_chapters, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving seen chapters: {e}")

def fetch_chapters():
    ajax_url = "https://olympustaff.com/ajax/get-manga-lastChapter/44"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'text/html, */*; q=0.01',
        'Referer': 'https://olympustaff.com/team/straw-hat'
    }
    for attempt in range(3):
        try:
            response = requests.get(ajax_url, headers=headers, timeout=3)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            chapters = []
            items = soup.select("ol.list-group > li")
            for item in items:
                title_elem = item.select_one("div.fw-bold")
                chap_elem = item.select_one("span.badge")
                img_elem = item.select_one("img")
                if title_elem and chap_elem:
                    title = title_elem.get_text().strip()
                    chapter_text = chap_elem.get_text().strip()
                    chapter_match = re.search(r"(\d+(?:\.\d+)?)", chapter_text)
                    if chapter_match:
                        chapter_number = chapter_match.group(1)
                        image = img_elem.get("src", "") if img_elem else ""
                        if image and not image.startswith('http'):
                            image = f"https://olympustaff.com{image}" if image.startswith('/') else f"https://olympustaff.com/{image}"
                        manga_url = generate_manga_url(title)
                        chapter_data = {
                            "title": title,
                            "chapter": chapter_number,
                            "image": image,
                            "url": manga_url,
                            "id": f"{title}_{chapter_number}"
                        }
                        chapters.append(chapter_data)
            return chapters
        except requests.RequestException as e:
            print(f"❌ Request error (attempt {attempt + 1}): {e}")
            sleep(1)
    print("❌ Failed to fetch chapters after 3 attempts")
    return []

@bot.event
async def on_ready():
    global seen_chapters
    seen_chapters = load_seen()
    print(f"✅ Logged in as {bot.user}")
    check_updates.start()

@tasks.loop(seconds=30)
async def check_updates():
    print("🔄 Checking for updates...")
    try:
        chapters = fetch_chapters()
        if not chapters:
            print("⚠️ No chapters found or error occurred")
            return
        new_chapters = [chap for chap in chapters if chap["id"] not in seen_chapters]
        if new_chapters:
            for user_id, channel_id in user_channel_ids.items():
                for chap in reversed(new_chapters):
                    await send_to_channel(channel_id, chap)
            seen_chapters.extend([chap["id"] for chap in new_chapters])
            save_seen()
        else:
            print("✅ No new chapters found")
    except Exception as e:
        print(f"❌ Error in check_updates: {e}")

async def send_to_channel(channel_id, chap):
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            print("❌ Channel not found")
            return

        phrase = random.choice(PHRASES)
        title_phrase = random.choice(NOTIFICATION_TITLES)

        desc = f"""
{phrase}

════════════════════════════
📋 **تفاصيل الإصدار:**
📖 **الفصل:** `{chap['chapter']}`
🕐 **تم النشر:** <t:{int(__import__('time').time())}:R>
════════════════════════════
        """.strip()

        embed = discord.Embed(
            title=f"{title_phrase} {chap['title']}",
            description=desc,
            color=0x2C2F33  # مظهر داكن / ليلي
        )

        embed.set_footer(
            text="🏴‍☠️ Straw Hat Team • مترجم بواسطة فريق قبعة القش",
            icon_url="https://olympustaff.com/images/teams/9c0db844720e541fe7597589c3256c72.jpg"
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="📖 اقرأ الآن", url=chap["url"], style=discord.ButtonStyle.link))

        await channel.send(content="🚨 @everyone 🚨", embed=embed, view=view)
        print(f"📤 Sent notification: {chap['title']} - Chapter {chap['chapter']}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

@bot.command()
async def setchannel(ctx):
    user_channel_ids[str(ctx.author.id)] = ctx.channel.id
    save_channels()
    await ctx.send("✅ تم تعيين هذه القناة لتلقي إشعارات الفصول الجديدة.")

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Discord Manga Bot is running!"

@app.route('/status')
def status():
    return {
        "status": "online",
        "bot_user": str(bot.user) if bot.user else "Not logged in",
        "guilds": len(bot.guilds) if bot.guilds else 0
    }

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

def keep_alive():
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask keep-alive server started on port 5000")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ الأمر غير موجود! استخدم `!help` لرؤية الأوامر المتاحة.")
    else:
        print(f"Command error: {error}")
        await ctx.send("❌ حدث خطأ أثناء تنفيذ الأمر.")

if __name__ == "__main__":
    keep_alive()
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
