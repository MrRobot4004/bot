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

# Get environment variables
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Initialize Discord bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

def generate_manga_url(title):
    """Generate dynamic manga URL from title"""
    # Convert title to URL-friendly format
    url_slug = title.lower()
    
    # Remove special characters and replace spaces with hyphens
    url_slug = re.sub(r'[^\w\s-]', '', url_slug)  # Remove special chars except spaces and hyphens
    url_slug = re.sub(r'[-\s]+', '-', url_slug)   # Replace spaces and multiple hyphens with single hyphen
    url_slug = url_slug.strip('-')                # Remove leading/trailing hyphens
    
    return f"https://olympustaff.com/series/{url_slug}"

# Random notification messages in Arabic - Enhanced and more professional
PHRASES = [
    "🔥 فصل جديد متاح للقراءة",
    "⚡ إصدار حصري جديد",
    "🎯 أحدث فصل نزل الآن",
    "🌟 مغامرة جديدة تنتظرك",
    "💎 فصل مميز متاح حصرياً",
    "🚀 إصدار جديد من المانجا",
    "✨ لحظة انتظرتها طويلاً"
]

# Enhanced notification titles for variety
NOTIFICATION_TITLES = [
    "📚 إصدار جديد من",
    "🎭 الفصل الجديد من",
    "🗡️ أحدث فصل من",
    "⭐ قراءة ممتعة من",
    "🔖 استمتع بقراءة"
]

