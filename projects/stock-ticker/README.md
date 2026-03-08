# 📈 Stock Ticker Price Checker

A lightweight Node.js CLI that reads stock tickers from a CSV file, fetches current prices via Yahoo Finance, and prints a color-coded terminal table.

---

## Features

- 🗂 **CSV-driven watchlist** — add/remove tickers with a simple text file
- 🌐 **No API key required** — uses the unofficial `yahoo-finance2` library
- 🎨 **Color-coded output** — green for gains, red for losses
- ⚡ **Parallel fetching** — all symbols fetched concurrently with `Promise.allSettled()`
- 🛡 **Graceful error handling** — one bad ticker won't kill the whole run
- ⏱ **Timing output** — shows how long the fetch took

---

## Requirements

- Node.js ≥ 18.0.0
- npm

---

## Installation

```bash
git clone <repo-url>
cd stock-ticker
npm install
```

---

## Usage

```bash
# Use default tickers.csv in the current directory
node index.js

# Specify a custom CSV file
node index.js --file ./my-watchlist.csv
node index.js -f /path/to/tickers.csv

# Disable colors (e.g., for piping to a log file)
node index.js --no-color

# Show help
node index.js --help
```

---

## CSV Format

The CSV file must have a `ticker` column header. An optional `label` column is ignored but allowed.

```csv
ticker,label
AAPL,Apple Inc.
MSFT,Microsoft
GOOGL,Alphabet
AMZN,Amazon
TSLA,Tesla
RBRK,Rubrik
CVLT,Commvault
```

**Rules:**
- Header row with `ticker` column is required
- Whitespace is trimmed automatically
- Symbols are uppercased automatically
- Duplicate tickers are deduplicated (first occurrence wins)
- Empty rows are skipped with a warning

---

## Sample Output

```
📈 Stock Ticker Price Checker

  Loading: /path/to/tickers.csv
  Symbols: AAPL, MSFT, GOOGL, AMZN, TSLA, RBRK, CVLT

┌──────────┬────────────────────────┬────────────┬────────────┬────────────┬──────────┬──────────┐
│ Ticker   │ Name                   │ Price      │ Change     │ Change %   │ Market   │ Currency │
├──────────┼────────────────────────┼────────────┼────────────┼────────────┼──────────┼──────────┤
│ AAPL     │ Apple Inc.             │ 212.45     │ +1.34      │ +0.63%     │ REGULAR  │ USD      │
│ MSFT     │ Microsoft Corporation  │ 468.18     │ -2.11      │ -0.45%     │ REGULAR  │ USD      │
│ GOOGL    │ Alphabet Inc.          │ 175.60     │ +0.85      │ +0.49%     │ REGULAR  │ USD      │
│ AMZN     │ Amazon.com, Inc.       │ 201.32     │ +3.44      │ +1.74%     │ REGULAR  │ USD      │
│ TSLA     │ Tesla, Inc.            │ 276.98     │ -5.02      │ -1.78%     │ REGULAR  │ USD      │
│ RBRK     │ Rubrik, Inc.           │ 64.55      │ +1.20      │ +1.90%     │ REGULAR  │ USD      │
│ CVLT     │ Commvault Systems      │ 145.33     │ +0.67      │ +0.46%     │ REGULAR  │ USD      │
└──────────┴────────────────────────┴────────────┴────────────┴────────────┴──────────┴──────────┘
  7 symbols processed • 7 succeeded • fetched in 1.23s
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All symbols fetched successfully |
| `1` | Fatal error (CSV not found, no network, all symbols failed) |
| `2` | Partial success — some symbols failed, others succeeded |

This makes the tool composable in shell scripts:

```bash
node index.js && echo "All good!" || echo "Some failures"
```

---

## File Structure

```
stock-ticker/
├── index.js        # CLI entry point (arg parsing + orchestration)
├── csv.js          # CSV reader + ticker validation
├── quotes.js       # yahoo-finance2 wrapper
├── format.js       # Color table renderer
├── utils.js        # Shared helpers (number/percent formatting)
├── tickers.csv     # Default watchlist
├── package.json
└── README.md
```

---

## ⚠️ Important Caveat

This tool uses [`yahoo-finance2`](https://github.com/gadicc/node-yahoo-finance2), an **unofficial** Yahoo Finance API wrapper. That means:

- ✅ Great for personal/internal use — no API key, no account, no cost
- ❌ Not suitable for regulated, commercial, or mission-critical workloads
- ⚡ Yahoo could change their internal response format at any time, which may require a library update

For production-grade use, consider [Finnhub](https://finnhub.io/) or [Twelve Data](https://twelvedata.com/) (both have free tiers with official APIs).

---

## Future Enhancements

- `--sort <field>` — sort by ticker, price, or change percent
- `--json` — output raw JSON for scripting
- ETF and crypto support
- Caching within a single run
- Fallback provider if Yahoo is unavailable

---

## License

MIT
