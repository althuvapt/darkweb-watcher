# Dark Web Intelligence Crawler

A production-grade, modular, and scalable Dark Web crawler designed for VAPT, OSINT, and threat intelligence.

## 🚀 Features

- **Asynchronous Engine**: Built with `Python` and `aiohttp` for high-concurrency crawling.
- **Tor Integration**: All traffic is securely routed through the Tor network.
- **Deep Intelligence Extraction**: 
  - Regex-based extraction for BTC/XMR addresses, Emails, and PGP keys.
  - Named Entity Recognition (NER) via `SpaCy` for identifying People, Organizations, and Locations.
- **Persistence & Search**:
  - Raw HTML stored in **MongoDB**.
  - Full-text and entity search indexed in **Elasticsearch**.
- **Real-time Alerting**: Proactive alerts via console/logs when watchlist targets (keywords/emails/crypto) are found.
- **Modern Dashboard**: A sleek "Dark Ops" dashboard for searching intelligence and viewing analytics.

## 🛠 Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Data Layers**: Elasticsearch 8.x, MongoDB, Redis
- **Networking**: Tor (SOCKS5 Proxy)
- **Frontend**: Vanilla HTML/JS/CSS, Chart.js

## 📦 Setup & Deployment

Ensure you have [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed.

1. **Clone the repository**
2. **Build and Start Services**
   ```bash
   docker-compose up --build -d
   ```
3. **Access the Dashboard**
   Navigate to `http://localhost:8000` in your browser.

## 🕵️‍♂️ Usage

- **Search**: Use the dashboard search bar to query indexed pages.
- **Watchlists**: Modify `src/watchlist.yaml` to include your own target keywords, emails, or crypto addresses.
- **Logs**: Monitor crawl progress and alerts in real-time:
  ```bash
  docker logs dwcrawler-crawler-1 -f
  ```

## ⚖️ Legal & Ethical Disclaimer

This tool is for educational, research, and authorized security testing purposes ONLY. Crawling .onion sites can expose you to harmful content. Always ensure you are following local laws and ethical guidelines.

--- 
*Developed for Dark Web Intelligence & Threat Research.*