def load_seen():
    """Load the list of previously seen chapters from JSON file"""
    try:
        with open("last_seen.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_seen(seen):
    """Save the list of seen chapters to JSON file"""
    try:
        with open("last_seen.json", "w", encoding="utf-8") as f:
            json.dump(seen, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving seen chapters: {e}")

def fetch_chapters():
    """Scrape manga chapters from olympustaff.com AJAX endpoint"""
    try:
        # Use the AJAX endpoint that loads the latest chapters
        ajax_url = "https://olympustaff.com/ajax/get-manga-lastChapter/44"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'text/html, */*; q=0.01',
            'Referer': 'https://olympustaff.com/team/straw-hat'
        }
        
        response = requests.get(ajax_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML returned by the AJAX endpoint
        soup = BeautifulSoup(response.text, "html.parser")
        chapters = []
        
        # Parse the list items from the AJAX response
        items = soup.select("ol.list-group > li")
        print(f"🔍 Found {len(items)} chapter items from AJAX")
        
        for item in items:
            try:
                # Extract title from fw-bold div
                title_elem = item.select_one("div.fw-bold")
                # Extract chapter number from badge
                chap_elem = item.select_one("span.badge")
                # Extract image
                img_elem = item.select_one("img")
                
                if title_elem and chap_elem and img_elem:
                    title = title_elem.get_text().strip()
                    # Extract chapter number from Arabic badge text (الفصل رقم X)
                    chapter_text = chap_elem.get_text().strip()
                    chapter_match = re.search(r"(\d+(?:\.\d+)?)", chapter_text)
                    
                    if chapter_match:
                        chapter_number = chapter_match.group(1)
                        image = img_elem.get("src", "")
                        
                        # Ensure absolute URLs
                        if image and not image.startswith('http'):
                            if image.startswith('/'):
                                image = f"https://olympustaff.com{image}"
                            else:
                                image = f"https://olympustaff.com/{image}"
                        
                        # Generate dynamic manga URL from title
                        manga_url = generate_manga_url(title)
                        
                        chapter_data = {
                            "title": title,
                            "chapter": chapter_number,
                            "image": image,
                            "url": manga_url,
                            "id": f"{title}_{chapter_number}"
                        }
                        
                        chapters.append(chapter_data)
                        print(f"✅ Found chapter: {title} - Chapter {chapter_number}")
                    else:
                        print(f"⚠️ Could not extract chapter number from: {chapter_text}")
                else:
                    print(f"⚠️ Could not find required elements in item")
                    
            except Exception as item_error:
                print(f"⚠️ Error processing item: {item_error}")
                continue
        
        print(f"📚 Total chapters found: {len(chapters)}")
        return chapters
        
    except requests.RequestException as e:
        print(f"❌ Error fetching chapters: {e}")
        return []
    except Exception as e:
        print(f"❌ Error parsing chapters: {e}")
        return []

@bot.event
async def on_ready():
    """Event triggered when bot successfully connects to Discord"""
    print(f"✅ Logged in as {bot.user}")
    print(f"📡 Monitoring channel ID: {CHANNEL_ID}")
    check_updates.start()

@tasks.loop(minutes=5)
async def check_updates():
    """Scheduled task to check for new manga chapters every 5 minutes"""
    print("🔄 Checking for updates...")
    
    try:
        seen = load_seen()
        chapters = fetch_chapters()
        
        if not chapters:
            print("⚠️ No chapters found or error occurred")
            return
            
        # Find new chapters that haven't been seen before
        new_chapters = [chap for chap in chapters if chap["id"] not in seen]
        
        if new_chapters:
            print(f"📚 Found {len(new_chapters)} new chapters")
            
            # Send notifications for new chapters (reversed to maintain chronological order)
            for chap in reversed(new_chapters):
                await send_to_channel(chap)
                seen.append(chap["id"])
            
            # Save updated seen list
            save_seen(seen)
        else:
            print("✅ No new chapters found")
            
    except Exception as e:
        print(f"❌ Error in check_updates: {e}")

async def send_to_channel(chap):
    """Send manga chapter notification to Discord channel with enhanced design"""
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Channel not found")
            return

        # Select random phrases for variety
        phrase = random.choice(PHRASES)
        title_phrase = random.choice(NOTIFICATION_TITLES)
        
        # Create professional description with better formatting
        desc = f"""
{phrase}
━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **تفاصيل الإصدار:**
📖 **الفصل:** `{chap['chapter']}`
🕐 **تاريخ النشر:** <t:{int(__import__('time').time())}:R>
━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 **[اقرأ الفصل الآن]({chap['url']})**
        """.strip()

        # Enhanced color scheme - alternating colors for visual appeal
        colors = [0xFF6B6B, 0x4ECDC4, 0x45B7D1, 0x96CEB4, 0xFECA57, 0xFF9FF3, 0x54A0FF]
        selected_color = random.choice(colors)

        # Create rich embed message with enhanced styling
        embed = discord.Embed(
            title=f"{title_phrase} {chap['title']}",
            description=desc,
            color=selected_color
        )
        
        # Add thumbnail image if available
        if chap['image']:
            image_url = chap['image']
            if image_url.startswith('/'):
                image_url = f"https://olympustaff.com{image_url}"
            embed.set_thumbnail(url=image_url)
        
        # Enhanced footer with team info
        embed.set_footer(
            text="🏴‍☠️ Straw Hat Team • مترجم بواسطة فريق قبعة القش",
            icon_url="https://olympustaff.com/images/teams/9c0db844720e541fe7597589c3256c72.jpg"
        )
        
        # Add author field for branding
        embed.set_author(
            name="🔔 إشعار فصل جديد",
            icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"
        )

        # Send message with @everyone mention and enhanced styling
        await channel.send(content="🚨 @everyone 🚨", embed=embed)
        print(f"📤 Sent enhanced notification for: {chap['title']} - Chapter {chap['chapter']}")
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")

# Manual testing command with enhanced design
@bot.command()
async def test(ctx):
    """Manual command to test bot functionality with sample data"""
    test_title = "The Fake Master Who Accidentally Became the Strongest"
    test_chapter = {
        "title": test_title,
        "chapter": "99",
        "image": "https://olympustaff.com/images/manga/11141563592135497564.jpg",
        "url": generate_manga_url(test_title),
        "id": "test_99"
    }
    
    await send_to_channel(test_chapter)
    
    # Send confirmation with enhanced styling
    confirm_embed = discord.Embed(
        title="✅ تم إرسال الإشعار التجريبي",
        description="🧪 تم إرسال إشعار تجريبي بالتصميم الجديد المحسن",
        color=0x00FF00
    )
    await ctx.send(embed=confirm_embed)

# Command to test URL generation
@bot.command()
async def testurl(ctx, *, manga_title):
    """Test URL generation for a manga title"""
    generated_url = generate_manga_url(manga_title)
    
    test_embed = discord.Embed(
        title="🔗 اختبار توليد الرابط",
        description=f"**اسم المانجا:** {manga_title}\n**الرابط المولد:** {generated_url}",
        color=0x3498DB
    )
    await ctx.send(embed=test_embed)

# Manual update check command
@bot.command()
async def check(ctx):
    """Manual command to trigger immediate update check"""
    await ctx.send("🔄 يتم فحص آخر التحديثات الآن...")
    await check_updates()
    await ctx.send("✅ تم الانتهاء من فحص التحديثات!")

# Flask keep-alive server to prevent bot from sleeping
app = Flask(__name__)

@app.route('/')
def home():
    """Simple health check endpoint"""
    return "🤖 Discord Manga Bot is running!"

@app.route('/status')
def status():
    """Status endpoint with bot information"""
    return {
        "status": "online",
        "bot_user": str(bot.user) if bot.user else "Not logged in",
        "guilds": len(bot.guilds) if bot.guilds else 0
    }

def run_flask():
    """Run Flask server on port 5000"""
    app.run(host='0.0.0.0', port=5000, debug=False)

def keep_alive():
    """Start Flask server in separate thread"""
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask keep-alive server started on port 5000")

# Error handler for bot commands
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ الأمر غير موجود! استخدم `!help` لرؤية الأوامر المتاحة.")
    else:
        print(f"Command error: {error}")
        await ctx.send("❌ حدث خطأ أثناء تنفيذ الأمر.")

# Main execution
if __name__ == "__main__":
    # Start keep-alive server
    keep_alive()
    
    # Start Discord bot
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
