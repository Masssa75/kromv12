const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env' });

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

console.log('Supabase URL:', supabaseUrl ? 'Found' : 'Not found');
console.log('Supabase Key:', supabaseKey ? 'Found' : 'Not found');

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkMomoData() {
  // Search for MOMO token
  const { data, error } = await supabase
    .from('crypto_calls')
    .select('krom_id, ticker, token_address, market_cap_at_call, current_market_cap, price_at_call, current_price, ath_market_cap, fdv_at_call, current_fdv, ath_fdv')
    .eq('ticker', 'MOMO')
    .limit(5);

  if (error) {
    console.error('Error fetching data:', error);
  } else {
    console.log('MOMO token data:');
    data?.forEach((row, index) => {
      console.log(`\nRow ${index + 1}:`);
      console.log('- Token:', row.ticker);
      console.log('- Contract:', row.token_address);
      console.log('- Price at call:', row.price_at_call);
      console.log('- Current price:', row.current_price);
      console.log('- Market cap at call:', row.market_cap_at_call);
      console.log('- Current market cap:', row.current_market_cap);
      console.log('- ATH market cap:', row.ath_market_cap);
      console.log('- FDV at call:', row.fdv_at_call);
      console.log('- Current FDV:', row.current_fdv);
      console.log('- ATH FDV:', row.ath_fdv);
    });
  }

  // Also check one specific contract if we know it
  const momoContract = '0x3E80A0fE65beD6bAEdF6919425FDB6FDCD04444';
  console.log('\n\nChecking specific contract:', momoContract);
  const { data: specificData, error: specificError } = await supabase
    .from('crypto_calls')
    .select('*')
    .eq('token_address', momoContract)
    .single();
    
  if (specificData) {
    console.log('Market cap at call (raw):', specificData.market_cap_at_call);
    console.log('Market cap at call (stringified):', JSON.stringify(specificData.market_cap_at_call));
    console.log('Type:', typeof specificData.market_cap_at_call);
    console.log('Is it a number?', !isNaN(specificData.market_cap_at_call));
    
    // Try to see the actual number
    if (specificData.market_cap_at_call) {
      console.log('Formatted:', new Intl.NumberFormat('en-US').format(specificData.market_cap_at_call));
      console.log('Scientific notation:', specificData.market_cap_at_call.toExponential());
    }
  }
}

checkMomoData();