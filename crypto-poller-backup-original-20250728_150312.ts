import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';
const KROM_API_URL = 'https://krom.one/api/v1/calls?limit=10';

// Function to fetch current price for new calls (within 1-3 minutes of call)
async function fetchCurrentPrice(network: string, poolAddress: string) {
  try {
    const response = await fetch(`https://api.geckoterminal.com/api/v2/networks/${network}/pools/${poolAddress}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    });

    if (!response.ok) {
      console.log(`Current price fetch failed for pool ${poolAddress}: ${response.status}`);
      return { price: null, source: "DEAD_TOKEN" };
    }

    const data = await response.json();
    const price = parseFloat(data.data?.attributes?.base_token_price_usd || '0');
    
    if (price > 0) {
      console.log(`✅ Got current price: $${price} for pool ${poolAddress}`);
      return { price, source: "GECKO_LIVE" };
    } else {
      console.log(`❌ No price data for pool ${poolAddress}`);
      return { price: null, source: "DEAD_TOKEN" };
    }
    
  } catch (error) {
    console.error(`Error fetching current price for pool ${poolAddress}:`, error);
    return { price: null, source: "DEAD_TOKEN" };
  }
}
serve(async (req)=>{
  try {
    // Create Supabase client with service role
    const supabase = createClient(Deno.env.get('SUPABASE_URL') ?? '', Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '', {
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    });
    // Get KROM API token
    const kromApiToken = Deno.env.get('KROM_API_TOKEN');
    if (!kromApiToken) {
      throw new Error('KROM_API_TOKEN not configured');
    }
    // Fetch from KROM API
    console.log('Fetching from KROM API...');
    const response = await fetch(KROM_API_URL, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${kromApiToken}`
      }
    });
    if (!response.ok) {
      throw new Error(`KROM API error: ${response.status}`);
    }
    const calls = await response.json();
    console.log(`Fetched ${calls.length} calls from KROM`);
    // Only process the first 5 calls (newest ones)
    const recentCalls = calls.slice(0, 5);
    console.log(`Processing only the ${recentCalls.length} most recent calls`);
    // Store new calls
    let newCallsCount = 0;
    const errors = [];
    for (const call of recentCalls){
      try {
        // Prepare base call data
        const callData: any = {
          krom_id: call._id,
          ticker: call.token?.symbol || 'UNKNOWN',
          buy_timestamp: call.trade?.buyTimestamp ? new Date(call.trade.buyTimestamp * 1000).toISOString() : null,
          contract_address: call.token?.ca || null,
          pool_address: call.token?.pa || null,
          network: call.token?.network || null,
          raw_data: call
        };

        // Fetch current price if we have pool address and network
        if (call.token?.pa && call.token?.network) {
          console.log(`Fetching current price for ${call.token.symbol || 'UNKNOWN'} on ${call.token.network}...`);
          const priceData = await fetchCurrentPrice(call.token.network, call.token.pa);
          
          callData.historical_price_usd = priceData.price;
          callData.price_source = priceData.source;
          callData.price_updated_at = new Date().toISOString();
        } else {
          console.log(`No pool address or network for ${call.token?.symbol || 'UNKNOWN'} - skipping price fetch`);
          callData.historical_price_usd = null;
          callData.price_source = "NO_POOL_DATA";
          callData.price_updated_at = new Date().toISOString();
        }

        // Try to insert - if it already exists, it will fail with unique constraint
        const { data, error } = await supabase.from('crypto_calls').insert(callData).select();
        if (error) {
          if (error.code === '23505') {
            continue;
          } else {
            console.error(`Error inserting call ${call._id}:`, error);
            errors.push({
              id: call._id,
              error: error.message
            });
          }
        } else {
          newCallsCount++;
          const priceInfo = callData.historical_price_usd 
            ? `Price: $${callData.historical_price_usd} (${callData.price_source})`
            : `No price (${callData.price_source})`;
          
          console.log(`Added new call: ${call._id} - ${call.token?.symbol || 'Unknown'} on ${call.token?.network || 'unknown'} - ${priceInfo}`);
        }
      } catch (err) {
        console.error(`Error processing call ${call._id}:`, err);
        errors.push({
          id: call._id,
          error: err.message
        });
      }
    }
    return new Response(JSON.stringify({
      success: true,
      totalFetched: calls.length,
      newCallsAdded: newCallsCount,
      errors: errors.length > 0 ? errors : undefined
    }), {
      headers: {
        "Content-Type": "application/json"
      }
    });
  } catch (error) {
    console.error('Error in crypto-poller:', error);
    return new Response(JSON.stringify({
      success: false,
      error: error.message,
      details: error.toString()
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json"
      }
    });
  }
});