const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Navigate to the app
  await page.goto('https://lively-torrone-8199e0.netlify.app');
  
  // Wait for the table to load
  await page.waitForSelector('table', { timeout: 30000 });
  
  // Click on the ROI header to sort by highest first
  console.log('Clicking ROI header to sort...');
  await page.click('th:has-text("Price / ROI")');
  
  // Wait a moment for sorting
  await page.waitForTimeout(1000);
  
  // Click again to sort by highest first (descending)
  await page.click('th:has-text("Price / ROI")');
  await page.waitForTimeout(1000);
  
  // Get the first few rows to see what tokens have no prices
  const tokensWithoutPrices = await page.evaluate(() => {
    const rows = document.querySelectorAll('tbody tr');
    const results = [];
    
    for (let i = 0; i < Math.min(20, rows.length); i++) {
      const row = rows[i];
      const ticker = row.querySelector('td:nth-child(2) .font-medium')?.textContent || '';
      const network = row.querySelector('td:nth-child(2) .text-xs')?.textContent || '';
      const priceCell = row.querySelector('td:nth-child(7)')?.textContent || '';
      const contractLink = row.querySelector('td:nth-child(2) a')?.href || '';
      
      results.push({
        ticker,
        network,
        priceCell,
        contractLink,
        hasPrice: !priceCell.includes('N/A')
      });
    }
    
    return results;
  });
  
  console.log('First 20 tokens when sorted by highest ROI:');
  console.log(JSON.stringify(tokensWithoutPrices, null, 2));
  
  // Check pagination info
  const paginationText = await page.textContent('.text-sm.text-gray-600');
  console.log('\nPagination info:', paginationText);
  
  // Navigate through a few pages to see the pattern
  let pagesWithoutPrices = 0;
  let firstPageWithPrices = 0;
  
  for (let pageNum = 1; pageNum <= 20; pageNum++) {
    // Check if current page has any prices
    const hasAnyPrices = await page.evaluate(() => {
      const rows = document.querySelectorAll('tbody tr');
      for (const row of rows) {
        const priceCell = row.querySelector('td:nth-child(7)')?.textContent || '';
        if (!priceCell.includes('N/A')) return true;
      }
      return false;
    });
    
    if (!hasAnyPrices) {
      pagesWithoutPrices++;
    } else if (firstPageWithPrices === 0) {
      firstPageWithPrices = pageNum;
    }
    
    // Try to go to next page
    const nextButton = await page.$('button:has-text("Next")');
    if (nextButton && await nextButton.isEnabled()) {
      await nextButton.click();
      await page.waitForTimeout(1000);
    } else {
      break;
    }
  }
  
  console.log(`\nPages without any prices: ${pagesWithoutPrices}`);
  console.log(`First page with prices: ${firstPageWithPrices}`);
  
  // Let's check one specific token without price in detail
  await page.goto('https://lively-torrone-8199e0.netlify.app');
  await page.waitForSelector('.divide-y', { timeout: 10000 });
  await page.click('th:has-text("Price / ROI")');
  await page.waitForTimeout(1000);
  await page.click('th:has-text("Price / ROI")');
  await page.waitForTimeout(1000);
  
  // Click on the first token to see details
  await page.click('tbody tr:first-child');
  await page.waitForTimeout(2000);
  
  // Get detail panel info
  const detailInfo = await page.evaluate(() => {
    const panel = document.querySelector('[role="dialog"]');
    if (!panel) return null;
    
    return {
      title: panel.querySelector('h2')?.textContent || '',
      content: panel.textContent || ''
    };
  });
  
  console.log('\nDetail panel for first token without price:');
  console.log(JSON.stringify(detailInfo, null, 2));
  
  // Keep browser open for 30 seconds to inspect
  await page.waitForTimeout(30000);
  
  await browser.close();
})();