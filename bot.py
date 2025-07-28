import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import random
from time import sleep

TOKEN = os.getenv("TOKEN")
ROLE_ID = 1332317530685177908  # يجب تغييره إذا كان مختلفًا

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

seen_chapters = []
user_channel_ids = {}
CHANNELS_FILE = "channels.json"

# تحميل القنوات المسجلة
if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r") as f:
        user_channel_ids = json.load(f)

def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(user_channel_ids, f, indent=2)

def generate_manga_url(title):
    base_url = "https://olympustaff.com/series/"
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    return f"{base_url}{slug}"

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
                
            chapter_data = {
                'title': title,
                'chapter': re.search(r'(\d+(?:\.\d+)?)', chapter).group(),
                'image': img_url,
                'url': generate_manga_url(title),
                'id': f"{title}_{chapter}"
            }
            chapters.append(chapter_data)
            
        return chapters
        
    except Exception as e:
        print(f"Error fetching chapters: {e}")
        return []

@bot.event
async def on_ready():
    global seen_chapters
    try:
        with open("last_seen.json", "r") as f:
            seen_chapters = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        seen_chapters = []
    
    print(f"Bot ready as {bot.user}")
    check_updates.start()

@tasks.loop(minutes=5)
async def check_updates():
    print("Checking for updates...")
    chapters = fetch_chapters()
    
    if not chapters:
        return
        
    new_chapters = [c for c in chapters if c['id'] not in seen_chapters]
    
    if new_chapters:
        for user_id, channel_id in user_channel_ids.items():
            channel = bot.get_channel(int(channel_id))
            if channel:
                for chap in new_chapters:
                    await send_chapter_notification(channel, chap)
        
        seen_chapters.extend([c['id'] for c in new_chapters])
        with open("last_seen.json", "w") as f:
            json.dump(seen_chapters, f)

async def send_chapter_notification(channel, chapter):
    try:
        role_mention = f"<@&{ROLE_ID}>"
        phrase = random.choice(PHRASES)
        title_phrase = random.choice(NOTIFICATION_TITLES)

        desc = f"""
{phrase}

════════════════════════════
📋 **تفاصيل الإصدار:**
📖 **الفصل:** `{chapter['chapter']}`
🕐 **تم النشر:** <t:{int(__import__('time').time())}:R>
════════════════════════════
        """.strip()

        embed = discord.Embed(
            title=f"{title_phrase} {chapter['title']}",
            description=desc,
            color=0x2C2F33
        )

        if chapter['image']:
            embed.set_image(url=chapter['image'])

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

        await channel.send(
            content=f"🚨 {role_mention} 🚨",
            embed=embed,
            view=view
        )
    except Exception as e:
        print(f"Error sending notification: {e}")

@bot.command()
async def setchannel(ctx):
    user_channel_ids[str(ctx.author.id)] = ctx.channel.id
    save_channels()
    await ctx.send("✅ تم تعيين هذه القناة لتلقي إشعارات الفصول الجديدة.")

@bot.command()
async def test(ctx):
    """إرسال إشعار تجريبي مطابق للإشعار الأصلي"""
    user_id = str(ctx.author.id)
    
    if user_id not in user_channel_ids:
        await ctx.send("❌ لم يتم تعيين قناة بعد! استخدم `!setchannel` أولاً")
        return
    
    channel_id = user_channel_ids[user_id]
    channel = bot.get_channel(channel_id)
    
    if not channel:
        await ctx.send("❌ القناة المسجلة غير موجودة أو البوت لا يستطيع الوصول إليها")
        return
    
    try:
        # إنشاء فصل تجريبي بنفس هيكل الإشعار الأصلي
        test_chapter = {
            "title": "ون بيس",
            "chapter": "999",
            "image": "https://olympustaff.com/uploads/thumbs/cover_63e0e3b0d587a-230x320.jpg",
            "url": "https://olympustaff.com/series/one-piece",
            "id": "test_999"
        }
        
        await send_chapter_notification(channel, test_chapter)
        await ctx.send(f"✅ تم إرسال الإشعار التجريبي إلى {channel.mention}")
        
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {str(e)}")
        print(f"Test command error: {e}")

bot.run(TOKEN)
