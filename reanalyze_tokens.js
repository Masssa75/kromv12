// Re-analyze CLX and APD with new scoring system
require('dotenv').config();

const SCRAPERAPI_KEY = process.env.SCRAPERAPI_KEY;
const OPENROUTER_API_KEY = process.env.OPEN_ROUTER_API_KEY;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

async function scrapeWebsite(url) {
  console.log(`Scraping: ${url}`);
  const renderUrl = `http://api.scraperapi.com?api_key=${SCRAPERAPI_KEY}&url=${encodeURIComponent(url)}&render=true&wait=3000`;
  
  const response = await fetch(renderUrl);
  if (!response.ok) throw new Error(`Failed to scrape: ${response.status}`);
  
  const html = await response.text();
  console.log(`Scraped ${html.length} chars`);
  return html;
}

function parseHtml(html) {
  // Extract text content
  const textContent = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 15000);
  
  // Extract headers
  const headers = [];
  const headerRegex = /<h([1-6])[^>]*>([^<]+)<\/h[1-6]>/gi;
  let match;
  while ((match = headerRegex.exec(html)) !== null) {
    headers.push(`H${match[1]}: ${match[2].trim()}`);
  }
  
  // Extract links
  const links = [];
  const linkRegex = /<a[^>]*href=["']([^"']+)["'][^>]*>([^<]*)<\/a>/gi;
  while ((match = linkRegex.exec(html)) !== null) {
    links.push(`${match[2] || 'Link'}: ${match[1]}`);
  }
  
  return {
    textContent,
    headers: headers.slice(0, 20).join('\n'),
    links: links.slice(0, 30).join('\n')
  };
}

async function analyzeWithNewScoring(parsedContent, ticker) {
  const prompt = `Analyze this cryptocurrency project website focusing on LEGITIMACY and REAL-WORLD SIGNALS.

Project: ${ticker}

WEBSITE CONTENT:
${parsedContent.textContent}

HEADERS:
${parsedContent.headers}

LINKS:
${parsedContent.links}

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

IF UTILITY TOKEN - Score these 7 categories:
1. technical_substance: Whitepaper, GitHub, documentation, business model, utility description all combined
2. product_evidence: Proof of actual working product/platform
3. legitimacy_signals: Unfakeable proofs (partnerships, users, revenue, integrations)
4. team_credibility: Who's behind this
5. execution_quality: Professional implementation
6. fast_track_bonus: Additional points for extraordinary signals
7. community_traction: Real engagement and adoption

Return JSON only with all scores and analysis.`;

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
  let content = data.choices[0].message.content;
  
  // Clean up markdown code blocks if present
  if (content.includes('```')) {
    content = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  }
  
  const result = JSON.parse(content);
  console.log('AI Response:', JSON.stringify(result, null, 2));
  return result;
}

async function updateDatabase(ticker, analysis) {
  // Calculate total score
  let totalScore = 0;
  Object.values(analysis.category_scores || {}).forEach(score => {
    totalScore += score;
  });
  
  // Apply fast-track minimum
  if (analysis.fast_track_triggered && totalScore < 12) {
    totalScore = 12;
  }
  
  // Calculate tier
  let tier;
  if (totalScore >= 18) tier = 'ALPHA';
  else if (totalScore >= 12) tier = 'SOLID';
  else if (totalScore >= 7) tier = 'BASIC';
  else tier = 'TRASH';
  
  console.log(`\n${ticker} Analysis Results:`);
  console.log(`Type: ${analysis.token_type}`);
  console.log(`Score: ${totalScore}/21`);
  console.log(`Tier: ${tier}`);
  console.log(`Fast-track: ${analysis.fast_track_triggered ? 'YES - ' + analysis.fast_track_reason : 'NO'}`);
  
  // Show category breakdown
  if (analysis.category_scores) {
    console.log('\nCategory Scores:');
    Object.entries(analysis.category_scores).forEach(([cat, score]) => {
      console.log(`  ${cat}: ${score}/3`);
    });
  }
  
  // Update database
  const updateData = {
    website_score: totalScore,
    website_tier: tier,
    website_analyzed_at: new Date().toISOString(),
    website_analysis: {
      score: totalScore,
      tier: tier,
      quick_take: analysis.quick_take || `${tier} tier ${analysis.token_type} token`
    },
    website_analysis_full: analysis,
    website_token_type: analysis.token_type,
    website_analysis_reasoning: analysis.reasoning,
    analysis_token_type: analysis.token_type
  };
  
  const response = await fetch(`${SUPABASE_URL}/rest/v1/crypto_calls?ticker=eq.${ticker}`, {
    method: 'PATCH',
    headers: {
      'apikey': SUPABASE_SERVICE_ROLE_KEY,
      'Content-Type': 'application/json',
      'Prefer': 'return=minimal'
    },
    body: JSON.stringify(updateData)
  });
  
  if (!response.ok) {
    throw new Error(`Database update failed: ${response.status}`);
  }
  
  console.log(`✅ Updated ${ticker} in database`);
}

async function reanalyzeToken(ticker, url) {
  try {
    console.log(`\n🔍 Re-analyzing ${ticker} from ${url}`);
    
    // Scrape website
    const html = await scrapeWebsite(url);
    const content = parseHtml(html);
    
    // Analyze with new scoring
    const analysis = await analyzeWithNewScoring(content, ticker);
    
    // Update database
    await updateDatabase(ticker, analysis);
    
  } catch (error) {
    console.error(`Error analyzing ${ticker}:`, error.message);
  }
}

async function main() {
  console.log('Starting re-analysis with new scoring system...\n');
  
  // Re-analyze CLX (Ballies)
  await reanalyzeToken('CLX', 'https://ai.ballies.gg/');
  
  // Re-analyze APD (APU-Card)
  await reanalyzeToken('APD', 'https://alphapartner.vip/');
  
  console.log('\n✅ Re-analysis complete!');
}

main().catch(console.error);