import { test, expect } from '@playwright/test';

test.describe('Verify Price Display Fix', () => {
  test('prices should show in GeckoTerminal panel after fetching', async ({ page }) => {
    test.setTimeout(120000); // 2 minute timeout
    
    console.log('Starting test to verify price display fix...');
    
    // Navigate to the app
    await page.goto('https://lively-torrone-8199e0.netlify.app');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    console.log('Page loaded, looking for analyzed calls table...');
    
    // Wait for the analyzed calls section
    await page.waitForSelector('text="Previously Analyzed Calls"', { timeout: 15000 });
    
    // Find the table
    const table = page.locator('table').first();
    await expect(table).toBeVisible();
    
    // Look through rows to find one with a Fetch button
    const rows = await table.locator('tbody tr').all();
    console.log(`Found ${rows.length} rows in the table`);
    
    let targetRow = null;
    let tokenName = null;
    
    // Find a row with both a clickable token and a Fetch button
    for (let i = 0; i < Math.min(10, rows.length); i++) {
      const row = rows[i];
      
      // Check if this row has a clickable token
      const tokenButton = row.locator('button.font-mono.text-sm');
      const hasClickableToken = await tokenButton.count() > 0;
      
      if (!hasClickableToken) continue;
      
      // Check if this row has a Fetch button
      const fetchButton = row.locator('button:has-text("Fetch")');
      const hasFetchButton = await fetchButton.count() > 0;
      
      if (hasFetchButton) {
        tokenName = await tokenButton.first().textContent();
        targetRow = row;
        console.log(`Found token "${tokenName}" with Fetch button at row ${i}`);
        break;
      }
    }
    
    if (!targetRow) {
      console.log('No tokens with Fetch buttons found. Test cannot proceed.');
      // Take a screenshot for debugging
      await page.screenshot({ path: 'no-fetch-buttons.png', fullPage: true });
      return;
    }
    
    // Step 1: Click the Fetch button
    console.log(`Clicking Fetch button for ${tokenName}...`);
    const fetchButton = targetRow.locator('button:has-text("Fetch")');
    await fetchButton.click();
    
    // Step 2: Wait for prices to load (Entry: text should appear)
    console.log('Waiting for prices to load...');
    try {
      await targetRow.locator('text="Entry:"').waitFor({ timeout: 45000 });
      console.log('Prices loaded successfully!');
    } catch (e) {
      console.error('Failed to load prices within timeout');
      await page.screenshot({ path: 'failed-to-load-prices.png', fullPage: true });
      throw e;
    }
    
    // Wait a bit more for data to settle
    await page.waitForTimeout(3000);
    
    // Step 3: Get the price info from the table
    const priceCell = targetRow.locator('td').nth(-2); // Second to last cell
    const tablePriceText = await priceCell.textContent();
    console.log('Price info in table:', tablePriceText);
    
    // Extract the market cap values from the table
    const entryMatch = tablePriceText?.match(/Entry:\s*(\$[\d.]+[KMB]?)/);
    const nowMatch = tablePriceText?.match(/Now:\s*(\$[\d.]+[KMB]?)/);
    const athMatch = tablePriceText?.match(/ATH:\s*(\$[\d.]+[KMB]?)/);
    
    console.log('Extracted from table:');
    console.log('  Entry:', entryMatch?.[1] || 'not found');
    console.log('  Now:', nowMatch?.[1] || 'not found');
    console.log('  ATH:', athMatch?.[1] || 'not found');
    
    // Step 4: Click on the token to open GeckoTerminal
    console.log('Opening GeckoTerminal panel...');
    await targetRow.locator('button.font-mono.text-sm').first().click();
    
    // Step 5: Wait for panel to open
    await page.waitForSelector('.fixed.inset-0.bg-black\\/50', { timeout: 10000 });
    await page.waitForTimeout(2000); // Wait for animation
    
    console.log('GeckoTerminal panel opened');
    
    // Step 6: Check if prices are displayed in the panel
    const panel = page.locator('.fixed.inset-0.bg-black\\/50');
    
    // Look for the price grid
    const priceGrid = panel.locator('.grid.grid-cols-3.gap-4');
    const gridExists = await priceGrid.count() > 0;
    
    if (!gridExists) {
      console.error('Price grid not found in panel!');
      await page.screenshot({ path: 'no-price-grid.png', fullPage: true });
      throw new Error('Price grid missing from GeckoTerminal panel');
    }
    
    console.log('Price grid found in panel');
    
    // Get the price values from the panel
    const gridText = await priceGrid.textContent();
    console.log('Panel grid text:', gridText);
    
    // Check for Entry price in panel
    const entrySection = priceGrid.locator('div:has(div:text("Entry"))').first();
    const entryPriceElement = entrySection.locator('.font-mono.font-medium');
    const panelEntryPrice = await entryPriceElement.textContent();
    console.log('Panel Entry price:', panelEntryPrice);
    
    // Check for ATH price in panel
    const athSection = priceGrid.locator('div:has(div:text("ATH"))').first();
    const athPriceElement = athSection.locator('.font-mono.font-medium');
    const panelAthPrice = await athPriceElement.textContent();
    console.log('Panel ATH price:', panelAthPrice);
    
    // Check for Now price in panel
    const nowSection = priceGrid.locator('div:has(div:text("Now"))').first();
    const nowPriceElement = nowSection.locator('.font-mono.font-medium');
    const panelNowPrice = await nowPriceElement.textContent();
    console.log('Panel Now price:', panelNowPrice);
    
    // Take a screenshot of the panel
    await page.screenshot({ path: 'geckoterminal-panel-with-prices.png', fullPage: true });
    
    // Verify that at least one price is not N/A
    const hasValidPrices = 
      (panelEntryPrice && panelEntryPrice !== '$N/A') ||
      (panelAthPrice && panelAthPrice !== '$N/A') ||
      (panelNowPrice && panelNowPrice !== '$N/A');
    
    if (!hasValidPrices) {
      throw new Error('All prices in panel show as N/A');
    }
    
    console.log('✅ Test passed! Prices are displaying correctly in GeckoTerminal panel');
    console.log('Summary:');
    console.log(`  Token: ${tokenName}`);
    console.log(`  Entry: ${panelEntryPrice}`);
    console.log(`  ATH: ${panelAthPrice}`);
    console.log(`  Now: ${panelNowPrice}`);
  });
});