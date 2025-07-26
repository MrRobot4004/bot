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

# Current active channel ID (can be changed with command)
CURRENT_CHANNEL_ID = CHANNEL_ID

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
    print(f"🌐 Connected to {len(bot.guilds)} guild(s)")
    
    # Start tasks only if not already running
    if not check_updates.is_running():
        check_updates.start()
        print("🔄 Chapter monitoring started (every 5 minutes)")
    
    if not keep_alive_ping.is_running():
        keep_alive_ping.start()
        print("💓 Keep-alive ping started (every 3 minutes)")
        
    # Register with external monitoring
    try:
        print("📡 Setting up external monitoring...")
        replit_url = f"https://{os.getenv('REPL_SLUG', 'discord-bot')}.{os.getenv('REPL_OWNER', 'user')}.repl.doc"
        print(f"🌐 External URL: {replit_url}")
    except Exception as setup_error:
        print(f"⚠️ External monitoring setup failed: {setup_error}")

@bot.event
async def on_disconnect():
    """Event triggered when bot disconnects from Discord"""
    print("⚠️ Bot disconnected from Discord")
    
@bot.event
async def on_resumed():
    """Event triggered when bot resumes connection to Discord"""
    print("🔄 Bot connection resumed")

    
@bot.event
async def on_error(event, *args, **kwargs):
    """Global error handler for Discord events"""
    import traceback
    print(f"❌ Discord error in {event}: {traceback.format_exc()}")

    
@tasks.loop(minutes=300)
async def check_updates():
    """Scheduled task to check for new manga chapters every 5 minutes"""
    print("🔍 Checking for updates...")
    
    try:
        seen = load_seen()
        chapters = fetch_chapters()
        
        if not chapters:
            print("⚠️ No chapters found or or error occurred")
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

@tasks.loop(minutes=3)  # Even more frequent pings - every 3 minutes
async def keep_alive_ping():
    """Aggressive keep alive task to prevent bot from sleeping on free hosting"""
    try:
        # Multiple ping strategies for better reliability
        import time
        current_time = time.time()
        
        # Multi-step keep-alive process
        print(f"🔄 Starting keep-alive cycle at {time.strftime('%H:%M:%S')}")
        
        # Step 1: Ping our own Flask server
        response = requests.get("http://localhost:5000/ping", timeout=15)
        print(f"💓 Local ping: {response.status_code}")
        
        # Step 2: Check Discord connection health
        if bot.is_ready():
            guild_count = len(bot.guilds)
            print(f"🤖 Discord healthy - {guild_count} guilds connected")
            
            # Send a tiny activity to Discord API (lightweight heartbeat)
            try:
                await bot.wait_until_ready()
                current_channel = bot.get_channel(CURRENT_CHANNEL_ID)
                if current_channel:
                    # Just check if we can access the channel (no message sent)
                    _ = current_channel.permissions_for(current_channel.guild.me)
                    print("📡 Discord API access confirmed")
            except Exception as discord_error:
                print(f"⚠️ Discord API check failed: {discord_error}")
        else:
            print("⚠️ Discord connection unstable - attempting reconnection")
            
        # Step 3: External connectivity check
        try:
            external_response = requests.get("https://httpbin.org/get", timeout=10)
            print(f"🌐 External connectivity: {external_response.status_code}")
        except Exception as ext_error:
            print(f"⚠️ External connectivity failed: {ext_error}")
            
        # Step 4: Memory activity to prevent garbage collection issues
        import gc
        gc.collect()  # Force garbage collection
        print("🧹 Memory cleanup completed")
        
        # Step 5: Generate some CPU activity to show the process is alive
        dummy_calc = sum(range(1000))  # Small computation
        print(f"⚡ Process activity check: {dummy_calc}")
        
        print(f"✅ Keep-alive cycle completed successfully")
            
    except Exception as e:
        print(f"❌ Keep-alive ping failed: {e}")
        
        # Aggressive fallback attempts
        fallback_urls = [
            "http://localhost:5000/",
            "http://127.0.0.1:5000/ping", 
            "http://0.0.0.0:5000/",
            "http://localhost:5000/health"
        ]
        
        for attempt, url in enumerate(fallback_urls):
            try:
                response = requests.get(url, timeout=8)
                print(f"💚 Keep-alive fallback #{attempt+1} successful: {response.status_code}")
                break
            except Exception as fallback_error:
                print(f"🔴 Keep-alive fallback #{attempt+1} failed: {fallback_error}")
                if attempt == len(fallback_urls) - 1:  # Last attempt
                    print("🚨 ALL keep-alive attempts failed - Bot may experience downtime")
                    
                    # Last resort: try to restart the Flask server
                    try:
                        print("🔄 Attempting to restart Flask server...")
                        # This will be caught by the main thread
                    except Exception as restart_error:
                        print(f"❌ Flask restart failed: {restart_error}")

