// crawler_v2.js — Sequential crawler (one page at a time + 3s delay + save-after-each)
// Reviewed & hardened for OpenClaw ProjectScraper (March 2026)

const fs = require('fs/promises');
const path = require('path');

const OUTPUT_FILE = path.join(__dirname, 'results.jsonl');

async function scrapePage(url) {
  // ←←← REPLACE THIS WITH YOUR REAL SCRAPING CODE
  console.log(`🌐 Scraping: ${url}`);

  // Placeholder — delete/replace with your actual logic (axios, puppeteer, etc.)
  const data = {
    title: "Example title from " + url,
    content: "Your real scraped data here",
    timestamp: new Date().toISOString()
  };

  return { url, ...data };
}

async function saveResult(result) {
  const line = JSON.stringify(result) + '\n';
  await fs.appendFile(OUTPUT_FILE, line, 'utf8');
  console.log(`💾 Saved: ${result.url}`);
}

async function main() {
  // ←←← PUT YOUR REAL URL LIST HERE
  const urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    // Add as many as you want — processed ONE AT A TIME
  ];

  console.log(`🚀 Starting sequential crawl of ${urls.length} pages (3s delay between each)...`);

  for (const url of urls) {
    try {
      const result = await scrapePage(url);
      await saveResult(result);                    // ← saved immediately after each page
      await new Promise(r => setTimeout(r, 3000)); // ← 3 second delay
    } catch (err) {
      console.error(`❌ Failed ${url}:`, err.message);
      // Continues to next page — never crashes the whole run
    }
  }

  console.log('✅ Crawl complete! Results saved to:', OUTPUT_FILE);
}

main().catch(console.error);
