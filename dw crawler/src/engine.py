import logging
import asyncio
import hashlib
from .crawler import OnionCrawler
from .storage import Storage
from .db import DatabaseClient
from .extractor import IntelligenceExtractor
from .alerting import AlertManager
from .config import settings

logger = logging.getLogger(__name__)

class CrawlEngine:
    def __init__(self):
        self.storage = Storage(settings.REDIS_URL)
        self.db = DatabaseClient(settings.MONGO_URL, settings.ES_URL)
        self.crawler = OnionCrawler()
        self.extractor = IntelligenceExtractor()
        self.alert_manager = AlertManager()
        self.max_depth = settings.MAX_CRAWL_DEPTH
        self.max_concurrent_tasks = settings.MAX_CONCURRENT_TASKS

    async def worker(self, worker_id: int):
        """Worker task that continuously pulls URLs from the Redis queue."""
        logger.info(f"Worker {worker_id} started.")
        while True:
            item = await self.storage.get_next_url()
            if not item:
                # Queue is empty, wait a bit
                await asyncio.sleep(2)
                continue
                
            url, depth = item
            logger.info(f"[Worker {worker_id}] Processing: {url} (Depth: {depth})")
            
            if depth > self.max_depth:
                logger.debug(f"Skipping {url} (Max depth reached)")
                continue
                
            html = await self.crawler.fetch_page(url)
            if html:
                links, text = self.crawler.extract_links_and_text(html, url)
                logger.info(f"[Worker {worker_id}] Found {len(links)} links on {url}")
                
                # Extract Intelligence
                entities = self.extractor.extract_entities(text)
                
                # Check against Watchlists
                self.alert_manager.check_for_alerts(url, text, entities)
                
                # Log a summary of found entities
                found_entity_counts = {k: len(v) for k, v in entities.items() if len(v) > 0}
                if found_entity_counts:
                    logger.info(f"[Worker {worker_id}] Extracted entities from {url}: {found_entity_counts}")

                
                # Hash content to track changes
                content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
                
                # Store and Index
                stored = await self.db.store_content(url, html, text, content_hash, entities)
                if stored:
                    logger.debug(f"[Worker {worker_id}] Stored and indexed content for {url}")

                
                # Add new links to queue
                added_count = 0
                for link in links:
                    if await self.storage.add_to_queue(link, depth + 1):
                        added_count += 1
                
                logger.debug(f"[Worker {worker_id}] Added {added_count} new unique links to queue.")
            
            await asyncio.sleep(0.5) # Polite crawl delay

    async def run(self):
        """Start the engine and worker tasks."""
        # Initialize MongoDB indices and ES mappings
        await self.db.initialize()
        
        # Clean state for testing MVP
        await self.storage.clear_all()
        
        # Seed the queue
        seed_url = settings.DEFAULT_SEED_URL
        logger.info(f"Seeding queue with {seed_url}")
        await self.storage.add_to_queue(seed_url, depth=0)
        
        workers = []
        for i in range(self.max_concurrent_tasks):
            task = asyncio.create_task(self.worker(i))
            workers.append(task)
            
        try:
            # Let it run indefinitely or until interrupted
            await asyncio.gather(*workers)
        except asyncio.CancelledError:
            logger.info("Engine cancelled. Shutting down...")
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        await self.crawler.close()
        await self.storage.close()
        await self.db.close()
        logger.info("Engine shutdown complete.")

