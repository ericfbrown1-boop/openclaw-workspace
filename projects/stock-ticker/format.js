/**
 * format.js — Render the quotes table with colors
 */
import chalk from 'chalk';
import Table from 'cli-table3';
import { formatPrice, formatChange, formatPercent, formatDuration } from './utils.js';

/**
 * Color a change value string: green for positive, red for negative, yellow for zero/null.
 */
function colorChange(value, formatted) {
  if (value == null || isNaN(value)) return chalk.dim(formatted);
  if (value > 0) return chalk.green(formatted);
  if (value < 0) return chalk.red(formatted);
  return chalk.yellow(formatted);
}

/**
 * Color the market state label.
 */
function colorMarketState(state) {
  if (!state || state === 'UNKNOWN') return chalk.dim('UNKNOWN');
  switch (state.toUpperCase()) {
    case 'REGULAR':
      return chalk.green('REGULAR');
    case 'PRE':
      return chalk.cyan('PRE');
    case 'POST':
      return chalk.magenta('POST');
    case 'CLOSED':
      return chalk.dim('CLOSED');
    default:
      return chalk.dim(state);
  }
}

/**
 * Render the full quote table to stdout.
 *
 * @param {Object[]} rows - Array of quote result objects
 * @param {Object} options
 * @param {number} [options.elapsedMs] - Total fetch time in ms (for footer)
 */
export function printQuotesTable(rows, options = {}) {
  const table = new Table({
    head: [
      chalk.bold.cyan('Ticker'),
      chalk.bold.cyan('Name'),
      chalk.bold.cyan('Price'),
      chalk.bold.cyan('Change'),
      chalk.bold.cyan('Change %'),
      chalk.bold.cyan('Market'),
      chalk.bold.cyan('Currency'),
    ],
    style: {
      head: [],
      border: ['dim'],
    },
    colWidths: [10, 26, 12, 12, 12, 10, 10],
    wordWrap: false,
  });

  for (const row of rows) {
    if (row.status === 'error') {
      table.push([
        chalk.bold.white(row.symbol),
        chalk.dim(row.name ?? '-'),
        chalk.dim('N/A'),
        chalk.dim('N/A'),
        chalk.dim('N/A'),
        chalk.dim('ERROR'),
        chalk.dim('-'),
      ]);
    } else {
      const changeStr = formatChange(row.change);
      const changePctStr = formatPercent(row.changePercent);

      table.push([
        chalk.bold.white(row.symbol),
        row.name ?? '-',
        chalk.bold(formatPrice(row.price)),
        colorChange(row.change, changeStr),
        colorChange(row.changePercent, changePctStr),
        colorMarketState(row.marketState),
        row.currency ?? '-',
      ]);
    }
  }

  console.log(table.toString());

  // Footer summary
  const total = rows.length;
  const succeeded = rows.filter((r) => r.status === 'ok').length;
  const failed = rows.filter((r) => r.status === 'error').length;

  const parts = [
    chalk.dim(`${total} symbol${total !== 1 ? 's' : ''} processed`),
    chalk.green(`${succeeded} succeeded`),
  ];
  if (failed > 0) {
    parts.push(chalk.red(`${failed} failed`));
  }
  if (options.elapsedMs != null) {
    parts.push(chalk.dim(`fetched in ${formatDuration(options.elapsedMs)}`));
  }

  console.log(chalk.dim('  ') + parts.join(chalk.dim(' • ')));

  // Show error details for failed symbols
  const errorRows = rows.filter((r) => r.status === 'error');
  if (errorRows.length > 0) {
    console.log('');
    for (const err of errorRows) {
      console.warn(chalk.yellow(`  ⚠ ${err.symbol}: ${err.error ?? 'unknown error'}`));
    }
  }
}
