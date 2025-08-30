// Test script to verify CLX scoring with new criteria
require('dotenv').config();
const OPENROUTER_API_KEY = process.env.OPEN_ROUTER_API_KEY;

const websiteContent = `
Ballies - AI-powered sports prediction platform
102,000+ users
Partnerships: NBA, Crypto.com, BGA, GSIC
Products: Score Stack predictions, AI Agents, Perpetual markets, Free Roll contests
Whitepaper available
Working platform at ballies.gg
`;

const prompt = `Analyze this cryptocurrency project website focusing on LEGITIMACY and REAL-WORLD SIGNALS.

Project: CLX

WEBSITE CONTENT:
${websiteContent}

STEP 1 - TOKEN TYPE CLASSIFICATION:
Classify as either:
- "meme": Community/humor/viral FIRST (even if has utility features like staking)
- "utility": Product/service/infrastructure FIRST (even if has meme elements)

STEP 2 - FAST-TRACK CHECK:
Look for extraordinary legitimacy signals. If ANY of these exist, minimum score = 12:
- Partnership with Fortune 500 company or major brand (NBA, Google, etc.)
- Notable VC funding (>$1M verified)
- Proven founder with exit history or notable background
- Government/institutional partnership
- 100k+ verified users/customers
- Any other EXTRAORDINARY signal that would be impossible/extremely costly to fake

If fast-track applies, note which signal(s) triggered it.

STEP 3 - ADAPTIVE SCORING (0-3 each):

Score these 7 categories for UTILITY TOKEN:
1. technical_substance: Whitepaper, GitHub, documentation, business model, utility description all combined
2. product_evidence: Proof of actual working product/platform
3. legitimacy_signals: Unfakeable proofs (partnerships, users, revenue, integrations)
4. team_credibility: Who's behind this
5. execution_quality: Professional implementation
6. fast_track_bonus: Additional points for extraordinary signals
7. community_traction: Real engagement and adoption

Return JSON only with scores and reasoning.`;

async function testScoring() {
  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'moonshotai/kimi-k2',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.3,
        max_tokens: 1000,
        response_format: { type: "json_object" }
      })
    });

    const data = await response.json();
    console.log('API Response:', JSON.stringify(data, null, 2));
    
    if (!data.choices || !data.choices[0]) {
      console.error('Invalid response from API');
      return;
    }
    
    const result = JSON.parse(data.choices[0].message.content);
    
    console.log('CLX Scoring Results:');
    console.log('===================');
    console.log('Token Type:', result.token_type);
    console.log('Total Score:', result.total_score, '/21');
    console.log('Tier:', result.tier);
    console.log('\nCategory Scores:');
    Object.entries(result.category_scores).forEach(([cat, score]) => {
      console.log(`  ${cat}: ${score}/3`);
    });
    console.log('\nFast-track:', result.fast_track_triggered ? 'YES' : 'NO');
    if (result.fast_track_triggered) {
      console.log('Fast-track Reason:', result.fast_track_reason);
    }
    console.log('\nReasoning:', result.reasoning);
    
  } catch (error) {
    console.error('Error:', error);
  }
}

testScoring();