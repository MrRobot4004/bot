# Discord Manga Chapter Notification Bot

## Overview

This is a Discord bot designed to monitor manga releases from the Olympus Staff website and automatically notify users in a specified Discord channel when new chapters are published. The bot scrapes the team's release page, tracks previously seen chapters, and sends notifications in Arabic with custom links to specific manga titles.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture
- **Bot Framework**: Discord.py library for Discord API integration
- **Web Scraping**: BeautifulSoup4 for parsing HTML content from the manga website
- **Data Persistence**: JSON file-based storage for tracking seen chapters
- **Task Scheduling**: Discord.py's task loop system for periodic checks
- **Web Server**: Flask integration (imported but not implemented) for potential web interface

### Programming Language
- **Python**: Main language chosen for its excellent Discord bot libraries and web scraping capabilities

## Key Components

### 1. Discord Bot Core (`bot.py`)
- **Purpose**: Main bot logic and Discord API interaction
- **Key Features**:
  - Command prefix: "!" 
  - All Discord intents enabled for full functionality
  - Environment variable configuration for security

### 2. Manga Monitoring System
- **Custom Manga Links**: Hardcoded mapping of manga titles to their specific URLs
- **Supported Titles**:
  - "Devil Summoner, I Am the Abyss Lord"
  - "One Hundred Thousand Years of Tribulation by Heavenly Thunder" 
  - "Playing the Perfect Fox-Eyed Villain"

### 3. Chapter Tracking System
- **Storage**: `last_seen.json` file for persistence
- **Functions**:
  - `load_seen()`: Loads previously seen chapters from JSON
  - `save_seen()`: Saves current seen chapters to JSON
- **Error Handling**: Graceful fallback to empty list if file doesn't exist

### 4. Notification System
- **Arabic Messages**: Random selection from predefined Arabic phrases
- **Message Variety**: 5 different notification messages to avoid repetition

## Data Flow

1. **Initialization**: Bot loads previously seen chapters from JSON file
2. **Monitoring**: Periodic scraping of Olympus Staff team page
3. **Comparison**: New chapters identified by comparing against seen list
4. **Notification**: Discord message sent to configured channel
5. **Persistence**: Updated seen list saved to JSON file

## External Dependencies

### Python Packages (requirements.txt)
- **discord.py**: Discord API wrapper for bot functionality
- **beautifulsoup4**: HTML parsing for web scraping
- **requests**: HTTP client for web requests
- **flask**: Web framework (imported but not actively used)

### External Services
- **Discord API**: For bot functionality and message sending
- **Olympus Staff Website**: Source for manga chapter data
- **Target URL**: `https://olympustaff.com/team/straw-hat`

## Deployment Strategy

### Environment Configuration
- **TOKEN**: Discord bot token (with fallback value provided)
- **CHANNEL_ID**: Target Discord channel ID (with fallback value)

### Security Considerations
- Environment variables used for sensitive data
- Fallback values present (should be removed in production)

### Current State  
- **Fully Functional**: The bot is now completely operational and successfully monitoring manga updates
- **Fixed Web Scraping**: Updated to use AJAX endpoint (`/ajax/get-manga-lastChapter/44`) instead of static HTML parsing
- **Recent Success**: July 25, 2025 - Bot successfully detected and sent notifications for 50+ new chapters
- **Active Components**:
  - Automatic chapter monitoring every 5 minutes
  - Discord message sending with Arabic notifications
  - Chapter tracking and persistence system
  - Flask keep-alive server on port 5000

### Deployment Requirements
- Python environment with required packages
- Discord bot token and permissions
- Target Discord channel access
- File system write permissions for JSON storage

## Development Notes

The bot is currently in an incomplete state with the core infrastructure established but missing the main functionality loop. The architecture supports:
- Scalable manga tracking (easy to add new titles)
- Robust error handling for file operations
- Internationalization (Arabic messages)
- Modular design for easy maintenance

The Flask import suggests potential future web interface capabilities, though not currently implemented.