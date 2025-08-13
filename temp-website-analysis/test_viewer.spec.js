const { test, expect } = require('@playwright/test');

test('Flask server and viewer integration', async ({ page }) => {
  // First check if Flask server is responding
  console.log('Testing Flask API endpoint...');
  
  try {
    const response = await page.request.get('http://localhost:5000/api/analysis');
    console.log('API Response Status:', response.status());
    
    if (response.ok()) {
      const data = await response.json();
      console.log('API returned', data.results?.length || 0, 'results');
      console.log('First result:', data.results?.[0]?.ticker);
    } else {
      console.log('API Error:', response.status(), response.statusText());
    }
  } catch (error) {
    console.log('Cannot reach Flask server:', error.message);
  }
  
  // Now test the HTML viewer
  console.log('\nTesting HTML viewer...');
  await page.goto('file:///Users/marcschwyn/Desktop/projects/KROMV12/temp-website-analysis/all-results.html');
  
  // Wait for either data or error message
  await page.waitForTimeout(2000);
  
  // Check what's displayed
  const hasError = await page.locator('text=/Unable to load data/').isVisible();
  const hasResults = await page.locator('.token-card').count();
  
  console.log('Page has error message:', hasError);
  console.log('Page has token cards:', hasResults);
  
  // Check console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Browser console error:', msg.text());
    }
  });
  
  // Check network requests
  page.on('requestfailed', request => {
    console.log('Failed request:', request.url());
  });
  
  await page.waitForTimeout(1000);
});

test('Check database directly', async ({ page }) => {
  const { execSync } = require('child_process');
  
  try {
    const result = execSync('sqlite3 analysis_results.db "SELECT COUNT(*) FROM website_analysis;"');
    console.log('Database has', result.toString().trim(), 'records');
  } catch (error) {
    console.log('Database error:', error.message);
  }
});