import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.8'
import { corsHeaders } from '../_shared/cors.ts'

const GECKOTERMINAL_BASE_URL = 'https://api.geckoterminal.com/api/v2';

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
        console.log(`Trying ${interval} timeframe: ${url}`);
        
        const response = await fetch(url);
        
        if (!response.ok) {
          console.log(`Failed to fetch ${interval} data: ${response.status}`);
          continue;
        }
        
        const data = await response.json();
        const ohlcvData = data.data?.attributes?.ohlcv_list;
        
        if (!ohlcvData || ohlcvData.length === 0) {
          console.log(`No ${interval} data available`);
          continue;
        }
        
        console.log(`Found ${ohlcvData.length} ${interval} candles`);
        
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
          console.log(`Found historical price: ${closestPrice} (${Math.round(closestDiff / 60)} minutes difference)`);
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

  async getTokenDataWithMarketCaps(network: string, address: string, callTimestamp: number, providedPoolAddress?: string) {
    const tokenInfo = await this.getTokenInfo(network, address);
    
    if (!tokenInfo) {
      console.log(`No token info found for ${address}`);
      return {
        tokenInfo: null,
        priceAtCall: null,
        currentPrice: null,
        marketCapAtCall: null,
        currentMarketCap: null,
        fdvAtCall: null,
        currentFDV: null,
      };
    }
    
    console.log(`Token info retrieved: ${tokenInfo.symbol} - Current price: $${tokenInfo.price_usd}`);
    
    // For historical price, we need to find pools if not already available
    let priceAtCall = null;
    let poolAddress = providedPoolAddress || tokenInfo.pool_address;
    
    if (providedPoolAddress) {
      console.log(`Using provided pool address: ${providedPoolAddress}`);
    }
    
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
            console.log(`Auto-selected most liquid pool: ${poolAddress}`);
          }
        }
      } catch (error) {
        console.log(`Error fetching pools: ${error}`);
      }
    }
    
    if (poolAddress) {
      priceAtCall = await this.getHistoricalPrice(network, poolAddress, callTimestamp);
      if (!priceAtCall) {
        console.log(`No historical price data available`);
      }
    } else {
      console.log(`No pool found for token ${address}`);
    }
    
    // Calculate market caps if we have supply info
    // Parse supply carefully - it might be in scientific notation or have many digits
    let supply = null;
    let totalSupply = null;
    
    try {
      if (tokenInfo.circulating_supply) {
        supply = parseFloat(tokenInfo.circulating_supply);
        // Sanity check - if supply is absurdly large, it might be an error
        if (supply > 1e30) {
          console.warn(`Circulating supply seems too large: ${tokenInfo.circulating_supply}`);
          supply = null;
        }
      }
      
      if (tokenInfo.total_supply) {
        totalSupply = parseFloat(tokenInfo.total_supply);
        // Sanity check
        if (totalSupply > 1e30) {
          console.warn(`Total supply seems too large: ${tokenInfo.total_supply}`);
          totalSupply = null;
        }
      }
      
      // If no circulating supply but we have total supply, use it
      if (!supply && totalSupply) {
        supply = totalSupply;
      }
    } catch (e) {
      console.error('Error parsing supply:', e);
    }
    
    // Log for debugging
    console.log('Supply calculation:', {
      circulatingSupply: tokenInfo.circulating_supply,
      totalSupply: tokenInfo.total_supply,
      parsedSupply: supply,
      parsedTotalSupply: totalSupply,
      priceAtCall,
      currentPrice: tokenInfo.price_usd
    });
    
    // If we already have market cap from the API, prefer that over calculating it
    const marketCapAtCall = priceAtCall && supply ? priceAtCall * supply : null;
    const currentMarketCap = tokenInfo.market_cap_usd || (tokenInfo.price_usd && supply ? tokenInfo.price_usd * supply : null);
    const fdvAtCall = priceAtCall && totalSupply ? priceAtCall * totalSupply : null;
    const currentFDV = tokenInfo.fdv_usd || (tokenInfo.price_usd && totalSupply ? tokenInfo.price_usd * totalSupply : null);
    
    return {
      tokenInfo,
      priceAtCall,
      currentPrice: tokenInfo.price_usd,
      marketCapAtCall,
      currentMarketCap,
      fdvAtCall,
      currentFDV,
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
    // Parse request body
    const { contractAddress, callTimestamp, network: providedNetwork, poolAddress } = await req.json()
    
    if (!contractAddress) {
      return new Response(
        JSON.stringify({ error: 'Contract address is required' }),
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }
    
    const geckoTerminal = new GeckoTerminalAPI()
    const network = providedNetwork || GeckoTerminalAPI.guessNetwork(contractAddress)
    
    // Convert timestamp to seconds if it's in milliseconds
    const timestampInSeconds = callTimestamp > 1000000000000 
      ? Math.floor(callTimestamp / 1000) 
      : callTimestamp
    
    console.log('Fetching price data for:', {
      contractAddress,
      network,
      callTimestamp: new Date(timestampInSeconds * 1000).toISOString(),
      poolAddress: poolAddress || 'not provided'
    })
    
    // Fetch comprehensive token data
    const tokenData = await geckoTerminal.getTokenDataWithMarketCaps(
      network,
      contractAddress,
      timestampInSeconds,
      poolAddress
    )
    
    // Calculate ROI
    const roi = tokenData.priceAtCall && tokenData.currentPrice 
      ? ((tokenData.currentPrice - tokenData.priceAtCall) / tokenData.priceAtCall) * 100 
      : null
    
    const result = {
      contractAddress,
      network,
      priceAtCall: tokenData.priceAtCall,
      currentPrice: tokenData.currentPrice,
      roi,
      callDate: new Date(timestampInSeconds * 1000).toISOString(),
      fetchedAt: new Date().toISOString(),
      marketCapAtCall: tokenData.marketCapAtCall,
      currentMarketCap: tokenData.currentMarketCap,
      fdvAtCall: tokenData.fdvAtCall,
      currentFDV: tokenData.currentFDV,
      tokenSupply: tokenData.tokenInfo?.total_supply || null,
      duration: ((Date.now() - startTime) / 1000).toFixed(1)
    }
    
    console.log('Price fetch completed:', result)
    
    return new Response(
      JSON.stringify(result),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Failed to fetch price data',
        details: error instanceof Error ? error.message : 'Unknown error'
      }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})