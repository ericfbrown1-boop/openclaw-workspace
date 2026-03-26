// Bank Document Downloader
// Connects to existing Chrome window and downloads all financial documents

const playwright = require('playwright');
const fs = require('fs');
const path = require('path');

async function downloadBankDocuments(bankName, startingUrl) {
  console.log(`\n🏦 Starting download for: ${bankName}`);
  console.log(`📍 Starting URL: ${startingUrl || 'Current page'}`);
  
  // Create download folder
  const downloadDir = path.join(process.env.HOME, 'Downloads', 'Tax-Documents', bankName);
  if (!fs.existsSync(downloadDir)) {
    fs.mkdirSync(downloadDir, { recursive: true });
    console.log(`✅ Created folder: ${downloadDir}`);
  }
  
  try {
    // Connect to existing Chrome instance via CDP
    const cdpEndpoint = process.env.CHROME_CDP_ENDPOINT || 'http://localhost:9222';
    console.log(`🔌 Connecting to Chrome at ${cdpEndpoint}...`);
    
    const browser = await playwright.chromium.connectOverCDP(cdpEndpoint);
    const contexts = browser.contexts();
    
    if (contexts.length === 0) {
      console.log(`❌ No browser contexts found. Make sure Chrome has a page open.`);
      await browser.close();
      return { success: false, error: 'No browser contexts available' };
    }
    
    const context = contexts[0];
    const pages = context.pages();
    
    if (pages.length === 0) {
      console.log(`❌ No pages found. Please open a page in Chrome first.`);
      await browser.close();
      return { success: false, error: 'No pages open in Chrome' };
    }
    
    // Use the currently active page
    const page = pages[pages.length - 1];
    const title = await page.title().catch(() => 'Unknown Page');
    console.log(`✅ Connected to page: ${title}`);
    
    // Navigate to starting URL if provided
    if (startingUrl) {
      console.log(`🧭 Navigating to ${startingUrl}...`);
      await page.goto(startingUrl, { waitUntil: 'networkidle' });
    }
    
    // Note: Can't set download dir in CDP mode, files will go to default Chrome download location
    console.log(`📁 Files will be downloaded to Chrome's default download folder`);
    
    // Search for document links
    console.log(`\n🔍 Searching for downloadable documents...`);
    
    const documentKeywords = [
      'statement', 'statements',
      'tax document', 'tax documents',
      '1099', '1099-INT', '1099-DIV', '1099-B',
      'report', 'reports',
      'PDF', 'download',
      'export', 'account statement'
    ];
    
    // Find all links that might be documents
    const links = await page.$$eval('a[href]', (anchors, keywords) => {
      return anchors
        .filter(a => {
          const text = a.textContent.toLowerCase();
          const href = a.href.toLowerCase();
          return keywords.some(kw => text.includes(kw) || href.includes(kw)) ||
                 href.endsWith('.pdf') ||
                 href.includes('download');
        })
        .map(a => ({
          text: a.textContent.trim(),
          href: a.href,
          isPDF: a.href.toLowerCase().endsWith('.pdf')
        }));
    }, documentKeywords);
    
    console.log(`📄 Found ${links.length} potential document links`);
    
    if (links.length === 0) {
      console.log(`⚠️  No document links found. Make sure you're on the statements/documents page.`);
      await browser.disconnect();
      return { success: false, downloaded: 0 };
    }
    
    // Display found links
    links.slice(0, 10).forEach((link, i) => {
      console.log(`  ${i + 1}. ${link.text} ${link.isPDF ? '(PDF)' : ''}`);
    });
    if (links.length > 10) {
      console.log(`  ... and ${links.length - 10} more`);
    }
    
    // Download each document
    console.log(`\n⬇️  Starting downloads...`);
    let downloaded = 0;
    
    for (let i = 0; i < links.length; i++) {
      const link = links[i];
      console.log(`\n[${i + 1}/${links.length}] Downloading: ${link.text}`);
      
      try {
        // Simply click/navigate to trigger the download
        // Chrome will handle it and save to default download folder
        await page.goto(link.href);
        await page.waitForTimeout(3000); // Wait for download to start
        downloaded++;
        console.log(`  ✅ Download initiated`);
        
        // Go back to main page
        await page.goBack({ waitUntil: 'networkidle' });
        await page.waitForTimeout(1000);
        
      } catch (error) {
        console.log(`  ⚠️  Failed: ${error.message}`);
        try {
          await page.goBack();
        } catch (e) {
          // Ignore back errors
        }
      }
      
      // Small delay between downloads
      await page.waitForTimeout(1000);
    }
    
    console.log(`\n✅ Complete! Initiated ${downloaded} downloads`);
    
    await browser.disconnect();
    return { success: true, downloaded, total: links.length, folder: downloadDir };
    
  } catch (error) {
    console.error(`\n❌ Error: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Export for use
module.exports = { downloadBankDocuments };

// CLI usage
if (require.main === module) {
  const bankName = process.argv[2] || 'Unknown-Bank';
  const startingUrl = process.argv[3];
  
  if (!bankName) {
    console.log('Usage: node bank-document-downloader.js "Bank Name" [starting-url]');
    console.log('Example: node bank-document-downloader.js "Chase" "https://secure.chase.com/statements"');
    process.exit(1);
  }
  
  downloadBankDocuments(bankName, startingUrl)
    .then(result => {
      console.log('\n📊 Result:', result);
      process.exit(result.success ? 0 : 1);
    });
}
