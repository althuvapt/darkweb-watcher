from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TOR_SOCKS_URL: str = "socks5://tor:9050"
    REDIS_URL: str = "redis://redis:6379/0"
    MONGO_URL: str = "mongodb://mongodb:27017/"
    ES_URL: str = "http://elasticsearch:9200/"
    CRAWL_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    DEFAULT_SEED_URL: str = "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/"
    MAX_CRAWL_DEPTH: int = 3
    MAX_CONCURRENT_TASKS: int = 5

settings = Settings()
