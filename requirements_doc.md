# Telegram Monitoring Bot - Requirements Documentation

## Overview
This document outlines the requirements for a production-ready Telegram bot that monitors multiple sources for keyword mentions and sends formatted alerts to one or more Telegram channels.

## Functional Requirements

### 1. Sources to Monitor
1. **Reddit**
   - Monitor selected subreddits for keywords in posts and comments
   - Use Pushshift or PRAW for data access
   - No API key requirement specified

2. **Twitter (X)**
   - Monitor for keyword mentions
   - Use snscrape library
   - No API key required

3. **Telegram**
   - Monitor public channels for keyword mentions
   - Use Telethon library
   - Require Telegram API credentials

4. **News**
   - Monitor RSS feeds (e.g., Google News)
   - No API key required

### 2. Alert Format
When a keyword match is found, send an alert with the following format:
```
🔍 Source: [Source Name]
🕒 [Time] UTC
🧩 Match: "[matched keyword]"
📎 [Context information - subreddit, channel, etc.]
💬 "[Message content with match]"
🔗 [URL to original content]
```

### 3. Keyword Management
The bot must support the following Telegram commands for keyword management:
- `/keywords` — List all keywords
- `/add <word>` — Add a new keyword
- `/remove <word>` — Remove a keyword

All keywords must be stored in a persistent SQLite database and used across all source modules.

### 4. Telegram Channel Management
The bot must support dynamic management of monitored Telegram channels:
- `/channels` — List monitored channels
- `/add_channel <https://t.me/CHANNEL>` — Add and start monitoring
- `/remove_channel <https://t.me/CHANNEL>` — Remove from monitoring

The bot must subscribe via Telethon and scan messages from those channels. Channel list must be saved in SQLite.

### 5. Alert Channel Management
The bot must allow dynamic configuration of alert destinations:
- `/get_chat_id` — Returns current chat ID when typed in any group/channel
- `/set_alert_channel <id>` — Define the main alert channel
- `/add_alert_channel <id>` — Add additional channels
- `/remove_alert_channel <id>` — Remove one
- `/list_alert_channels` — List all configured alert channels

All alert channels must be saved persistently in SQLite.

### 6. Bot Behavior
- Admin-only commands: Only specific Telegram user IDs can execute commands
- Admin list should be configurable (default: only creator)
- `/status` — Show total keywords, channels, and active alert destinations
- `/ping` — Return "✅ Online"
- `/help` — List all commands

## Technical Requirements

### 1. Architecture
- Async Python 3
- Modular design with separate modules:
  - `reddit_watcher.py`
  - `twitter_watcher.py`
  - `telegram_watcher.py`
  - `news_watcher.py`
  - `notifier.py`
  - `command_handler.py`
  - `config.py`
- SQLite database for persistent storage
- Requirements.txt and README.md

### 2. Credentials
- Telegram bot token: `8183207624:AAE9-7JDZ7u_0WM0U9-fy4l8d4QDnwOlyi0`
- Telegram API ID: `23287022`
- Telegram API Hash: `1814d8ac60252e0f9fa600b06ca39dc6`

### 3. Deployment
- No deployment required
- Push full working code to GitHub repository: `https://github.com/PadreGreg/monitoring-bot`
- Code must be clean, modular, and production-ready

## Non-Functional Requirements
1. **Modularity**: The code should be organized into separate modules with clear responsibilities.
2. **Persistence**: All settings must be stored in SQLite for persistence across restarts.
3. **Security**: Admin-only commands must be restricted to authorized users.
4. **Reliability**: The bot should handle errors gracefully and continue operation.
5. **Maintainability**: Code should be well-documented and follow best practices.
