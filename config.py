"""
Configuration module for the Telegram Monitoring Bot.
Contains all configurable parameters and settings.
"""

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
    
    # Alert formatting
    ALERT_TEMPLATE = """
🔍 Source: {source}
🕒 {time} UTC
🧩 Match: "{keyword}"
📎 {context}
💬 "{content}"
🔗 {url}
"""
