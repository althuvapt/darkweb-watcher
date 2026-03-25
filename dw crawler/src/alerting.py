import yaml
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    def send_alert(self, match_type: str, value: str, source_url: str):
        """Send an alert. Currently logs to console, but could trigger webhooks."""
        alert_msg = f"🚨 [ALERT] Watchlist Match - {match_type}: '{value}' found on {source_url}"
        logger.warning(alert_msg)

class AlertManager:
    def __init__(self, config_path: str = "src/watchlist.yaml"):
        self.watchlist = self._load_watchlist(config_path)
        self.dispatcher = NotificationDispatcher()

    def _load_watchlist(self, path: str) -> dict:
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                return {
                    "keywords": [k.lower() for k in data.get("keywords", [])],
                    "emails": [e.lower() for e in data.get("emails", [])],
                    "crypto": data.get("crypto", [])
                }
        except Exception as e:
            logger.error(f"Failed to load watchlist from {path}: {e}")
            return {"keywords": [], "emails": [], "crypto": []}

    def check_for_alerts(self, url: str, text: str, entities: Dict[str, List[str]]):
        """Check text and extracted entities against the watchlist."""
        text_lower = text.lower()
        
        # 1. Check Keywords
        for kw in self.watchlist["keywords"]:
            if kw in text_lower:
                self.dispatcher.send_alert("Keyword", kw, url)
                
        # 2. Check Emails
        for email in self.watchlist["emails"]:
            if email in [e.lower() for e in entities.get("emails", [])]:
                self.dispatcher.send_alert("Email", email, url)
                
        # 3. Check Crypto (BTC + XMR)
        all_crypto = entities.get("btc_addresses", []) + entities.get("xmr_addresses", [])
        for address in self.watchlist["crypto"]:
            if address in all_crypto:
                self.dispatcher.send_alert("Crypto Address", address, url)
