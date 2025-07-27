// Debug KAVR price issue
const fetch = require('node-fetch');

async function debugKAVR() {
  console.log('=== Debugging KAVR Price Issue ===\n');
  
  // Try different contract address formats
  const addresses = [
    '0x5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd', // Ethereum format
    '5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd',   // Without 0x
    'KAVRrjFCS7tF1zjWNj7s82N87KDL6hnxXRPvDSkPZhb' // Possible Solana address
  ];
  
  for (const address of addresses) {
    console.log(`\nTesting address: ${address}`);
    
    // Check GeckoTerminal directly
    const network = address.startsWith('0x') ? 'eth' : 'solana';
    const geckoUrl = `https://api.geckoterminal.com/api/v2/networks/${network}/tokens/${address}`;
    
    try {
      const response = await fetch(geckoUrl);
      const data = await response.json();
      
      if (data.data) {
        console.log(`✅ Found on ${network.toUpperCase()}`);
        console.log(`Name: ${data.data.attributes.name}`);
        console.log(`Symbol: ${data.data.attributes.symbol}`);
        console.log(`Price USD: $${data.data.attributes.price_usd}`);
        console.log(`FDV: $${data.data.attributes.fdv_usd}`);
        console.log(`Market Cap: $${data.data.attributes.market_cap_usd}`);
        
        // Try to get pools
        const poolsUrl = `https://api.geckoterminal.com/api/v2/networks/${network}/tokens/${address}/pools`;
        const poolsResponse = await fetch(poolsUrl);
        const poolsData = await poolsResponse.json();
        
        if (poolsData.data && poolsData.data.length > 0) {
          console.log(`\nFound ${poolsData.data.length} pools`);
          const mainPool = poolsData.data[0];
          console.log(`Main pool: ${mainPool.attributes.name}`);
          console.log(`Pool address: ${mainPool.attributes.address}`);
        }
      } else {
        console.log(`❌ Not found on ${network.toUpperCase()}`);
      }
    } catch (error) {
      console.log(`❌ Error: ${error.message}`);
    }
  }
  
  console.log('\n=== Possible Issues ===');
  console.log('1. KAVR might be too new (no price history)');
  console.log('2. Token might not be listed on GeckoTerminal');
  console.log('3. Wrong contract address or network');
  console.log('4. Token might be on a different chain (BSC, Polygon, etc)');
  
  console.log('\n=== Solutions ===');
  console.log('1. Use CoinGecko API as fallback');
  console.log('2. Try DEXScreener API');
  console.log('3. Show "No price data available" instead of identical values');
  console.log('4. Add manual price override option');
}