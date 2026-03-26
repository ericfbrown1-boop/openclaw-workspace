---
name: competitive-intel
description: >
  Daily competitive intelligence for Rubrik, Commvault, and Veeam.
  Monitors pricing, product announcements, news, and stock movements.
  Feeds into 6 AM daily briefing.
---

# Competitive Intelligence Aggregator

## When to Use

- **Daily at 5:30 AM PT**: Auto-run to feed 6 AM briefing
- Eric asks about competitor activity or news
- Earnings season for RBRK or CVLT (heightened monitoring)
- Cohesity deal competitive situation requiring latest intel
- Product launch or pricing change detected

## Competitors Tracked

| Company   | Ticker | Segment         | Monitor Priority |
|-----------|--------|-----------------|------------------|
| Rubrik    | RBRK   | Primary rival   | High             |
| Commvault | CVLT   | Enterprise      | High             |
| Veeam     | —      | Mid-market      | Medium           |
| Veritas   | —      | Legacy          | Low              |
| Druva     | —      | SaaS-only       | Low              |

## Data Sources

- **Stock prices**: yfinance for RBRK, CVLT (price, volume, % change)
- **News feeds**: Web search for "[company] data protection" + RSS via blogwatcher
- **Competitor blogs**: Rubrik blog, Commvault blog, Veeam blog (via ProjectScraper)
- **SEC filings**: 8-K for material events (earnings, acquisitions)
- **Job postings**: LinkedIn/Greenhouse for hiring signals (product direction)
- **Analyst reports**: Gartner, IDC, Forrester alert keywords

## Workflow

1. **Pull stock data** (RBRK, CVLT): Price, % change, volume, after-hours moves
2. **Scan news** (last 24h): Search for company names + "data protection", "backup", "ransomware"
3. **Check competitor blogs**: Via ProjectScraper crawl of known URLs
4. **Check RSS feeds**: Via blogwatcher skill for subscribed feeds
5. **Score and rank**: Filter noise, keep only material items
6. **Format briefing bullets**: 3-5 bullets, most important first
7. **Inject into daily briefing**: Merge with calendar and email summary

## Sample Code: Stock Price Pull

```python
import yfinance as yf
from datetime import datetime, timedelta

def get_competitor_stocks() -> list[dict]:
    tickers = {"RBRK": "Rubrik", "CVLT": "Commvault"}
    results = []
    for ticker, name in tickers.items():
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if len(hist) >= 2:
            current = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            pct_change = ((current - prev) / prev) * 100
            results.append({
                "company": name,
                "ticker": ticker,
                "price": round(current, 2),
                "change_pct": round(pct_change, 2),
                "volume": int(hist["Volume"].iloc[-1]),
                "market_cap": stock.info.get("marketCap"),
            })
    return results
```

## Sample Code: News Aggregation

```python
import json
from datetime import datetime

# Use web search (via WebSearch tool or requests to news APIs)
SEARCH_QUERIES = [
    "Rubrik RBRK earnings announcement",
    "Commvault CVLT data protection news",
    "Veeam backup product launch",
    "Rubrik Commvault Veeam pricing",
    "data protection ransomware vendor",
]

def score_news_item(title: str, snippet: str) -> int:
    """Score 0-10 based on relevance to competitive intel."""
    high_keywords = ["earnings", "revenue", "acquisition", "partnership", "pricing",
                     "layoff", "IPO", "ransomware", "Gartner", "Magic Quadrant"]
    med_keywords = ["product", "launch", "update", "customer", "deal", "cloud"]
    score = 0
    text = (title + " " + snippet).lower()
    for kw in high_keywords:
        if kw.lower() in text:
            score += 3
    for kw in med_keywords:
        if kw.lower() in text:
            score += 1
    return min(score, 10)

def format_briefing_bullets(stocks: list[dict], news: list[dict]) -> str:
    """Format top items into daily briefing bullets."""
    lines = ["## Competitive Intel\n"]
    # Stock moves
    for s in stocks:
        direction = "up" if s["change_pct"] > 0 else "down"
        lines.append(f"- **{s['company']}** ({s['ticker']}): ${s['price']} "
                      f"({direction} {abs(s['change_pct'])}%)")
    # Top 3 news items by score
    ranked = sorted(news, key=lambda x: x.get("score", 0), reverse=True)[:3]
    for item in ranked:
        lines.append(f"- {item['title']} — {item['source']}")
    return "\n".join(lines)
```

## Alerting Rules

| Condition                          | Action                        |
|------------------------------------|-------------------------------|
| Stock moves > 5% in a day         | Flag as HIGH in briefing      |
| Earnings release detected (8-K)   | Trigger earnings-analyzer     |
| Product launch or pricing change   | Summarize with link           |
| Acquisition announcement           | Immediate alert + analysis    |
| Gartner/IDC report published       | Flag for Eric review          |

## Error Handling

- **yfinance timeout**: Retry once after 5s. Use cached data from `memory/market-data-cache.json`.
- **News API rate limit**: Spread queries over 60s window. Fall back to cached results.
- **ProjectScraper unavailable**: Skip blog monitoring, note gap in briefing.
- **No material news found**: Output "No significant competitor activity in last 24h."
- Log all failures to `memory/incidents.jsonl`.

## Integration Points

- **blogwatcher skill**: Provides RSS feed items for competitor blogs
- **ProjectScraper** (`~/ProjectScraper/`): Crawls competitor websites for changes
- **earnings-analyzer**: Triggered when 8-K earnings filing detected
- **financial-report-gen**: For weekly competitive summary report
- **Daily briefing pipeline**: Output merged into 6 AM email via `gog gmail send`
- **Google Sheets**: Historical stock and news tracking log
- **memory/competitive-intel-cache.json**: Last-known-good data for fallback

## Output Format

Daily briefing section (Markdown, converted to HTML for email):

```
## Competitive Intel — 2026-03-25

**Stock Watch**
- Rubrik (RBRK): $42.15 (up 2.3%, vol 1.2M)
- Commvault (CVLT): $138.90 (down 0.8%, vol 450K)

**News & Activity**
- Rubrik announces FedRAMP High authorization for Gov Cloud — CRN
- Commvault Q4 earnings beat: subscription ARR up 28% YoY — SEC 8-K
- No significant Veeam news in last 24h

**Action Items**
- [ ] Review Commvault earnings detail (earnings-analyzer triggered)
```
