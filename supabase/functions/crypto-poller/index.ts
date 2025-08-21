import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';
const KROM_API_URL = 'https://krom.one/api/v1/calls?limit=10';

// DexScreener doesn't need network mapping - uses same names as KROM
// But keeping this for compatibility if needed
function mapNetworkName(kromNetwork: string): string {
  const networkMap: Record<string, string> = {
    'ethereum': 'ethereum',
    'solana': 'solana', 
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
  };
  
  return networkMap[kromNetwork.toLowerCase()] || kromNetwork.toLowerCase();
}

// Function to fetch current price, supply, liquidity AND social data from DexScreener
async function fetchCurrentPriceAndSupply(network: string, poolAddress: string) {
  try {
    const dexNetwork = mapNetworkName(network);
    console.log(`Fetching from DexScreener: ${network} -> ${dexNetwork}`);
    
    // DexScreener pairs endpoint - works with pool address
    const response = await fetch(`https://api.dexscreener.com/latest/dex/pairs/${dexNetwork}/${poolAddress}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    });

    if (!response.ok) {
      console.log(`Price/supply fetch failed for pool ${poolAddress}: ${response.status}`);
      return { 
        price: null, 
        totalSupply: null, 
        circulatingSupply: null, 
        liquidity: 0, 
        source: "DEAD_TOKEN",
        socials: {} 
      };
    }

    const data = await response.json();
    
    // DexScreener returns pairs array or single pair
    let pair = null;
    if (data.pairs && data.pairs.length > 0) {
      pair = data.pairs[0]; // Take first pair (usually highest liquidity)
    } else if (data.pair) {
      pair = data.pair;
    } else {
      console.log(`❌ No pair data for pool ${poolAddress}`);
      return { 
        price: null, 
        totalSupply: null, 
        circulatingSupply: null, 
        liquidity: 0, 
        source: "DEAD_TOKEN",
        socials: {}
      };
    }
    
    // Extract data from DexScreener response
    const price = parseFloat(pair.priceUsd || '0');
    const fdv = parseFloat(pair.fdv || '0');
    const marketCap = parseFloat(pair.marketCap || '0');
    
    // Handle liquidity - can be number or object
    const liquidity = typeof pair.liquidity === 'object' 
      ? parseFloat(pair.liquidity?.usd || '0')
      : parseFloat(pair.liquidity || '0');
    
    // Calculate supplies from FDV and market cap (same as GeckoTerminal)
    const totalSupply = (fdv && price > 0) ? fdv / price : null;
    const circulatingSupply = (marketCap && price > 0) ? marketCap / price : 
                             totalSupply; // If no market cap, assume circulating = total
    
    // Extract social links (NEW!)
    const socials: any = {
      website_url: null,
      twitter_url: null,
      telegram_url: null,
      discord_url: null
    };
    
    // Check info.socials array
    if (pair.info?.socials && Array.isArray(pair.info.socials)) {
      for (const social of pair.info.socials) {
        if (!social || !social.type) continue;
        
        const socialType = social.type.toLowerCase();
        const socialUrl = social.url;
        
        if (socialType === 'website' && !socials.website_url) {
          socials.website_url = socialUrl;
        } else if (socialType === 'twitter' && !socials.twitter_url) {
          socials.twitter_url = socialUrl;
        } else if (socialType === 'telegram' && !socials.telegram_url) {
          socials.telegram_url = socialUrl;
        } else if (socialType === 'discord' && !socials.discord_url) {
          socials.discord_url = socialUrl;
        }
      }
    }
    
    // Also check info.websites array (sometimes website is here)
    if (!socials.website_url && pair.info?.websites) {
      const websites = pair.info.websites;
      if (Array.isArray(websites) && websites.length > 0) {
        socials.website_url = typeof websites[0] === 'string' 
          ? websites[0] 
          : websites[0]?.url || null;
      }
    }
    
    if (price > 0) {
      console.log(`✅ Got price: $${price}, FDV: $${fdv}, MCap: $${marketCap}, Liquidity: $${liquidity} for pool ${poolAddress}`);
      if (totalSupply) {
        console.log(`   Total Supply: ${totalSupply.toLocaleString()}, Circulating: ${circulatingSupply?.toLocaleString()}`);
      }
      if (socials.website_url || socials.twitter_url) {
        console.log(`   Social links found - Website: ${socials.website_url ? '✓' : '✗'}, Twitter: ${socials.twitter_url ? '✓' : '✗'}`);
      }
      
      // Check liquidity threshold
      const LIQUIDITY_THRESHOLD = 1000;
      if (liquidity < LIQUIDITY_THRESHOLD) {
        console.log(`⚠️ LOW LIQUIDITY: $${liquidity.toFixed(2)} < $${LIQUIDITY_THRESHOLD} threshold`);
      }
      
      return { 
        price, 
        totalSupply, 
        circulatingSupply, 
        liquidity, 
        source: "DEXSCREENER_LIVE",
        socials 
      };
    } else {
      console.log(`❌ No price data for pool ${poolAddress}`);
      return { 
        price: null, 
        totalSupply: null, 
        circulatingSupply: null, 
        liquidity: 0, 
        source: "DEAD_TOKEN",
        socials: {}
      };
    }
    
  } catch (error) {
    console.error(`Error fetching price/supply for pool ${poolAddress}:`, error);
    return { 
      price: null, 
      totalSupply: null, 
      circulatingSupply: null, 
      liquidity: 0, 
      source: "DEAD_TOKEN",
      socials: {}
    };
  }
}

serve(async (req)=>{
  try {
    // Create Supabase client with service role
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '', 
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '', 
      {
        auth: {
          persistSession: false,
          autoRefreshToken: false
        }
      }
    );
    
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

        // Fetch current price, supply, liquidity AND social data if we have pool address and network
        if (call.token?.pa && call.token?.network) {
          console.log(`Fetching price/supply/liquidity/socials for ${call.token.symbol || 'UNKNOWN'} on ${call.token.network}...`);
          const priceData = await fetchCurrentPriceAndSupply(call.token.network, call.token.pa);
          
          // Price and supply data (same as before)
          callData.price_at_call = priceData.price;
          // ALSO set current_price to avoid N/A display until ultra-tracker runs
          callData.current_price = priceData.price;
          
          callData.price_source = priceData.source;
          callData.total_supply = priceData.totalSupply || null;
          callData.circulating_supply = priceData.circulatingSupply || null;
          callData.liquidity_usd = priceData.liquidity || 0;
          
          // ADD SOCIAL DATA
          if (priceData.socials) {
            // Only set social fields if they have actual values
            const hasAnySocial = priceData.socials.website_url || 
                               priceData.socials.twitter_url || 
                               priceData.socials.telegram_url || 
                               priceData.socials.discord_url;
                               
            if (hasAnySocial) {
              callData.website_url = priceData.socials.website_url || null;
              callData.twitter_url = priceData.socials.twitter_url || null;
              callData.telegram_url = priceData.socials.telegram_url || null;
              callData.discord_url = priceData.socials.discord_url || null;
              callData.socials_fetched_at = new Date().toISOString();
            }
          }
          
          // Mark as dead if liquidity is below threshold
          const LIQUIDITY_THRESHOLD = 1000;
          if (priceData.liquidity < LIQUIDITY_THRESHOLD) {
            callData.is_dead = true;
            console.log(`🪦 Token ${call.token.symbol} marked as DEAD - liquidity $${priceData.liquidity.toFixed(2)} < $${LIQUIDITY_THRESHOLD}`);
          } else {
            callData.is_dead = false;
          }
          
          // Calculate market_cap_at_call if we have supply data
          if (priceData.price && priceData.totalSupply) {
            // Calculate the market cap regardless of supply similarity
            const estimatedMarketCap = priceData.price * priceData.totalSupply;
            
            // Check if supplies are similar (within 5%)
            const supplyDiff = priceData.circulatingSupply && priceData.totalSupply 
              ? Math.abs(priceData.circulatingSupply - priceData.totalSupply) / priceData.totalSupply * 100
              : 0;
            const suppliesAreSimilar = supplyDiff < 5;
            
            if (!suppliesAreSimilar) {
              console.log(`   Supply mismatch (${supplyDiff.toFixed(1)}% diff), but still calculating market cap`);
            }
            
            // ALWAYS set both market caps to avoid N/A display
            callData.market_cap_at_call = estimatedMarketCap;
            callData.current_market_cap = estimatedMarketCap;
            console.log(`   Calculated market_cap_at_call: $${callData.market_cap_at_call.toLocaleString()}`);
          }
          
          // FALLBACK 1: If we have price but no fresh supply, check existing DB supply
          if (!callData.current_market_cap && callData.current_price) {
            // Check if token already has supply in database
            const existingSupply = existingToken?.total_supply || existingToken?.circulating_supply;
            if (existingSupply) {
              callData.current_market_cap = callData.current_price * existingSupply;
              // Also set market_cap_at_call if not set
              if (!callData.market_cap_at_call) {
                callData.market_cap_at_call = callData.current_market_cap;
              }
              console.log(`   Fallback: Using existing supply for market cap: $${callData.current_market_cap.toLocaleString()}`);
            }
          }
          
          // FALLBACK 2: If still no market cap but we just set supply, calculate it
          if (!callData.current_market_cap && callData.current_price && callData.total_supply) {
            callData.current_market_cap = callData.current_price * callData.total_supply;
            // Also set market_cap_at_call if not set
            if (!callData.market_cap_at_call) {
              callData.market_cap_at_call = callData.current_market_cap;
            }
            console.log(`   Fallback: Using new supply for market cap: $${callData.current_market_cap.toLocaleString()}`);
          }
          
          // Initialize ROI fields to 0 for new tokens (so UI doesn't show "-")
          callData.roi_percent = 0;
          callData.ath_price = callData.current_price || callData.price_at_call;
          callData.ath_roi_percent = 0;
          
          // Initialize ATH market cap to current market cap (for new tokens)
          callData.ath_market_cap = callData.current_market_cap || callData.market_cap_at_call;
          
          if (callData.total_supply || callData.circulating_supply) {
            callData.supply_updated_at = new Date().toISOString();
          }
          
          // If KROM didn't provide a buy timestamp, use current time as the effective buy time
          if (!callData.buy_timestamp) {
            callData.buy_timestamp = new Date().toISOString();
          }
        } else {
          console.log(`No pool address or network for ${call.token?.symbol || 'UNKNOWN'} - skipping price/supply/liquidity fetch`);
          callData.price_at_call = null;
          callData.price_source = "NO_POOL_DATA";
          callData.total_supply = null;
          callData.circulating_supply = null;
          callData.liquidity_usd = null;
          callData.is_dead = false; // Can't determine without pool data
          // If KROM didn't provide a buy timestamp, use current time as the effective buy time
          if (!callData.buy_timestamp) {
            callData.buy_timestamp = new Date().toISOString();
          }
        }

        // Try to insert - if it already exists, it will fail with unique constraint
        const { data, error } = await supabase.from('crypto_calls').insert(callData).select();
        
        if (error) {
          if (error.code === '23505') {
            continue; // Duplicate - skip
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
          
          const liquidityInfo = callData.liquidity_usd !== undefined
            ? `, Liquidity: $${callData.liquidity_usd.toFixed(2)}`
            : '';
          
          const socialInfo = callData.website_url || callData.twitter_url
            ? `, Socials: ${callData.website_url ? 'Web ' : ''}${callData.twitter_url ? 'Twitter' : ''}`
            : '';
          
          const deadStatus = callData.is_dead ? ' [DEAD - LOW LIQUIDITY]' : '';
          
          console.log(`Added new call: ${call._id} - ${call.token?.symbol || 'Unknown'} on ${call.token?.network || 'unknown'} - ${priceInfo}${liquidityInfo}${socialInfo}${deadStatus}`);
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