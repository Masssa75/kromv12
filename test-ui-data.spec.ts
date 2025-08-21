import { test, expect } from '@playwright/test';

test('Check recent calls for N/A data', async ({ page }) => {
  // Go to the live site
  await page.goto('https://lively-torrone-8199e0.netlify.app/');
  
  // Wait for the table to load
  await page.waitForSelector('table', { timeout: 10000 });
  
  // Take a screenshot
  await page.screenshot({ path: 'recent-calls-check.png', fullPage: false });
  
  // Look for N/A values in market cap columns
  const naValues = await page.locator('td:has-text("N/A")').count();
  console.log(`Found ${naValues} cells with N/A values`);
  
  // Check for YZY tokens
  const yzyTokens = await page.locator('td:has-text("YZY")').count();
  console.log(`Found ${yzyTokens} YZY tokens`);
  
  // Wait to see the page
  await page.waitForTimeout(5000);
});