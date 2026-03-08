/**
 * csv.js — Load and validate ticker symbols from a CSV file
 */
import { createReadStream, existsSync } from 'fs';
import { parse } from 'csv-parse';
import { normalizeTicker } from './utils.js';

/**
 * Reads a CSV file and returns a deduplicated array of normalized ticker symbols.
 * The CSV must have a 'ticker' column header.
 *
 * @param {string} filePath - Path to the CSV file
 * @returns {Promise<string[]>} Array of uppercase ticker symbols
 */
export async function loadTickers(filePath) {
  if (!existsSync(filePath)) {
    throw new Error(`CSV file not found: ${filePath}`);
  }

  return new Promise((resolve, reject) => {
    const tickers = [];
    let headerValidated = false;

    const stream = createReadStream(filePath).pipe(
      parse({
        columns: true,
        skip_empty_lines: true,
        trim: true,
      })
    );

    stream.on('data', (row) => {
      // Validate that the 'ticker' column exists (check on first row)
      if (!headerValidated) {
        const keys = Object.keys(row).map((k) => k.toLowerCase().trim());
        if (!keys.includes('ticker')) {
          stream.destroy(new Error("CSV must include a 'ticker' column"));
          return;
        }
        headerValidated = true;
      }

      const symbol = normalizeTicker(row.ticker);
      if (symbol) {
        tickers.push(symbol);
      } else {
        console.warn(`Warning: skipping empty ticker row`);
      }
    });

    stream.on('end', () => {
      if (tickers.length === 0) {
        return reject(new Error('No tickers found in CSV'));
      }

      // Deduplicate while preserving order
      const seen = new Set();
      const unique = tickers.filter((t) => {
        if (seen.has(t)) {
          console.warn(`Warning: duplicate ticker '${t}' skipped`);
          return false;
        }
        seen.add(t);
        return true;
      });

      resolve(unique);
    });

    stream.on('error', (err) => {
      reject(new Error(`Failed to read CSV: ${err.message}`));
    });
  });
}
