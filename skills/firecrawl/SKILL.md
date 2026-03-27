---
name: firecrawl
description: "Scrape, crawl, and extract structured data from websites using self-hosted Firecrawl on PowerSpec. Use when: (1) scraping a single page for markdown/HTML content, (2) crawling an entire site or section with depth/page limits, (3) extracting structured data from pages via LLM (uses local Ollama nemotron-nano), (4) mapping a site's URLs without downloading content, (5) competitive intelligence web research, (6) replacing or upgrading ProjectScraper workflows. NOT for: simple URL fetching where web_fetch suffices, or sites that block headless browsers despite Playwright."
---

# Firecrawl (Self-Hosted on PowerSpec)

Self-hosted Firecrawl instance running on the PowerSpec PC (100.67.128.123) via Docker Compose.

## Connection

- **Base URL:** `http://100.67.128.123:3002`
- **Auth:** None required (`USE_DB_AUTHENTICATION=false`)
- **All requests:** `Content-Type: application/json`

## Endpoints

### 1. Scrape a Single Page

Extract content from one URL. Best for targeted page reads.

```bash
curl -s -X POST http://100.67.128.123:3002/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/page",
    "formats": ["markdown"],
    "onlyMainContent": true
  }'
```

**Key options:**
- `formats`: `["markdown"]`, `["html"]`, `["links"]`, `["screenshot"]`, or combine them
- `onlyMainContent`: `true` strips nav/footer/sidebar (recommended)
- `waitFor`: milliseconds to wait for JS rendering (default: 0)
- `timeout`: request timeout in ms (default: 30000)
- `includeTags` / `excludeTags`: CSS selectors to include/exclude
- `mobile`: `true` for mobile viewport

**Response:** `{ "success": true, "data": { "markdown": "...", "metadata": { "title": "...", "sourceURL": "..." } } }`

### 2. Crawl a Website

Crawl multiple pages starting from a URL. Returns a job ID for async polling.

```bash
# Start crawl
curl -s -X POST http://100.67.128.123:3002/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "limit": 50,
    "maxDepth": 3,
    "includePaths": ["/blog/*", "/docs/*"],
    "excludePaths": ["/admin/*"],
    "scrapeOptions": {
      "formats": ["markdown"],
      "onlyMainContent": true
    }
  }'
# Response: { "success": true, "id": "<crawl-id>" }

# Poll status
curl -s http://100.67.128.123:3002/v1/crawl/<crawl-id>
# Response: { "status": "scraping|completed", "completed": N, "total": N, "data": [...] }
```

**Key options:**
- `limit`: max pages to crawl (default: 10000)
- `maxDepth`: link depth from seed URL
- `includePaths` / `excludePaths`: glob patterns to filter URLs
- `allowBackwardLinks`: `true` to follow links to parent paths
- `allowExternalLinks`: `true` to follow links to other domains
- `scrapeOptions`: same options as single scrape

**Polling pattern:**
```bash
# Poll until status is "completed"
while true; do
  STATUS=$(curl -s http://100.67.128.123:3002/v1/crawl/$CRAWL_ID | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")
  [ "$STATUS" = "completed" ] && break
  sleep 5
done
```

### 3. Map a Site (URL Discovery)

Get all URLs from a site without downloading content. Fast site structure mapping.

```bash
curl -s -X POST http://100.67.128.123:3002/v1/map \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "limit": 500
  }'
```

**Response:** `{ "success": true, "links": ["https://example.com/page1", ...] }`

### 4. Extract Structured Data (LLM)

Use local Ollama (nemotron-nano) to extract structured data from pages.

```bash
curl -s -X POST http://100.67.128.123:3002/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/pricing"],
    "prompt": "Extract the pricing tiers with name, price, and features",
    "schema": {
      "type": "object",
      "properties": {
        "tiers": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "price": {"type": "string"},
              "features": {"type": "array", "items": {"type": "string"}}
            }
          }
        }
      }
    }
  }'
```

## Infrastructure

| Component | Container | Purpose |
|-----------|-----------|---------|
| API | `firecrawl-api-1` | Main API server (port 3002) |
| Playwright | `firecrawl-playwright-service-1` | JS rendering for dynamic sites |
| RabbitMQ | `firecrawl-rabbitmq-1` | Job queue for crawl tasks |
| Redis | `firecrawl-redis-1` | Caching + rate limiting |
| Postgres | `firecrawl-nuq-postgres-1` | Persistent storage |

**Config:** Local Ollama at `http://host.docker.internal:11434` for LLM extraction (model: `nemotron-nano`).

## Concurrency Limits

- `NUM_WORKERS_PER_QUEUE`: 8
- `MAX_CONCURRENT_JOBS`: 5
- `CRAWL_CONCURRENT_REQUESTS`: 10
- `BROWSER_POOL_SIZE`: 5

For large crawls (>100 pages), use `limit` and `maxDepth` to stay within capacity.

## Competitive Intel Workflow

For crawling competitor sites (Rubrik, Commvault, Veeam):

1. **Map** the site first to get URL inventory
2. **Filter** URLs to relevant sections (products, pricing, docs, blog)
3. **Crawl** filtered sections with `includePaths`
4. **Extract** structured data (pricing, features) with LLM extraction
5. Save results to workspace or Google Sheets

```bash
# Example: Map Rubrik's site
curl -s -X POST http://100.67.128.123:3002/v1/map \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.rubrik.com", "limit": 500}'

# Crawl just products + solutions
curl -s -X POST http://100.67.128.123:3002/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.rubrik.com",
    "limit": 100,
    "includePaths": ["/products/*", "/solutions/*", "/pricing*"],
    "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": true}
  }'
```

## Troubleshooting

- **Connection refused:** Verify PowerSpec is reachable (`tailscale ping remote-coder-main`) and containers are up (`ssh ericf@100.67.128.123 "docker ps --filter name=firecrawl"`)
- **Slow crawls:** Check `MAX_CONCURRENT_JOBS` and `BROWSER_POOL_SIZE`; reduce `limit` for initial tests
- **JS-heavy sites not rendering:** Playwright service handles this automatically; increase `waitFor` if content loads late
- **Extract returns empty:** Local Ollama model (nemotron-nano) may struggle with complex schemas; simplify the prompt or schema
