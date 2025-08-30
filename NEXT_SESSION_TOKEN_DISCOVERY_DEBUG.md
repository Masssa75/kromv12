# Token Discovery Debug Interface - Implementation Guide

## Context & Problem Statement

The token discovery pipeline (token_discovery → crypto_calls) has visibility issues:
1. **Scraping failures go unnoticed** - APD token showed legitimate payment product in browser but scraper only got 21 chars
2. **Good tokens score low** - CLX/Ballies has 102k users and NBA partnership but scored 11/21 (BASIC) instead of 16-18 (SOLID/ALPHA)
3. **No visibility into unpromoted tokens** - Can't see why tokens aren't making it to crypto_calls
4. **Can't debug AI decisions** - Don't store what content the scraper actually extracted

## Current System Architecture

### Tables
- `token_discovery` - Holds discovered tokens from GeckoTerminal/DexScreener (~7,000/hour)
- `crypto_calls` - Production table for promoted tokens (shown on krom1.com)

### Key Edge Function
- `/supabase/functions/token-discovery-analyzer/` - Scrapes websites, analyzes with AI, promotes high-scoring tokens

### Current Flow
1. Token discovered → stored in token_discovery
2. If has website → scraper fetches content → AI analyzes → score 0-21
3. If score ≥ 7 (normalized ≥ 3/10) → promoted to crypto_calls
4. **Problem**: Only stores AI analysis results, not what scraper saw

## Task 1: Update Analyzer to Store Diagnostic Metrics

### File: `/supabase/functions/token-discovery-analyzer/index.ts`

#### Step 1.1: Modify parseHtmlContent function (around line 98)
Current function returns parsed content but we don't store it. Add diagnostic metrics to the return:

```typescript
function parseHtmlContent(html: string) {
  // ... existing parsing logic ...
  
  // Add diagnostic metrics
  const diagnostics = {
    text_length: textContent.length,
    link_count: linksWithContext.length,
    header_count: headers.length,
    has_meta_description: !!metaDescription,
    has_og_tags: !!(ogTitle || ogDescription),
    html_length: html.length,
    scrape_timestamp: new Date().toISOString()
  };
  
  // Extract key signals for debugging
  const extractedSignals = {
    partnerships_mentioned: [],
    user_count_claims: null,
    funding_mentioned: null,
    has_whitepaper: false,
    has_github: false,
    team_members_found: 0
  };
  
  // Look for partnerships (NBA, Google, Fortune 500, etc.)
  const partnershipKeywords = ['NBA', 'Google', 'Microsoft', 'Amazon', 'Visa', 'Mastercard', 'Crypto.com'];
  partnershipKeywords.forEach(partner => {
    if (textContent.includes(partner) || html.includes(partner)) {
      extractedSignals.partnerships_mentioned.push(partner);
    }
  });
  
  // Look for user count claims (102k users, 100,000 users, etc.)
  const userMatch = textContent.match(/(\d{1,3}[,.]?\d{0,3})[k+]?\s*(users|customers|members|traders)/i);
  if (userMatch) {
    extractedSignals.user_count_claims = userMatch[0];
  }
  
  // Check for whitepaper
  extractedSignals.has_whitepaper = linksWithContext.some(l => 
    l.url.toLowerCase().includes('whitepaper') || 
    l.text.toLowerCase().includes('whitepaper')
  );
  
  // Check for GitHub
  extractedSignals.has_github = linksWithContext.some(l => 
    l.url.includes('github.com')
  );
  
  return {
    text_content: textContent,
    links_with_context: linksWithContext.slice(0, 100),
    headers: headers.slice(0, 50),
    meta_tags: {
      description: metaDescription,
      og_title: ogTitle,
      og_description: ogDescription
    },
    text_length: textContent.length,
    diagnostics,  // NEW
    extracted_signals: extractedSignals  // NEW
  };
}
```

#### Step 1.2: Store diagnostics with analysis (around line 432)
Update the token_discovery update to include diagnostics:

