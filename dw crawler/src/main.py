import logging
import sys
import asyncio
from src.engine import CrawlEngine


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def run_crawler():
    """Initialize and run the async crawl engine."""
    engine = CrawlEngine()
    
    logger.info("Initializing Dark Web Intelligence Crawler...")
    try:
        await engine.run()
    except asyncio.CancelledError:
        logger.info("Crawler task cancelled.")
    except Exception as e:
        logger.error(f"Engine encountered a fatal error: {e}")
    finally:
        logger.info("Shutting down engine components...")
        await engine.shutdown()

def main():
    """Main entry point with infrastructure warmup."""
    # Infrastructure warmup
    print("Waiting for infrastructure to stabilize...")
    import time
    time.sleep(10)
    
    try:
        asyncio.run(run_crawler())
    except KeyboardInterrupt:
        logger.info("Received exit signal.")
    except Exception as e:
        logger.error(f"Main loop failed: {e}")
    finally:
        logger.info("Crawler process finished.")

if __name__ == "__main__":
    main()

