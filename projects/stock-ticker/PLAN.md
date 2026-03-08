# Stock Ticker Price Checker — Project Plan

## Goal
Build a small Node.js CLI tool that:
- reads stock tickers from a CSV file,
- fetches current prices from a free stock data source,
- prints a clean color-coded table in the terminal,
- stays simple enough for a solo developer to build and maintain,
- avoids a database and unnecessary infrastructure.

---

## Recommendation
**Use `yahoo-finance2` as the primary data source.**

### Why this is the best fit
For this project, the key constraint is **free + simple + no API key preferred**. `yahoo-finance2` is the best match because:
- **No API key required**
- Strong **Node.js / TypeScript support**
- Easy `quote(symbol)` API for current prices
- Good fit for a lightweight CLI
- No account setup or secret management
- Minimal code and friction for a solo developer

### Important tradeoff
`yahoo-finance2` is an **unofficial Yahoo Finance wrapper**, not an official paid market-data product. That means:
- it is excellent for a personal/internal CLI,
- but it is not ideal for regulated, commercial, or mission-critical production workloads,
- Yahoo response formats can occasionally change.

For a small CLI utility, that tradeoff is worth it.

---

## API Options Comparison

| Option | API Key Needed | Free Tier | Pros | Cons | Verdict |
|---|---:|---|---|---|---|
| **yahoo-finance2** | **No** | Free, no signup | Best Node DX, no secrets, simple quote lookup, ideal for CLI tools | Unofficial API, possible breakage if Yahoo changes internals | **Recommended** |
| **Alpha Vantage** | Yes | Free but restrictive | Official docs, popular, simple REST API | Current free limit is commonly cited as low; key management required; can throttle quickly | Good backup, not first choice |
| **Finnhub** | Yes | Free tier available | Real-time quote endpoint, cleaner “official API” feel, solid data product | Requires signup/API key; rate limits and plan boundaries may change | Strong second choice if official-style API preferred |
| **Twelve Data** | Yes | Free tier available | Nice docs, broad market coverage, quote/latest endpoints | Requires key, usage credits/rate limits, more operational friction | Fine, but overkill here |

### Source notes from current research
- `yahoo-finance2` GitHub/README shows direct Node usage like `await yahooFinance.quote('AAPL')` and explicitly notes it is an unofficial Yahoo Finance API wrapper.
- Alpha Vantage’s premium page states the free offering exists but that the standard free usage limit is **25 API requests per day** before premium plans.
- Finnhub and Twelve Data both have free offerings, but both add account/key management, which is unnecessary friction for this specific tool.

---

## Recommended Architecture
Keep it boring and small.

### High-level flow
1. User runs CLI with a CSV file path.
2. App parses the CSV and extracts ticker symbols.
3. App normalizes and deduplicates symbols.
4. App fetches quote data for each symbol using `yahoo-finance2`.
5. App maps results into a display-friendly structure.
6. App prints a color-coded terminal table.
7. App exits with a success/non-zero code depending on whether errors occurred.

### Architecture style
A **simple layered CLI**:
- **CLI layer**: parse arguments and orchestrate flow
- **CSV layer**: load/validate ticker input
- **Quote service**: fetch data from Yahoo
- **Formatter layer**: render terminal output

This is enough structure to stay clean without turning a tiny CLI into a framework.

---

## Minimal File Structure

```text
stock-ticker/
├─ package.json
├─ README.md
├─ .gitignore
├─ sample-tickers.csv
└─ src/
   ├─ index.js           # CLI entry point
   ├─ csv.js             # read + validate CSV input
   ├─ quotes.js          # yahoo-finance2 wrapper
   ├─ format.js          # console table + colors
   └─ utils.js           # small shared helpers
```

### If using TypeScript instead

```text
stock-ticker/
├─ package.json
├─ tsconfig.json
├─ README.md
├─ .gitignore
├─ sample-tickers.csv
└─ src/
   ├─ index.ts
   ├─ csv.ts
   ├─ quotes.ts
   ├─ format.ts
   └─ utils.ts
```

### Recommendation on JS vs TS
For this project, I’d still lean **TypeScript** if the developer is comfortable with it, because market data objects can be inconsistent and types help.

If the goal is **absolute minimum setup**, use plain **Node.js + ESM JavaScript**.

**Best practical choice:** plain JS first, unless Eric explicitly wants TS.

---

## Dependencies

### Core dependencies
- **`yahoo-finance2`** — fetch stock quotes
- **`csv-parse`** or **`csv-parser`** — parse CSV input
- **`chalk`** — color-coded terminal output
- **`cli-table3`** — nicely formatted console tables
- **`commander`** *(optional but useful)* — CLI argument parsing

### Optional helper dependencies
- **`p-limit`** — cap concurrent API requests if fetching many symbols
- **`zod`** — schema validation for input rows/config

