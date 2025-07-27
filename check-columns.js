const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env' });

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkColumns() {
  // First, let's see what columns exist
  const { data, error } = await supabase
    .from('crypto_calls')
    .select('*')
    .limit(1);
    
  if (data && data.length > 0) {
    console.log('Available columns:', Object.keys(data[0]));
    
    // Now let's look for MOMO
    console.log('\nLooking for MOMO token...');
    const columns = Object.keys(data[0]);
    const tokenColumn = columns.find(col => col.includes('token') || col.includes('ticker'));
    const contractColumn = columns.find(col => col.includes('contract') || col.includes('address'));
    
    console.log('Token column:', tokenColumn);
    console.log('Contract column:', contractColumn);
    
    if (tokenColumn) {
      const { data: momoData, error: momoError } = await supabase
        .from('crypto_calls')
        .select(`${tokenColumn}, ${contractColumn || '*'}, market_cap_at_call, current_market_cap, price_at_call`)
        .eq(tokenColumn, 'MOMO')
        .limit(1);
        
      if (momoData && momoData.length > 0) {
        console.log('\nMOMO data found:');
        console.log(momoData[0]);
        
        // Check the actual value
        const marketCap = momoData[0].market_cap_at_call;
        if (marketCap) {
          console.log('\nMarket cap analysis:');
          console.log('Value:', marketCap);
          console.log('Type:', typeof marketCap);
          console.log('Scientific:', marketCap.toExponential(2));
          console.log('Formatted:', new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(marketCap));
        }
      }
    }
  } else if (error) {
    console.error('Error:', error);
  }
}

checkColumns();