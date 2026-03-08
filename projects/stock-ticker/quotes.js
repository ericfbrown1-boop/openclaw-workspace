/**
 * quotes.js — Fetch stock quotes via yahoo-finance2
 */
import YahooFinance from 'yahoo-finance2';

// Create a single instance, suppressing the survey notice
const yahooFinance = new YahooFinance({ suppressNotices: ['yahooSurvey'] });

// Fields we want from the Yahoo Finance quote response
const QUOTE_FIELDS = [
  'symbol',
  'shortName',
  'longName',
  'regularMarketPrice',
  'regularMarketChange',
  'regularMarketChangePercent',
  'marketState',
  'currency',
];

/**
 * Map a raw Yahoo Finance quote result to a clean internal object.
 */
function mapQuote(raw) {
  return {
    symbol: raw.symbol ?? '-',
    name: raw.shortName ?? raw.longName ?? '-',
    price: raw.regularMarketPrice ?? null,
    change: raw.regularMarketChange ?? null,
    changePercent: raw.regularMarketChangePercent ?? null,
    marketState: raw.marketState ?? 'UNKNOWN',
    currency: raw.currency ?? '-',
    status: 'ok',
  };
}

/**
 * Fetch quotes for an array of ticker symbols.
 * Uses Promise.allSettled so one failure doesn't kill the whole batch.
 *
 * @param {string[]} symbols - Array of ticker symbols
 * @returns {Promise<Object[]>} Array of quote result objects
 */
export async function fetchQuotes(symbols) {
  const promises = symbols.map((symbol) =>
    yahooFinance.quote(symbol, { fields: QUOTE_FIELDS }, { validateResult: false })
  );

  const settled = await Promise.allSettled(promises);

  return settled.map((result, i) => {
    const symbol = symbols[i];

    if (result.status === 'fulfilled') {
      const raw = result.value;
      if (!raw || raw.regularMarketPrice == null) {
        return {
          symbol,
          name: raw?.shortName ?? raw?.longName ?? '-',
          price: null,
          change: null,
          changePercent: null,
          marketState: raw?.marketState ?? 'UNKNOWN',
          currency: raw?.currency ?? '-',
          status: 'error',
          error: 'Price data unavailable (possibly delisted or invalid symbol)',
        };
      }
      return mapQuote(raw);
    } else {
      return {
        symbol,
        name: null,
        price: null,
        change: null,
        changePercent: null,
        marketState: null,
        currency: null,
        status: 'error',
        error: result.reason?.message ?? 'Unknown error',
      };
    }
  });
}
