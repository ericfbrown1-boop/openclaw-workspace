/**
 * utils.js — Small shared helpers
 */

/**
 * Format a price number with 2 decimal places.
 */
export function formatPrice(value) {
  if (value == null || isNaN(value)) return '-';
  return value.toFixed(2);
}

/**
 * Format a change value with sign and 2 decimal places.
 */
export function formatChange(value) {
  if (value == null || isNaN(value)) return '-';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}`;
}

/**
 * Format a percent value with sign and 2 decimal places.
 */
export function formatPercent(value) {
  if (value == null || isNaN(value)) return '-';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Normalize a ticker symbol: trim whitespace and uppercase.
 */
export function normalizeTicker(symbol) {
  return (symbol || '').trim().toUpperCase();
}

/**
 * Format milliseconds into a human-readable duration string.
 */
export function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}
