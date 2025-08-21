const { test } = require('@playwright/test');

test('Check missing data issue for recent tokens', async ({ page }) => {
  // Navigate to the KROM interface
  await page.goto('https://lively-torrone-8199e0.netlify.app');
  
  // Wait for the page to load
  await page.waitForSelector('table', { timeout: 10000 });
  
  // Take a screenshot of the current state
  await page.screenshot({ path: 'missing-data-issue.png', fullPage: true });
  
  // Look for GT Trending tokens and check their data
  const gtTrendingTokens = await page.$$eval('tr', rows => {
    return rows
      .filter(row => row.textContent?.includes('GT Trending'))
      .slice(0, 5)
      .map(row => {
        const cells = Array.from(row.querySelectorAll('td'));
        return {
          ticker: cells[0]?.textContent?.trim(),
          group: cells[cells.length - 1]?.textContent?.trim(),
          entryMC: cells[7]?.textContent?.trim(),
          athMC: cells[8]?.textContent?.trim(),
          nowMC: cells[9]?.textContent?.trim(),
          roi: cells[10]?.textContent?.trim(),
          athRoi: cells[11]?.textContent?.trim()
        };
      });
  });
  
  console.log('GT Trending Tokens:', JSON.stringify(gtTrendingTokens, null, 2));
  
  // Check for tokens added ~9 hours ago with missing data
  const recentTokens = await page.$$eval('tr', rows => {
    return rows
      .filter(row => {
        const timeText = row.textContent || '';
        return timeText.includes('7h ago') || timeText.includes('8h ago') || 
               timeText.includes('9h ago') || timeText.includes('10h ago');
      })
      .slice(0, 10)
      .map(row => {
        const cells = Array.from(row.querySelectorAll('td'));
        return {
          ticker: cells[0]?.textContent?.trim(),
          time: cells[cells.length - 1]?.textContent?.trim(),
          entryMC: cells[7]?.textContent?.trim(),
          athMC: cells[8]?.textContent?.trim(),
          nowMC: cells[9]?.textContent?.trim(),
          roi: cells[10]?.textContent?.trim(),
          athRoi: cells[11]?.textContent?.trim(),
          liquidity: cells[6]?.textContent?.trim()
        };
      });
  });
  
  console.log('Recent Tokens (7-10h ago):', JSON.stringify(recentTokens, null, 2));
  
  // Count N/A values
  const naCount = await page.$$eval('td', cells => {
    return cells.filter(cell => cell.textContent?.trim() === 'N/A').length;
  });
  
  console.log(`Total N/A values on page: ${naCount}`);
  
  // Check network status
  const networkResponses = [];
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      networkResponses.push({
        url: response.url(),
        status: response.status(),
        ok: response.ok()
      });
    }
  });
  
  // Reload to capture API calls
  await page.reload();
  await page.waitForTimeout(3000);
  
  console.log('API Responses:', networkResponses);
});

test('Check database directly for missing data', async ({ page }) => {
  // We'll check the database via a simple script after this
  console.log('Will check database for token data issues...');
});