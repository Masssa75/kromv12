const http = require('http');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '../.env' });

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const server = http.createServer(async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.url === '/api/top-utility-tokens' && req.method === 'GET') {
    try {
      // Fetch top 9 utility tokens by liquidity
      const { data, error } = await supabase
        .from('crypto_calls')
        .select('ticker, network, contract_address, liquidity_usd, current_market_cap, analysis_score, x_analysis_score, roi_percent, analysis_reasoning, analysis_token_type, x_analysis_token_type, ath_roi_percent, website_url, twitter_url')
        .or('analysis_token_type.eq.utility,x_analysis_token_type.eq.utility')
        .not('liquidity_usd', 'is', null)
        .gt('liquidity_usd', 50000) // Only tokens with >$50k liquidity
        .order('liquidity_usd', { ascending: false })
        .limit(9);

      if (error) {
        console.error('Error fetching tokens:', error);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Failed to fetch tokens' }));
        return;
      }

      console.log(`Found ${data.length} utility tokens with >$50k liquidity`);
      
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(data || []));
    } catch (error) {
      console.error('Error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Internal server error' }));
    }
  } else if (req.url === '/api/latest-with-websites' && req.method === 'GET') {
    try {
      // Fetch latest 9 calls that have websites
      const { data, error } = await supabase
        .from('crypto_calls')
        .select('ticker, network, contract_address, liquidity_usd, current_market_cap, analysis_score, x_analysis_score, roi_percent, analysis_reasoning, analysis_token_type, x_analysis_token_type, ath_roi_percent, website_url, twitter_url, buy_timestamp, created_at')
        .not('website_url', 'is', null)
        .neq('website_url', '')
        .order('created_at', { ascending: false })
        .limit(9);

      if (error) {
        console.error('Error fetching tokens with websites:', error);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Failed to fetch tokens' }));
        return;
      }

      console.log(`Found ${data.length} latest tokens with websites`);
      
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(data || []));
    } catch (error) {
      console.error('Error:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Internal server error' }));
    }
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

const PORT = 3001;
server.listen(PORT, () => {
  console.log(`Token store API server running on http://localhost:${PORT}`);
  console.log(`Endpoints:`);
  console.log(`  - http://localhost:${PORT}/api/top-utility-tokens`);
  console.log(`  - http://localhost:${PORT}/api/latest-with-websites`);
});