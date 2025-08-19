const { test, expect } = require('@playwright/test');

test('dashboard is running', async ({ page }) => {
  await page.goto('http://localhost:5020');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Check for main elements of the Token Discovery Dashboard
  const heading = await page.locator('h1').first();
  await expect(heading).toBeVisible();
  
  // Check for the stats section
  const statsSection = await page.locator('.stats-grid').first();
  await expect(statsSection).toBeVisible();
  
  console.log('✅ Token Discovery Dashboard is running successfully at http://localhost:5020');
});