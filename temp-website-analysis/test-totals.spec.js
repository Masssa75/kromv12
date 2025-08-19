const { test, expect } = require('@playwright/test');

test('dashboard shows database totals', async ({ page }) => {
  // Navigate to the dashboard
  await page.goto('http://localhost:5020');
  
  // Wait for stats to load
  await page.waitForSelector('.stats');
  
  // Get the stats text
  const statsText = await page.locator('.stats').textContent();
  console.log('Stats displayed:', statsText);
  
  // Check that it contains the database totals
  expect(statsText).toContain('Total Tokens in DB:');
  expect(statsText).toContain('Total With Websites:');
  
  // Extract the numbers using regex
  const totalMatch = statsText.match(/Total Tokens in DB:\s*(\d+)/);
  const websitesMatch = statsText.match(/Total With Websites:\s*(\d+)/);
  
  if (totalMatch && websitesMatch) {
    console.log(`✅ Dashboard shows ${totalMatch[1]} total tokens and ${websitesMatch[1]} tokens with websites`);
  }
  
  // Take a screenshot
  await page.screenshot({ path: 'dashboard-totals.png' });
});