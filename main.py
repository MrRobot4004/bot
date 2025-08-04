import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os
import time
import random
from datetime import datetime, timezone
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SETTINGS_FILE = "settings.json"
LAST_CHAPTER_FILE = "last_chapter.json"

# جمل عشوائية لزر الإشعار
PHRASES = [
    "فصل جديد مشوق ينتظرك!",
    "مغامرة جديدة بدأت للتو!",
    "الأحداث تشتعل الآن!",
    "لا تفوّت هذا الفصل الرائع!"
]
NOTIFICATION_TITLES = [
    "🚨 فصل جديد لـ",
    "🔥 تم إصدار فصل جديد:",
    "📢 جديد:",
    "📚 تحديث جديد:"
]

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def load_last_chapters():
    if os.path.exists(LAST_CHAPTER_FILE):
        with open(LAST_CHAPTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_last_chapters(chapters):
    with open(LAST_CHAPTER_FILE, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    check_for_new_chapters.start()

@bot.command()
async def setchannel(ctx):
    await ctx.send("من فضلك منشن الرول اللي هيتم الإشارة ليه عند نزول الفصل الجديد.")

    def check_role(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.role_mentions) > 0

    role_msg = await bot.wait_for("message", check=check_role)
    role_id = role_msg.role_mentions[0].id

    settings = load_settings()
    settings[str(ctx.guild.id)] = {
        "channel_id": ctx.channel.id,
        "role_id": role_id
    }
    save_settings(settings)

    await ctx.send("✅ تم حفظ الإعدادات بنجاح!")

def fetch_latest_chapter(max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            url = "https://olympustaff.com/ajax/get-manga-lastChapter/44"
            response = requests.get(url, headers=headers, timeout=10)  # إضافة مهلة زمنية

            if response.status_code != 200 or not response.text.strip():
                print(f"⚠️ الرد غير صالح أو فشل الطلب: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            item = soup.select_one(".list-group-item")
            if not item:
                print("❌ لم يتم العثور على أي فصول.")
                return None

            title = item.select_one(".fw-bold").text.strip()
            chapter_number = item.select_one(".badge").text.strip().replace("الفصل رقم ", "")
            chapter_date = item.select_one(".date-time").text.strip()
            image = item.select_one("img")
            image_url = image["src"] if image else None

            manga_url = f"https://olympustaff.com/series/{title.lower().replace(' ', '-').replace('’', '').replace("'", '')}"

            return {
                "title": title,
                "chapter": chapter_number,
                "date": chapter_date,
                "url": manga_url,
                "image": image_url
            }
        except requests.exceptions.RequestException as e:
            print(f"❌ محاولة {attempt + 1} فشلت: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)  # الانتظار قبل المحاولة التالية
            else:
                print(f"❌ فشل جميع المحاولات: {e}")
                return None

@tasks.loop(seconds=30)
async def check_for_new_chapters():
    chapter = fetch_latest_chapter()
    if not chapter:
        return

    unique_key = f"{chapter['title']}_{chapter['chapter']}"
    last_chapters = load_last_chapters()
    if unique_key in last_chapters:
        return  # تم الإشعار مسبقًا

    settings = load_settings()
    for guild_id, data in settings.items():
        channel = bot.get_channel(data["channel_id"])
        role_id = data.get("role_id")

        if not channel:
            continue

        try:
            role_mention = f"<@&{role_id}>" if role_id else ""
            phrase = random.choice(PHRASES)
            title_phrase = random.choice(NOTIFICATION_TITLES)

            embed = discord.Embed(
                title=f"{title_phrase} {chapter['title']}",
                description=f"**{phrase}**",
                color=0x1ABC9C,
                timestamp=datetime.now(timezone.utc)
            )
            if chapter['image']:
                embed.set_author(name=chapter['title'], icon_url=chapter['image'])
                embed.set_thumbnail(url=chapter['image'])
                embed.set_image(url=chapter['image'])

            embed.add_field(name="📖 الفصل", value=f"**{chapter['chapter']}**", inline=True)
            embed.add_field(name="⏰ نشر منذ", value=f"<t:{int(time.time())}:R>", inline=True)
            embed.add_field(name="🔗 اقرأ الآن", value=f"[اضغط هنا]({chapter['url']})", inline=False)

            embed.set_footer(
                text="🏴‍☠️ Straw Hat Team • مترجم بواسطة فريق قبعة القش",
                icon_url="https://olympustaff.com/images/teams/9c0db844720e541fe7597589c3256c72.jpg"
            )

            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="📖 اقرأ الآن",
                url=chapter["url"],
                style=discord.ButtonStyle.link
            ))

            await channel.send(content=f"🚨 {role_mention} 🚨", embed=embed, view=view)
        except Exception as e:
            print(f"Error sending notification: {e}")

    last_chapters.append(unique_key)
    save_last_chapters(last_chapters[-50:])

@bot.command()
async def testchapter(ctx):
    chapter = fetch_latest_chapter()
    if not chapter:
        await ctx.send("❌ لم يتم جلب الفصل.")
        return

    role_id = load_settings().get(str(ctx.guild.id), {}).get("role_id")
    role_mention = f"<@&{role_id}>" if role_id else ""
    phrase = random.choice(PHRASES)
    title_phrase = random.choice(NOTIFICATION_TITLES)

    embed = discord.Embed(
        title=f"{title_phrase} {chapter['title']}",
        description=f"**{phrase}**",
        color=0x1ABC9C,
        timestamp=datetime.now(timezone.utc)
    )
    if chapter['image']:
        embed.set_author(name=chapter['title'], icon_url=chapter['image'])
        embed.set_thumbnail(url=chapter['image'])
        embed.set_image(url=chapter['image'])

    embed.add_field(name="📖 الفصل", value=f"**{chapter['chapter']}**", inline=True)
    embed.add_field(name="⏰ نشر منذ", value=f"<t:{int(time.time())}:R>", inline=True)
    embed.add_field(name="🔗 اقرأ الآن", value=f"[اضغط هنا]({chapter['url']})", inline=False)

    embed.set_footer(
        text="🏴‍☠️ Straw Hat Team • مترجم بواسطة فريق قبعة القش",
        icon_url="https://olympustaff.com/images/teams/9c0db844720e541fe7597589c3256c72.jpg"
    )

    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="📖 اقرأ الآن",
        url=chapter["url"],
        style=discord.ButtonStyle.link
    ))

    await ctx.send(content=f"🚨 {role_mention} 🚨", embed=embed, view=view)

bot.run(TOKEN)