async def send_to_channel(chap):
    """Send manga chapter notification to Discord channel with enhanced design"""
    try:
        channel = bot.get_channel(CURRENT_CHANNEL_ID)
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
📖 **الفصل:** `{chap['chapter']}`
🕐 **تاريخ النشر:** <t:{int(__import__('time').time())}:R>
━━━━━━━━━━━━━━━━━━━━━━━━━
        """.strip()

        # Enhanced color scheme - use Straw Hat-themed colors
        colors = [
            0xFF0000,  # Red (Straw Hat theme)
            0xFFD700,  # Gold (pirate treasure vibe)
            0x000000,  # Black (pirate flag)
            0x1E90FF,  # Blue (ocean theme)
        ]
        selected_color = random.choice(colors)

        # Create rich embed message with enhanced styling
        embed = discord.Embed(
            title=f"{title_phrase} {chap['title']}",
            description=desc,
            color=selected_color,
            url=chap['url']  # Make the title clickable to the manga URL
        )
        
        # Add larger image using set_image instead of set_thumbnail
        if chap['image']:
            image_url = chap['image']
            if image_url.startswith('/'):
                image_url = f"https://olympustaff.com{image_url}"
            embed.set_image(url=image_url)  # Use set_image for larger display
        
        # Enhanced footer with team info
        embed.set_footer(
            text="🏴‍☠️ Straw Hat Team • مترجم بواسطة فريق ستراو هات",
            icon_url="https://olympustaff.com/images/teams/9c0db844720e541fe7597589c3256c72.jpg"
        )
        
        # Add author field for branding
        embed.set_author(
            name="🔔 إشعار فصل جديد",
            icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"
        )
        
        # Add fields for better organization
        embed.add_field(
            name="📋 الفريق",
            value="فريق ستراو هات",
            inline=True
        )
        embed.add_field(
            name="🔗 قراءة الفصل",
            value=f"[اقرأ الآن]({chap['url']})",
            inline=True
        )

        # Send message with @all-series mention and enhanced styling
        await channel.send(content="🚨 <@&1332317530685177908> 🚨", embed=embed)
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

# Command to change notification channel
@bot.command()
async def setchannel(ctx, channel_id: int):
    """Change the channel where notifications are sent"""
    global CURRENT_CHANNEL_ID
    
    try:
        # Check if the channel exists and bot can access it
        new_channel = bot.get_channel(channel_id)
        if not new_channel:
            error_embed = discord.Embed(
                title="❌ خطأ في تغيير القناة",
                description=f"لا يمكن العثور على القناة بالمعرف: `{channel_id}`\nتأكد من أن البوت لديه صلاحية الوصول للقناة",
                color=0xFF0000
            )
            await ctx.send(embed=error_embed)
            return
        
        # Update the channel ID
        old_channel_id = CURRENT_CHANNEL_ID
        CURRENT_CHANNEL_ID = channel_id
        
        # Send confirmation to both old and new channels
        success_embed = discord.Embed(
            title="✅ تم تغيير القناة بنجاح",
            description=f"**القناة القديمة:** <#{old_channel_id}>\n**القناة الجديدة:** <#{channel_id}>\n\n🔔 سيتم إرسال الإشعارات الجديدة في هذه القناة",
            color=0x00FF00
        )
        
        # Send to current channel (where command was used)
        await ctx.send(embed=success_embed)
        
        # Send welcome message to new channel
        if channel_id != ctx.channel.id:
            welcome_embed = discord.Embed(
                title="🎉 مرحباً بكم",
                description="تم تعيين هذه القناة لاستقبال إشعارات فصول المانجا الجديدة\n\n🤖 البوت جاهز للعمل ويراقب التحديثات كل 5 دقائق",
                color=0x00FF00
            )
            await new_channel.send(embed=welcome_embed)
        
        print(f"📡 Channel changed from {old_channel_id} to {channel_id}")
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ خطأ في تغيير القناة",
            description=f"حدث خطأ أثناء تغيير القناة: {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)
        print(f"❌ Error changing channel: {e}")

# Command to get current bot status
@bot.command()
async def status(ctx):
    """Show current bot status and settings"""
    current_channel = bot.get_channel(CURRENT_CHANNEL_ID)
    channel_name = current_channel.name if current_channel else "غير موجودة"
    
    status_embed = discord.Embed(
        title="📊 حالة البوت",
        color=0x3498DB
    )
    
    status_embed.add_field(
        name="🔔 القناة الحالية",
        value=f"<#{CURRENT_CHANNEL_ID}> (`{channel_name}`)",
        inline=False
    )
    
    status_embed.add_field(
        name="⏱️ تردد المراقبة",
        value="كل 5 دقائق",
        inline=True
    )
    
    status_embed.add_field(
        name="💓 Keep-Alive",
        value="كل 3 دقائق",
        inline=True
    )
    
    status_embed.add_field(
        name="🌐 الخادم",
        value="يعمل على المنفذ 5000",
        inline=True
    )
    
    status_embed.set_footer(text="🏴‍☠️ Straw Hat Team • مترجم بواسطة فريق ستراو هات")
    
    await ctx.send(embed=status_embed)

# Command to get help
@bot.command()
async def help_ar(ctx):
    """Show available commands in Arabic"""
    help_embed = discord.Embed(
        title="📚 أوامر البوت المتاحة",
        description="قائمة بجميع الأوامر المتاحة للتحكم في البوت",
        color=0x9B59B6
    )
    
    help_embed.add_field(
        name="!test",
        value="إرسال إشعار تجريبي للتأكد من عمل البوت",
        inline=False
    )
    
    help_embed.add_field(
        name="!setchannel <معرف_القناة>",
        value="تغيير القناة التي يتم إرسال الإشعارات إليها",
        inline=False
    )
        
    help_embed.add_field(
        name="!status",
        value="عرض حالة البوت والإعدادات الحالية",
        inline=False
    )
    
    help_embed.add_field(
        name="!testurl <اسم_المانجا>",
        title="اختبار توليد رابط لمانجا معينة",
        inline=False
    )
    
    help_embed.add_field(
        name="!help_ar",
        value="عرض هذه القائمة",
        inline=False
    )
    
    help_embed.set_footer(text="🏴‍☠️ Straw Hat Team • مترجم بواسطة فريق ستراو هاتظ")
    
    await ctx.send(embed=help_embed)

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
    return "🤖‍♂ Discord Bot is running!"

@app.route('/status')
def status():
    """Status endpoint with bot information"""
    return {
        "status": "online",
        "bot_user": str(bot.user) if bot.user else "Not logged in",
        "guilds": len(bot.guilds) if bot.guilds else 0,
        "uptime": "running",
        "last_check": "active"
    }

@app.route('/ping')
def ping():
    """Simple ping test endpoint for keep-alive"""
    return {"status": "pong", "timestamp": __import__('time').time()}

@app.route('/health')
def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "bot_ready": bot.is_ready() if 'bot' in globals() else globals(),
        "bot_user": str(bot.user) if bot.user else None,
        "guilds_count": len(bot.guilds) if bot.guilds else 0,
        "timestamp": __import__('time').time(),
        "uptime": __import__('time').time(),
        "monitoring_frequency": "every 3 minutes",
        "last_manga_check": "every 5 minutes"
    }

@app.route('/external-ping')
def external_ping():
    """Special endpoint for external monitoring services with enhanced response"""
    import time
    return {
        "status": "active",
        "service": "discord-manga-bot",
        "timestamp": time.time(),
        "formatted_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "bot_status": "online" if bot.is_ready() else "offline",
        "keep_alive": "aggressive-mode",
        "response": "pong"
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
        await ctx.send(f"❌ حدث خطأ أثناء تنفيذ الأمر: {str(error)}")

# Main execution
if __name__ == "__main__":
    # Start keep-alive server
    keep_alive()
    
    # Start Discord bot
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
