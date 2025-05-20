"""
News watcher module for the Telegram Monitoring Bot.
Monitors RSS feeds for keyword matches.
"""

import asyncio
import logging
import time
import aiohttp
import feedparser
from datetime import datetime, timezone, timedelta
import hashlib

from watcher_base import WatcherBase
from config import Config

logger = logging.getLogger(__name__)

class NewsWatcher(WatcherBase):
    """Monitors RSS feeds for keyword matches."""
    
    def __init__(self, db_manager, notifier):
        """Initialize the News watcher."""
        super().__init__(db_manager, notifier, name="NewsWatcher")
        self.check_interval = Config.NEWS_CHECK_INTERVAL
        self.feeds = [
            "https://news.google.com/rss/search?q=cryptocurrency&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=blockchain&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=python+programming&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=technology&hl=en-US&gl=US&ceid=US:en"
        ]  # Default feeds
        self.session = None
        self.processed_entries = set()  # Store hashes of processed entries
    
    async def _monitor_source(self):
        """Monitor RSS feeds for keyword matches."""
        logger.info("Starting News monitoring")
        
        self.session = aiohttp.ClientSession()
        
        try:
            while self.running:
                try:
                    # Fetch and parse all feeds
                    for feed_url in self.feeds:
                        await self.process_feed(feed_url)
                    
                    # Wait for the next check interval
                    await asyncio.sleep(self.check_interval)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error in News monitoring: {e}")
                    await asyncio.sleep(60)  # Wait a minute before retrying
        finally:
            if self.session:
                await self.session.close()
                self.session = None
            logger.info("News monitoring stopped")
    
    async def process_feed(self, feed_url):
        """Process an RSS feed and check for keyword matches."""
        try:
            # Fetch the feed content
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch feed {feed_url}: {response.status}")
                    return
                
                content = await response.text()
            
            # Parse the feed
            feed = feedparser.parse(content)
            
            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                return
            
            # Process each entry
            for entry in feed.entries:
                # Generate a unique hash for this entry
                entry_id = entry.get('id', entry.get('link', ''))
                entry_hash = hashlib.md5(entry_id.encode()).hexdigest()
                
                # Skip if already processed
                if entry_hash in self.processed_entries:
                    continue
                
                # Add to processed set
                self.processed_entries.add(entry_hash)
                
                # Limit the size of the processed set
                if len(self.processed_entries) > 1000:
                    self.processed_entries = set(list(self.processed_entries)[-500:])
                
                # Extract entry details
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                
                # Try to parse the published date
                try:
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    time_str = pub_date.strftime("%H:%M")
                except (AttributeError, TypeError):
                    time_str = datetime.now(timezone.utc).strftime("%H:%M")
                
                # Prepare source info
                source_info = {
                    "source": "News",
                    "time": time_str,
                    "context": feed.feed.get('title', 'RSS Feed'),
                    "url": link
                }
                
                # Check title for keywords
                match_info = await self.check_for_keywords(title, source_info)
                if match_info:
                    await self.notifier.send_alert(match_info)
                    continue
                
                # Check summary for keywords
                match_info = await self.check_for_keywords(summary, source_info)
                if match_info:
                    await self.notifier.send_alert(match_info)
        
        except Exception as e:
            logger.error(f"Error processing feed {feed_url}: {e}")
    
    async def add_feed(self, feed_url):
        """Add an RSS feed to the monitoring list."""
        if feed_url not in self.feeds:
            self.feeds.append(feed_url)
            logger.info(f"Added RSS feed: {feed_url}")
            return True
        return False
    
    async def remove_feed(self, feed_url):
        """Remove an RSS feed from the monitoring list."""
        if feed_url in self.feeds:
            self.feeds.remove(feed_url)
            logger.info(f"Removed RSS feed: {feed_url}")
            return True
        return False
    
    async def get_feeds(self):
        """Get the list of monitored RSS feeds."""
        return self.feeds
