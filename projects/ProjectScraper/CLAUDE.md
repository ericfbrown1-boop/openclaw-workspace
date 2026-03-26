# ProjectScraper — Claude Code Instructions

## What This Is
Node.js + Playwright web crawler for competitive intelligence. Crawls company websites (Rubrik, Commvault, Veeam, Cohesity) and outputs structured data.

## Build & Run
```bash
cd code/
npm install
node crawler_v2.js
```
- Requires: Node.js, Playwright with Chromium
- Output: `results.jsonl` (JSON Lines format)

## Key Rules
- Add 3-second delay between requests (bot detection mitigation)
- Process URLs one at a time, NOT in batch (context window overflow)
- Run on PowerSpec for crawls >5 minutes
- Results sync back via git push

## Testing
- `npm test` (if test suite exists)
- Verify: `node -e "require('./code/crawler_v2.js')"` for import check
