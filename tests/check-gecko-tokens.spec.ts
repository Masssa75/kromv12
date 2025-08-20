const { test, expect } = require('@playwright/test');

test('Check GeckoTerminal trending tokens in UI', async ({ page }) => {
  // Go to the main interface
  await page.goto('https://lively-torrone-8199e0.netlify.app/');
  
  // Wait for the page to load
  await page.waitForSelector('.font-mono', { timeout: 10000 });
  
  // Look for gecko_trending tokens by searching for the source
  // First, let's take a screenshot of the current state
  await page.screenshot({ path: 'gecko-tokens-initial.png', fullPage: false });
  
  // Try to find tokens with gecko source - look for TROLL, ZORA, AERO, etc.
  const trollToken = await page.locator('text=TROLL').first();
  const zoraToken = await page.locator('text=ZORA').first();
  
  if (await trollToken.isVisible()) {
    console.log('Found TROLL token, clicking to check details...');
    await trollToken.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'troll-token-modal.png' });
    
    // Check what fields are present in the modal
    const modalContent = await page.locator('.fixed.inset-0').textContent();
    console.log('Modal content:', modalContent);
    
    // Close modal
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
  }
  
  // Scroll down to see more tokens
  await page.evaluate(() => window.scrollBy(0, 500));
  await page.waitForTimeout(1000);
  
  // Take screenshot of recent calls section
  await page.screenshot({ path: 'recent-calls-with-gecko.png' });
  
  // Check the table headers and data
  const headers = await page.locator('thead th').allTextContents();
  console.log('Table headers:', headers);
  
  // Find a row with gecko_trending source if visible
  const rows = await page.locator('tbody tr').all();
  console.log(`Found ${rows.length} rows in the table`);
  
  // Check first few rows for data completeness
  for (let i = 0; i < Math.min(5, rows.length); i++) {
    const rowText = await rows[i].textContent();
    console.log(`Row ${i + 1}:`, rowText);
    
    // Check if this is a gecko trending token
    if (rowText.includes('TROLL') || rowText.includes('ZORA') || rowText.includes('EDGE')) {
      console.log('Found GeckoTerminal token - checking fields...');
      const cells = await rows[i].locator('td').allTextContents();
      console.log('Cell values:', cells);
    }
  }
});