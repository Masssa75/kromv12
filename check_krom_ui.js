const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    timeout: 60000 
  });
  
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  
  const page = await context.newPage();
  
  console.log('Navigating to KROM UI...');
  await page.goto('https://krom1.com', { 
    waitUntil: 'networkidle',
    timeout: 30000 
  });
  
  // Wait for the recent calls section to load
  await page.waitForSelector('.recent-calls, [class*="calls"], div:has-text("RECENT CALLS")', { 
    timeout: 10000 
  }).catch(() => console.log('Could not find recent calls selector'));
  
  console.log('Page loaded, checking for tokens...');
  
  // Wait a bit for dynamic content
  await page.waitForTimeout(3000);
  
  // Look for our promoted tokens
  const tokenNames = ['BIO', 'LUMERIN', 'SESH', 'CARROT', 'BITTY', 'GASS', 'WTSAI'];
  
  for (const token of tokenNames) {
    const elements = await page.locator(`text="${token}"`).all();
    if (elements.length > 0) {
      console.log(`✅ Found ${token} - ${elements.length} instance(s)`);
      
      // Try to get the row context
      try {
        const row = await page.locator(`text="${token}"`).first().locator('xpath=ancestor::*[contains(@class, "row") or contains(@class, "item")]').first();
        const rowText = await row.textContent().catch(() => 'Could not get row text');
        console.log(`   Row content: ${rowText?.substring(0, 100)}...`);
      } catch (e) {
        // Try alternative approach
        const parent = await page.locator(`text="${token}"`).first().locator('..');
        const parentText = await parent.textContent().catch(() => 'Could not get parent text');
        console.log(`   Context: ${parentText?.substring(0, 100)}...`);
      }
    } else {
      console.log(`❌ ${token} not found`);
    }
  }
  
  // Check for "Discovery Pools" group
  const discoveryPools = await page.locator('text="Discovery Pools"').all();
  console.log(`\n"Discovery Pools" group found: ${discoveryPools.length} instance(s)`);
  
  // Check what tokens ARE visible
  console.log('\n--- Visible tokens in the list ---');
  const visibleTokens = await page.locator('[class*="ticker"], [class*="symbol"], div:has-text("UTILITY") + div, div:has-text("MEME") + div').allTextContents();
  console.log('First 10 visible tokens:', visibleTokens.slice(0, 10));
  
  // Check if there's any filtering active
  const filters = await page.locator('[class*="filter"], input[type="checkbox"]:checked').all();
  console.log(`\nActive filters: ${filters.length}`);
  
  // Try to get the network request to the API
  console.log('\n--- Checking API calls ---');
  
  // Set up request interception
  page.on('response', response => {
    if (response.url().includes('/api/') || response.url().includes('supabase')) {
      console.log(`API Response: ${response.url()} - Status: ${response.status()}`);
    }
  });
  
  // Try refreshing to capture API calls
  console.log('Refreshing page to capture API calls...');
  await page.reload({ waitUntil: 'networkidle' });
  
  await page.waitForTimeout(5000);
  
  // Take a screenshot
  await page.screenshot({ path: 'krom_ui_check.png', fullPage: false });
  console.log('\nScreenshot saved as krom_ui_check.png');
  
  await browser.close();
})();