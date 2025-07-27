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
        // We want data from BEFORE the timestamp, not after
        const url = `${GECKOTERMINAL_BASE_URL}/networks/${network}/pools/${poolAddress}/ohlcv/${interval}?before_timestamp=${timestamp}&limit=${limit}&currency=usd`;
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

  async getATHSinceTimestamp(network: string, poolAddress: string, sinceTimestamp: number): Promise<{ price: number; timestamp: number } | null> {
    try {
      console.log(`Fetching ATH since ${new Date(sinceTimestamp * 1000).toISOString()}`);
      
      let maxPrice = 0;
      let maxTimestamp = 0;
      const currentTime = Math.floor(Date.now() / 1000);
      
      // Fetch OHLCV data to find ATH
      const url = `${GECKOTERMINAL_BASE_URL}/networks/${network}/pools/${poolAddress}/ohlcv/day?limit=1000&currency=usd`;
      const response = await fetch(url);
      
      if (response.ok) {
        const data = await response.json();
        const ohlcvData = data.data?.attributes?.ohlcv_list || [];
        
        // Filter data since call timestamp and find highest price
        for (const candle of ohlcvData) {
          if (candle[0] >= sinceTimestamp && candle[2] > maxPrice) { // candle[2] is high
            maxPrice = candle[2];
            maxTimestamp = candle[0];
          }
        }
        
        if (maxPrice > 0) {
          console.log(`Found ATH: $${maxPrice} at ${new Date(maxTimestamp * 1000).toISOString()}`);
          return { price: maxPrice, timestamp: maxTimestamp };
        }
      }
      
      return null;
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
        currentMarketCap: null,
        athMarketCap: null,
        fdvAtCall: null,
        currentFDV: null,
        athFDV: null,
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
            console.log(`Found pool: ${poolAddress}`);
          }
        }
      } catch (error) {
        console.log(`Error fetching pools: ${error}`);
      }
    }
    
    let ath = null;
    
    if (poolAddress) {
      // Fetch both historical price and ATH
      const [historicalPrice, athData] = await Promise.all([
        this.getHistoricalPrice(network, poolAddress, callTimestamp),
        this.getATHSinceTimestamp(network, poolAddress, callTimestamp)
      ]);
      
      priceAtCall = historicalPrice;
      ath = athData;
      
      if (!priceAtCall) {
        console.log(`No historical price data available`);
      }
    } else {
      console.log(`No pool found for token ${address}`);
    }
    
    // Calculate market caps if we have supply info
    const supply = tokenInfo.circulating_supply ? parseFloat(tokenInfo.circulating_supply) : 
                   tokenInfo.total_supply ? parseFloat(tokenInfo.total_supply) : null;
    
    // Calculate FDVs
    const currentFDV = tokenInfo.fdv_usd || 
      (tokenInfo.price_usd && tokenInfo.total_supply ? tokenInfo.price_usd * parseFloat(tokenInfo.total_supply) : null);
    
    let fdvAtCall = null;
    let athFDV = null;
    
    if (currentFDV && tokenInfo.price_usd && tokenInfo.price_usd > 0) {
      if (priceAtCall) {
        fdvAtCall = (priceAtCall / tokenInfo.price_usd) * currentFDV;
      }
      if (ath?.price) {
        athFDV = (ath.price / tokenInfo.price_usd) * currentFDV;
      }
    }
    
    return {
      tokenInfo,
      priceAtCall,
      currentPrice: tokenInfo.price_usd,
      ath,
      marketCapAtCall: priceAtCall && supply ? priceAtCall * supply : null,
      currentMarketCap: tokenInfo.market_cap_usd || (tokenInfo.price_usd && supply ? tokenInfo.price_usd * supply : null),
      athMarketCap: ath?.price && supply ? ath.price * supply : null,
      fdvAtCall,
      currentFDV,
      athFDV,
    };
  }
}

// Helper function to format date in Thai timezone
function formatThaiDate(timestamp: number | null): string | null {
  if (!timestamp) return null
  
  const date = new Date(timestamp * 1000)
  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Bangkok',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  }
  
  return date.toLocaleString('en-US', options) + ' (Thai Time)'
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const startTime = Date.now()

  try {
    // Parse request body
    const { contractAddress, callTimestamp, network: providedNetwork } = await req.json()
    
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
      callTimestamp: new Date(timestampInSeconds * 1000).toISOString()
    })
    
    // Fetch comprehensive token data
    const tokenData = await geckoTerminal.getTokenDataWithMarketCaps(
      network,
      contractAddress,
      timestampInSeconds
    )
    
    // Calculate ROIs
    const roi = tokenData.priceAtCall && tokenData.currentPrice 
      ? ((tokenData.currentPrice - tokenData.priceAtCall) / tokenData.priceAtCall) * 100 
      : null
    
    const athROI = tokenData.priceAtCall && tokenData.ath?.price 
      ? ((tokenData.ath.price - tokenData.priceAtCall) / tokenData.priceAtCall) * 100 
      : null
    
    const drawdownFromATH = tokenData.ath?.price && tokenData.currentPrice
      ? ((tokenData.ath.price - tokenData.currentPrice) / tokenData.ath.price) * 100
      : null
    
    const result = {
      contractAddress,
      network,
      priceAtCall: tokenData.priceAtCall,
      currentPrice: tokenData.currentPrice,
      ath: tokenData.ath?.price || null,
      athDate: tokenData.ath?.timestamp ? new Date(tokenData.ath.timestamp * 1000).toISOString() : null,
      athDateFormatted: formatThaiDate(tokenData.ath?.timestamp || null),
      roi,
      athROI,
      drawdownFromATH,
      callDate: new Date(timestampInSeconds * 1000).toISOString(),
      callDateFormatted: formatThaiDate(timestampInSeconds),
      fetchedAt: new Date().toISOString(),
      marketCapAtCall: tokenData.marketCapAtCall,
      currentMarketCap: tokenData.currentMarketCap,
      athMarketCap: tokenData.athMarketCap,
      fdvAtCall: tokenData.fdvAtCall,
      currentFDV: tokenData.currentFDV,
      athFDV: tokenData.athFDV,
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