import { corsHeaders } from '../_shared/cors.ts'

const GECKOTERMINAL_BASE_URL = 'https://api.geckoterminal.com/api/v2';

interface HistoricalPriceRequest {
  contractAddress: string;
  network: string;
  timestamp: number;
  poolAddress: string;
}

interface HistoricalPriceResponse {
  contractAddress: string;
  network: string;
  poolAddress: string;
  timestamp: number;
  callDate: string;
  price: number | null;
  candle: {
    timestamp: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  } | null;
  timeDifference: number | null;
  fetchedAt: string;
  duration: string;
}

async function getHistoricalPrice(
  network: string, 
  poolAddress: string, 
  targetTimestamp: number
): Promise<{ price: number | null; candle: any; timeDifference: number | null }> {
  try {
    // Get minute candles around the target timestamp
    const beforeTimestamp = targetTimestamp + 300; // 5 minutes after to ensure we get the candle
    const url = `${GECKOTERMINAL_BASE_URL}/networks/${network}/pools/${poolAddress}/ohlcv/minute?before_timestamp=${beforeTimestamp}&limit=10&currency=usd`;
    
    console.log(`Fetching OHLCV data: ${url}`);
    
    const response = await fetch(url);
    
    if (!response.ok) {
      console.log(`GeckoTerminal API error: ${response.status}`);
      return { price: null, candle: null, timeDifference: null };
    }
    
    const data = await response.json();
    const ohlcvList = data.data?.attributes?.ohlcv_list;
    
    if (!ohlcvList || ohlcvList.length === 0) {
      console.log('No OHLCV data available');
      return { price: null, candle: null, timeDifference: null };
    }
    
    console.log(`Found ${ohlcvList.length} candles`);
    
    // Find the closest candle to our target timestamp
    let closestCandle = null;
    let smallestDifference = Infinity;
    
    for (const candle of ohlcvList) {
      const candleTimestamp = candle[0];
      const timeDifference = Math.abs(candleTimestamp - targetTimestamp);
      
      if (timeDifference < smallestDifference) {
        smallestDifference = timeDifference;
        closestCandle = {
          timestamp: candleTimestamp,
          open: candle[1],
          high: candle[2],
          low: candle[3],
          close: candle[4],
          volume: candle[5]
        };
      }
    }
    
    if (!closestCandle) {
      console.log('No suitable candle found');
      return { price: null, candle: null, timeDifference: null };
    }
    
    // Only return price if candle is within reasonable time range (5 minutes)
    if (smallestDifference > 300) {
      console.log(`Closest candle is ${smallestDifference} seconds away (too far)`);
      return { price: null, candle: closestCandle, timeDifference: smallestDifference };
    }
    
    console.log(`Using candle from ${new Date(closestCandle.timestamp * 1000).toISOString()}, ${smallestDifference}s difference`);
    console.log(`OHLC: ${closestCandle.open} / ${closestCandle.high} / ${closestCandle.low} / ${closestCandle.close}`);
    
    // Return the close price (this is what trading platforms typically show)
    return { 
      price: closestCandle.close, 
      candle: closestCandle, 
      timeDifference: smallestDifference 
    };
    
  } catch (error) {
    console.error('Error fetching historical price:', error);
    return { price: null, candle: null, timeDifference: null };
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
    const body: HistoricalPriceRequest = await req.json()
    
    const { contractAddress, network, timestamp, poolAddress } = body;
    
    // Validate required parameters
    if (!contractAddress) {
      return new Response(
        JSON.stringify({ error: 'contractAddress is required' }),
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }
    
    if (!network) {
      return new Response(
        JSON.stringify({ error: 'network is required' }),
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }
    
    if (!timestamp) {
      return new Response(
        JSON.stringify({ error: 'timestamp is required' }),
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }
    
    if (!poolAddress) {
      return new Response(
        JSON.stringify({ error: 'poolAddress is required' }),
        { 
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }
    
    // Convert timestamp to seconds if it's in milliseconds
    const timestampInSeconds = timestamp > 1000000000000 
      ? Math.floor(timestamp / 1000) 
      : timestamp
    
    console.log('Fetching historical price for:', {
      contractAddress,
      network,
      poolAddress: poolAddress.substring(0, 10) + '...',
      timestamp: timestampInSeconds,
      callDate: new Date(timestampInSeconds * 1000).toISOString()
    })
    
    // Get historical price
    const { price, candle, timeDifference } = await getHistoricalPrice(
      network,
      poolAddress,
      timestampInSeconds
    )
    
    const result: HistoricalPriceResponse = {
      contractAddress,
      network,
      poolAddress,
      timestamp: timestampInSeconds,
      callDate: new Date(timestampInSeconds * 1000).toISOString(),
      price,
      candle,
      timeDifference,
      fetchedAt: new Date().toISOString(),
      duration: ((Date.now() - startTime) / 1000).toFixed(1)
    }
    
    console.log('Historical price fetch completed:', {
      price,
      timeDifference,
      duration: result.duration + 's'
    })
    
    return new Response(
      JSON.stringify(result),
      { 
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json',
          // Cache historical prices forever since they never change
          'Cache-Control': 'public, max-age=31536000, immutable'
        } 
      }
    )

  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Failed to fetch historical price',
        details: error instanceof Error ? error.message : 'Unknown error'
      }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})