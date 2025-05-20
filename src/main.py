"""
Main application module for the Telegram Monitoring Bot.
Integrates all components and manages the event loop.
"""

import asyncio
import logging
import sys
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import Config
from db_manager import DatabaseManager
from notifier import Notifier
from reddit_watcher import RedditWatcher
from twitter_watcher import TwitterWatcher
from telegram_watcher import TelegramWatcher
from news_watcher import NewsWatcher
from command_handler import CommandHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting Telegram Monitoring Bot")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        await db_manager.init_db()
        logger.info("Database initialized")
        
        # Initialize Telegram client
        client = TelegramClient(
            StringSession(),
            Config.API_ID,
            Config.API_HASH
        )
        await client.start(bot_token=Config.BOT_TOKEN)
        logger.info("Telegram client started")
        
        # Get bot info
        me = await client.get_me()
        logger.info(f"Bot started as @{me.username} ({me.id})")
        
        # Initialize notifier
        notifier = Notifier(db_manager, client)
        logger.info("Notifier initialized")
        
        # Initialize watchers
        reddit_watcher = RedditWatcher(db_manager, notifier)
        twitter_watcher = TwitterWatcher(db_manager, notifier)
        telegram_watcher = TelegramWatcher(db_manager, notifier, client)
        news_watcher = NewsWatcher(db_manager, notifier)
        logger.info("Watchers initialized")
        
        # Initialize command handler
        watchers = {
            "reddit": reddit_watcher,
            "twitter": twitter_watcher,
            "telegram": telegram_watcher,
            "news": news_watcher
        }
        command_handler = CommandHandler(db_manager, client, watchers, notifier)
        await command_handler.register_handlers()
        logger.info("Command handlers registered")
        
        # Start all watchers
        await reddit_watcher.start()
        await twitter_watcher.start()
        await telegram_watcher.start()
        await news_watcher.start()
        logger.info("All watchers started")
        
        # Run the bot until disconnected
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        await client.run_until_disconnected()
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main application: {e}")
    finally:
        # Stop all watchers
        if 'reddit_watcher' in locals():
            await reddit_watcher.stop()
        if 'twitter_watcher' in locals():
            await twitter_watcher.stop()
        if 'telegram_watcher' in locals():
            await telegram_watcher.stop()
        if 'news_watcher' in locals():
            await news_watcher.stop()
        
        # Close database connection
        if 'db_manager' in locals():
            await db_manager.close()
        
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
