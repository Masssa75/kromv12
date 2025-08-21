import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0';

serve(async (req) => {
  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
    
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    });

    console.log('Starting GeckoTerminal trending token fetcher...');
    
    // Define networks to check for trending pools
    const networks = ['solana', 'ethereum', 'base', 'arbitrum', 'bsc'];
    const allTrendingPools = [];
    
    // Fetch trending pools from each network
    for (const network of networks) {
      try {
        const geckoResponse = await fetch(`https://api.geckoterminal.com/api/v2/networks/${network}/trending_pools`, {
          headers: {
            'Accept': 'application/json'
          }
        });

        if (!geckoResponse.ok) {
          console.log(`Failed to fetch trending pools for ${network}: ${geckoResponse.status}`);
          continue;
        }

        const geckoData = await geckoResponse.json();
        const pools = geckoData.data || [];
        
        // Add network info to each pool and collect them
        pools.forEach(pool => {
          pool.network = network;
          allTrendingPools.push(pool);
        });
        
        console.log(`Fetched ${pools.length} trending pools from ${network}`);
      } catch (error) {
        console.error(`Error fetching ${network} trending pools:`, error);
      }
    }
    
    // Sort all pools by volume and take top 20
    const trendingPools = allTrendingPools
      .sort((a, b) => {
        const volumeA = parseFloat(a.attributes?.volume_usd?.h24 || '0');
        const volumeB = parseFloat(b.attributes?.volume_usd?.h24 || '0');
        return volumeB - volumeA;
      })
      .slice(0, 20);
    
    console.log(`Processing top ${trendingPools.length} trending pools from GeckoTerminal`);
    
    // Batch fetch social data from DexScreener for all pools at once
    const poolsWithSocials = new Map();
    
    // Build pool identifier strings for batch request (network_poolAddress format)
    const poolIdentifiers = trendingPools.map(pool => {
      const network = pool.network;
      const poolAddress = pool.attributes?.address;
      return `${network}_${poolAddress}`;
    });
    
    // DexScreener batch endpoint accepts up to 30 pools
    try {
      console.log(`Fetching social data for ${poolIdentifiers.length} pools from DexScreener...`);
      const batchUrl = `https://api.dexscreener.com/latest/dex/pairs/${poolIdentifiers.join(',')}`;
      
      const dexScreenerResponse = await fetch(batchUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0'
        }
      });
      
      if (dexScreenerResponse.ok) {
        const dexData = await dexScreenerResponse.json();
        const pairs = dexData.pairs || [];
        
        // Map social data by pool address
        for (const pair of pairs) {
          if (pair?.info) {
            const socials: any = {
              website_url: null,
              twitter_url: null,
              telegram_url: null,
              discord_url: null
            };
            
            // Check info.socials array
            if (pair.info.socials && Array.isArray(pair.info.socials)) {
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
            
            // Also check info.websites array
            if (!socials.website_url && pair.info.websites) {
              const websites = pair.info.websites;
              if (Array.isArray(websites) && websites.length > 0) {
                socials.website_url = typeof websites[0] === 'string' 
                  ? websites[0] 
                  : websites[0]?.url || null;
              }
            }
            
            // Store socials mapped by pool address
            poolsWithSocials.set(pair.pairAddress.toLowerCase(), socials);
          }
        }
        
        console.log(`   📱 Found social data for ${poolsWithSocials.size}/${trendingPools.length} pools`);
      }
    } catch (error) {
      console.error('Failed to batch fetch social data from DexScreener:', error);
    }
    
    let newTokensAdded = 0;
    let duplicatesSkipped = 0;
    const errors = [];
    
    // Process each trending pool
    for (const pool of trendingPools) {
      try {
        // Extract pool and token attributes
        const attributes = pool.attributes || {};
        const relationships = pool.relationships || {};
        
        // Get the base token info (this is typically the token we're interested in)
        const baseToken = relationships.base_token?.data || {};
        const baseTokenId = baseToken.id || '';
        
        // Extract network and contract address from base token ID (format: network_address)
        const [network, contractAddress] = baseTokenId.split('_');
        
        if (!network || !contractAddress) {
          console.log(`Invalid token ID format: ${baseTokenId}`);
          continue;
        }
        
        // Map GeckoTerminal network names to our format
        const networkMap: { [key: string]: string } = {
          'eth': 'ethereum',
          'bsc': 'bsc',
          'polygon': 'polygon',
          'arbitrum': 'arbitrum',
          'base': 'base',
          'solana': 'solana',
          'avalanche': 'avalanche',
          'fantom': 'fantom',
          'optimism': 'optimism'
        };
        
        const mappedNetwork = networkMap[network] || network;
        
        // Extract token details from pool name (format: "TOKEN / QUOTE")
        const poolName = attributes.name || '';
        const ticker = poolName.split(' / ')[0] || 'UNKNOWN';
        const poolAddress = attributes.address;
        
        // Get social data from batch fetch results
        const socials = poolsWithSocials.get(poolAddress.toLowerCase()) || {
          website_url: null,
          twitter_url: null,
          telegram_url: null,
          discord_url: null
        };
        
        // Check if token already exists in crypto_calls
        const { data: existingTokens } = await supabase
          .from('crypto_calls')
          .select('id, source, coin_of_interest_notes')
          .eq('contract_address', contractAddress)
          .eq('network', mappedNetwork)
          .limit(1);
        
        const existingToken = existingTokens?.[0];
        
        if (existingToken) {
          console.log(`Token ${ticker} already exists (source: ${existingToken.source})`);
          
          // Update coin_of_interest_notes if it's from a different source
          if (existingToken.source !== 'gecko_trending') {
            const notes = existingToken.coin_of_interest_notes || '';
            const updatedNotes = notes.includes('GeckoTerminal trending') 
              ? notes 
              : `${notes}${notes ? ' | ' : ''}GeckoTerminal trending on ${new Date().toISOString().split('T')[0]}`;
            
            await supabase
              .from('crypto_calls')
              .update({ 
                coin_of_interest_notes: updatedNotes,
                is_coin_of_interest: true
              })
              .eq('id', existingToken.id);
            
            console.log(`Updated notes for existing token ${ticker}`);
          }
          
          duplicatesSkipped++;
          continue;
        }
        
        // Calculate price and market cap values
        const price = attributes.base_token_price_usd ? parseFloat(attributes.base_token_price_usd) : null;
        const marketCap = attributes.market_cap_usd ? parseFloat(attributes.market_cap_usd) : null;
        const fdv = attributes.fdv_usd ? parseFloat(attributes.fdv_usd) : null;
        const liquidity = attributes.reserve_in_usd ? parseFloat(attributes.reserve_in_usd) : null;
        const volume24h = attributes.volume_usd?.h24 ? parseFloat(attributes.volume_usd.h24) : null;
        
        // Calculate supply from FDV and market cap (same logic as crypto-poller)
        const totalSupply = (fdv && price && price > 0) ? fdv / price : null;
        const circulatingSupply = (marketCap && price && price > 0) ? marketCap / price : totalSupply;
        
        // Check if token is dead (liquidity < $1000)
        const LIQUIDITY_THRESHOLD = 1000;
        const isDead = liquidity !== null && liquidity < LIQUIDITY_THRESHOLD;
        
        // Prepare data for insertion
        const rawData = {
          gecko_terminal_data: {
            pool_id: pool.id,
            pool_name: poolName,
            pool_address: poolAddress,
            base_token_id: baseTokenId,
            base_token_price_usd: attributes.base_token_price_usd,
            market_cap_usd: attributes.market_cap_usd,
            fdv_usd: attributes.fdv_usd,
            volume_24h: attributes.volume_usd?.h24,
            price_change_24h: attributes.price_change_percentage?.h24,
            liquidity_usd: attributes.reserve_in_usd,
            pool_created_at: attributes.pool_created_at,
            transactions_24h: attributes.transactions?.h24,
            locked_liquidity_percentage: attributes.locked_liquidity_percentage
          },
          discovered_at: new Date().toISOString(),
          trending_rank: trendingPools.indexOf(pool) + 1
        };
        
        // Generate a unique ID for non-KROM tokens (using prefix to distinguish from KROM)
        const generatedId = `gecko_${Date.now()}_${Math.random().toString(36).substring(7)}`;
        
        // Insert new token with all proper fields
        const { error: insertError } = await supabase
          .from('crypto_calls')
          .insert({
            krom_id: generatedId,
            source: 'gecko_trending',
            network: mappedNetwork,
            contract_address: contractAddress,
            ticker: ticker,
            buy_timestamp: new Date().toISOString(),
            raw_data: rawData,
            is_coin_of_interest: true,
            coin_of_interest_notes: `GeckoTerminal trending #${rawData.trending_rank} on ${new Date().toISOString().split('T')[0]}`,
            pool_address: poolAddress,
            // Set both current AND at_call prices (since we're discovering it now)
            current_price: price,
            price_at_call: price,  // KEY: Set initial price
            price_source: liquidity && liquidity > 0 ? 'GECKO_TERMINAL' : 'DEAD_TOKEN',
            // Set both current AND at_call market caps
            current_market_cap: marketCap,
            market_cap_at_call: marketCap,  // KEY: Set initial market cap
            // Volume and liquidity
            volume_24h: volume24h,
            liquidity_usd: liquidity,
            // Supply data
            total_supply: totalSupply,
            circulating_supply: circulatingSupply,
            supply_updated_at: (totalSupply || circulatingSupply) ? new Date().toISOString() : null,
            // Social data from DexScreener
            website_url: socials.website_url,
            twitter_url: socials.twitter_url,
            telegram_url: socials.telegram_url,
            discord_url: socials.discord_url,
            socials_fetched_at: (socials.website_url || socials.twitter_url || socials.telegram_url) ? new Date().toISOString() : null,
            // Initialize ATH data (important for ROI calculations)
            ath_price: price,  // Initialize ATH to entry price
            ath_timestamp: new Date().toISOString(),
            ath_roi_percent: 0.0,  // Start at 0% ROI
            ath_market_cap: marketCap,
            // Dead token tracking
            is_dead: isDead
          });
        
        if (insertError) {
          console.error(`Error inserting ${ticker}:`, insertError);
          errors.push({ ticker, error: insertError.message });
        } else {
          newTokensAdded++;
          console.log(`Added new trending token: ${ticker} (${mappedNetwork})`);
          if (isDead) {
            console.log(`   🪦 Token marked as DEAD - liquidity $${liquidity?.toFixed(2)} < $${LIQUIDITY_THRESHOLD}`);
          }
          if (totalSupply || circulatingSupply) {
            console.log(`   📊 Supply data: Total=${totalSupply?.toLocaleString()}, Circulating=${circulatingSupply?.toLocaleString()}`);
          }
          console.log(`   💰 Market Cap: $${marketCap?.toLocaleString()}, Price: $${price?.toFixed(6)}`);
        }
        
      } catch (error) {
        console.error(`Error processing pool:`, error);
        errors.push({ pool: pool.id, error: error.message });
      }
    }
    
    const summary = {
      success: true,
      timestamp: new Date().toISOString(),
      stats: {
        totalTrending: trendingPools.length,
        newTokensAdded,
        duplicatesSkipped,
        errors: errors.length
      },
      errors: errors.length > 0 ? errors : undefined
    };
    
    console.log('GeckoTerminal trending summary:', summary);
    
    return new Response(JSON.stringify(summary), {
      headers: { "Content-Type": "application/json" }
    });
    
  } catch (error) {
    console.error('Error in crypto-gecko-trending:', error);
    return new Response(JSON.stringify({
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
});