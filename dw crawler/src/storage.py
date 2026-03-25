import redis.asyncio as redis
from typing import Optional

class Storage:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.queue_key = "crawl_queue"
        self.seen_key = "crawl_seen"

    async def add_to_queue(self, url: str, depth: int = 0):
        """Add a URL to the queue if it hasn't been seen."""
        # Use a transaction to ensure atomic check-and-add
        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.sismember(self.seen_key, url).execute()
        
        is_seen = await self.redis.sismember(self.seen_key, url)
        if not is_seen:
            await self.redis.sadd(self.seen_key, url)
            # Store as "url|depth" format
            await self.redis.rpush(self.queue_key, f"{url}|{depth}")
            return True
        return False

    async def get_next_url(self) -> Optional[tuple[str, int]]:
        """Get the next URL from the queue."""
        item = await self.redis.lpop(self.queue_key)
        if item:
            parts = item.split("|")
            if len(parts) == 2:
                return parts[0], int(parts[1])
            else:
                return parts[0], 0 # default depth if malformed
        return None

    async def queue_length(self) -> int:
        return await self.redis.llen(self.queue_key)
        
    async def seen_count(self) -> int:
        return await self.redis.scard(self.seen_key)

    async def clear_all(self):
        """Clear queue and seen sets."""
        await self.redis.delete(self.queue_key, self.seen_key)

    async def close(self):
        await self.redis.close()
