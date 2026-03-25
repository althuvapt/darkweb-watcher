import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from elasticsearch import AsyncElasticsearch
from .config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="DarkOps Intelligence API")

# Initialize ES client
es_client = AsyncElasticsearch([settings.ES_URL])
ES_INDEX = "crawled_pages"

# Mount static files correctly by resolving the path
current_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(current_dir, "static")

# Ensure static directory exists
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("shutdown")
async def shutdown_event():
    await es_client.close()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>API Running</h1><p>Dashboard UI not found at src/static/index.html</p>"

@app.get("/api/search")
async def search(q: str = ""):
    if not q:
        return {"hits": []}
    
    try:
        query_body = {
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["text_content", "url", "entities.*"]
                }
            },
            "highlight": {
                "fields": {
                    "text_content": {}
                }
            },
            "_source": ["url", "timestamp", "entities"], # Don't return the full body text
            "size": 20
        }
        
        res = await es_client.search(index=ES_INDEX, body=query_body)
        
        results = []
        for hit in res.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            results.append({
                "url": source.get("url"),
                "timestamp": source.get("timestamp"),
                "entities": source.get("entities", {}),
                "highlights": hit.get("highlight", {}).get("text_content", [])
            })
            
        return {"hits": results, "total": res.get("hits", {}).get("total", {}).get("value", 0)}
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search backend error")

@app.get("/api/stats")
async def get_stats():
    try:
        res = await es_client.count(index=ES_INDEX)
        total_docs = res.get("count", 0)
        
        # Aggregation for entities
        agg_query = {
            "size": 0,
            "aggs": {
                "btc_count": {"value_count": {"field": "entities.btc_addresses"}},
                "xmr_count": {"value_count": {"field": "entities.xmr_addresses"}},
                "email_count": {"value_count": {"field": "entities.emails"}},
                "person_count": {"value_count": {"field": "entities.nlp_persons"}},
                "org_count": {"value_count": {"field": "entities.nlp_organizations"}},
                "loc_count": {"value_count": {"field": "entities.nlp_locations"}}
            }
        }
        
        agg_res = await es_client.search(index=ES_INDEX, body=agg_query)
        aggs = agg_res.get("aggregations", {})
        
        return {
            "total_pages": total_docs,
            "entities": {
                "BTC": aggs.get("btc_count", {}).get("value", 0),
                "XMR": aggs.get("xmr_count", {}).get("value", 0),
                "Emails": aggs.get("email_count", {}).get("value", 0),
                "Persons": aggs.get("person_count", {}).get("value", 0),
                "Organizations": aggs.get("org_count", {}).get("value", 0),
                "Locations": aggs.get("loc_count", {}).get("value", 0)
            }
        }
    except Exception as e:
        logger.error(f"Stats failed: {e}")
        return {"total_pages": 0, "entities": {}}

