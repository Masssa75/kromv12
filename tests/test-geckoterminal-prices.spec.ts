import { test, expect } from '@playwright/test';

test.describe('GeckoTerminal Price Display', () => {
  test('should display fetched prices in GeckoTerminal panel', async ({ page }) => {
    // Navigate to the app
    await page.goto('https://lively-torrone-8199e0.netlify.app');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Give time for React to render
    
    // Look for the main table
    const table = page.locator('table').last();
    await expect(table).toBeVisible();
    
    // Find rows with fetch buttons
    const rows = await table.locator('tbody tr').all();
    console.log(`Found ${rows.length} rows in the table`);
    
    let targetRow = null;
    let tokenName = null;
    
    // Find a row with a Fetch button and a clickable token
    for (const row of rows) {
      const hasContract = await row.locator('button.font-mono.text-sm').count() > 0;
      const hasFetchButton = await row.locator('button:has-text("Fetch")').count() > 0;
      
      if (hasContract && hasFetchButton) {
        targetRow = row;
        tokenName = await row.locator('button.font-mono.text-sm').first().textContent();
        console.log(`Found token with fetch button: ${tokenName}`);
        break;
      }
    }
    
    if (!targetRow) {
      console.log('No tokens with both contract and unfetched prices found');
      return;
    }
    
    // Get the fetch button in this row
    const fetchButton = targetRow.locator('button:has-text("Fetch")').first();
    
    // Click fetch and wait for completion
    console.log('Clicking fetch button...');
    await fetchButton.click();
    
    // Wait for the price to be fetched (Entry: text should appear)
    await targetRow.locator('text="Entry:"').waitFor({ timeout: 30000 });
    await page.waitForTimeout(1000); // Extra wait for data to settle
    
    // Get the fetched price info
    const entryText = await targetRow.locator('div:has-text("Entry:")').textContent();
    console.log('Fetched price info:', entryText);
    
    // Click on the token name to open GeckoTerminal
    console.log('Opening GeckoTerminal panel...');
    await targetRow.locator('button.font-mono.text-sm').first().click();
    
    // Wait for GeckoTerminal panel to open
    await page.waitForSelector('.fixed.inset-0.bg-black\\/50', { timeout: 5000 });
    await page.waitForTimeout(1000); // Wait for panel animation
    
    // Check if price data is displayed in the panel
    const geckoPanel = page.locator('.fixed.inset-0.bg-black\\/50');
    
    // Debug: Let's see what's in the panel header
    const panelHeader = geckoPanel.locator('.flex.justify-between.items-center').first();
    const headerHTML = await panelHeader.innerHTML();
    console.log('Panel header HTML:', headerHTML.substring(0, 500));
    
    // Look for the price grid in the header
    const priceGrid = geckoPanel.locator('.grid.grid-cols-3.gap-4');
    const hasGrid = await priceGrid.count() > 0;
    console.log('Price grid count:', await priceGrid.count());
    
    if (hasGrid) {
      const gridHTML = await priceGrid.innerHTML();
      console.log('Grid HTML:', gridHTML);
      
      // Check if the grid is actually visible
      const isGridVisible = await priceGrid.isVisible();
      console.log('Is grid visible?', isGridVisible);
      
      // Try different selectors for the prices
      const entryDivs = await geckoPanel.locator('div:has-text("Entry")').all();
      console.log('Found Entry divs:', entryDivs.length);
      
      // Look for font-mono elements in the grid
      const priceElements = await priceGrid.locator('.font-mono').all();
      console.log('Found price elements:', priceElements.length);
      
      for (const elem of priceElements) {
        const text = await elem.textContent();
        console.log('Price element text:', text);
      }
    } else {
      console.log('No price grid found in panel');
      
      // Check what's actually in the panel
      const panelContent = await geckoPanel.innerHTML();
      console.log('Panel content preview:', panelContent.substring(0, 1000));
    }
    
    // Take a screenshot for debugging
    await page.screenshot({ path: 'geckoterminal-panel-test.png', fullPage: true });
    
    // Keep panel open for manual inspection
    console.log('Test complete. Check screenshot at geckoterminal-panel-test.png');
  });
});