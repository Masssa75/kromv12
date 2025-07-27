const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env' });

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

async function fixMomoMarketCap() {
  console.log('Fixing MOMO market cap data...');
  
  // Clear the incorrect market cap data for MOMO
  const { data, error } = await supabase
    .from('crypto_calls')
    .update({
      market_cap_at_call: null,
      current_market_cap: null,
      ath_market_cap: null,
      fdv_at_call: null,
      current_fdv: null,
      ath_fdv: null,
      price_fetched_at: null // Clear this so it can be refetched
    })
    .eq('ticker', 'MOMO')
    .select();
    
  if (error) {
    console.error('Error updating MOMO data:', error);
  } else {
    console.log(`Updated ${data.length} MOMO records`);
    console.log('Market cap data cleared. The prices will be refetched when you click "Fetch" again.');
  }
  
  // Also check for any other tokens with absurdly high market caps
  console.log('\nChecking for other tokens with incorrect market caps...');
  const { data: badData, error: badError } = await supabase
    .from('crypto_calls')
    .select('ticker, market_cap_at_call, current_market_cap')
    .or('market_cap_at_call.gt.1e15,current_market_cap.gt.1e15') // Greater than 1 quadrillion
    .limit(10);
    
  if (badData && badData.length > 0) {
    console.log('\nFound tokens with suspiciously high market caps:');
    badData.forEach(token => {
      console.log(`- ${token.ticker}: Market cap at call: ${token.market_cap_at_call?.toExponential(2)}, Current: ${token.current_market_cap?.toExponential(2)}`);
    });
    
    // Optionally clear all bad data
    const clearAll = true; // Set to true if you want to clear all bad data
    if (clearAll) {
      const { error: clearError } = await supabase
        .from('crypto_calls')
        .update({
          market_cap_at_call: null,
          current_market_cap: null,
          ath_market_cap: null,
          fdv_at_call: null,
          current_fdv: null,
          ath_fdv: null,
          price_fetched_at: null
        })
        .or('market_cap_at_call.gt.1e15,current_market_cap.gt.1e15');
        
      if (!clearError) {
        console.log('Cleared all bad market cap data');
      }
    }
  } else {
    console.log('No other tokens found with incorrect market caps');
  }
}

fixMomoMarketCap();