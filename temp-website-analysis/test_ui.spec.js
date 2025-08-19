const { test, expect } = require('@playwright/test');

test('Token Discovery UI is running on port 5020', async ({ page }) => {
  await page.goto('http://localhost:5020');
  
  // Check if page loads (give it a moment)
  await page.waitForLoadState('networkidle');
  
  // Check for main content - just verify it's not an error page
  await expect(page.locator('body')).toBeVisible();
  
  // Take a screenshot to see what's actually on the page
  await page.screenshot({ path: 'ui-status.png', fullPage: true });
  
  // Print page content to help debug
  const content = await page.content();
  console.log('Page title:', await page.title());
  console.log('Page has table:', await page.locator('table').count());
  console.log('Page has h1:', await page.locator('h1').count());
});