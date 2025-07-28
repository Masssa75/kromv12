const { createClient } = require('@supabase/supabase-js');

// Load environment variables
require('dotenv').config();

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function checkSpecificTokens() {
  try {
    // Check specific tokens from the screenshot
    const tickers = ['RECC', 'BONKFILLES', 'T', 'BONKGIRLS', 'BONKFILES'];
    
    const { data, error } = await supabase
      .from('crypto_calls')
      .select('krom_id, ticker, market_cap_at_call, fdv_at_call, price_at_call, current_fdv, current_market_cap, ath_fdv, ath_market_cap')
      .in('ticker', tickers)
      .order('buy_timestamp', { ascending: false });

    if (error) {
      console.error('Error fetching data:', error);
      return;
    }

    console.log('Analyzing specific tokens from screenshot...\n');
    console.log('Data found for these tokens:');
    
    for (const ticker of tickers) {
      const tokenData = data.filter(d => d.ticker === ticker);
      console.log(`\n${ticker}: ${tokenData.length} entries found`);
      
      if (tokenData.length > 0) {
        const latest = tokenData[0];
        console.log(`  Market Cap at Call: ${formatLargeNumber(latest.market_cap_at_call)}`);
        console.log(`  FDV at Call: ${formatLargeNumber(latest.fdv_at_call)}`);
        console.log(`  Current Market Cap: ${formatLargeNumber(latest.current_market_cap)}`);
        console.log(`  Current FDV: ${formatLargeNumber(latest.current_fdv)}`);
        console.log(`  ATH Market Cap: ${formatLargeNumber(latest.ath_market_cap)}`);
        console.log(`  ATH FDV: ${formatLargeNumber(latest.ath_fdv)}`);
        
        // Check if the issue is in display logic
        const displayValue = latest.fdv_at_call || latest.market_cap_at_call;
        console.log(`  Display would show: ${formatLargeNumber(displayValue)} (using ${latest.fdv_at_call ? 'FDV' : 'MC'})`);
      }
    }

  } catch (err) {
    console.error('Error:', err);
  }
}

function formatLargeNumber(num) {
  if (num === null || num === undefined) return 'null';
  if (num > 1e15) return `${(num / 1e15).toFixed(2)}Q (QUADRILLION - ERROR!)`;
  if (num > 1e12) return `${(num / 1e12).toFixed(2)}T (TRILLION - ERROR!)`;
  if (num > 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (num > 1e6) return `${(num / 1e6).toFixed(2)}M`;
  if (num > 1e3) return `${(num / 1e3).toFixed(2)}K`;
  return num.toFixed(2);
}

checkSpecificTokens();