```typescript
const { error: updateError } = await supabase
  .from('token_discovery')
  .update({
    website_analyzed_at: new Date().toISOString(),
    website_stage1_score: analysis.total_score,
    website_stage1_tier: analysis.tier,
    website_stage1_analysis: {
      category_scores: analysis.category_scores,
      token_type: analysis.token_type,
      exceptional_signals: analysis.exceptional_signals,
      missing_elements: analysis.missing_elements,
      quick_take: analysis.quick_take,
      quick_assessment: analysis.quick_assessment,
      reasoning: analysis.reasoning,
      fast_track_triggered: analysis.fast_track_triggered || false,
      fast_track_reason: analysis.fast_track_reason || null,
      // ADD THESE NEW FIELDS:
      scrape_metrics: parsedContent.diagnostics,
      extracted_signals: parsedContent.extracted_signals
    }
  })
  .eq('id', token.id);
```

#### Step 1.3: Deploy the updated function
```bash
source .env && SUPABASE_ACCESS_TOKEN=$SUPABASE_ACCESS_TOKEN npx supabase functions deploy token-discovery-analyzer --project-ref eucfoommxxvqmmwdbkdv
```

## Task 2: Create Token Discovery Debug Interface

### File: `/krom-analysis-app/app/discovery-debug/page.tsx`

Create a new page that shows ALL tokens from token_discovery with websites:

