"""
Reddit watcher module for the Telegram Monitoring Bot.
Monitors Reddit for keyword matches in posts and comments.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
import aiohttp
import json
import re

from watcher_base import WatcherBase
from config import Config

logger = logging.getLogger(__name__)

class RedditWatcher(WatcherBase):
    """Monitors Reddit for keyword matches in posts and comments."""
    
    def __init__(self, db_manager, notifier):
        """Initialize the Reddit watcher."""
        super().__init__(db_manager, notifier, name="RedditWatcher")
        self.check_interval = Config.REDDIT_CHECK_INTERVAL
        self.subreddits = ["cryptocurrency", "programming", "technology", "python"]  # Default subreddits
        self.last_check_time = int(time.time())
        self.session = None
    
    async def _monitor_source(self):
        """Monitor Reddit for keyword matches."""
        logger.info("Starting Reddit monitoring")
        
        self.session = aiohttp.ClientSession()
        
        try:
            while self.running:
                try:
                    current_time = int(time.time())
                    
                    # Check each subreddit for new posts and comments
                    for subreddit in self.subreddits:
                        await self.check_subreddit(subreddit)
                    
                    self.last_check_time = current_time
                    
                    # Wait for the next check interval
                    await asyncio.sleep(self.check_interval)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error in Reddit monitoring: {e}")
                    await asyncio.sleep(60)  # Wait a minute before retrying
        finally:
            if self.session:
                await self.session.close()
                self.session = None
            logger.info("Reddit monitoring stopped")
    
    async def check_subreddit(self, subreddit):
        """Check a subreddit for new posts and comments."""
        try:
            # Get new posts
            posts = await self.get_new_posts(subreddit)
            for post in posts:
                # Check post title and body for keywords
                source_info = {
                    "source": "Reddit",
                    "time": datetime.fromtimestamp(post["created_utc"], tz=timezone.utc).strftime("%H:%M"),
                    "context": f"r/{subreddit}",
                    "url": f"https://reddit.com{post['permalink']}"
                }
                
                # Check title
                match_info = await self.check_for_keywords(post["title"], source_info)
                if match_info:
                    await self.notifier.send_alert(match_info)
                
                # Check selftext if available
                if post.get("selftext"):
                    match_info = await self.check_for_keywords(post["selftext"], source_info)
                    if match_info:
                        await self.notifier.send_alert(match_info)
            
            # Get new comments
            comments = await self.get_new_comments(subreddit)
            for comment in comments:
                # Check comment body for keywords
                source_info = {
                    "source": "Reddit",
                    "time": datetime.fromtimestamp(comment["created_utc"], tz=timezone.utc).strftime("%H:%M"),
                    "context": f"r/{subreddit} (comment)",
                    "url": f"https://reddit.com{comment['permalink']}"
                }
                
                match_info = await self.check_for_keywords(comment["body"], source_info)
                if match_info:
                    await self.notifier.send_alert(match_info)
        
        except Exception as e:
            logger.error(f"Error checking subreddit {subreddit}: {e}")
    
    async def get_new_posts(self, subreddit):
        """Get new posts from a subreddit using Pushshift API."""
        try:
            url = f"https://api.pushshift.io/reddit/search/submission?subreddit={subreddit}&sort=desc&sort_type=created_utc&after={self.last_check_time}&size=25"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.warning(f"Failed to get posts from r/{subreddit}: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting posts from r/{subreddit}: {e}")
            return []
    
    async def get_new_comments(self, subreddit):
        """Get new comments from a subreddit using Pushshift API."""
        try:
            url = f"https://api.pushshift.io/reddit/search/comment?subreddit={subreddit}&sort=desc&sort_type=created_utc&after={self.last_check_time}&size=25"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.warning(f"Failed to get comments from r/{subreddit}: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting comments from r/{subreddit}: {e}")
            return []
    
    async def add_subreddit(self, subreddit):
        """Add a subreddit to the monitoring list."""
        subreddit = subreddit.lower().strip()
        if subreddit not in self.subreddits:
            self.subreddits.append(subreddit)
            logger.info(f"Added subreddit: r/{subreddit}")
            return True
        return False
    
    async def remove_subreddit(self, subreddit):
        """Remove a subreddit from the monitoring list."""
        subreddit = subreddit.lower().strip()
        if subreddit in self.subreddits:
            self.subreddits.remove(subreddit)
            logger.info(f"Removed subreddit: r/{subreddit}")
            return True
        return False
    
    async def get_subreddits(self):
        """Get the list of monitored subreddits."""
        return self.subreddits
