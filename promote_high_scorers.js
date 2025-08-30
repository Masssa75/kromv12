// Quick script to promote already-analyzed high-scoring tokens
const fetch = require('node-fetch');
require('dotenv').config();

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

async function promoteHighScorers() {
  console.log('🚀 Promoting high-scoring tokens to crypto_calls...\n');

  // Get high-scoring tokens (score >= 8)
  const response = await fetch(
    `${SUPABASE_URL}/rest/v1/token_discovery?select=*&website_stage1_score=gte.8&order=website_stage1_score.desc`,
    {
      headers: {
        'apikey': SUPABASE_KEY,
        'Content-Type': 'application/json'
      }
    }
  );

  const tokens = await response.json();
  console.log(`Found ${tokens.length} high-scoring tokens\n`);

  let promoted = 0;
  let skipped = 0;

  for (const token of tokens) {
    const normalizedScore = Math.round((token.website_stage1_score / 21) * 10);
    console.log(`Processing ${token.symbol} (${token.network}) - Score: ${token.website_stage1_score}/21 (normalized: ${normalizedScore}/10)`);

    // Check if already exists
    const checkResponse = await fetch(
      `${SUPABASE_URL}/rest/v1/crypto_calls?select=id&contract_address=eq.${token.contract_address}&network=eq.${token.network}`,
      {
        headers: {
          'apikey': SUPABASE_KEY
        }
      }
    );

    const existing = await checkResponse.json();
    
    if (existing.length > 0) {
      console.log(`  ⚠️ Already exists in crypto_calls\n`);
      skipped++;
      continue;
    }

    // Prepare data for insertion
    const callData = {
      source: 'new pools',
      contract_address: token.contract_address,
      network: token.network,
      ticker: token.symbol,
      pool_address: token.pool_address,
      buy_timestamp: token.first_seen_at,
      created_at: new Date().toISOString(),
      
      // Market data
      liquidity_usd: token.current_liquidity_usd || token.initial_liquidity_usd || 0,
      price_at_call: token.current_price_usd,
      current_price: token.current_price_usd,
      market_cap_at_call: token.current_market_cap,
      current_market_cap: token.current_market_cap,
      volume_24h: token.current_volume_24h,
      
      // Social data
      website_url: token.website_url,
      twitter_url: token.twitter_url,
      telegram_url: token.telegram_url,
      discord_url: token.discord_url,
      
      // Website analysis (using crypto_calls column names)
      website_score: token.website_stage1_score,
      website_tier: token.website_stage1_tier,
      website_analysis_full: token.website_stage1_analysis,
      website_analyzed_at: token.website_analyzed_at,
      website_analyzed: true,
      
      // Raw data
      raw_data: {
        discovery_id: token.id,
        discovery_data: {
          first_seen_at: token.first_seen_at,
          initial_liquidity: token.initial_liquidity_usd,
          website_found_at: token.website_found_at
        }
      }
    };

    // Insert into crypto_calls
    const insertResponse = await fetch(
      `${SUPABASE_URL}/rest/v1/crypto_calls`,
      {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_KEY,
          'Content-Type': 'application/json',
          'Prefer': 'return=representation'
        },
        body: JSON.stringify(callData)
      }
    );

    if (insertResponse.ok) {
      const newCall = await insertResponse.json();
      console.log(`  ✅ Promoted to crypto_calls with ID: ${newCall[0].id}\n`);
      promoted++;
    } else {
      const error = await insertResponse.text();
      console.log(`  ❌ Failed to promote: ${error}\n`);
    }
  }

  console.log('\n📊 Summary:');
  console.log(`Promoted: ${promoted}`);
  console.log(`Skipped (already exists): ${skipped}`);
}

promoteHighScorers().catch(console.error);