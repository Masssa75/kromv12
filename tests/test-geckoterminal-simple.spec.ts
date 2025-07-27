import { test, expect } from '@playwright/test';

test.describe('GeckoTerminal Price Display - Simple', () => {
  test('debug price display issue', async ({ page }) => {
    test.setTimeout(120000); // 2 minute timeout
    
    // Navigate to the app
    await page.goto('https://lively-torrone-8199e0.netlify.app');
    
    // Wait for the page to load and wait extra time
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    // Take initial screenshot
    await page.screenshot({ path: 'debug-1-initial.png', fullPage: true });
    
    // Check if we're on the right page
    const title = await page.title();
    console.log('Page title:', title);
    
    // Look for any tables
    const tableCount = await page.locator('table').count();
    console.log('Number of tables found:', tableCount);
    
    if (tableCount === 0) {
      console.log('No tables found. Looking for main content...');
      const bodyText = await page.locator('body').textContent();
      console.log('Page text preview:', bodyText?.substring(0, 200));
      return;
    }
    
    // Wait for the main analyzed calls table
    const analyzedSection = page.locator('text="Previously Analyzed Calls"');
    await analyzedSection.waitFor({ timeout: 10000 });
    
    // Get the table after the analyzed calls header
    const table = page.locator('table').first();
    await expect(table).toBeVisible();
    
    // Look for first few rows
    const rows = await table.locator('tbody tr').all();
    console.log(`Found ${rows.length} rows`);
    
    // Find a row with a token that has a contract (clickable)
    let targetRow = null;
    let targetToken = null;
    
    for (let i = 0; i < Math.min(5, rows.length); i++) {
      const row = rows[i];
      const hasClickableToken = await row.locator('button.font-mono').count() > 0;
      
      if (hasClickableToken) {
        const tokenText = await row.locator('button.font-mono').first().textContent();
        const hasPrice = await row.locator('text="Entry:"').count() > 0;
        
        console.log(`Row ${i}: Token=${tokenText}, HasPrice=${hasPrice}`);
        
        if (!hasPrice) {
          // This token doesn't have prices yet - perfect for our test
          targetRow = row;
          targetToken = tokenText;
          break;
        }
      }
    }
    
    if (!targetRow) {
      console.log('No tokens without prices found. Using first clickable token...');
      for (const row of rows) {
        const hasClickableToken = await row.locator('button.font-mono').count() > 0;
        if (hasClickableToken) {
          targetRow = row;
          targetToken = await row.locator('button.font-mono').first().textContent();
          break;
        }
      }
    }
    
    if (!targetRow) {
      console.log('No clickable tokens found!');
      return;
    }
    
    console.log(`Testing with token: ${targetToken}`);
    
    // If the token doesn't have prices, fetch them first
    const fetchButton = targetRow.locator('button:has-text("Fetch")').first();
    const hasFetchButton = await fetchButton.count() > 0;
    
    if (hasFetchButton) {
      console.log('Fetching prices...');
      await fetchButton.click();
      
      // Wait for prices to load
      await targetRow.locator('text="Entry:"').waitFor({ timeout: 30000 });
      await page.waitForTimeout(2000);
      
      // Log what we see after fetching
      const priceSection = await targetRow.locator('div:has-text("Entry:")').textContent();
      console.log('Price section after fetch:', priceSection);
    }
    
    // Take screenshot before clicking
    await page.screenshot({ path: 'debug-2-before-click.png', fullPage: true });
    
    // Click on the token to open GeckoTerminal
    console.log('Clicking on token to open GeckoTerminal...');
    await targetRow.locator('button.font-mono').first().click();
    
    // Wait for panel to open
    await page.waitForSelector('.fixed.inset-0', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    // Take screenshot of panel
    await page.screenshot({ path: 'debug-3-panel-open.png', fullPage: true });
    
    // Now let's analyze what's in the panel
    const panel = page.locator('.fixed.inset-0').first();
    
    // Check for the price grid
    const gridExists = await panel.locator('.grid.grid-cols-3').count() > 0;
    console.log('Grid exists in panel:', gridExists);
    
    if (gridExists) {
      // Get all text from the grid
      const gridText = await panel.locator('.grid.grid-cols-3').first().textContent();
      console.log('Grid text content:', gridText);
      
      // Check specifically for Entry, ATH, Now
      const hasEntry = gridText?.includes('Entry');
      const hasATH = gridText?.includes('ATH');
      const hasNow = gridText?.includes('Now');
      
      console.log(`Has Entry: ${hasEntry}, Has ATH: ${hasATH}, Has Now: ${hasNow}`);
      
      // Check for actual price values
      const pricePattern = /\$[\d,]+\.?\d*/g;
      const prices = gridText?.match(pricePattern) || [];
      console.log('Found prices:', prices);
    } else {
      console.log('No grid found. Panel structure:');
      const panelStructure = await panel.innerHTML();
      console.log(panelStructure.substring(0, 1000));
    }
    
    console.log('Test complete. Check debug-*.png screenshots');
  });
});