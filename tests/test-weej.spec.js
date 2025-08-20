const { test, expect } = require('@playwright/test');

test('Check WEEJ token visibility', async ({ page }) => {
  // Go to the main page
  await page.goto('https://lively-torrone-8199e0.netlify.app');
  
  // Wait for the page to load
  await page.waitForTimeout(5000);
  
  // Take a screenshot to see what's on the page
  await page.screenshot({ path: 'weej-page-loaded.png', fullPage: true });
  
  // Check if we're on the recent calls tab
  console.log('Checking page structure...');
  
  // Try to find any ticker elements to confirm data is loading
  const tickers = await page.locator('span.font-semibold.text-white').all();
  console.log(`Found ${tickers.length} ticker elements on page`);
  
  if (tickers.length > 0) {
    // Get first few ticker names
    for (let i = 0; i < Math.min(5, tickers.length); i++) {
      const text = await tickers[i].textContent();
      console.log(`  Ticker ${i + 1}: ${text}`);
    }
  }
  
  // Check if WEEJ is visible anywhere
  const weejVisible = await page.locator('text="WEEJ"').isVisible().catch(() => false);
  console.log(`WEEJ visible on page: ${weejVisible}`);
  
  if (!weejVisible) {
    // Try using the API directly to understand what's happening
    console.log('\nChecking API for WEEJ...');
    
    const apiResponse = await page.evaluate(async () => {
      const response = await fetch('https://lively-torrone-8199e0.netlify.app/api/recent-calls?search=WEEJ');
      const data = await response.json();
      return {
        totalCount: data.totalCount,
        hasWeej: data.data?.some(call => call.ticker === 'WEEJ'),
        firstTicker: data.data?.[0]?.ticker,
        error: data.error
      };
    });
    
    console.log('API Response:', apiResponse);
    
    // Check filters that might be excluding WEEJ
    console.log('\nChecking why WEEJ might be filtered out...');
    
    // WEEJ has: analysis_score: 1, no X score, no website score
    // ROI and ATH ROI are null, liquidity is 10.75
    
    console.log('WEEJ properties:');
    console.log('  - Analysis score: 1 (very low)');
    console.log('  - X analysis score: None');
    console.log('  - Website score: None');
    console.log('  - Liquidity: $10.75 (very low)');
    console.log('  - ROI: None');
    console.log('  - ATH ROI: None');
    console.log('');
    console.log('Possible reasons for exclusion:');
    console.log('  1. "Exclude Rugs" filter might be active (WEEJ has no ROI data)');
    console.log('  2. Liquidity filter might exclude tokens < $1000');
    console.log('  3. Score filters might exclude low-scoring tokens');
  }
  
  // Try searching if search exists
  const searchInput = await page.locator('input[type="text"]').first();
  if (await searchInput.count() > 0) {
    console.log('\nFound search input, trying to search for WEEJ...');
    await searchInput.fill('WEEJ');
    await page.waitForTimeout(2000);
    
    const afterSearch = await page.locator('text="WEEJ"').isVisible().catch(() => false);
    console.log(`WEEJ visible after search: ${afterSearch}`);
    
    if (!afterSearch) {
      const noResults = await page.locator('text=/no.*found/i').textContent().catch(() => 'No message');
      console.log('Search result message:', noResults);
    }
    
    await page.screenshot({ path: 'weej-search-result.png', fullPage: true });
  }
});