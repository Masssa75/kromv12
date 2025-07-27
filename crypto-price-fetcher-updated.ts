// Copy this entire file and paste it into the Supabase Dashboard
// Edge Functions > crypto-price-fetcher > Edit

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.8'
import { corsHeaders } from '../_shared/cors.ts'

const BATCH_SIZE = 50 // Can process many more with 150s timeout
const DELAY_MS = 1000 // 1 second between API calls to be safe

interface TokenPrice {
  usd: number;
  timestamp: number;
}

interface OHLCVData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TokenInfo {
  address: string;
  name: string;
  symbol: string;
  price_usd: number;
  fdv_usd?: number;
  market_cap_usd?: number;
  pool_address?: string;
  total_supply?: string;
  circulating_supply?: string;
}

const GECKOTERMINAL_BASE_URL = 'https://api.geckoterminal.com/api/v2';

class GeckoTerminalAPI {
  private async delay(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  static guessNetwork(address: string): string {
    // Simple heuristic based on address format
    if (address.length === 42 && address.startsWith('0x')) {
      return 'eth';
    } else if (address.length >= 32 && address.length <= 44 && !address.startsWith('0x')) {
      return 'solana';
    }
    return 'eth'; // default
  }

  async getTokenInfo(network: string, address: string): Promise<TokenInfo | null> {
    try {
      const url = `${GECKOTERMINAL_BASE_URL}/networks/${network}/tokens/${address}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch token info: ${response.status}`);
      }
      
      const data = await response.json();
      const attributes = data.data?.attributes;
      
      if (!attributes) {
        return null;
      }
      
      return {
        address: attributes.address,
        name: attributes.name,
        symbol: attributes.symbol,
        price_usd: parseFloat(attributes.price_usd || '0'),
        fdv_usd: attributes.fdv_usd ? parseFloat(attributes.fdv_usd) : undefined,
        market_cap_usd: attributes.market_cap_usd ? parseFloat(attributes.market_cap_usd) : undefined,
        pool_address: attributes.pool_address,
        total_supply: attributes.total_supply,
        circulating_supply: attributes.circulating_supply
      };
    } catch (error) {
      console.error(`Error fetching token info: ${error}`);
      return null;
    }
  }

  async getHistoricalPrice(network: string, poolAddress: string, timestamp: number): Promise<number | null> {
    try {
      // Try different timeframes to find historical data
      const timeframes = [
        { interval: 'day', beforeOffset: 86400, limit: 30 },
        { interval: 'hour', beforeOffset: 3600, limit: 168 },
        { interval: 'minute', beforeOffset: 300, limit: 288 }
      ];
      
      for (const { interval, beforeOffset, limit } of timeframes) {
        const url = `${GECKOTERMINAL_BASE_URL}/networks/${network}/pools/${poolAddress}/ohlcv/${interval}?before_timestamp=${timestamp + beforeOffset}&limit=${limit}&currency=usd`;
        const response = await fetch(url);
        
        if (!response.ok) {
          continue;
        }
        
        const data = await response.json();
        const ohlcvData = data.data?.attributes?.ohlcv_list;
        
        if (!ohlcvData || ohlcvData.length === 0) {
          continue;
        }
        
        // Find closest price to target timestamp
        let closestPrice = null;
        let closestDiff = Infinity;
        
        for (const candle of ohlcvData) {
          const diff = Math.abs(candle[0] - timestamp);
          if (diff < closestDiff) {
            closestDiff = diff;
            closestPrice = candle[4]; // close price
          }
        }
        
        if (closestPrice !== null) {
          return closestPrice;
        }
        
        // Add delay between requests
        await this.delay(100);
      }
      
      return null;
    } catch (error) {
      console.error(`Error fetching historical price: ${error}`);
      return null;
    }
  }

  async getATH(network: string, poolAddress: string, sinceTimestamp: number): Promise<{ price: number; timestamp: number } | null> {
    try {
      const now = Math.floor(Date.now() / 1000);
      let maxPrice = 0;
      let maxPriceTimestamp = 0;
      let currentTime = now;
      
      // Fetch OHLCV data in batches going backwards from current time
      while (currentTime > sinceTimestamp && currentTime > sinceTimestamp - 86400 * 365) { // Don't go back more than 1 year from call
        const fromTime = Math.max(sinceTimestamp, currentTime - 86400 * 30); // 30 days per batch
        
        const url = `${GECKOTERMINAL_BASE_URL}/networks/${network}/pools/${poolAddress}/ohlcv/day?from_timestamp=${fromTime}&to_timestamp=${currentTime}&limit=1000`;
        const response = await fetch(url);
        
        if (!response.ok) {
          console.log(`Failed to fetch OHLCV data: ${response.status}`);
          break;
        }
        
        const data = await response.json();
        const ohlcvData = data.data?.attributes?.ohlcv_list;
        
        if (!ohlcvData || ohlcvData.length === 0) {
          break;
        }
        
        // Find the highest price in this batch
        for (const candle of ohlcvData) {
          const high = candle[2]; // high price
          if (high > maxPrice) {
            maxPrice = high;
            maxPriceTimestamp = candle[0]; // timestamp
          }
        }
        
        // Move to the next batch
        const oldestCandle = ohlcvData[ohlcvData.length - 1];
        currentTime = oldestCandle[0] - 86400; // Go back 1 day before the oldest candle
        
        // Add delay to respect rate limits
        await this.delay(100);
      }
      
      if (maxPrice === 0) {
        return null;
      }
      
      return {
        price: maxPrice,
        timestamp: maxPriceTimestamp
      };
    } catch (error) {
      console.error(`Error fetching ATH: ${error}`);
      return null;
    }
  }

  async getTokenDataWithMarketCaps(network: string, address: string, callTimestamp: number) {
    const tokenInfo = await this.getTokenInfo(network, address);
    
    if (!tokenInfo) {
      console.log(`No token info found for ${address}`);
      return {
        tokenInfo: null,
        priceAtCall: null,
        currentPrice: null,
        ath: null,
        marketCapAtCall: null,
        currentMarketCap: tokenInfo?.market_cap_usd || null,
        athMarketCap: null,
        fdvAtCall: null,
        currentFDV: tokenInfo?.fdv_usd || null,
        athFDV: null
      };
    }
    
    console.log(`Token info retrieved: ${tokenInfo.symbol} - Current price: $${tokenInfo.price_usd}`);
    
    // For historical price, we need to find pools if not already available
    let priceAtCall = null;
    let poolAddress = tokenInfo.pool_address;
    
    // If no pool address, try to find pools
    if (!poolAddress) {
      try {
        const poolsUrl = `${GECKOTERMINAL_BASE_URL}/networks/${network}/tokens/${address}/pools`;
        const poolsResponse = await fetch(poolsUrl);
        
        if (poolsResponse.ok) {
          const poolsData = await poolsResponse.json();
          const pools = poolsData.data || [];
          
          if (pools.length > 0) {
            // Get the most liquid pool
            const sortedPools = pools.sort((a: any, b: any) => {
              const liquidityA = parseFloat(a.attributes?.reserve_in_usd || '0');
              const liquidityB = parseFloat(b.attributes?.reserve_in_usd || '0');
              return liquidityB - liquidityA;
            });
            
            poolAddress = sortedPools[0].attributes?.address;
          }
        }
      } catch (error) {
        console.log(`Error fetching pools: ${error}`);
      }
    }
    
    if (poolAddress) {
      priceAtCall = await this.getHistoricalPrice(network, poolAddress, callTimestamp);
      if (!priceAtCall) {
        console.log(`No OHLCV data available for token ${address}`);
      }
    } else {
      console.log(`No pool found for token ${address}`);
    }
    
    // Get ATH - use the pool address we found
    let ath = null;
    if (poolAddress) {
      ath = await this.getATH(network, poolAddress, callTimestamp);
    }
    
    // Calculate market caps if we have supply info
    const supply = tokenInfo.circulating_supply ? parseFloat(tokenInfo.circulating_supply) : 
                   tokenInfo.total_supply ? parseFloat(tokenInfo.total_supply) : null;
    
    return {
      tokenInfo,
      priceAtCall,
      currentPrice: tokenInfo.price_usd,
      ath,
      marketCapAtCall: priceAtCall && supply ? priceAtCall * supply : null,
      currentMarketCap: tokenInfo.market_cap_usd || (tokenInfo.price_usd && supply ? tokenInfo.price_usd * supply : null),
      athMarketCap: ath && supply ? ath.price * supply : null,
      fdvAtCall: priceAtCall && tokenInfo.total_supply ? priceAtCall * parseFloat(tokenInfo.total_supply) : null,
      currentFDV: tokenInfo.fdv_usd || (tokenInfo.price_usd && tokenInfo.total_supply ? tokenInfo.price_usd * parseFloat(tokenInfo.total_supply) : null),
      athFDV: ath && tokenInfo.total_supply ? ath.price * parseFloat(tokenInfo.total_supply) : null
    };
  }
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const startTime = Date.now()

  try {
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Missing Supabase credentials')
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey)
    const geckoTerminal = new GeckoTerminalAPI()

    // Get calls that have contracts but no price data
    // Prioritize recently analyzed calls
    const { data: calls, error } = await supabase
      .from('crypto_calls')
      .select('krom_id, ticker, raw_data, buy_timestamp, created_at, analysis_score, x_analysis_score')
      .not('raw_data->token->ca', 'is', null)
      .is('price_at_call', null)
      .or('analysis_score.not.is.null,x_analysis_score.not.is.null')
      .order('analysis_score', { ascending: false, nullsFirst: false })
      .order('created_at', { ascending: false })
      .limit(BATCH_SIZE)

    if (error) {
      console.error('Database error:', error)
      throw new Error('Failed to fetch calls')
    }

    if (!calls || calls.length === 0) {
      return new Response(
        JSON.stringify({ 
          message: 'No calls found that need price data',
          processed: 0,
          duration: ((Date.now() - startTime) / 1000).toFixed(1)
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const results = {
      processed: 0,
      successful: 0,
      failed: 0,
      errors: [] as any[]
    }

    console.log(`Processing ${calls.length} calls for price fetching`)

    // Process calls sequentially to avoid rate limits
    for (const call of calls) {
      try {
        const contractAddress = call.raw_data?.token?.ca
        if (!contractAddress) {
          throw new Error('No contract address found')
        }

        const network = call.raw_data?.token?.network || GeckoTerminalAPI.guessNetwork(contractAddress)
        const callTimestamp = call.buy_timestamp || call.created_at
        const timestampInSeconds = new Date(callTimestamp).getTime() / 1000

        console.log(`Fetching token data for ${contractAddress} on ${network}`)

        // Fetch comprehensive token data
        const tokenData = await geckoTerminal.getTokenDataWithMarketCaps(
          network,
          contractAddress,
          timestampInSeconds
        )

        // Calculate metrics
        const roi = tokenData.priceAtCall && tokenData.currentPrice 
          ? ((tokenData.currentPrice - tokenData.priceAtCall) / tokenData.priceAtCall) * 100 
          : null

        const athROI = tokenData.priceAtCall && tokenData.ath?.price 
          ? ((tokenData.ath.price - tokenData.priceAtCall) / tokenData.priceAtCall) * 100 
          : null

        // Update database with price data
        const { error: updateError } = await supabase
          .from('crypto_calls')
          .update({
            price_at_call: tokenData.priceAtCall,
            current_price: tokenData.currentPrice,
            ath_price: tokenData.ath?.price || null,
            ath_timestamp: tokenData.ath?.timestamp ? new Date(tokenData.ath.timestamp * 1000).toISOString() : null,
            roi_percent: roi,
            ath_roi_percent: athROI,
            price_network: network,
            price_fetched_at: new Date().toISOString(),
            market_cap_at_call: tokenData.marketCapAtCall,
            current_market_cap: tokenData.currentMarketCap,
            ath_market_cap: tokenData.athMarketCap,
            fdv_at_call: tokenData.fdvAtCall,
            current_fdv: tokenData.currentFDV,
            ath_fdv: tokenData.athFDV,
            token_supply: tokenData.tokenInfo?.total_supply || null
          })
          .eq('krom_id', call.krom_id)

        if (updateError) {
          throw updateError
        }

        results.successful++
        console.log(`✓ Price fetched for ${call.ticker}`)

        // Add delay to respect rate limits
        if (results.processed < calls.length - 1) {
          await geckoTerminal.delay(DELAY_MS)
        }

      } catch (error) {
        results.failed++
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'
        results.errors.push({
          ticker: call.ticker,
          krom_id: call.krom_id,
          error: errorMessage
        })
        console.error(`✗ Failed to fetch price for ${call.ticker}:`, errorMessage)
      }

      results.processed++
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(1)
    console.log(`Price fetch completed in ${duration}s: ${results.successful} successful, ${results.failed} failed`)

    return new Response(
      JSON.stringify({
        message: `Processed ${results.processed} calls in ${duration}s`,
        ...results,
        duration
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Failed to process price fetch',
        details: error instanceof Error ? error.message : 'Unknown error'
      }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})