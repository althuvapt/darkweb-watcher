import logging
from motor.motor_asyncio import AsyncIOMotorClient
from elasticsearch import AsyncElasticsearch
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self, mongo_url: str, es_url: str):
        self.mongo_client = AsyncIOMotorClient(mongo_url)
        self.db = self.mongo_client["dark_web_intel"]
        self.raw_html_collection = self.db["raw_html"]
        
        self.es_client = AsyncElasticsearch(es_url)
        self.es_index = "crawled_pages"

    async def initialize(self):
        """Initialize connections and indices."""
        # Create MongoDB unique index on URL to prevent duplicates if crawler logic misses it
        await self.raw_html_collection.create_index([("url", 1)], unique=True)
        
        # Create Elasticsearch index if it doesn't exist
        try:
            if not await self.es_client.indices.exists(index=self.es_index):
                await self.es_client.indices.create(
                    index=self.es_index,
                    body={
                        "mappings": {
                            "properties": {
                                "url": {"type": "keyword"},
                                "timestamp": {"type": "date"},
                                "content_hash": {"type": "keyword"},
                                "text_content": {"type": "text"},
                                "entities": {
                                    "properties": {
                                        "btc_addresses": {"type": "keyword"},
                                        "xmr_addresses": {"type": "keyword"},
                                        "emails": {"type": "keyword"},
                                        "pgp_keys": {"type": "keyword"},
                                        "nlp_persons": {"type": "keyword"},
                                        "nlp_organizations": {"type": "keyword"},
                                        "nlp_locations": {"type": "keyword"}
                                    }
                                }
                            }
                        }
                    }
                )
                logger.info(f"Created Elasticsearch index: {self.es_index}")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch index: {e}")

    async def store_content(self, url: str, html: str, text_content: str, content_hash: str, entities: dict) -> bool:
        """Store raw HTML in MongoDB and index text/entities in Elasticsearch."""
        timestamp = datetime.now(timezone.utc)
        
        # 1. Store/Update in MongoDB
        try:
            await self.raw_html_collection.update_one(
                {"url": url},
                {"$set": {
                    "url": url,
                    "html": html,
                    "content_hash": content_hash,
                    "entities": entities,
                    "last_updated": timestamp
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"MongoDB storage failed for {url}: {e}")
            return False

        # 2. Index in Elasticsearch
        try:
            await self.es_client.index(
                index=self.es_index,
                id=content_hash, # Use hash as ID to avoid duplicate text indexing if we want
                document={
                    "url": url,
                    "timestamp": timestamp,
                    "content_hash": content_hash,
                    "text_content": text_content,
                    "entities": entities
                }
            )
            return True
        except Exception as e:
            logger.error(f"Elasticsearch indexing failed for {url}: {e}")
            return False

    async def close(self):
        self.mongo_client.close()
        await self.es_client.close()

