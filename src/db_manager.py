"""
Database manager module for the Telegram Monitoring Bot.
Handles all database operations and provides an interface for other modules.
"""

import aiosqlite
import asyncio
import logging
import time
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path=None):
        """Initialize the database manager with the specified database path."""
        self.db_path = db_path or Config.DB_PATH
        self.db = None
        
    async def init_db(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            self.db = await aiosqlite.connect(self.db_path)
            
            # Enable foreign keys
            await self.db.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            await self._create_tables()
            
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    async def close(self):
        """Close the database connection."""
        if self.db:
            await self.db.close()
            logger.info("Database connection closed")
    
    async def _create_tables(self):
        """Create all required tables if they don't exist."""
        # Keywords table
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY,
            keyword TEXT UNIQUE NOT NULL,
            added_by INTEGER NOT NULL,
            added_at TIMESTAMP NOT NULL
        )
        """)
        
        # Monitored Channels table
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS monitored_channels (
            id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            channel_url TEXT UNIQUE NOT NULL,
            channel_name TEXT,
            added_by INTEGER NOT NULL,
            added_at TIMESTAMP NOT NULL
        )
        """)
        
        # Alert Channels table
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS alert_channels (
            id INTEGER PRIMARY KEY,
            channel_id INTEGER UNIQUE NOT NULL,
            is_primary BOOLEAN NOT NULL,
            added_by INTEGER NOT NULL,
            added_at TIMESTAMP NOT NULL
        )
        """)
        
        # Admins table
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            added_by INTEGER NOT NULL,
            added_at TIMESTAMP NOT NULL
        )
        """)
        
        # Config table
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        
        await self.db.commit()
    
    # Keywords management
    
    async def add_keyword(self, keyword, added_by):
        """Add a new keyword to the database."""
        try:
            await self.db.execute(
                "INSERT INTO keywords (keyword, added_by, added_at) VALUES (?, ?, ?)",
                (keyword.lower(), added_by, datetime.now().isoformat())
            )
            await self.db.commit()
            logger.info(f"Added keyword: {keyword}")
            return True
        except aiosqlite.IntegrityError:
            logger.warning(f"Keyword already exists: {keyword}")
            return False
        except Exception as e:
            logger.error(f"Error adding keyword: {e}")
            return False
    
    async def remove_keyword(self, keyword):
        """Remove a keyword from the database."""
        try:
            cursor = await self.db.execute(
                "DELETE FROM keywords WHERE keyword = ?",
                (keyword.lower(),)
            )
            await self.db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Removed keyword: {keyword}")
                return True
            else:
                logger.warning(f"Keyword not found: {keyword}")
                return False
        except Exception as e:
            logger.error(f"Error removing keyword: {e}")
            return False
    
    async def get_all_keywords(self):
        """Get all keywords from the database."""
        try:
            async with self.db.execute("SELECT keyword FROM keywords") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error getting keywords: {e}")
            return []
    
    # Monitored channels management
    
    async def add_monitored_channel(self, channel_id, channel_url, channel_name, added_by):
        """Add a new monitored channel to the database."""
        try:
            await self.db.execute(
                "INSERT INTO monitored_channels (channel_id, channel_url, channel_name, added_by, added_at) VALUES (?, ?, ?, ?, ?)",
                (channel_id, channel_url, channel_name, added_by, datetime.now().isoformat())
            )
            await self.db.commit()
            logger.info(f"Added monitored channel: {channel_name} ({channel_url})")
            return True
        except aiosqlite.IntegrityError:
            logger.warning(f"Channel already exists: {channel_url}")
            return False
        except Exception as e:
            logger.error(f"Error adding monitored channel: {e}")
            return False
    
    async def remove_monitored_channel(self, channel_url):
        """Remove a monitored channel from the database."""
        try:
            cursor = await self.db.execute(
                "DELETE FROM monitored_channels WHERE channel_url = ?",
                (channel_url,)
            )
            await self.db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Removed monitored channel: {channel_url}")
                return True
            else:
                logger.warning(f"Monitored channel not found: {channel_url}")
                return False
        except Exception as e:
            logger.error(f"Error removing monitored channel: {e}")
            return False
    
    async def get_all_monitored_channels(self):
        """Get all monitored channels from the database."""
        try:
            async with self.db.execute(
                "SELECT channel_id, channel_url, channel_name FROM monitored_channels"
            ) as cursor:
                rows = await cursor.fetchall()
                return [{"channel_id": row[0], "channel_url": row[1], "channel_name": row[2]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting monitored channels: {e}")
            return []
    
    # Alert channels management
    
    async def add_alert_channel(self, channel_id, is_primary, added_by):
        """Add a new alert channel to the database."""
        try:
            # If this is set as primary, unset any existing primary
            if is_primary:
                await self.db.execute(
                    "UPDATE alert_channels SET is_primary = 0 WHERE is_primary = 1"
                )
            
            await self.db.execute(
                "INSERT INTO alert_channels (channel_id, is_primary, added_by, added_at) VALUES (?, ?, ?, ?)",
                (channel_id, is_primary, added_by, datetime.now().isoformat())
            )
            await self.db.commit()
            logger.info(f"Added alert channel: {channel_id} (Primary: {is_primary})")
            return True
        except aiosqlite.IntegrityError:
            # If channel already exists, update its primary status
            if is_primary:
                await self.db.execute(
                    "UPDATE alert_channels SET is_primary = 0 WHERE is_primary = 1"
                )
                await self.db.execute(
                    "UPDATE alert_channels SET is_primary = 1 WHERE channel_id = ?",
                    (channel_id,)
                )
                await self.db.commit()
                logger.info(f"Updated alert channel {channel_id} as primary")
            return False
        except Exception as e:
            logger.error(f"Error adding alert channel: {e}")
            return False
    
    async def remove_alert_channel(self, channel_id):
        """Remove an alert channel from the database."""
        try:
            # Check if it's the primary channel
            async with self.db.execute(
                "SELECT is_primary FROM alert_channels WHERE channel_id = ?",
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    logger.warning("Cannot remove primary alert channel")
                    return False
            
            cursor = await self.db.execute(
                "DELETE FROM alert_channels WHERE channel_id = ?",
                (channel_id,)
            )
            await self.db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Removed alert channel: {channel_id}")
                return True
            else:
                logger.warning(f"Alert channel not found: {channel_id}")
                return False
        except Exception as e:
            logger.error(f"Error removing alert channel: {e}")
            return False
    
    async def get_all_alert_channels(self):
        """Get all alert channels from the database."""
        try:
            async with self.db.execute(
                "SELECT channel_id, is_primary FROM alert_channels"
            ) as cursor:
                rows = await cursor.fetchall()
                return [{"channel_id": row[0], "is_primary": bool(row[1])} for row in rows]
        except Exception as e:
            logger.error(f"Error getting alert channels: {e}")
            return []
    
    async def get_primary_alert_channel(self):
        """Get the primary alert channel from the database."""
        try:
            async with self.db.execute(
                "SELECT channel_id FROM alert_channels WHERE is_primary = 1"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting primary alert channel: {e}")
            return None
    
    # Admins management
    
    async def add_admin(self, user_id, username, added_by):
        """Add a new admin to the database."""
        try:
            await self.db.execute(
                "INSERT INTO admins (user_id, username, added_by, added_at) VALUES (?, ?, ?, ?)",
                (user_id, username, added_by, datetime.now().isoformat())
            )
            await self.db.commit()
            logger.info(f"Added admin: {username} ({user_id})")
            return True
        except aiosqlite.IntegrityError:
            logger.warning(f"Admin already exists: {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
            return False
    
    async def remove_admin(self, user_id):
        """Remove an admin from the database."""
        try:
            # Check if it's the creator
            creator_id = await self.get_config("creator_id")
            if creator_id and int(creator_id) == user_id:
                logger.warning("Cannot remove creator admin")
                return False
            
            cursor = await self.db.execute(
                "DELETE FROM admins WHERE user_id = ?",
                (user_id,)
            )
            await self.db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Removed admin: {user_id}")
                return True
            else:
                logger.warning(f"Admin not found: {user_id}")
                return False
        except Exception as e:
            logger.error(f"Error removing admin: {e}")
            return False
    
    async def is_admin(self, user_id):
        """Check if a user is an admin."""
        try:
            async with self.db.execute(
                "SELECT 1 FROM admins WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return bool(row)
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False
    
    async def get_all_admins(self):
        """Get all admins from the database."""
        try:
            async with self.db.execute(
                "SELECT user_id, username FROM admins"
            ) as cursor:
                rows = await cursor.fetchall()
                return [{"user_id": row[0], "username": row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting admins: {e}")
            return []
    
    # Config management
    
    async def get_config(self, key, default=None):
        """Get a configuration value from the database."""
        try:
            async with self.db.execute(
                "SELECT value FROM config WHERE key = ?",
                (key,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else default
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return default
    
    async def set_config(self, key, value):
        """Set a configuration value in the database."""
        try:
            await self.db.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (key, value)
            )
            await self.db.commit()
            logger.info(f"Set config: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Error setting config: {e}")
            return False
