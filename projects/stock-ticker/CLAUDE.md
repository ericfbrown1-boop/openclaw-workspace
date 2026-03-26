# Stock Ticker — Claude Code Instructions

## What This Is
Node.js stock price tracker. Monitors Rubrik (RBRK), Commvault (CVLT), and other tickers.

## Build & Run
```bash
npm install
node index.js
```
- Reads tickers from `tickers.csv`
- Output: formatted quotes via `format.js`

## Key Rules
- Competitive tickers: RBRK, CVLT (see USER.md)
- Run on MacBook for quick checks, PowerSpec for batch processing
- Feed results into daily briefing competitive section

## Testing
- `node -e "require('./index.js')"` for import check
- Verify: `node quotes.js` returns valid price data
