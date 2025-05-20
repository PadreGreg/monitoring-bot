# Telegram Monitoring Bot

A production-ready Telegram bot that monitors multiple sources for keyword mentions and sends formatted alerts to one or more Telegram channels.

## Features

- **Multi-Source Monitoring**: Monitor Reddit, Twitter, Telegram channels, and RSS news feeds
- **Keyword Management**: Add, remove, and list keywords via Telegram commands
- **Channel Management**: Dynamically add and remove Telegram channels to monitor
- **Alert Destinations**: Configure multiple Telegram channels to receive alerts
- **Admin Controls**: All commands are restricted to authorized admin users
- **Persistent Storage**: All settings are stored in SQLite database

## Monitored Sources

1. **Reddit** - Monitors selected subreddits for keywords in posts and comments using Pushshift API
2. **Twitter (X)** - Monitors for keyword mentions using snscrape (no API key required)
3. **Telegram** - Monitors public channels for keyword mentions using Telethon
4. **News** - Monitors RSS feeds (e.g., Google News) for keyword mentions

## Alert Format

When a keyword match is found, the bot sends an alert with the following format:

```
🔍 Source: Reddit
🕒 12:04 UTC
🧩 Match: "crypto processing"
📎 r/cryptocurrency
💬 "What are the best crypto processing platforms for B2B payouts?"
🔗 https://reddit.com/...
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/PadreGreg/monitoring-bot.git
   cd monitoring-bot
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure the bot:
   - The bot comes pre-configured with the provided credentials
   - You can modify `src/config.py` if needed

4. Run the bot:
   ```
   cd src
   python main.py
   ```

## Commands

### Basic Commands

- `/ping` — Check if the bot is online (returns "✅ Online")
- `/get_chat_id` — Get the ID of the current chat
- `/help` — Show help message with all available commands

### Admin Commands

#### Status

- `/status` — Show total keywords, channels, and active alert destinations

#### Keyword Management

- `/keywords` — List all monitored keywords
- `/add <word>` — Add a new keyword
- `/remove <word>` — Remove a keyword

#### Channel Management

- `/channels` — List monitored Telegram channels
- `/add_channel <https://t.me/CHANNEL>` — Add and start monitoring a channel
- `/remove_channel <https://t.me/CHANNEL>` — Remove a channel from monitoring

#### Alert Channel Management

- `/set_alert_channel <id>` — Define the main alert channel
- `/add_alert_channel <id>` — Add additional alert channel
- `/remove_alert_channel <id>` — Remove an alert channel
- `/list_alert_channels` — List all configured alert channels

## Architecture

The bot is built with a modular, async Python architecture:

- **Database Manager**: Handles all database operations
- **Watcher Modules**: Monitor different sources for keyword matches
  - `reddit_watcher.py`
  - `twitter_watcher.py`
  - `telegram_watcher.py`
  - `news_watcher.py`
- **Notifier**: Formats and sends alerts to configured Telegram channels
- **Command Handler**: Processes Telegram commands from admin users
- **Main Application**: Orchestrates all components and manages the event loop

## First-Time Setup

When you first run the bot:

1. Start a chat with your bot on Telegram
2. Send the `/start` command
3. The first user to do this will be set as the creator and admin
4. Use `/set_alert_channel <id>` to configure where alerts should be sent
   - You can get the chat ID by adding the bot to a group/channel and using `/get_chat_id`
5. Add keywords with `/add <keyword>`
6. Add Telegram channels to monitor with `/add_channel <https://t.me/CHANNEL>`

## Admin Management

By default, only the creator (first user) is an admin. Admin management is handled internally in the database.

## Dependencies

- Python 3.7+
- aiohttp
- aiosqlite
- feedparser
- snscrape
- telethon
- python-dateutil

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses Telethon for Telegram API interaction
- Uses snscrape for Twitter monitoring without API keys
- Uses Pushshift API for Reddit monitoring
