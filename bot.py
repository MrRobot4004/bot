import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import random
import time
from datetime import datetime

# تحميل المتغيرات من البيئة
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))  # يجب ضبطه إلى قناة الإشعارات
ROLE_ID = int(os.getenv("ROLE_ID", 1332317530685177908))  # يمكن ضبطه من env أيضًا

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

seen_chapters = []
CHANNELS_FILE = "last_seen.json"

PHRASES = [
    "🔥 فصل جديد متاح للقراءة",
    "⚡ إصدار حصري جديد",
    "🎯 أحدث فصل نزل الآن",
    "🌟 مغامرة جديدة تنتظرك",
    "💎 فصل مميز متاح حصرياً"
]

NOTIFICATION_TITLES = [
    "📚 إصدار جديد من",
    "🎭 الفصل الجديد من",
    "🗡️ أحدث فصل من"
]


def fetch_chapters():
    try:
        url = "https://olympustaff.com/ajax/get-manga-lastChapter/44"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'X-Requested-With': 'XMLHttpRequest'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        chapters = []

        for item in soup.select('ol.list-group li'):
            title = item.select_one('div.fw-bold').get_text(strip=True)
            chapter = item.select_one('span.badge').get_text(strip=True)
            img = item.select_one('img')
            img_url = img['src'] if img else None
            if img_url and not img_url.startswith('http'):
                img_url = f"https://olympustaff.com{img_url}"

            chap_num = re.search(r'(\d+(?:\.\d+)?)', chapter)
            chapter_str = chap_num.group() if chap_num else chapter

            chapters.append({
                'title': title,
                'chapter': chapter_str,
                'image': img_url,
                'url': generate_manga_url(title),
                'id': f"{title}_{chapter_str}"
            })
        return chapters
    except Exception as e:
        print(f"Error fetching chapters: {e}")
        return []


def generate_manga_url(title):
    base_url = "https://olympustaff.com/series/"
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    return f"{base_url}{slug}"


@bot.event
async def on_ready():
    global seen_chapters
    try:
        with open(CHANNELS_FILE, "r") as f:
            seen_chapters = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        seen_chapters = []
    print(f"Bot ready as {bot.user}")
    check_updates.start()


@tasks.loop(minutes=5)
async def check_updates():
    chapters = fetch_chapters()
    if not chapters:
        return

    new_chapters = [c for c in chapters if c['id'] not in seen_chapters]
    if not new_chapters:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel {CHANNEL_ID} not found or bot lacks permission.")
        return

    for chap in new_chapters:
        await send_chapter_notification(channel, chap)
    seen_chapters.extend([c['id'] for c in new_chapters])

    with open(CHANNELS_FILE, "w") as f:
        json.dump(seen_chapters, f, indent=2)


async def send_chapter_notification(channel, chapter):
    try:
        role_mention = f"<@&{ROLE_ID}>" if ROLE_ID else ""
        phrase = random.choice(PHRASES)
        title_phrase = random.choice(NOTIFICATION_TITLES)

        # إعداد Embed أكثر جاذبية
        embed = discord.Embed(
            title=f"{title_phrase} {chapter['title']}",
            description=f"**{phrase}**",
            color=0x1ABC9C,
            timestamp=datetime.utcnow()
        )
        # عرض العنوان كـ author مع أيقونة الغلاف
        if chapter['image']:
            embed.set_author(name=chapter['title'], icon_url=chapter['image'])
        # الحقول
        embed.add_field(name="📖 الفصل", value=f"**{chapter['chapter']}**", inline=True)
        embed.add_field(name="⏰ نشر منذ", value=f"<t:{int(time.time())}:R>", inline=True)
        embed.add_field(name="🔗 اقرأ الآن", value=f"[اضغط هنا]({chapter['url']})", inline=False)

        # thumbnail وصورة الغلاف
        if chapter['image']:
            embed.set_thumbnail(url=chapter['image'])
            embed.set_image(url=chapter['image'])

        # Footer مع أيقونة الفريق
        embed.set_footer(
            text="🏴‍☠️ Straw Hat Team • مترجم بواسطة فريق قبعة القش",
            icon_url="https://olympustaff.com/images/teams/9c0db844720e541fe7597589c3256c72.jpg"
        )

        # زر القراءة
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="📖 اقرأ الآن", 
            url=chapter["url"], 
            style=discord.ButtonStyle.link
        ))

        await channel.send(content=f"🚨 {role_mention} 🚨", embed=embed, view=view)
    except Exception as e:
        print(f"Error sending notification: {e}")


@bot.command()
async def test(ctx):
    """إرسال إشعار تجريبي جميل"""
    test_chapter = {
        'title': 'ون بيس',
        'chapter': '999',
        'image': 'https://olympustaff.com/uploads/thumbs/cover_63e0e3b0d587a-230x320.jpg',
        'url': 'https://olympustaff.com/series/one-piece',
        'id': 'test_999'
    }
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await send_chapter_notification(channel, test_chapter)
        await ctx.send(f"✅ تم إرسال الإشعار التجريبي إلى {channel.mention}")
    else:
        await ctx.send("❌ فشلت محاولة إرسال الإشعار التجريبي. تحقق من CHANNEL_ID.")

bot.run(TOKEN)
