import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

// Constants
const SCRAPERAPI_KEY = Deno.env.get('SCRAPERAPI_KEY') || '';
const OPENROUTER_API_KEY = Deno.env.get('OPEN_ROUTER_API_KEY') || '';
const GITHUB_TOKEN = Deno.env.get('GITHUB_TOKEN') || '';
const ETHERSCAN_API_KEY = Deno.env.get('ETHERSCAN_API_KEY') || 'YourAPIKeyToken';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

// Check for required environment variables
if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error('Missing required environment variables');
}

// Initialize Supabase client with service role for writes
const supabase = createClient(SUPABASE_URL!, SUPABASE_SERVICE_KEY!, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
});

// Block explorer URL mapping
const getBlockExplorerUrls = (network: string, contractAddress: string) => {
  const baseUrls: Record<string, string> = {
    ethereum: 'https://etherscan.io',
    bsc: 'https://bscscan.com',
    solana: 'https://solscan.io',
    base: 'https://basescan.org',
    arbitrum: 'https://arbiscan.io',
    polygon: 'https://polygonscan.com'
  };
  
  const baseUrl = baseUrls[network.toLowerCase()];
  if (!baseUrl) return null;
  
  // Return both token page and contract page URLs
  if (network.toLowerCase() === 'solana') {
    // Solana uses same URL for both
    return {
      tokenPage: `${baseUrl}/token/${contractAddress}`,
      contractPage: `${baseUrl}/token/${contractAddress}`
    };
  }
  
  return {
    tokenPage: `${baseUrl}/token/${contractAddress}`,
    contractPage: `${baseUrl}/address/${contractAddress}#code`
  };
};

// Scrape block explorer with ScraperAPI
async function scrapeBlockExplorer(url: string, waitTime: number = 3000): Promise<string> {
  try {
    console.log(`Scraping: ${url}`);
    
    // Use render=true and wait for JavaScript content
    const scraperUrl = `http://api.scraperapi.com?api_key=${SCRAPERAPI_KEY}&url=${encodeURIComponent(url)}&render=true&wait=${waitTime}`;
    
    const response = await fetch(scraperUrl, {
      method: 'GET',
      headers: {
        'Accept': 'text/html,application/xhtml+xml'
      }
    });
    
    if (!response.ok) {
      throw new Error(`ScraperAPI failed: ${response.status}`);
    }
    
    const html = await response.text();
    console.log(`Scraped ${html.length} characters`);
    
    return html;
  } catch (error) {
    console.error('Scraping error:', error);
    throw error;
  }
}

// Get contract source from Etherscan API
async function getContractSource(network: string, contractAddress: string): Promise<string> {
  // Map network to API endpoints
  const apiEndpoints: Record<string, string> = {
    ethereum: 'https://api.etherscan.io/api',
    bsc: 'https://api.bscscan.com/api',
    polygon: 'https://api.polygonscan.com/api',
    arbitrum: 'https://api.arbiscan.io/api',
    base: 'https://api.basescan.org/api'
  };
  
  const endpoint = apiEndpoints[network.toLowerCase()];
  if (!endpoint) {
    console.log(`No API endpoint for ${network}, will use scraping only`);
    return '';
  }
  
  try {
    const url = `${endpoint}?module=contract&action=getsourcecode&address=${contractAddress}&apikey=${ETHERSCAN_API_KEY}`;
    const response = await fetch(url);
    const data = await response.json();
    
    if (data.status === '1' && data.result && data.result[0]) {
      const sourceCode = data.result[0].SourceCode;
      const contractName = data.result[0].ContractName;
      const compilerVersion = data.result[0].CompilerVersion;
      
      console.log(`Got verified source for ${contractName} (${compilerVersion})`);
      return `Contract Name: ${contractName}\nCompiler: ${compilerVersion}\n\nSOURCE CODE:\n${sourceCode}`;
    }
  } catch (error) {
    console.error('Error fetching contract source:', error);
  }
  
  return '';
}

