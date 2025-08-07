import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';
const KROM_API_URL = 'https://krom.one/api/v1/calls?limit=10';

// Map KROM network names to GeckoTerminal API network names
function mapNetworkName(kromNetwork: string): string {
  const networkMap: Record<string, string> = {
    'ethereum': 'eth',
    'solana': 'solana', 
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
  };
  
  return networkMap[kromNetwork.toLowerCase()] || kromNetwork.toLowerCase();
}

// Function to fetch current price and supply data for new calls
async function fetchCurrentPriceAndSupply(network: string, poolAddress: string) {
  try {
    const geckoNetwork = mapNetworkName(network);
    console.log(`Mapping network: ${network} -> ${geckoNetwork}`);
    
    const response = await fetch(`https://api.geckoterminal.com/api/v2/networks/${geckoNetwork}/pools/${poolAddress}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    });

    if (!response.ok) {
      console.log(`Price/supply fetch failed for pool ${poolAddress}: ${response.status}`);
      return { price: null, totalSupply: null, circulatingSupply: null, source: "DEAD_TOKEN" };
    }

    const data = await response.json();
    const attributes = data.data?.attributes;
    const price = parseFloat(attributes?.base_token_price_usd || '0');
    const fdv = parseFloat(attributes?.fdv_usd || '0');
    const marketCap = parseFloat(attributes?.market_cap_usd || '0');
    
    // Calculate supplies from FDV and market cap
    const totalSupply = (fdv && price > 0) ? fdv / price : null;
    const circulatingSupply = (marketCap && price > 0) ? marketCap / price : 
                             totalSupply; // If no market cap, assume circulating = total
    
    if (price > 0) {
      console.log(`✅ Got price: $${price}, FDV: $${fdv}, MCap: $${marketCap} for pool ${poolAddress}`);
      if (totalSupply) {
        console.log(`   Total Supply: ${totalSupply.toLocaleString()}, Circulating: ${circulatingSupply?.toLocaleString()}`);
      }
      return { price, totalSupply, circulatingSupply, source: "GECKO_LIVE" };
    } else {
      console.log(`❌ No price data for pool ${poolAddress}`);
      return { price: null, totalSupply: null, circulatingSupply: null, source: "DEAD_TOKEN" };
    }
    
  } catch (error) {
    console.error(`Error fetching price/supply for pool ${poolAddress}:`, error);
    return { price: null, totalSupply: null, circulatingSupply: null, source: "DEAD_TOKEN" };
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

        // Fetch current price and supply if we have pool address and network
        if (call.token?.pa && call.token?.network) {
          console.log(`Fetching price/supply for ${call.token.symbol || 'UNKNOWN'} on ${call.token.network}...`);
          const priceData = await fetchCurrentPriceAndSupply(call.token.network, call.token.pa);
          
          callData.price_at_call = priceData.price;
          callData.price_source = priceData.source;
          callData.total_supply = priceData.totalSupply || null;
          callData.circulating_supply = priceData.circulatingSupply || null;
          
          // Calculate market_cap_at_call if we have supply data
          if (priceData.price && priceData.totalSupply) {
            // Check if supplies are similar (within 5%)
            const supplyDiff = priceData.circulatingSupply && priceData.totalSupply 
              ? Math.abs(priceData.circulatingSupply - priceData.totalSupply) / priceData.totalSupply * 100
              : 0;
            const suppliesAreSimilar = supplyDiff < 5;
            
            if (suppliesAreSimilar) {
              callData.market_cap_at_call = priceData.price * priceData.totalSupply;
              console.log(`   Calculated market_cap_at_call: $${callData.market_cap_at_call.toLocaleString()}`);
            } else {
              console.log(`   Supply mismatch (${supplyDiff.toFixed(1)}% diff), skipping market_cap_at_call`);
            }
          }
          
          if (callData.total_supply || callData.circulating_supply) {
            callData.supply_updated_at = new Date().toISOString();
          }
          
          // If KROM didn't provide a buy timestamp, use current time as the effective buy time
          if (!callData.buy_timestamp) {
            callData.buy_timestamp = new Date().toISOString();
          }
        } else {
          console.log(`No pool address or network for ${call.token?.symbol || 'UNKNOWN'} - skipping price/supply fetch`);
          callData.price_at_call = null;
          callData.price_source = "NO_POOL_DATA";
          callData.total_supply = null;
          callData.circulating_supply = null;
          // If KROM didn't provide a buy timestamp, use current time as the effective buy time
          if (!callData.buy_timestamp) {
            callData.buy_timestamp = new Date().toISOString();
          }
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
          const priceInfo = callData.price_at_call 
            ? `Price: $${callData.price_at_call} (${callData.price_source})`
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