#!/usr/bin/env node
/**
 * index.js — Stock Ticker Price Checker CLI entry point
 *
 * Usage:
 *   node index.js [--file ./tickers.csv]
 *   node index.js --help
 */
import { program } from 'commander';
import { resolve } from 'path';
import { loadTickers } from './csv.js';
import { fetchQuotes } from './quotes.js';
import { printQuotesTable } from './format.js';
import chalk from 'chalk';

program
  .name('stock-ticker')
  .description('Fetch and display current stock prices from a CSV watchlist')
  .version('1.0.0')
  .option('-f, --file <path>', 'path to tickers CSV file', './tickers.csv')
  .option('--no-color', 'disable colored output')
  .addHelpText(
    'after',
    `
Examples:
  node index.js
  node index.js --file ./tickers.csv
  node index.js -f /path/to/watchlist.csv
  node index.js --no-color

CSV format (requires 'ticker' column):
  ticker,label
  AAPL,Apple Inc.
  MSFT,Microsoft
  TSLA,Tesla

Exit codes:
  0  All symbols fetched successfully
  1  Fatal error (bad CSV, no network, etc.)
  2  Partial success (some symbols failed)
`
  );

program.parse(process.argv);

const opts = program.opts();

async function main() {
  const filePath = resolve(opts.file);

  console.log(chalk.bold.cyan('\n📈 Stock Ticker Price Checker\n'));

  // Step 1: Load tickers from CSV
  let symbols;
  try {
    symbols = await loadTickers(filePath);
    console.log(chalk.dim(`  Loading: ${filePath}`));
    console.log(chalk.dim(`  Symbols: ${symbols.join(', ')}\n`));
  } catch (err) {
    console.error(chalk.red(`\nError: ${err.message}\n`));
    process.exit(1);
  }

  // Step 2: Fetch quotes with timing
  const startMs = Date.now();
  let results;
  try {
    results = await fetchQuotes(symbols);
  } catch (err) {
    console.error(chalk.red(`\nError: Quote service unavailable. ${err.message}\n`));
    process.exit(1);
  }
  const elapsedMs = Date.now() - startMs;

  // Step 3: Render the table
  printQuotesTable(results, { elapsedMs });

  // Step 4: Set exit code based on results
  const failed = results.filter((r) => r.status === 'error');
  if (failed.length === symbols.length) {
    process.exit(1);
  } else if (failed.length > 0) {
    process.exit(2);
  } else {
    process.exit(0);
  }
}

main().catch((err) => {
  console.error(chalk.red(`\nUnhandled error: ${err.message}\n`));
  process.exit(1);
});