```typescript
'use client';

import { useState, useEffect } from 'react';

interface TokenDiscovery {
  id: number;
  symbol: string;
  network: string;
  contract_address: string;
  website_url: string;
  website_analyzed_at: string;
  website_stage1_score: number;
  website_stage1_tier: string;
  website_stage1_analysis: {
    category_scores?: any;
    scrape_metrics?: {
      text_length: number;
      link_count: number;
      header_count: number;
      html_length: number;
    };
    extracted_signals?: {
      partnerships_mentioned: string[];
      user_count_claims: string;
      has_whitepaper: boolean;
      has_github: boolean;
    };
    quick_take?: string;
    reasoning?: string;
  };
  current_liquidity_usd: number;
  first_seen_at: string;
}

export default function DiscoveryDebugPage() {
  const [tokens, setTokens] = useState<TokenDiscovery[]>([]);
  const [filter, setFilter] = useState<'all' | 'analyzed' | 'unanalyzed' | 'lowscore' | 'scrape_failed'>('all');
  const [loading, setLoading] = useState(true);

  // Fetch tokens from token_discovery
  useEffect(() => {
    fetchTokens();
  }, [filter]);

  const fetchTokens = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/discovery-debug?filter=${filter}`);
      const data = await response.json();
      setTokens(data.tokens || []);
    } catch (error) {
      console.error('Failed to fetch tokens:', error);
    }
    setLoading(false);
  };

  // Determine scrape health
  const getScrapeHealth = (token: TokenDiscovery) => {
    const textLength = token.website_stage1_analysis?.scrape_metrics?.text_length || 0;
    if (textLength === 0) return { color: 'bg-gray-500', label: 'Not Analyzed' };
    if (textLength < 100) return { color: 'bg-red-500', label: 'Failed' };
    if (textLength < 1000) return { color: 'bg-yellow-500', label: 'Partial' };
    return { color: 'bg-green-500', label: 'Success' };
  };

  return (
    <div className="min-h-screen bg-black text-green-400 p-8">
      <h1 className="text-3xl font-bold mb-6">Token Discovery Debug Interface</h1>
      
      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <button onClick={() => setFilter('all')} className={`px-4 py-2 ${filter === 'all' ? 'bg-green-600' : 'bg-gray-800'}`}>
          All with Websites
        </button>
        <button onClick={() => setFilter('analyzed')} className={`px-4 py-2 ${filter === 'analyzed' ? 'bg-green-600' : 'bg-gray-800'}`}>
          Analyzed
        </button>
        <button onClick={() => setFilter('unanalyzed')} className={`px-4 py-2 ${filter === 'unanalyzed' ? 'bg-green-600' : 'bg-gray-800'}`}>
          Not Analyzed
        </button>
        <button onClick={() => setFilter('lowscore')} className={`px-4 py-2 ${filter === 'lowscore' ? 'bg-green-600' : 'bg-gray-800'}`}>
          Low Score (≤7)
        </button>
        <button onClick={() => setFilter('scrape_failed')} className={`px-4 py-2 ${filter === 'scrape_failed' ? 'bg-green-600' : 'bg-gray-800'}`}>
          Scrape Issues
        </button>
      </div>

      {/* Stats */}
      <div className="mb-6 grid grid-cols-4 gap-4">
        <div className="bg-gray-900 p-4 rounded">
          <div className="text-2xl font-bold">{tokens.length}</div>
          <div className="text-sm">Total Tokens</div>
        </div>
        <div className="bg-gray-900 p-4 rounded">
          <div className="text-2xl font-bold">
            {tokens.filter(t => t.website_stage1_score !== null).length}
          </div>
          <div className="text-sm">Analyzed</div>
        </div>
        <div className="bg-gray-900 p-4 rounded">
          <div className="text-2xl font-bold">
            {tokens.filter(t => t.website_stage1_score && t.website_stage1_score >= 7).length}
          </div>
          <div className="text-sm">Promotable (≥7)</div>
        </div>
        <div className="bg-gray-900 p-4 rounded">
          <div className="text-2xl font-bold text-red-400">
            {tokens.filter(t => {
              const textLen = t.website_stage1_analysis?.scrape_metrics?.text_length || 0;
              return t.website_analyzed_at && textLen < 100;
            }).length}
          </div>
          <div className="text-sm">Scrape Failures</div>
        </div>
      </div>

      {/* Token List */}
      <div className="space-y-4">
        {loading && <div>Loading...</div>}
        
        {tokens.map(token => {
          const health = getScrapeHealth(token);
          const metrics = token.website_stage1_analysis?.scrape_metrics;
          const signals = token.website_stage1_analysis?.extracted_signals;
          
          return (
            <div key={token.id} className="bg-gray-900 p-4 rounded-lg border border-gray-800">
              <div className="grid grid-cols-12 gap-4">
                {/* Token Info */}
                <div className="col-span-2">
                  <div className="font-bold text-lg">{token.symbol}</div>
                  <div className="text-xs text-gray-400">{token.network}</div>
                  <a href={token.website_url} target="_blank" className="text-xs text-blue-400 hover:underline">
                    Website ↗
                  </a>
                </div>

                {/* Score */}
                <div className="col-span-2">
                  <div className="text-2xl font-bold">
                    {token.website_stage1_score !== null ? `${token.website_stage1_score}/21` : 'N/A'}
                  </div>
                  <div className={`text-sm ${
                    token.website_stage1_tier === 'ALPHA' ? 'text-purple-400' :
                    token.website_stage1_tier === 'SOLID' ? 'text-green-400' :
                    token.website_stage1_tier === 'BASIC' ? 'text-yellow-400' :
                    'text-red-400'
                  }`}>
                    {token.website_stage1_tier || 'Not Analyzed'}
                  </div>
                </div>

                {/* Scrape Health */}
                <div className="col-span-2">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${health.color}`}></div>
                    <span className="text-sm">{health.label}</span>
                  </div>
                  {metrics && (
                    <div className="text-xs text-gray-400 mt-1">
                      {metrics.text_length} chars
                      {metrics.text_length < 500 && ' ⚠️'}
                    </div>
                  )}
                </div>

                {/* Extracted Signals */}
                <div className="col-span-3">
                  {signals && (
                    <div className="text-xs">
                      {signals.partnerships_mentioned?.length > 0 && (
                        <div className="text-green-400">🤝 {signals.partnerships_mentioned.join(', ')}</div>
                      )}
                      {signals.user_count_claims && (
                        <div className="text-blue-400">👥 {signals.user_count_claims}</div>
                      )}
                      {signals.has_whitepaper && <span className="text-gray-400">📄 WP </span>}
                      {signals.has_github && <span className="text-gray-400">🔧 GitHub </span>}
                    </div>
                  )}
                </div>

                {/* Quick Take */}
                <div className="col-span-3">
                  <div className="text-xs text-gray-300">
                    {token.website_stage1_analysis?.quick_take || 'No analysis'}
                  </div>
                </div>
              </div>

              {/* Expandable Debug Info */}
              {metrics && metrics.text_length < 500 && (
                <div className="mt-2 p-2 bg-red-900/20 rounded text-xs">
                  ⚠️ Scraping Issue Detected:
                  <ul className="ml-4">
                    <li>Text: {metrics.text_length} chars (expected 1000+)</li>
                    <li>Links: {metrics.link_count}</li>
                    <li>Headers: {metrics.header_count}</li>
                  </ul>
                  Likely causes: JavaScript-heavy site, loading screen, or blocking
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

### File: `/krom-analysis-app/app/api/discovery-debug/route.ts`

Create API endpoint to fetch token_discovery data:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const filter = searchParams.get('filter') || 'all';

  try {
    let query = supabase
      .from('token_discovery')
      .select('*')
      .not('website_url', 'is', null)
      .order('website_analyzed_at', { ascending: false, nullsFirst: true })
      .limit(100);

    // Apply filters
    if (filter === 'analyzed') {
      query = query.not('website_analyzed_at', 'is', null);
    } else if (filter === 'unanalyzed') {
      query = query.is('website_analyzed_at', null);
    } else if (filter === 'lowscore') {
      query = query.lte('website_stage1_score', 7);
    } else if (filter === 'scrape_failed') {
      // This will work once we have scrape_metrics data
      query = query.not('website_stage1_analysis->scrape_metrics', 'is', null)
        .lt('website_stage1_analysis->scrape_metrics->text_length', 500);
    }

    const { data, error } = await query;

    if (error) throw error;

    return NextResponse.json({ tokens: data });
  } catch (error) {
    console.error('Error fetching discovery tokens:', error);
    return NextResponse.json({ error: 'Failed to fetch tokens' }, { status: 500 });
  }
}
```

## Task 3: Test & Debug

1. **Deploy the updated analyzer**
2. **Clear analysis for test tokens** (CLX, APD) to force re-analysis:
```sql
UPDATE token_discovery 
SET website_analyzed_at = NULL, website_stage1_score = NULL 
WHERE symbol IN ('CLX', 'APD');
```

3. **Run analyzer** and check if diagnostic data is stored
4. **Load debug interface** at `/discovery-debug`
5. **Look for patterns**:
   - Do all tokens from certain networks fail scraping?
   - Are partnerships being detected correctly?
   - What's the typical text_length for successful scrapes?

## Expected Outcomes

1. **APD will show as scrape failure** (21 chars) - making the problem obvious
2. **CLX will show NBA partnership extracted** but not triggering fast-track
3. **Pattern identification** - maybe all heavily JavaScript sites fail
4. **Clear promotion pipeline** - see exactly why tokens aren't making it to crypto_calls

## Critical Context

- **NO COSMETIC FIXES** - Don't manually adjust scores to hide problems
- **Current scoring issues**:
  - Fast-track not triggering for obvious signals (NBA partnership, 100k+ users)
  - Scraper getting minimal content from JavaScript-heavy sites
  - AI not recognizing partnerships shown in logos/images
- **The goal** is visibility into the pipeline, not fixing individual tokens

## Success Criteria

1. Can immediately identify scraping failures by text_length
2. Can see what partnerships/signals were extracted vs what AI recognized
3. Can understand why good projects score low
4. Have data to improve the scoring algorithm

This debug interface will be invaluable for tuning the discovery pipeline!