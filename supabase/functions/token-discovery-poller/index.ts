import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    });

    console.log('🔍 Starting token discovery polling...');

    // Networks to poll
    const networks = ['solana', 'eth', 'base', 'polygon', 'arbitrum', 'bsc'];
    let totalNewTokens = 0;
    let totalErrors = 0;

    for (const network of networks) {
      try {
        console.log(`\n📊 Fetching new pools for ${network}...`);
        
        // Fetch new pools from GeckoTerminal
        const response = await fetch(
          `https://api.geckoterminal.com/api/v2/networks/${network}/new_pools?page=1`,
          {
            headers: {
              'Accept': 'application/json',
              'User-Agent': 'KROM Token Discovery Bot'
            }
          }
        );

        if (!response.ok) {
          console.error(`❌ Failed to fetch ${network}: ${response.status}`);
          totalErrors++;
          continue;
        }

        const data = await response.json();
        const pools = data.data || [];
        
        console.log(`  Found ${pools.length} pools for ${network}`);

        // Process each pool
        for (const pool of pools) {
          try {
            const attrs = pool.attributes || {};
            const relationships = pool.relationships || {};
            
            // Extract token info from relationships
            const baseToken = relationships.base_token?.data || {};
            const baseTokenId = baseToken.id || '';
            
            // Parse token address from ID (format: network_address)
            const tokenAddress = baseTokenId.split('_').pop() || '';
            
            if (!tokenAddress) {
              console.log(`  ⚠️ No token address found for pool`);
              continue;
            }

            // Extract pool data
            const poolData = {
              contract_address: tokenAddress,
              symbol: attrs.name?.split(' / ')[0] || null,
              name: attrs.name || null,
              network: network,
              pool_address: attrs.address || null,
              initial_liquidity_usd: parseFloat(attrs.reserve_in_usd || '0'),
              initial_volume_24h: parseFloat(attrs.volume_usd?.h24 || '0'),
              raw_data: {
                pool_attrs: attrs,
                created_at: attrs.pool_created_at
              }
            };

            // Skip if liquidity is too low (likely scam/test)
            if (poolData.initial_liquidity_usd < 100) {
              continue;
            }

            // Try to insert (will be ignored if duplicate due to unique constraint)
            const { data: insertedData, error } = await supabase
              .from('token_discovery')
              .insert(poolData)
              .select()
              .single();

            if (error) {
              // Ignore duplicate key errors
              if (!error.message.includes('duplicate key')) {
                console.error(`  ❌ Insert error for ${poolData.symbol}: ${error.message}`);
              }
            } else {
              console.log(`  ✅ New token discovered: ${poolData.symbol} (${network}) - $${poolData.initial_liquidity_usd.toFixed(0)} liquidity`);
              totalNewTokens++;
            }

          } catch (poolError) {
            console.error(`  ❌ Error processing pool: ${poolError}`);
            totalErrors++;
          }
        }

      } catch (networkError) {
        console.error(`❌ Error processing ${network}: ${networkError}`);
        totalErrors++;
      }
    }

    // Summary
    const summary = {
      success: true,
      message: `Token discovery completed`,
      stats: {
        new_tokens_discovered: totalNewTokens,
        networks_processed: networks.length,
        errors: totalErrors
      },
      timestamp: new Date().toISOString()
    };

    console.log('\n📊 Discovery Summary:', summary);

    return new Response(
      JSON.stringify(summary),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('❌ Fatal error in token discovery:', error);
    
    return new Response(
      JSON.stringify({ 
        error: error.message,
        success: false 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    );
  }
});