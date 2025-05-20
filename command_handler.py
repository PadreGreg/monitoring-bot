"""
Command handler module for the Telegram Monitoring Bot.
Handles all Telegram commands and admin controls.
"""

import asyncio
import logging
import re
from telethon import events, Button
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChatAdminRequiredError, ChannelPrivateError

from config import Config

logger = logging.getLogger(__name__)

class CommandHandler:
    """Handles all Telegram commands and admin controls."""
    
    def __init__(self, db_manager, client, watchers, notifier):
        """Initialize the command handler."""
        self.db_manager = db_manager
        self.client = client
        self.watchers = watchers
        self.notifier = notifier
        self.commands = {
            'start': self.cmd_start,
            'help': self.cmd_help,
            'ping': self.cmd_ping,
            'status': self.cmd_status,
            'keywords': self.cmd_keywords,
            'add': self.cmd_add_keyword,
            'remove': self.cmd_remove_keyword,
            'channels': self.cmd_channels,
            'add_channel': self.cmd_add_channel,
            'remove_channel': self.cmd_remove_channel,
            'get_chat_id': self.cmd_get_chat_id,
            'set_alert_channel': self.cmd_set_alert_channel,
            'add_alert_channel': self.cmd_add_alert_channel,
            'remove_alert_channel': self.cmd_remove_alert_channel,
            'list_alert_channels': self.cmd_list_alert_channels
        }
    
    async def register_handlers(self):
        """Register all command handlers."""
        @self.client.on(events.NewMessage(pattern=r'/([a-zA-Z0-9_]+)(@\w+)?(\s+.*)?'))
        async def handle_command(event):
            """Handle all commands."""
            # Extract command and arguments
            match = re.match(r'/([a-zA-Z0-9_]+)(@\w+)?(\s+.*)?', event.raw_text)
            if not match:
                return
            
            command = match.group(1).lower()
            args_str = match.group(3)
            args = args_str.strip() if args_str else ""
            
            # Check if command exists
            if command not in self.commands:
                return
            
            # Check if user is admin (except for get_chat_id and ping)
            if command not in ['get_chat_id', 'ping', 'start', 'help']:
                sender = await event.get_sender()
                if not await self.is_admin(sender.id):
                    await event.reply("⚠️ You are not authorized to use this command.")
                    return
            
            # Execute the command
            try:
                await self.commands[command](event, args)
            except Exception as e:
                logger.error(f"Error executing command /{command}: {e}")
                await event.reply(f"⚠️ Error: {str(e)}")
    
    async def is_admin(self, user_id):
        """Check if a user is an admin."""
        return await self.db_manager.is_admin(user_id)
    
    async def cmd_start(self, event, args):
        """Handle /start command."""
        sender = await event.get_sender()
        
        # Check if this is the first run
        creator_id = await self.db_manager.get_config("creator_id")
        if not creator_id:
            # Set the first user as creator and admin
            await self.db_manager.set_config("creator_id", str(sender.id))
            await self.db_manager.add_admin(
                sender.id,
                sender.username or "Unknown",
                sender.id
            )
            await event.reply(
                "🎉 Welcome to the Telegram Monitoring Bot!\n\n"
                "You have been set as the creator and admin of this bot.\n"
                "Use /help to see available commands."
            )
        else:
            await event.reply(
                "👋 Welcome to the Telegram Monitoring Bot!\n\n"
                "Use /help to see available commands."
            )
    
    async def cmd_help(self, event, args):
        """Handle /help command."""
        sender = await event.get_sender()
        is_admin = await self.is_admin(sender.id)
        
        basic_commands = (
            "📋 **Available Commands**:\n\n"
            "/ping — Check if bot is online\n"
            "/get_chat_id — Get the ID of the current chat\n"
            "/help — Show this help message\n"
        )
        
        admin_commands = (
            "\n🔐 **Admin Commands**:\n\n"
            "**Status**:\n"
            "/status — Show monitoring status\n\n"
            
            "**Keyword Management**:\n"
            "/keywords — List all monitored keywords\n"
            "/add <word> — Add a new keyword\n"
            "/remove <word> — Remove a keyword\n\n"
            
            "**Channel Management**:\n"
            "/channels — List monitored Telegram channels\n"
            "/add_channel <https://t.me/CHANNEL> — Add channel\n"
            "/remove_channel <https://t.me/CHANNEL> — Remove channel\n\n"
            
            "**Alert Destination Management**:\n"
            "/set_alert_channel <id> — Set primary alert channel\n"
            "/add_alert_channel <id> — Add additional alert channel\n"
            "/remove_alert_channel <id> — Remove alert channel\n"
            "/list_alert_channels — List all alert channels"
        )
        
        if is_admin:
            await event.reply(basic_commands + admin_commands)
        else:
            await event.reply(basic_commands)
    
    async def cmd_ping(self, event, args):
        """Handle /ping command."""
        await event.reply("✅ Online")
    
    async def cmd_status(self, event, args):
        """Handle /status command."""
        try:
            # Get counts
            keywords = await self.db_manager.get_all_keywords()
            channels = await self.db_manager.get_all_monitored_channels()
            alert_channels = await self.db_manager.get_all_alert_channels()
            
            # Format status message
            status = (
                "📊 **Bot Status**\n\n"
                f"🧩 Keywords: {len(keywords)}\n"
                f"📺 Monitored channels: {len(channels)}\n"
                f"🔔 Alert destinations: {len(alert_channels)}\n\n"
                f"🤖 Bot is running and monitoring all sources."
            )
            
            await event.reply(status)
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await event.reply(f"⚠️ Error getting status: {str(e)}")
    
    async def cmd_keywords(self, event, args):
        """Handle /keywords command."""
        try:
            keywords = await self.db_manager.get_all_keywords()
            
            if not keywords:
                await event.reply("No keywords configured yet. Add some with /add <keyword>")
                return
            
            # Format keywords list
            keywords_list = "\n".join([f"• {keyword}" for keyword in keywords])
            message = f"🧩 **Monitored Keywords** ({len(keywords)}):\n\n{keywords_list}"
            
            await event.reply(message)
        except Exception as e:
            logger.error(f"Error in keywords command: {e}")
            await event.reply(f"⚠️ Error getting keywords: {str(e)}")
    
    async def cmd_add_keyword(self, event, args):
        """Handle /add command to add a keyword."""
        if not args:
            await event.reply("⚠️ Please specify a keyword to add: /add <keyword>")
            return
        
        try:
            sender = await event.get_sender()
            keyword = args.strip()
            
            result = await self.db_manager.add_keyword(keyword, sender.id)
            
            if result:
                await event.reply(f"✅ Added keyword: **{keyword}**")
            else:
                await event.reply(f"⚠️ Keyword already exists: **{keyword}**")
        except Exception as e:
            logger.error(f"Error adding keyword: {e}")
            await event.reply(f"⚠️ Error adding keyword: {str(e)}")
    
    async def cmd_remove_keyword(self, event, args):
        """Handle /remove command to remove a keyword."""
        if not args:
            await event.reply("⚠️ Please specify a keyword to remove: /remove <keyword>")
            return
        
        try:
            keyword = args.strip()
            
            result = await self.db_manager.remove_keyword(keyword)
            
            if result:
                await event.reply(f"✅ Removed keyword: **{keyword}**")
            else:
                await event.reply(f"⚠️ Keyword not found: **{keyword}**")
        except Exception as e:
            logger.error(f"Error removing keyword: {e}")
            await event.reply(f"⚠️ Error removing keyword: {str(e)}")
    
    async def cmd_channels(self, event, args):
        """Handle /channels command to list monitored Telegram channels."""
        try:
            channels = await self.db_manager.get_all_monitored_channels()
            
            if not channels:
                await event.reply("No channels configured yet. Add some with /add_channel <url>")
                return
            
            # Format channels list
            channels_list = "\n".join([f"• {channel['channel_name']} - {channel['channel_url']}" for channel in channels])
            message = f"📺 **Monitored Channels** ({len(channels)}):\n\n{channels_list}"
            
            await event.reply(message)
        except Exception as e:
            logger.error(f"Error in channels command: {e}")
            await event.reply(f"⚠️ Error getting channels: {str(e)}")
    
    async def cmd_add_channel(self, event, args):
        """Handle /add_channel command to add a Telegram channel."""
        if not args:
            await event.reply("⚠️ Please specify a channel URL: /add_channel <https://t.me/CHANNEL>")
            return
        
        try:
            sender = await event.get_sender()
            channel_url = args.strip()
            
            # Validate URL format
            if not re.match(r'https?://t\.me/[a-zA-Z0-9_]+', channel_url):
                await event.reply("⚠️ Invalid channel URL format. Use https://t.me/CHANNEL")
                return
            
            # Add the channel
            result = await self.watchers['telegram'].add_channel(channel_url)
            
            if result:
                await event.reply(f"✅ Added channel: {channel_url}")
            else:
                await event.reply(f"⚠️ Failed to add channel: {channel_url}")
        except Exception as e:
            logger.error(f"Error adding channel: {e}")
            await event.reply(f"⚠️ Error adding channel: {str(e)}")
    
    async def cmd_remove_channel(self, event, args):
        """Handle /remove_channel command to remove a Telegram channel."""
        if not args:
            await event.reply("⚠️ Please specify a channel URL: /remove_channel <https://t.me/CHANNEL>")
            return
        
        try:
            channel_url = args.strip()
            
            # Remove the channel
            result = await self.watchers['telegram'].remove_channel(channel_url)
            
            if result:
                await event.reply(f"✅ Removed channel: {channel_url}")
            else:
                await event.reply(f"⚠️ Failed to remove channel: {channel_url}")
        except Exception as e:
            logger.error(f"Error removing channel: {e}")
            await event.reply(f"⚠️ Error removing channel: {str(e)}")
    
    async def cmd_get_chat_id(self, event, args):
        """Handle /get_chat_id command to get the current chat ID."""
        try:
            chat = await event.get_chat()
            await event.reply(f"🆔 Chat ID: `{chat.id}`")
        except Exception as e:
            logger.error(f"Error getting chat ID: {e}")
            await event.reply(f"⚠️ Error getting chat ID: {str(e)}")
    
    async def cmd_set_alert_channel(self, event, args):
        """Handle /set_alert_channel command to set the primary alert channel."""
        if not args:
            await event.reply("⚠️ Please specify a channel ID: /set_alert_channel <id>")
            return
        
        try:
            sender = await event.get_sender()
            channel_id = int(args.strip())
            
            result = await self.db_manager.add_alert_channel(channel_id, True, sender.id)
            
            if result:
                await event.reply(f"✅ Set primary alert channel: {channel_id}")
                
                # Send a test message to the channel
                await self.notifier.send_message(
                    channel_id,
                    "✅ This channel has been set as the primary alert channel."
                )
            else:
                await event.reply(f"✅ Updated primary alert channel: {channel_id}")
                
                # Send a test message to the channel
                await self.notifier.send_message(
                    channel_id,
                    "✅ This channel has been updated as the primary alert channel."
                )
        except ValueError:
            await event.reply("⚠️ Invalid channel ID. Please use a numeric ID.")
        except Exception as e:
            logger.error(f"Error setting alert channel: {e}")
            await event.reply(f"⚠️ Error setting alert channel: {str(e)}")
    
    async def cmd_add_alert_channel(self, event, args):
        """Handle /add_alert_channel command to add an additional alert channel."""
        if not args:
            await event.reply("⚠️ Please specify a channel ID: /add_alert_channel <id>")
            return
        
        try:
            sender = await event.get_sender()
            channel_id = int(args.strip())
            
            result = await self.db_manager.add_alert_channel(channel_id, False, sender.id)
            
            if result:
                await event.reply(f"✅ Added alert channel: {channel_id}")
                
                # Send a test message to the channel
                await self.notifier.send_message(
                    channel_id,
                    "✅ This channel has been added as an alert channel."
                )
            else:
                await event.reply(f"⚠️ Alert channel already exists: {channel_id}")
        except ValueError:
            await event.reply("⚠️ Invalid channel ID. Please use a numeric ID.")
        except Exception as e:
            logger.error(f"Error adding alert channel: {e}")
            await event.reply(f"⚠️ Error adding alert channel: {str(e)}")
    
    async def cmd_remove_alert_channel(self, event, args):
        """Handle /remove_alert_channel command to remove an alert channel."""
        if not args:
            await event.reply("⚠️ Please specify a channel ID: /remove_alert_channel <id>")
            return
        
        try:
            channel_id = int(args.strip())
            
            result = await self.db_manager.remove_alert_channel(channel_id)
            
            if result:
                await event.reply(f"✅ Removed alert channel: {channel_id}")
            else:
                await event.reply(f"⚠️ Failed to remove alert channel: {channel_id}")
        except ValueError:
            await event.reply("⚠️ Invalid channel ID. Please use a numeric ID.")
        except Exception as e:
            logger.error(f"Error removing alert channel: {e}")
            await event.reply(f"⚠️ Error removing alert channel: {str(e)}")
    
    async def cmd_list_alert_channels(self, event, args):
        """Handle /list_alert_channels command to list all alert channels."""
        try:
            channels = await self.db_manager.get_all_alert_channels()
            
            if not channels:
                await event.reply("No alert channels configured yet. Add some with /set_alert_channel <id> or /add_alert_channel <id>")
 
(Content truncated due to size limit. Use line ranges to read in chunks)