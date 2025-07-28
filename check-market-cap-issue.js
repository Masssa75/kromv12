const { createClient } = require('@supabase/supabase-js');

// Load environment variables
require('dotenv').config();

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function checkMarketCapIssue() {
  try {
    // Get tokens with market cap data
    const { data, error } = await supabase
      .from('crypto_calls')
      .select('krom_id, ticker, market_cap_at_call, fdv_at_call, price_at_call, current_fdv, current_market_cap')
      .not('market_cap_at_call', 'is', null)
      .gt('market_cap_at_call', 0)
      .order('buy_timestamp', { ascending: false })
      .limit(20);

    if (error) {
      console.error('Error fetching data:', error);
      return;
    }

    console.log('Analyzing market cap vs FDV data...\n');
    console.log('Ticker     | Market Cap at Call      | FDV at Call    | Current MC      | Current FDV    | Issue?');
    console.log('-----------|------------------------|----------------|-----------------|----------------|-------');

    for (const item of data) {
      const mc = item.market_cap_at_call || 0;
      const fdv = item.fdv_at_call || 0;
      const currentMc = item.current_market_cap || 0;
      const currentFdv = item.current_fdv || 0;
      
      // Check if market cap is suspiciously high (> 1 trillion)
      const issue = mc > 1e12 ? 'YES' : '';
      
      // Format numbers
      const formatNum = (num) => {
        if (num > 1e12) return `${(num / 1e12).toFixed(2)}T`;
        if (num > 1e9) return `${(num / 1e9).toFixed(2)}B`;
        if (num > 1e6) return `${(num / 1e6).toFixed(2)}M`;
        if (num > 1e3) return `${(num / 1e3).toFixed(2)}K`;
        return num.toFixed(2);
      };

      console.log(
        `${item.ticker.padEnd(10)} | ${formatNum(mc).padStart(22)} | ${formatNum(fdv).padStart(14)} | ${formatNum(currentMc).padStart(15)} | ${formatNum(currentFdv).padStart(14)} | ${issue}`
      );
    }

    // Count how many have the issue
    const issueCount = data.filter(item => item.market_cap_at_call > 1e12).length;
    console.log(`\nTokens with market cap > 1 trillion: ${issueCount} out of ${data.length}`);

  } catch (err) {
    console.error('Error:', err);
  }
}

checkMarketCapIssue();