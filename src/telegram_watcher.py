"""
Telegram watcher module for the Telegram Monitoring Bot.
Monitors Telegram channels for keyword matches using Telethon.
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import ChannelPrivateError, ChannelInvalidError

from watcher_base import WatcherBase
from config import Config

logger = logging.getLogger(__name__)

class TelegramWatcher(WatcherBase):
    """Monitors Telegram channels for keyword matches using Telethon."""
    
    def __init__(self, db_manager, notifier, client=None):
        """Initialize the Telegram watcher."""
        super().__init__(db_manager, notifier, name="TelegramWatcher")
        self.client = client
        self.realtime = Config.TELEGRAM_REALTIME
        self.monitored_channels = {}  # {channel_url: channel_entity}
    
    async def _monitor_source(self):
        """Monitor Telegram channels for keyword matches."""
        logger.info("Starting Telegram monitoring")
        
        if not self.client:
            logger.error("Telegram client not provided")
            return
        
        try:
            # Load monitored channels from database
            channels = await self.db_manager.get_all_monitored_channels()
            for channel in channels:
                await self.add_channel(channel["channel_url"])
            
            # Register event handler for new messages
            if self.realtime:
                @self.client.on(events.NewMessage())
                async def handler(event):
                    # Check if the message is from a monitored channel
                    if hasattr(event.chat, 'username'):
                        chat_username = event.chat.username
                        for url, entity in self.monitored_channels.items():
                            if chat_username and chat_username.lower() in url.lower():
                                await self.handle_new_message(event)
                                break
            
            # Keep the task running
            while self.running:
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error in Telegram monitoring: {e}")
        finally:
            logger.info("Telegram monitoring stopped")
    
    async def add_channel(self, channel_url):
        """Add a channel to the monitoring list."""
        try:
            if channel_url in self.monitored_channels:
                logger.warning(f"Channel already monitored: {channel_url}")
                return False
            
            # Extract channel username from URL
            match = re.search(r't\.me/([^/]+)', channel_url)
            if not match:
                logger.error(f"Invalid channel URL: {channel_url}")
                return False
            
            channel_username = match.group(1)
            
            # Join the channel
            try:
                entity = await self.client.get_entity(channel_username)
                await self.client(JoinChannelRequest(entity))
                
                # Store the channel entity
                self.monitored_channels[channel_url] = entity
                
                # Get channel info
                channel_id = entity.id
                channel_name = entity.title if hasattr(entity, 'title') else channel_username
                
                # Add to database if not already there
                await self.db_manager.add_monitored_channel(
                    channel_id, 
                    channel_url, 
                    channel_name, 
                    0  # Added by system
                )
                
                logger.info(f"Added Telegram channel: {channel_name} ({channel_url})")
                return True
            
            except (ChannelPrivateError, ChannelInvalidError) as e:
                logger.error(f"Cannot join channel {channel_url}: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Error adding Telegram channel {channel_url}: {e}")
            return False
    
    async def remove_channel(self, channel_url):
        """Remove a channel from the monitoring list."""
        try:
            if channel_url not in self.monitored_channels:
                logger.warning(f"Channel not monitored: {channel_url}")
                return False
            
            # Remove from local cache
            del self.monitored_channels[channel_url]
            
            # Remove from database
            await self.db_manager.remove_monitored_channel(channel_url)
            
            logger.info(f"Removed Telegram channel: {channel_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing Telegram channel {channel_url}: {e}")
            return False
    
    async def handle_new_message(self, event):
        """Handle a new message from a monitored channel."""
        try:
            # Get message text
            if not event.message or not event.message.text:
                return
            
            message_text = event.message.text
            
            # Get channel info
            chat = await event.get_chat()
            chat_title = chat.title if hasattr(chat, 'title') else chat.username
            
            # Prepare source info
            source_info = {
                "source": "Telegram",
                "time": datetime.now(timezone.utc).strftime("%H:%M"),
                "context": chat_title,
                "url": f"https://t.me/{chat.username}/{event.message.id}" if hasattr(chat, 'username') else "N/A"
            }
            
            # Check for keywords
            match_info = await self.check_for_keywords(message_text, source_info)
            if match_info:
                await self.notifier.send_alert(match_info)
                
        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}")
    
    async def get_monitored_channels(self):
        """Get the list of monitored channels."""
        return list(self.monitored_channels.keys())