// Get token page and contract source
async function getTokenData(network: string, contractAddress: string): Promise<{tokenHTML: string, contractSource: string}> {
  const urls = getBlockExplorerUrls(network, contractAddress);
  if (!urls) {
    throw new Error(`No block explorer URLs for network: ${network}`);
  }
  
  console.log(`Getting token page and contract source...`);
  
  // Get both in parallel
  const [tokenHTML, contractSource] = await Promise.all([
    scrapeBlockExplorer(urls.tokenPage, 3000),
    getContractSource(network, contractAddress)
  ]);
  
  return { tokenHTML, contractSource };
}

// Fetch GitHub stats using API
async function getGitHubStats(githubUrls: string[]): Promise<any> {
  if (!githubUrls || githubUrls.length === 0) {
    return null;
  }
  
  try {
    const stats = {
      repos: [],
      totalStars: 0,
      totalForks: 0,
      lastCommit: null as Date | null,
      contributors: 0
    };
    
    for (const url of githubUrls) {
      // Extract owner and repo from GitHub URL
      const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)/);
      if (!match) continue;
      
      const [, owner, repo] = match;
      
      // Fetch repository data
      const repoResponse = await fetch(`https://api.github.com/repos/${owner}/${repo}`, {
        headers: {
          'Authorization': `Bearer ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      });
      
      if (repoResponse.ok) {
        const repoData = await repoResponse.json();
        
        stats.repos.push({
          name: repoData.full_name,
          stars: repoData.stargazers_count,
          forks: repoData.forks_count,
          lastPush: repoData.pushed_at,
          openIssues: repoData.open_issues_count,
          language: repoData.language,
          description: repoData.description
        });
        
        stats.totalStars += repoData.stargazers_count || 0;
        stats.totalForks += repoData.forks_count || 0;
        
        const pushDate = new Date(repoData.pushed_at);
        if (!stats.lastCommit || pushDate > stats.lastCommit) {
          stats.lastCommit = pushDate;
        }
        
        // Fetch contributors count
        const contribResponse = await fetch(`https://api.github.com/repos/${owner}/${repo}/contributors?per_page=1`, {
          headers: {
            'Authorization': `Bearer ${GITHUB_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json'
          }
        });
        
        if (contribResponse.ok) {
          const linkHeader = contribResponse.headers.get('Link');
          if (linkHeader) {
            const match = linkHeader.match(/page=(\d+)>; rel="last"/);
            if (match) {
              stats.contributors += parseInt(match[1]);
            }
          } else {
            const contribs = await contribResponse.json();
            stats.contributors += contribs.length;
          }
        }
      }
    }
    
    return stats;
  } catch (error) {
    console.error('GitHub API error:', error);
    return null;
  }
}

// REMOVED - We're using pure AI discovery now
// The AI will find patterns we haven't even thought of
function extractCriticalData_DEPRECATED(tokenHTML: string, contractHTML: string): any {
  const data: any = {};
  
  // === From Token Page ===
  // Extract holder count
  const holderMatch = tokenHTML.match(/(?:holders?|Holders?)\s*[:)]?\s*([\d,]+)/i);
  if (holderMatch) {
    data.holders = parseInt(holderMatch[1].replace(/,/g, ''));
  }
  
  // Extract warnings
  const warnings = [];
  if (tokenHTML.includes('⚠') || tokenHTML.includes('Warning') || tokenHTML.includes('warning')) {
    const warningMatches = tokenHTML.match(/(?:⚠|Warning:?)\s*([^<\n]{1,200})/gi);
    if (warningMatches) {
      warnings.push(...warningMatches.slice(0, 3));
    }
  }
  if (warnings.length > 0) data.warnings = warnings;
  
  // Extract supply info
  const totalSupplyMatch = tokenHTML.match(/Total\s+Supply[:\s]+([\d,\.]+)/i);
  if (totalSupplyMatch) {
    data.totalSupply = totalSupplyMatch[1];
  }
  
  // === From Contract Page ===
  // Extract tax values from source code
  const taxInfo: any = {};
  
  // Look for initial tax assignments
  const buyTaxMatch = contractHTML.match(/buyTax\s*=\s*(\d+)/i);
  const sellTaxMatch = contractHTML.match(/sellTax\s*=\s*(\d+)/i);
  const buyFeeMatch = contractHTML.match(/buy(?:Fee|_fee)\s*=\s*(\d+)/i);
  const sellFeeMatch = contractHTML.match(/sell(?:Fee|_fee)\s*=\s*(\d+)/i);
  
  if (buyTaxMatch) taxInfo.buyTax = parseInt(buyTaxMatch[1]);
  if (sellTaxMatch) taxInfo.sellTax = parseInt(sellTaxMatch[1]);
  if (buyFeeMatch) taxInfo.buyFee = parseInt(buyFeeMatch[1]);
  if (sellFeeMatch) taxInfo.sellFee = parseInt(sellFeeMatch[1]);
  
  // Look for tax limits
  const maxTaxMatch = contractHTML.match(/(?:MAX|max)_?(?:TAX|Tax|FEE|Fee)\s*=\s*(\d+)/i);
  if (maxTaxMatch) {
    taxInfo.maxTax = parseInt(maxTaxMatch[1]);
  }
  
  // Check for tax validation in changeTax function
  const changeTaxRegex = /function\s+changeTax[\s\S]{0,500}require\s*\([^)]*(?:<=?|>=?)\s*(\d+)/i;
  const taxLimitMatch = contractHTML.match(changeTaxRegex);
  if (taxLimitMatch) {
    taxInfo.taxLimitValidation = parseInt(taxLimitMatch[1]);
  }
  
  // Look for tax-related comments
  const taxComments = contractHTML.match(/\/\/.*(?:tax|fee).*\d+%/gi);
  if (taxComments) {
    taxInfo.taxComments = taxComments.slice(0, 5);
  }
  
  if (Object.keys(taxInfo).length > 0) data.taxInfo = taxInfo;
  
  // Check for critical functions
  const criticalFunctions = [];
  if (contractHTML.match(/function\s+pause/i)) criticalFunctions.push('pause');
  if (contractHTML.match(/function\s+unpause/i)) criticalFunctions.push('unpause');
  if (contractHTML.match(/function\s+mint/i)) criticalFunctions.push('mint');
  if (contractHTML.match(/function\s+burn/i)) criticalFunctions.push('burn');
  if (contractHTML.match(/function\s+blacklist/i)) criticalFunctions.push('blacklist');
  if (contractHTML.match(/function\s+changeTax/i)) criticalFunctions.push('changeTax');
  if (contractHTML.match(/function\s+setFee/i)) criticalFunctions.push('setFee');
  if (contractHTML.match(/function\s+renounceOwnership/i)) criticalFunctions.push('renounceOwnership');
  
  if (criticalFunctions.length > 0) data.ownerFunctions = criticalFunctions;
  
  // Check if verified
  data.contractVerified = contractHTML.includes('Contract Source Code Verified') || 
                          contractHTML.includes('Exact Match');
  
  // Check if renounced
  data.ownershipRenounced = contractHTML.includes('0x0000000000000000000000000000000000000000') &&
                            contractHTML.includes('OwnershipTransferred');
  
  return data;
}

// Perform comprehensive AI analysis with pure discovery
async function analyzeWithAI(
  ticker: string,
  contractAddress: string,
  network: string,
  tokenHTML: string,
  contractSource: string,
  githubData: any,
  stage1Analysis: any
): Promise<any> {
  
  // Truncate HTML to fit within token limits
  const maxHtmlLength = 40000; // Characters for token page
  const maxSourceLength = 60000; // More space for contract source
  
  const truncatedTokenHTML = tokenHTML.length > maxHtmlLength 
    ? tokenHTML.substring(0, maxHtmlLength) + '\n... [TRUNCATED]'
    : tokenHTML;
  const truncatedSource = contractSource.length > maxSourceLength
    ? contractSource.substring(0, maxSourceLength) + '\n... [TRUNCATED]'
    : contractSource;

  const prompt = `You are a cryptocurrency security researcher. Perform a DEEP forensic analysis of this token.

Token: ${ticker}
Contract Address: ${contractAddress}
Network: ${network}

CRITICAL INVESTIGATIVE APPROACH:
- The contract source shows INITIAL/DEPLOYMENT values (what it started with)
- The token page might show CURRENT warnings or states
- Look for evidence of taxes being changed after deployment
- If you see "buyTax = 25" in constructor, that's the INITIAL value
- The token page or recent transactions might reveal CURRENT state
- ALWAYS distinguish between "initially deployed with X%" vs "currently has Y%"

TOKEN OVERVIEW PAGE (holder data, warnings, current activity):
${truncatedTokenHTML}

VERIFIED CONTRACT SOURCE CODE (shows initial deployment values and capabilities):
${truncatedSource || 'SOURCE CODE NOT AVAILABLE - Analyze token page warnings and patterns only'}

${githubData ? `GITHUB STATISTICS:
${JSON.stringify(githubData, null, 2)}` : 'GITHUB DATA: Not available'}

STAGE 1 WEBSITE ANALYSIS FINDINGS:
${JSON.stringify(stage1Analysis, null, 2)}

BE ESPECIALLY ALERT FOR:
- Constructor values (e.g., "buyTax = 25") show INITIAL deployment state
- Token page warnings might indicate CURRENT issues
- Look for discrepancies: if code shows "sellTax = 50" but no warnings appear, taxes may have been changed
- ANY form of trading restriction (not just "tax" - could be "fee", "penalty", "commission")
- Owner powers that could harm holders (pause, blacklist, mint, change fees)
- Hidden or obfuscated functions
- Comments that reveal intentions ("// initial sell tax 50%")

CRITICAL DISCOVERY GUIDELINES:
- If you find initial tax values in constructor, report as "Initially deployed with X%"
- If token page shows no current warnings about taxes, consider they might be 0% now
- If changeTax function exists, ALWAYS note "Owner can change taxes to any value"
- Look for evidence of manipulation (high initial taxes later reduced to trap buyers)
- Your verdict should consider the PATTERN of behavior, not just current state

IMPORTANT: Return ONLY valid JSON, no other text before or after. Use this EXACT format:
{
  "technical_assessment": {
    "score": <0-10>,
    "findings": ["specific technical finding 1", "specific technical finding 2", "..."]
  },
  "investment_red_flags": {
    "score": <0-10 where 10 is safest>,
    "issues": ["specific red flag 1", "specific red flag 2", "..."]
  },
  "key_highlights": ["positive highlight 1", "positive highlight 2", "..."],
  "smoking_guns": ["critical issue if found", "major red flag if found"],
  "verdict": "<HONEYPOT DETECTED|LEGITIMATE|SUSPICIOUS|EARLY STAGE>",
  "final_score": <0-10>,
  "summary": "One comprehensive paragraph summarizing your findings"
}`;

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'https://github.com/kromv12/stage2-analyzer',
        'X-Title': 'KROM Stage 2 Analyzer'
      },
      body: JSON.stringify({
        model: 'moonshotai/kimi-k2',
        messages: [{
          role: 'user',
          content: prompt
        }],
        temperature: 0.3,
        max_tokens: 2000
      })
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`AI analysis failed: ${error}`);
    }

    const result = await response.json();
    const content = result.choices[0].message.content;
    
    console.log('AI Response received, parsing JSON...');
    
    // Try to find JSON in the response
    let jsonStr = content;
    
    // Remove any text before the first {
    const jsonStart = content.indexOf('{');
    if (jsonStart > 0) {
      jsonStr = content.substring(jsonStart);
    }
    
    // First try to extract JSON from markdown code blocks
    const codeBlockMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (codeBlockMatch) {
      jsonStr = codeBlockMatch[1];
    } else {
      // Otherwise try to find raw JSON object
      const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        jsonStr = jsonMatch[0];
      }
    }
    
    try {
      const parsed = JSON.parse(jsonStr);
      console.log(`Analysis complete - Verdict: ${parsed.verdict}, Score: ${parsed.final_score}`);
      return parsed;
    } catch (e) {
      console.error('Failed to parse AI response as JSON:', jsonStr.substring(0, 500));
      throw new Error(`AI response parsing failed: ${e.message}`);
    }
  } catch (error) {
    console.error('AI analysis error:', error);
    throw error;
  }
}

// Main handler
serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  };

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    let tokenId: string | null = null;
    
    // Check if specific tokenId provided
    if (req.method === 'POST') {
      const body = await req.json();
      tokenId = body.tokenId || null;
    }
    
    // Build query
    let query = supabase
      .from('crypto_calls')
      .select('*');
    
    if (tokenId) {
      // Process specific token
      query = query.eq('id', tokenId);
    } else {
      // Process all qualified tokens that haven't been analyzed
      query = query
        .eq('website_stage2_qualified', true)
        .is('stage2_analyzed_at', null)
        .limit(5); // Process in batches
    }
    
    const { data: tokens, error: fetchError } = await query;
    
    if (fetchError) {
      throw fetchError;
    }
    
    if (!tokens || tokens.length === 0) {
      return new Response(
        JSON.stringify({ message: 'No tokens to process' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    const results = [];
    
    for (const token of tokens) {
      try {
        console.log(`Processing Stage 2 analysis for ${token.ticker} (${token.id})`);
        
        // Get token page and contract source
        const { tokenHTML, contractSource } = await getTokenData(
          token.network, 
          token.contract_address
        );
        
        if (contractSource) {
          console.log(`Got ${contractSource.length} chars of contract source`);
        } else {
          console.log('No contract source available, using token page only');
        }
        
        // Get GitHub stats if available
        let githubData = null;
        // Check for stage_2_links in website_analysis or website_analysis_full
        const stage2Links = token.website_analysis?.stage_2_links || 
                           token.website_analysis_full?.stage_2_links || 
                           [];
        
        if (stage2Links && stage2Links.length > 0) {
          const githubUrls = stage2Links.filter((link: string) => 
            link.includes('github.com')
          );
          if (githubUrls.length > 0) {
            githubData = await getGitHubStats(githubUrls);
          }
        }
        
        // Perform pure AI discovery analysis
        const analysis = await analyzeWithAI(
          token.ticker,
          token.contract_address,
          token.network,
          tokenHTML,
          contractSource,
          githubData,
          token.website_analysis || token.website_analysis_full || { score: token.website_score }
        );
        
        // Update database
        const { error: updateError } = await supabase
          .from('crypto_calls')
          .update({
            stage2_score: analysis.final_score,
            stage2_analysis: analysis,
            stage2_analyzed_at: new Date().toISOString()
          })
          .eq('id', token.id);
        
        if (updateError) {
          console.error(`Failed to update token ${token.ticker}:`, updateError);
        } else {
          console.log(`Successfully analyzed ${token.ticker} - Score: ${analysis.final_score}, Verdict: ${analysis.verdict}`);
          results.push({
            ticker: token.ticker,
            score: analysis.final_score,
            verdict: analysis.verdict,
            summary: analysis.summary
          });
        }
        
      } catch (error) {
        console.error(`Error processing ${token.ticker}:`, error);
        results.push({
          ticker: token.ticker,
          error: error.message
        });
      }
    }
    
    return new Response(
      JSON.stringify({ 
        message: `Processed ${results.length} tokens`,
        results 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
    
  } catch (error) {
    console.error('Stage 2 analyzer error:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});