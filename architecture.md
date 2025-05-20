# Telegram Monitoring Bot - Architecture Design

## System Architecture Overview

The monitoring bot is designed as a modular, asynchronous Python application with the following high-level components:

1. **Main Application** - Orchestrates all components and manages the event loop
2. **Database Manager** - Handles all database operations
3. **Watcher Modules** - Monitor different sources for keyword matches
4. **Notifier** - Formats and sends alerts to configured Telegram channels
5. **Command Handler** - Processes Telegram commands from admin users

```
┌─────────────────────────────────────────────────────────────┐
│                      Main Application                        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Command     │  │ Database    │  │ Notifier            │  │
│  │ Handler     │  │ Manager     │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────┐ │
│  │ Reddit      │  │ Twitter     │  │ Telegram    │  │ News │ │
│  │ Watcher     │  │ Watcher     │  │ Watcher     │  │ Wtchr│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

The SQLite database will have the following tables:

1. **Keywords**
   - id (INTEGER PRIMARY KEY)
   - keyword (TEXT, UNIQUE)
   - added_by (INTEGER) - Telegram user ID
   - added_at (TIMESTAMP)

2. **MonitoredChannels**
   - id (INTEGER PRIMARY KEY)
   - channel_id (INTEGER)
   - channel_url (TEXT)
   - channel_name (TEXT)
   - added_by (INTEGER) - Telegram user ID
   - added_at (TIMESTAMP)

3. **AlertChannels**
   - id (INTEGER PRIMARY KEY)
   - channel_id (INTEGER, UNIQUE)
   - is_primary (BOOLEAN)
   - added_by (INTEGER) - Telegram user ID
   - added_at (TIMESTAMP)

4. **Admins**
   - id (INTEGER PRIMARY KEY)
   - user_id (INTEGER, UNIQUE)
   - username (TEXT)
   - added_by (INTEGER) - Telegram user ID
   - added_at (TIMESTAMP)

5. **Config**
   - key (TEXT PRIMARY KEY)
   - value (TEXT)

## Module Interfaces

### 1. Database Manager (`db_manager.py`)

```python
class DatabaseManager:
    async def init_db()
    async def add_keyword(keyword, added_by)
    async def remove_keyword(keyword)
    async def get_all_keywords()
    async def add_monitored_channel(channel_id, channel_url, channel_name, added_by)
    async def remove_monitored_channel(channel_url)
    async def get_all_monitored_channels()
    async def add_alert_channel(channel_id, is_primary, added_by)
    async def remove_alert_channel(channel_id)
    async def get_all_alert_channels()
    async def get_primary_alert_channel()
    async def add_admin(user_id, username, added_by)
    async def remove_admin(user_id)
    async def is_admin(user_id)
    async def get_all_admins()
    async def get_config(key, default=None)
    async def set_config(key, value)
```

### 2. Config Manager (`config.py`)

```python
class Config:
    # Telegram API credentials
    BOT_TOKEN = "8183207624:AAE9-7JDZ7u_0WM0U9-fy4l8d4QDnwOlyi0"
    API_ID = 23287022
    API_HASH = "1814d8ac60252e0f9fa600b06ca39dc6"
    
    # Database settings
    DB_PATH = "bot_data.db"
    
    # Monitoring settings
    REDDIT_CHECK_INTERVAL = 300  # seconds
    TWITTER_CHECK_INTERVAL = 300  # seconds
    NEWS_CHECK_INTERVAL = 600  # seconds
    TELEGRAM_REALTIME = True
    
    # Default admin (bot creator)
    CREATOR_ID = None  # To be set on first run
```

### 3. Watcher Base Class (`watcher_base.py`)

```python
class WatcherBase:
    def __init__(self, db_manager, notifier)
    async def start()
    async def stop()
    async def check_for_keywords(content, keywords, source_info)
    async def _monitor_source()  # To be implemented by subclasses
```

### 4. Reddit Watcher (`reddit_watcher.py`)

```python
class RedditWatcher(WatcherBase):
    async def _monitor_source()
    async def check_subreddit(subreddit, keywords)
    async def get_new_posts(subreddit)
    async def get_new_comments(subreddit)
```

### 5. Twitter Watcher (`twitter_watcher.py`)

```python
class TwitterWatcher(WatcherBase):
    async def _monitor_source()
    async def search_tweets(keywords)
```

### 6. Telegram Watcher (`telegram_watcher.py`)

```python
class TelegramWatcher(WatcherBase):
    async def _monitor_source()
    async def add_channel(channel_url)
    async def remove_channel(channel_url)
    async def handle_new_message(event)
```

### 7. News Watcher (`news_watcher.py`)

```python
class NewsWatcher(WatcherBase):
    async def _monitor_source()
    async def fetch_rss_feeds()
    async def parse_feed_entries(feed)
```

### 8. Notifier (`notifier.py`)

```python
class Notifier:
    def __init__(self, db_manager, bot)
    async def send_alert(match_info)
    async def format_alert(match_info)
    async def send_message(chat_id, message, parse_mode="HTML")
```

### 9. Command Handler (`command_handler.py`)

```python
class CommandHandler:
    def __init__(self, db_manager, bot, watchers, notifier)
    async def register_handlers()
    async def cmd_start(event)
    async def cmd_help(event)
    async def cmd_ping(event)
    async def cmd_status(event)
    async def cmd_keywords(event)
    async def cmd_add_keyword(event)
    async def cmd_remove_keyword(event)
    async def cmd_channels(event)
    async def cmd_add_channel(event)
    async def cmd_remove_channel(event)
    async def cmd_get_chat_id(event)
    async def cmd_set_alert_channel(event)
    async def cmd_add_alert_channel(event)
    async def cmd_remove_alert_channel(event)
    async def cmd_list_alert_channels(event)
    async def is_admin(user_id)
```

### 10. Main Application (`main.py`)

```python
async def main():
    # Initialize components
    db_manager = DatabaseManager()
    await db_manager.init_db()
    
    # Initialize Telegram client
    bot = TelegramClient(...)
    
    # Initialize notifier
    notifier = Notifier(db_manager, bot)
    
    # Initialize watchers
    reddit_watcher = RedditWatcher(db_manager, notifier)
    twitter_watcher = TwitterWatcher(db_manager, notifier)
    telegram_watcher = TelegramWatcher(db_manager, notifier, bot)
    news_watcher = NewsWatcher(db_manager, notifier)
    
    # Initialize command handler
    watchers = {
        "reddit": reddit_watcher,
        "twitter": twitter_watcher,
        "telegram": telegram_watcher,
        "news": news_watcher
    }
    command_handler = CommandHandler(db_manager, bot, watchers, notifier)
    
    # Start all components
    await command_handler.register_handlers()
    await reddit_watcher.start()
    await twitter_watcher.start()
    await telegram_watcher.start()
    await news_watcher.start()
    
    # Run the bot
    await bot.run_until_disconnected()
```

## Async Workflow

The application uses asyncio for concurrent operations:

1. The main event loop runs the Telegram client
2. Each watcher module runs its monitoring tasks on separate intervals
3. The Telegram watcher listens for new messages in real-time
4. Command handlers process admin commands as they arrive
5. The notifier sends alerts to all configured channels when matches are found

## Error Handling Strategy

1. Each module implements its own error handling
2. Critical errors are logged and reported to the primary admin
3. Non-critical errors are logged but don't interrupt the bot's operation
4. Watchers implement retry mechanisms with exponential backoff

## Deployment Considerations

1. The application is designed to run as a long-running process
2. All settings are persisted in SQLite for restart resilience
3. Logging is configured for production use
4. The code follows best practices for maintainability and readability