### Minimal dependency set I recommend
```bash
npm install yahoo-finance2 csv-parse chalk cli-table3 commander
```

### Why not more?
No need for:
- Express
- dotenv (unless adding optional fallback API keys later)
- a database
- logging frameworks
- config frameworks
- testing frameworks on day one unless desired

This should stay tiny.

---

## CSV Input Design
Keep the CSV forgiving.

### Recommended format
Support a header row with at least:

```csv
ticker
AAPL
MSFT
GOOGL
NVDA
TSLA
```

### Nice optional format
Allow extra columns for future use, but only require `ticker`:

```csv
ticker,label
AAPL,Apple
MSFT,Microsoft
GOOGL,Alphabet
```

### Rules
- Required column: **`ticker`**
- Trim whitespace
- Convert symbols to uppercase
- Ignore blank rows
- Deduplicate repeated symbols

### Validation examples
Valid:
- `AAPL`
- `BRK-B` *(may require symbol normalization handling depending on source expectations)*
- `MSFT`

Potential edge handling:
- Empty ticker → skip with warning
- Invalid header → fail fast with helpful message
- Duplicate tickers → keep one entry

### Recommendation
Start with **exactly one required column: `ticker`**. Anything else is optional and ignored for MVP.

---

## Output Format
The terminal output should be fast to scan.

### Suggested columns
- **Ticker**
- **Name** *(if available)*
- **Price**
- **Change**
- **Change %**
- **Market State** *(regular / pre / post when available)*
- **Currency**

### Example output

```text
┌────────┬──────────────┬─────────┬─────────┬──────────┬─────────────┬──────────┐
│ Ticker │ Name         │ Price   │ Change  │ Change % │ Market      │ Currency │
├────────┼──────────────┼─────────┼─────────┼──────────┼─────────────┼──────────┤
│ AAPL   │ Apple Inc.   │ 212.45  │ +1.34   │ +0.63%   │ REGULAR     │ USD      │
│ MSFT   │ Microsoft    │ 468.18  │ -2.11   │ -0.45%   │ REGULAR     │ USD      │
│ NVDA   │ NVIDIA       │ 118.77  │ +3.08   │ +2.66%   │ POST        │ USD      │
└────────┴──────────────┴─────────┴─────────┴──────────┴─────────────┴──────────┘
```

### Color rules
- **Green**: positive change
- **Red**: negative change
- **Yellow/gray**: no change or unavailable data
- Optional:
  - blue/cyan for headers
  - dim text for warnings/footer

### Footer summary (optional but nice)
```text
3 symbols processed • 3 succeeded • 0 failed
```

---

## Data Fields to Use from Yahoo
From `yahoo-finance2 quote()` results, likely useful fields include:
- `symbol`
- `shortName` or `longName`
- `regularMarketPrice`
- `regularMarketChange`
- `regularMarketChangePercent`
- `marketState`
- `currency`

### Display fallback logic
- Name: `shortName ?? longName ?? '-'`
- Price: `regularMarketPrice ?? '-'`
- Change: `regularMarketChange ?? '-'`
- Change %: `regularMarketChangePercent ?? '-'`
- Market state: `marketState ?? 'UNKNOWN'`
- Currency: `currency ?? '-'`

---

## Error Handling Strategy
This matters more than fancy features.

### 1) CSV errors
Fail fast for structural issues.

Handle:
- file not found
- unreadable file
- missing `ticker` column
- empty CSV

User-facing examples:
- `Error: CSV file not found: ./tickers.csv`
- `Error: CSV must include a 'ticker' column`
- `Error: No tickers found in CSV`

### 2) Per-symbol API errors
Do **not** let one bad symbol kill the whole run.

Handle per symbol:
- invalid ticker
- delisted ticker
- quote missing fields
- network timeout / transient fetch failure

Behavior:
- continue processing other symbols
- display failed symbol with `ERROR` / `N/A`
- print warning summary at end

### 3) Global API/network failures
If Yahoo is fully unavailable:
- print a concise error
- return non-zero exit code

Example:
- `Error: Quote service unavailable. Please try again later.`

### 4) Exit codes
Use simple CLI-friendly exit codes:
- `0` → all good
- `1` → fatal input/runtime error
- `2` → partial success (some symbols failed)

That makes the tool scriptable.

---

## Concurrency Recommendation
For a small watchlist, sequential requests are okay. But a tiny concurrency limit is better.

### Recommendation
Use **`p-limit` with concurrency 3–5** if:
- more than ~10 symbols are expected,
- or you want gentler rate behavior.

For an MVP with small CSV files, you can even skip `p-limit` and keep it simple.

**My call:** implement `Promise.allSettled()` first; add `p-limit` only if the symbol count grows.

---

## CLI UX Recommendation

### Command shape
```bash
node src/index.js --file ./tickers.csv
```

