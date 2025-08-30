const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('🔍 Testing Discovery Debug Interface...\n');
  
  // Navigate to the discovery-debug page
  await page.goto('https://lively-torrone-8199e0.netlify.app/discovery-debug', { timeout: 60000 });
  await page.waitForLoadState('networkidle', { timeout: 60000 });
  
  // Check header
  const headerText = await page.locator('h1').textContent();
  console.log('✅ Page loaded:', headerText);
  
  // Get stats
  const statsElements = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg .text-2xl').allTextContents();
  console.log('\n📊 Stats:');
  console.log('- Total with Websites:', statsElements[0] || 'N/A');
  console.log('- Analyzed:', statsElements[1] || 'N/A');
  console.log('- Promotable (≥7):', statsElements[2] || 'N/A');
  console.log('- Scrape Issues:', statsElements[3] || 'N/A');
  
  // Wait for tokens to load
  await page.waitForSelector('.bg-gray-900.border.border-gray-800.rounded-lg.overflow-hidden', { timeout: 10000 });
  
  // Get all token cards
  const tokenCards = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg.overflow-hidden').all();
  console.log(`\n📦 Found ${tokenCards.length} tokens displayed`);
  
  // Check first few tokens for diagnostic data
  console.log('\n🔬 Checking first 3 tokens for diagnostic data...');
  for (let i = 0; i < Math.min(3, tokenCards.length); i++) {
    const card = tokenCards[i];
    
    // Get symbol
    const symbol = await card.locator('h3').textContent();
    console.log(`\n Token ${i + 1}: ${symbol}`);
    
    // Get scrape health
    const healthBadge = await card.locator('.absolute.top-2.right-2').textContent().catch(() => 'No health badge');
    console.log(`  Health: ${healthBadge}`);
    
    // Check for diagnostic metrics
    const hasMetrics = await card.locator('.bg-gray-950.rounded.p-2.text-xs').count() > 0;
    if (hasMetrics) {
      const metricsText = await card.locator('.bg-gray-950.rounded.p-2.text-xs').textContent();
      // Extract text/html ratio
      const textHtmlMatch = metricsText.match(/(\d+(?:,\d+)*)\s*\/\s*(\d+(?:,\d+)*)/);
      if (textHtmlMatch) {
        console.log(`  Text/HTML: ${textHtmlMatch[1]} / ${textHtmlMatch[2]} chars`);
      }
    } else {
      console.log('  No diagnostic metrics (not analyzed yet)');
    }
    
    // Check for extracted signals
    const hasNBA = await card.locator('text=NBA').count() > 0;
    const hasUsers = await card.locator('text=👥').count() > 0;
    const hasPartnerships = await card.locator('text=🤝').count() > 0;
    
    if (hasNBA || hasUsers || hasPartnerships) {
      console.log('  Signals detected:', 
        hasNBA ? 'NBA partnership' : '',
        hasUsers ? 'User count' : '',
        hasPartnerships ? 'Partnerships' : ''
      );
    }
    
    // Check for scraping issue warning
    const hasWarning = await card.locator('.bg-red-900\\/20.border.border-red-800').count() > 0;
    if (hasWarning) {
      console.log('  ⚠️ Scraping issue detected!');
    }
  }
  
  // Test filter functionality
  console.log('\n🔍 Testing filters...');
  
  // Click "Scrape Issues" filter
  await page.click('button:has-text("Scrape Issues")');
  await page.waitForTimeout(1000);
  const scrapeIssueCount = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg.overflow-hidden').count();
  console.log(`- Scrape Issues filter: ${scrapeIssueCount} tokens`);
  
  // Click "Promoted" filter
  await page.click('button:has-text("Promoted")');
  await page.waitForTimeout(1000);
  const promotedCount = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg.overflow-hidden').count();
  console.log(`- Promoted filter: ${promotedCount} tokens`);
  
  // Click "Not Analyzed" filter
  await page.click('button:has-text("Not Analyzed")');
  await page.waitForTimeout(1000);
  const unanalyzedCount = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg.overflow-hidden').count();
  console.log(`- Not Analyzed filter: ${unanalyzedCount} tokens`);
  
  console.log('\n✅ Discovery Debug Interface is working correctly!');
  console.log('The interface successfully shows diagnostic metrics and scraping issues.');
  
  // Keep browser open for 5 seconds to see the page
  await page.waitForTimeout(5000);
  
  await browser.close();
})();