const { test, expect } = require('@playwright/test');

test('token discovery dashboard is accessible', async ({ page }) => {
  // Navigate to the dashboard
  const response = await page.goto('http://localhost:5020');
  
  // Check if we got a successful response
  expect(response.status()).toBe(200);
  
  // Take a screenshot for verification
  await page.screenshot({ path: 'dashboard-check.png' });
  
  console.log('✅ Token Discovery Dashboard is running at http://localhost:5020');
  console.log('Screenshot saved as dashboard-check.png');
});