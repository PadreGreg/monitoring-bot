"""
Twitter watcher module for the Telegram Monitoring Bot.
Monitors Twitter for keyword matches using snscrape.
"""

import asyncio
import logging
import time
import json
import re
import sys
import subprocess
from datetime import datetime, timezone, timedelta

from watcher_base import WatcherBase
from config import Config

logger = logging.getLogger(__name__)

class TwitterWatcher(WatcherBase):
    """Monitors Twitter for keyword matches using snscrape."""
    
    def __init__(self, db_manager, notifier):
        """Initialize the Twitter watcher."""
        super().__init__(db_manager, notifier, name="TwitterWatcher")
        self.check_interval = Config.TWITTER_CHECK_INTERVAL
        self.last_check_time = datetime.now(timezone.utc) - timedelta(hours=1)  # Start with tweets from the last hour
    
    async def _monitor_source(self):
        """Monitor Twitter for keyword matches."""
        logger.info("Starting Twitter monitoring")
        
        try:
            while self.running:
                try:
                    # Get all keywords
                    keywords = await self.db_manager.get_all_keywords()
                    if not keywords:
                        logger.info("No keywords to monitor on Twitter")
                        await asyncio.sleep(self.check_interval)
                        continue
                    
                    # Search for tweets containing keywords
                    current_time = datetime.now(timezone.utc)
                    since_time = self.last_check_time.strftime("%Y-%m-%d_%H:%M:%S")
                    
                    for keyword in keywords:
                        tweets = await self.search_tweets(keyword, since_time)
                        
                        for tweet in tweets:
                            # Prepare source info
                            source_info = {
                                "source": "Twitter",
                                "time": tweet["date"].strftime("%H:%M"),
                                "context": f"@{tweet['username']}",
                                "url": tweet["url"]
                            }
                            
                            # Check tweet content for keyword
                            match_info = await self.check_for_keywords(tweet["content"], source_info)
                            if match_info:
                                await self.notifier.send_alert(match_info)
                    
                    self.last_check_time = current_time
                    
                    # Wait for the next check interval
                    await asyncio.sleep(self.check_interval)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error in Twitter monitoring: {e}")
                    await asyncio.sleep(60)  # Wait a minute before retrying
        finally:
            logger.info("Twitter monitoring stopped")
    
    async def search_tweets(self, keyword, since_time):
        """Search for tweets containing a keyword using snscrape."""
        try:
            # Construct the search query
            query = f"{keyword} since:{since_time}"
            
            # Run snscrape as a subprocess
            cmd = [
                sys.executable, "-m", "snscrape", "--jsonl", 
                "--max-results", "100", 
                "twitter-search", query
            ]
            
            # Execute the command asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"snscrape error: {stderr.decode()}")
                return []
            
            # Parse the JSON output
            tweets = []
            for line in stdout.decode().splitlines():
                if line.strip():
                    try:
                        tweet_data = json.loads(line)
                        tweet = {
                            "id": tweet_data["id"],
                            "url": tweet_data["url"],
                            "date": datetime.fromisoformat(tweet_data["date"].replace("Z", "+00:00")),
                            "content": tweet_data["content"],
                            "username": tweet_data["user"]["username"],
                            "user_id": tweet_data["user"]["id"]
                        }
                        tweets.append(tweet)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tweet JSON: {line}")
                    except KeyError as e:
                        logger.warning(f"Missing key in tweet data: {e}")
            
            return tweets
        except Exception as e:
            logger.error(f"Error searching tweets for '{keyword}': {e}")
            return []
