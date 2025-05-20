"""
Notifier module for the Telegram Monitoring Bot.
Handles formatting and sending alerts to configured Telegram channels.
"""

import asyncio
import logging
from datetime import datetime, timezone
import html

from config import Config

logger = logging.getLogger(__name__)

class Notifier:
    """Handles formatting and sending alerts to configured Telegram channels."""
    
    def __init__(self, db_manager, client):
        """Initialize the notifier with database manager and Telegram client."""
        self.db_manager = db_manager
        self.client = client
        self.alert_template = Config.ALERT_TEMPLATE
    
    async def send_alert(self, match_info):
        """Format and send an alert to all configured channels."""
        try:
            # Format the alert message
            message = await self.format_alert(match_info)
            
            # Get all alert channels
            channels = await self.db_manager.get_all_alert_channels()
            
            if not channels:
                logger.warning("No alert channels configured, alert not sent")
                return False
            
            # Send to all channels
            for channel in channels:
                await self.send_message(channel["channel_id"], message)
            
            logger.info(f"Alert sent to {len(channels)} channels")
            return True
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    async def format_alert(self, match_info):
        """Format an alert message according to the template."""
        try:
            # Ensure all required fields are present
            required_fields = ["source", "time", "keyword", "context", "content", "url"]
            for field in required_fields:
                if field not in match_info:
                    match_info[field] = "N/A"
            
            # Escape HTML in content
            match_info["content"] = html.escape(match_info["content"])
            match_info["keyword"] = html.escape(match_info["keyword"])
            
            # Format the message using the template
            message = self.alert_template.format(
                source=match_info["source"],
                time=match_info["time"],
                keyword=match_info["keyword"],
                context=match_info["context"],
                content=match_info["content"],
                url=match_info["url"]
            )
            
            return message.strip()
            
        except Exception as e:
            logger.error(f"Error formatting alert: {e}")
            return f"⚠️ Alert formatting error: {e}"
    
    async def send_message(self, chat_id, message, parse_mode="html"):
        """Send a message to a Telegram chat."""
        try:
            await self.client.send_message(
                chat_id,
                message,
                parse_mode=parse_mode,
                link_preview=False
            )
            return True
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False
    
    async def send_status_message(self, chat_id, message):
        """Send a status message to a Telegram chat."""
        try:
            await self.client.send_message(
                chat_id,
                message,
                parse_mode="html"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending status message to {chat_id}: {e}")
            return False
