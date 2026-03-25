import logging
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import random

logger = logging.getLogger(__name__)

class OnionCrawler:
    def __init__(self, socks_proxy="socks5://tor:9050"):
        self.socks_proxy = socks_proxy
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        ]

    async def fetch_page(self, url: str) -> str | None:
        """Fetch content from an onion URL using Tor SOCKS proxy with retries."""
        connector = ProxyConnector.from_url(self.socks_proxy)
        headers = {"User-Agent": random.choice(self.user_agents)}
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, headers=headers, timeout=30) as response:
                        if response.status == 200:
                            content_type = response.headers.get('Content-Type', '')
                            if 'text/html' not in content_type:
                                logger.debug(f"Skipping non-HTML content at {url}: {content_type}")
                                return None
                            return await response.text()
                        else:
                            logger.warning(f"Failed to fetch {url}: Status {response.status} (Attempt {attempt+1})")
            except Exception as e:
                logger.error(f"Error fetching {url} (Attempt {attempt+1}): {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt) # Exponential backoff
                
        logger.error(f"Max retries reached for {url}")
        return None

    def extract_links_and_text(self, html: str, base_url: str) -> tuple[list[str], str]:
        """Extract all .onion links and raw text from the HTML content."""
        if not html:
            return [], ""
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract Text
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        
        # Extract Links
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # Only keep .onion links, ignore fragments and queries
            if parsed.netloc.endswith(".onion"):
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                links.add(clean_url)
        
        return list(links), text

