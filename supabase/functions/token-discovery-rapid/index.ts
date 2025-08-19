import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Single poll function - fetch 3 pages for better coverage
async function pollOnce(supabase: any) {
  const networks = ['solana', 'eth', 'base', 'polygon', 'arbitrum', 'bsc'];
  let totalNewTokens = 0;
  
  for (const network of networks) {
    // Fetch more pages for Solana due to high volume
    const pagesToFetch = network === 'solana' ? 3 : 1;
    
    for (let page = 1; page <= pagesToFetch; page++) {
      try {
        const response = await fetch(
          `https://api.geckoterminal.com/api/v2/networks/${network}/new_pools?page=${page}`,
          {
            headers: {
              'Accept': 'application/json',
              'User-Agent': 'KROM Token Discovery Bot'
            }
          }
        );

        if (!response.ok) continue;

        const data = await response.json();
        const pools = data.data || [];
      
      for (const pool of pools) {
        try {
          const attrs = pool.attributes || {};
          const relationships = pool.relationships || {};
          const baseToken = relationships.base_token?.data || {};
          const baseTokenId = baseToken.id || '';
          const tokenAddress = baseTokenId.split('_').pop() || '';
          
          if (!tokenAddress) continue;

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

          // Skip if liquidity is too low
          if (poolData.initial_liquidity_usd < 100) continue;

          const { error } = await supabase
            .from('token_discovery')
            .insert(poolData)
            .select()
            .single();

          if (!error) {
            totalNewTokens++;
            console.log(`✅ New: ${poolData.symbol} (${network}) - $${poolData.initial_liquidity_usd.toFixed(0)}`);
          }
        } catch (e) {
          // Silent fail for duplicates
        }
        }
      } catch (e) {
        console.error(`Error polling ${network} page ${page}:`, e);
      }
    }
  }
  
  return totalNewTokens;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    });

    console.log('🚀 Starting rapid token discovery at', new Date().toISOString());
    
    // Single fast poll - no waiting
    const newTokens = await pollOnce(supabase);
    const total = newTokens;
    
    return new Response(
      JSON.stringify({
        success: true,
        message: `Discovery completed - ${total} new tokens found`,
        new_tokens: total,
        timestamp: new Date().toISOString()
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('❌ Fatal error:', error);
    return new Response(
      JSON.stringify({ error: error.message, success: false }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    );
  }
});