### Optional alias after package.json setup
```bash
stock-ticker --file ./tickers.csv
```

### Useful flags
- `-f, --file <path>` — input CSV path
- `--no-color` — disable ANSI colors
- `--sort <field>` *(optional later)* — sort by ticker, price, or change

### MVP CLI behavior
Only require:
- `--file`

Everything else can wait.

---

## Proposed Implementation Outline

### `src/index.js`
Responsibilities:
- parse CLI args
- call CSV reader
- call quote fetcher
- call formatter
- set exit code

### `src/csv.js`
Responsibilities:
- read file from disk
- parse CSV
- validate `ticker` column
- normalize symbols
- dedupe symbols

Pseudo-shape:
```js
export async function loadTickers(filePath) {
  // returns ['AAPL', 'MSFT', 'NVDA']
}
```

### `src/quotes.js`
Responsibilities:
- wrap `yahoo-finance2`
- fetch quote per symbol
- map raw quote to safe display object
- handle per-symbol failures cleanly

Pseudo-shape:
```js
export async function fetchQuotes(symbols) {
  // returns [{ symbol, price, change, changePercent, ... }]
}
```

### `src/format.js`
Responsibilities:
- render table
- apply color rules
- render warnings/summary

Pseudo-shape:
```js
export function printQuotesTable(rows) {
  // console output only
}
```

### `src/utils.js`
Small helpers only:
- number formatting
- percent formatting
- symbol normalization
- market-state label cleanup

---

## Pseudocode Flow

```js
async function main() {
  const filePath = getCliFileArg();
  const symbols = await loadTickers(filePath);

  const results = await fetchQuotes(symbols);

  printQuotesTable(results);

  const failed = results.filter(r => r.status === 'error');
  if (failed.length === symbols.length) process.exit(1);
  if (failed.length > 0) process.exit(2);
  process.exit(0);
}
```

---

## Sample Output Data Model

```js
[
  {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    price: 212.45,
    change: 1.34,
    changePercent: 0.63,
    marketState: 'REGULAR',
    currency: 'USD',
    status: 'ok'
  },
  {
    symbol: 'BADTICKER',
    name: null,
    price: null,
    change: null,
    changePercent: null,
    marketState: null,
    currency: null,
    status: 'error',
    error: 'Quote not found'
  }
]
```

---

## README Scope
The README should include:
- what the tool does
- install steps
- sample CSV format
- how to run it
- sample output
- caveat that Yahoo Finance is unofficial

### Example install/run
```bash
npm install
node src/index.js --file ./sample-tickers.csv
```

---

## MVP vs Later Enhancements

### MVP
- Read `ticker` column from CSV
- Fetch current quotes via `yahoo-finance2`
- Print color-coded table
- Gracefully handle bad symbols

### Nice next steps later
- sorting (`--sort changePercent`)
- output as JSON (`--json`)
- support ETFs/crypto if quote source allows
- optional watchlist labels from CSV
- caching during a single run
- fallback provider if Yahoo fails

### Not needed now
- database
- auth system
- web UI
- scheduling
- persistence layer
- background jobs

---

## Implementation Steps

### Step 1 — Bootstrap project
- create folder structure
- initialize `package.json`
- set Node ESM mode or TypeScript config
- install dependencies

### Step 2 — Build CSV reader
- load file
- parse rows
- validate header
- normalize/dedupe tickers

### Step 3 — Build quote service
- wire in `yahoo-finance2`
- fetch quote for one symbol
- map raw fields to a consistent internal object
- handle missing/invalid symbols

### Step 4 — Build formatter
- create console table
- add green/red/yellow colors
- format currency/percent values

### Step 5 — Connect CLI entry point
- parse `--file`
- call reader → quote service → formatter
- return appropriate exit code

### Step 6 — Test with realistic CSVs
Test cases:
- valid watchlist
- duplicate symbols
- lowercase symbols
- empty file
- invalid/missing ticker column
- mix of valid + invalid symbols

### Step 7 — Write README
- include setup, usage, CSV example, limitations

---

## Practical Recommendation Summary

### Best API choice
**Use `yahoo-finance2`.**

### Why
It best matches the actual project constraints:
- free
- no API key preferred
- Node-friendly
- minimal setup
- perfect for a personal CLI

### Best stack
- Node.js
- `yahoo-finance2`
- `csv-parse`
- `chalk`
- `cli-table3`
- optionally `commander`

### Best project shape
A tiny CLI with 4–5 source files and no database.

---

## Final Call
If I were building this today for a solo developer, I would choose:
- **JavaScript (ESM)** for lowest setup friction
- **`yahoo-finance2`** for quote retrieval
- **`csv-parse` + `chalk` + `cli-table3`** for input/output
- **simple layered modules** instead of overengineering

That gets you to a working, maintainable stock price checker very quickly.
