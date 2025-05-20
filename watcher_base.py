"""
Base watcher module for the Telegram Monitoring Bot.
Provides a common interface for all watcher modules.
"""

import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class WatcherBase(ABC):
    """Base class for all watcher modules."""
    
    def __init__(self, db_manager, notifier, name="BaseWatcher"):
        """Initialize the watcher with database manager and notifier."""
        self.db_manager = db_manager
        self.notifier = notifier
        self.name = name
        self.running = False
        self.task = None
        
    async def start(self):
        """Start the watcher monitoring task."""
        if self.running:
            logger.warning(f"{self.name} is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitor_source())
        logger.info(f"{self.name} started")
    
    async def stop(self):
        """Stop the watcher monitoring task."""
        if not self.running:
            logger.warning(f"{self.name} is not running")
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info(f"{self.name} stopped")
    
    @abstractmethod
    async def _monitor_source(self):
        """Monitor the source for keyword matches. To be implemented by subclasses."""
        pass
    
    async def check_for_keywords(self, content, source_info):
        """Check if content contains any of the monitored keywords."""
        if not content:
            return None
        
        keywords = await self.db_manager.get_all_keywords()
        if not keywords:
            return None
        
        content_lower = content.lower()
        for keyword in keywords:
            if keyword.lower() in content_lower:
                match_info = {
                    "source": source_info["source"],
                    "time": source_info["time"],
                    "keyword": keyword,
                    "context": source_info["context"],
                    "content": content,
                    "url": source_info["url"]
                }
                logger.info(f"Keyword match found: {keyword} in {source_info['source']}")
                return match_info
        
        return None
