---
name: earnings-analyzer
description: >
  Automated SEC earnings analysis for Cohesity, Rubrik, Commvault, and Veeam.
  Pulls 10-Q/10-K filings, calculates YoY ARR/revenue growth, margins,
  valuation multiples. Outputs Word doc + email delivery.
---

# Earnings Analyzer

## When to Use

- Quarterly earnings released for Rubrik (RBRK), Commvault (CVLT), or Veeam
- Eric asks for financial analysis or competitive benchmarking
- Daily briefing needs updated financial data
- Board prep requiring peer comparison metrics
- IPO/valuation analysis for Cohesity (private) using news + estimates

## Tracked Companies

| Company   | Ticker | Status  | Data Source                         |
|-----------|--------|---------|-------------------------------------|
| Cohesity  | —      | Private | News, press releases, analyst notes |
| Rubrik    | RBRK   | Public  | SEC EDGAR, Yahoo Finance            |
| Commvault | CVLT   | Public  | SEC EDGAR, Yahoo Finance            |
| Veeam     | —      | Private | News, press releases (Insight Partners) |

## Data Sources

- **SEC EDGAR API**: 10-Q, 10-K, 8-K filings (free, no key required for < 10 req/sec)
- **Yahoo Finance (yfinance)**: Real-time stock, market cap, enterprise value
- **Company IR pages**: Earnings call transcripts, press releases, investor decks
- **News feeds**: For private company estimates (Cohesity, Veeam)

## Workflow

1. **Detect trigger**: New filing on EDGAR or manual request from Eric
2. **Pull SEC filings**: Download latest 10-Q/10-K for RBRK and CVLT
3. **Extract financials**: Parse XBRL or HTML for revenue, ARR, margins, cash flow
4. **Pull market data**: Current stock price, market cap, EV from yfinance
5. **Calculate metrics**: YoY growth, QoQ growth, valuation multiples
6. **Compare quarters**: Build 4-quarter trend table per company
7. **Generate Word doc**: Using financial-report-gen skill
8. **Email delivery**: Via `gog gmail send` to Eric

## Key Metrics to Extract

- **Revenue**: Total, subscription, product, services (quarterly + TTM)
- **ARR**: Annual recurring revenue and net retention rate
- **Margins**: Gross (GAAP/non-GAAP), operating, net income
- **Cash flow**: Operating CF, free cash flow, FCF margin
- **Valuation**: EV/Revenue, EV/ARR, EV/non-GAAP operating income
- **Growth**: YoY revenue growth, YoY ARR growth, QoQ sequential

## Sample Code: Pull SEC Filings

```python
from sec_edgar_downloader import Downloader
import os

# SEC requires a user-agent with name and email
dl = Downloader("OpenClaw", "ericfbrown1@gmail.com", "./sec_filings")

# Download latest 10-Q for public competitors
for ticker in ["RBRK", "CVLT"]:
    dl.get("10-Q", ticker, limit=4)  # last 4 quarters
    dl.get("10-K", ticker, limit=1)  # latest annual

# Filings land in ./sec_filings/{ticker}/10-Q/
```

## Sample Code: Market Data via yfinance

```python
import yfinance as yf
from datetime import datetime

def get_market_snapshot(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "ticker": ticker,
        "price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "enterprise_value": info.get("enterpriseValue"),
        "ev_to_revenue": info.get("enterpriseToRevenue"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "pulled_at": datetime.now().isoformat(),
    }

# Pull for both public competitors
snapshots = {t: get_market_snapshot(t) for t in ["RBRK", "CVLT"]}
```

## Sample Code: Valuation Multiples

```python
def calc_multiples(ev: float, revenue_ttm: float, arr: float, nongaap_oi: float) -> dict:
    return {
        "ev_revenue": round(ev / revenue_ttm, 1) if revenue_ttm else None,
        "ev_arr": round(ev / arr, 1) if arr else None,
        "ev_nongaap_oi": round(ev / nongaap_oi, 1) if nongaap_oi and nongaap_oi > 0 else None,
    }
```

## Error Handling

- **SEC rate limit**: Max 10 requests/sec. Add `time.sleep(0.15)` between calls.
- **XBRL parsing failure**: Fall back to HTML table extraction with BeautifulSoup.
- **yfinance returns None**: Use last-known-good values from `memory/market-data-cache.json`.
- **Private company (Cohesity/Veeam)**: Log "no filing available" and use last known estimates from news.
- **Filing not yet available**: Check 8-K for earnings press release as interim source.
- Log all failures to `memory/incidents.jsonl`.

## Integration Points

- **financial-report-gen**: Passes extracted data for Word doc generation
- **competitive-intel**: Shares market cap and stock data for daily briefing
- **cohesity-domain**: References for product context in analysis commentary
- **Email**: `gog gmail send` to ericfbrown1@gmail.com + Eric.brown@cohesity.com
- **Storage**: Cache results in `memory/earnings-cache.json` keyed by ticker+quarter

## Output Format

Word document (.docx) with sections:
1. Executive Summary (2-3 sentences per company)
2. Revenue & ARR table (4 quarters, YoY growth)
3. Margin trends (gross, operating, net — GAAP and non-GAAP)
4. Cash flow summary (OCF, FCF, FCF margin)
5. Valuation multiples comparison table
6. Key takeaways for Cohesity positioning
