#!/usr/bin/env python3
"""
External monitoring service for Discord bot
This script can be run separately or used by external monitoring services
"""

import requests
import time
import threading
import schedule
from datetime import datetime

class BotMonitor:
    def __init__(self, bot_url="http://localhost:5000"):
        self.bot_url = bot_url
        self.ping_interval = 2  # minutes
        self.is_running = False
        
    def ping_bot(self):
        """Ping the bot to keep it alive"""
        try:
            response = requests.get(f"{self.bot_url}/ping", timeout=10)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if response.status_code == 200:
                print(f"[{timestamp}] ✅ Bot ping successful")
                return True
            else:
                print(f"[{timestamp}] ⚠️ Bot ping returned {response.status_code}")
                return False
                
        except requests.RequestException as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ❌ Bot ping failed: {e}")
            
            # Try alternative endpoints
            for endpoint in ["/health", "/status", "/"]:
                try:
                    response = requests.get(f"{self.bot_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        print(f"[{timestamp}] 🔄 Alternative endpoint {endpoint} successful")
                        return True
                except:
                    continue
                    
            return False
    
    def check_bot_health(self):
        """Check detailed bot health"""
        try:
            response = requests.get(f"{self.bot_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                timestamp = datetime.now().strftime("%H:%M:%S")
                bot_ready = data.get('bot_ready', False)
                guilds_count = data.get('guilds_count', 0)
                
                print(f"[{timestamp}] 📊 Health Check - Ready: {bot_ready}, Guilds: {guilds_count}")
                return bot_ready
            else:
                print(f"[{timestamp}] ⚠️ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ❌ Health check error: {e}")
            return False
    
    def start_monitoring(self):
        """Start the monitoring service"""
        print("🚀 Starting external bot monitoring service...")
        print(f"📡 Monitoring URL: {self.bot_url}")
        print(f"⏱️ Ping interval: {self.ping_interval} minutes")
        
        # Schedule regular pings
        schedule.every(self.ping_interval).minutes.do(self.ping_bot)
        schedule.every(5).minutes.do(self.check_bot_health)
        
        self.is_running = True
        
        # Initial ping
        self.ping_bot()
        self.check_bot_health()
        
        # Run monitoring loop
        while self.is_running:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.is_running = False
        print("🛑 Monitoring service stopped")

def create_uptime_config():
    """Create a configuration file for external uptime monitoring services"""
    config = {
        "urls_to_monitor": [
            "http://localhost:5000/ping",
            "http://localhost:5000/health",
            "http://localhost:5000/status"
        ],
        "check_interval": "2 minutes",
        "timeout": "10 seconds",
        "description": "Discord Manga Bot Keep-Alive Service"
    }
    
    import json
    with open("uptime_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("📄 Created uptime_config.json for external monitoring services")

if __name__ == "__main__":
    # Create uptime configuration
    create_uptime_config()
    
    # Start monitoring
    monitor = BotMonitor()
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("👋 External monitoring service terminated")
