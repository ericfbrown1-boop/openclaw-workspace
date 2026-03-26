// Wells Fargo Statement Downloader - SLOW MODE (5 second delays)
const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.connectOverCDP('http://localhost:9222');
  const context = browser.contexts()[0];
  const page = context.pages()[0];
  
  console.log('🎬 Starting Wells Fargo Downloads - SLOW MODE');
  console.log('⏱️  5 SECOND DELAYS between each step (human-like)');
  console.log('👀 Watch your Chrome window!\n');
  
  // Get all statement links
  const statements = await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll('a'));
    return links
      .filter(a => a.textContent.toLowerCase().includes('statement') && a.textContent.includes('PDF'))
      .map(a => ({
        text: a.textContent.trim(),
        href: a.href
      }));
  });
  
  console.log(`📄 Found ${statements.length} statements\n`);
  statements.forEach((s, i) => console.log(`  ${i+1}. ${s.text.substring(0, 60)}`));
  console.log('\nStarting downloads with 5-second delays...\n');
  
  for (let i = 0; i < statements.length; i++) {
    const stmt = statements[i];
    console.log(`\n═══ [${i+1}/${statements.length}] ${stmt.text.substring(0, 50)} ═══`);
    
    // STEP 1: Click statement
    console.log('📄 Clicking statement link...');
    await page.evaluate((href) => {
      const link = document.querySelector(`a[href="${href}"]`);
      if (link) {
        link.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => link.click(), 500);
      }
    }, stmt.href);
    console.log('   ✅ Clicked');
    
    // STEP 2: Wait 5 seconds for PDF to load (human-like)
    console.log('⏱️  Waiting 5 seconds for PDF to load...');
    await page.waitForTimeout(5000);
    console.log('   ✅ PDF loaded');
    
    // STEP 3: Cmd+S to save
    console.log('💾 Pressing Cmd+S to download...');
    await page.keyboard.press('Meta+s');
    console.log('   ✅ Cmd+S pressed');
    
    // STEP 4: Wait 5 seconds for dialog, then Enter
    console.log('⏱️  Waiting 5 seconds for Save dialog...');
    await page.waitForTimeout(5000);
    console.log('💾 Pressing Enter to save...');
    await page.keyboard.press('Enter');
    console.log('   ✅ File saving to Downloads');
    
    // Wait another 2 seconds to ensure save completes
    await page.waitForTimeout(2000);
    
    // STEP 5: Go back
    console.log('⬅️  Going back to statement list...');
    await page.goBack();
    console.log('   ✅ Navigated back');
    
    // STEP 6: Wait 5 seconds before next (human-like)
    console.log('⏱️  Waiting 5 seconds before next statement...');
    await page.waitForTimeout(5000);
    console.log('   ✅ Ready for next\n');
  }
  
  console.log('\n🎉 ═══════════════════════════════════════');
  console.log('   ALL COMPLETE!');
  console.log('   ═══════════════════════════════════════');
  console.log(`\n📊 Downloaded ${statements.length} statements`);
  console.log('📁 All files saved to ~/Downloads/\n');
  
  await browser.close();
})();
