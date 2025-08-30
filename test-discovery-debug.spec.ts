import { test, expect } from '@playwright/test';

test('Discovery Debug Interface', async ({ page }) => {
  // Navigate to the discovery-debug page
  await page.goto('https://lively-torrone-8199e0.netlify.app/discovery-debug');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Check that the header is present
  await expect(page.locator('h1')).toContainText('Token Discovery Debug Interface');
  
  // Check that stats are displayed
  await expect(page.locator('text=Total with Websites')).toBeVisible();
  await expect(page.locator('text=Analyzed')).toBeVisible();
  await expect(page.locator('text=Promotable')).toBeVisible();
  await expect(page.locator('text=Scrape Issues')).toBeVisible();
  
  // Check that filter buttons are present
  await expect(page.locator('button:has-text("All with Websites")')).toBeVisible();
  await expect(page.locator('button:has-text("Analyzed")')).toBeVisible();
  await expect(page.locator('button:has-text("Not Analyzed")')).toBeVisible();
  await expect(page.locator('button:has-text("Low Score")')).toBeVisible();
  await expect(page.locator('button:has-text("Scrape Issues")')).toBeVisible();
  
  // Wait for tokens to load
  await page.waitForSelector('.bg-gray-900.border.border-gray-800.rounded-lg', { timeout: 10000 });
  
  // Get all token cards
  const tokenCards = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg').all();
  console.log(`Found ${tokenCards.length} token cards`);
  
  // If there are tokens, check the first one has expected elements
  if (tokenCards.length > 0) {
    const firstCard = tokenCards[0];
    
    // Check for scrape health indicator
    const healthBadge = await firstCard.locator('.absolute.top-2.right-2').first();
    await expect(healthBadge).toBeVisible();
    const healthText = await healthBadge.textContent();
    console.log(`First token scrape health: ${healthText}`);
    
    // Check for token symbol
    const symbolElement = await firstCard.locator('h3').first();
    await expect(symbolElement).toBeVisible();
    const symbol = await symbolElement.textContent();
    console.log(`First token symbol: ${symbol}`);
    
    // Check for diagnostic metrics if present
    const metricsSection = await firstCard.locator('.bg-gray-950.rounded.p-2.text-xs');
    if (await metricsSection.count() > 0) {
      const textHtmlRatio = await metricsSection.locator('text=Text/HTML:').first();
      if (await textHtmlRatio.count() > 0) {
        console.log('Diagnostic metrics are displayed');
        
        // Check for warning if text length is low
        const warningSection = await firstCard.locator('.bg-red-900\\/20.border.border-red-800');
        if (await warningSection.count() > 0) {
          console.log('⚠️ Scraping issue warning is displayed');
          const warningText = await warningSection.textContent();
          console.log(`Warning: ${warningText}`);
        }
      }
    }
  }
  
  // Test filter functionality - click on "Scrape Issues"
  console.log('\nTesting Scrape Issues filter...');
  await page.click('button:has-text("Scrape Issues")');
  await page.waitForTimeout(1000);
  
  // Check if any tokens are shown
  const scrapeIssueCards = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg').all();
  console.log(`Found ${scrapeIssueCards.length} tokens with scrape issues`);
  
  // Test sorting functionality
  console.log('\nTesting sorting...');
  const sortDropdown = await page.locator('select').first();
  await sortDropdown.selectOption('website_stage1_score');
  await page.waitForTimeout(1000);
  
  // Test analyzing unanalyzed tokens
  console.log('\nTesting unanalyzed filter...');
  await page.click('button:has-text("Not Analyzed")');
  await page.waitForTimeout(1000);
  
  const unanalyzedCards = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg').all();
  console.log(`Found ${unanalyzedCards.length} unanalyzed tokens`);
  
  // Check promotion status indicators
  console.log('\nChecking promotion status...');
  await page.click('button:has-text("Promoted")');
  await page.waitForTimeout(1000);
  
  const promotedCards = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg').all();
  console.log(`Found ${promotedCards.length} promoted tokens (score >= 7)`);
  
  if (promotedCards.length > 0) {
    // Check that promoted tokens have the green promotion indicator
    const promotionIndicator = await promotedCards[0].locator('text=✅ Qualifies for promotion');
    if (await promotionIndicator.count() > 0) {
      console.log('✅ Promotion indicator is displayed correctly');
    }
  }
  
  console.log('\n✅ Discovery Debug Interface is working correctly!');
});

// Run the test
test('Check for specific problem tokens (APD, CLX)', async ({ page }) => {
  await page.goto('https://lively-torrone-8199e0.netlify.app/discovery-debug');
  await page.waitForLoadState('networkidle');
  
  // Search for APD token
  console.log('\nSearching for APD token...');
  const apdCards = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg:has(h3:has-text("APD"))').all();
  if (apdCards.length > 0) {
    console.log('Found APD token');
    const apdCard = apdCards[0];
    
    // Check scrape metrics
    const metricsSection = await apdCard.locator('.bg-gray-950.rounded.p-2.text-xs').first();
    if (await metricsSection.count() > 0) {
      const metricsText = await metricsSection.textContent();
      console.log(`APD metrics: ${metricsText}`);
      
      // Check if it shows low text content
      if (metricsText?.includes('21') || metricsText?.includes('chars')) {
        console.log('✅ APD shows low text content issue as expected');
      }
    }
  } else {
    console.log('APD token not found in current view');
  }
  
  // Search for CLX token
  console.log('\nSearching for CLX token...');
  const clxCards = await page.locator('.bg-gray-900.border.border-gray-800.rounded-lg:has(h3:has-text("CLX"))').all();
  if (clxCards.length > 0) {
    console.log('Found CLX token');
    const clxCard = clxCards[0];
    
    // Check for NBA partnership signal
    const signalsSection = await clxCard.locator('text=NBA').first();
    if (await signalsSection.count() > 0) {
      console.log('✅ CLX shows NBA partnership signal');
    }
    
    // Check score
    const scoreElement = await clxCard.locator('.absolute.top-2.left-2').first();
    if (await scoreElement.count() > 0) {
      const scoreText = await scoreElement.textContent();
      console.log(`CLX score: ${scoreText}`);
    }
  } else {
    console.log('CLX token not found in current view');
  }
});