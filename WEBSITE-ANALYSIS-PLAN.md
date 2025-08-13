# Website Analysis Integration Plan

## Overview
Add website analysis as a third quality signal alongside Call Analysis and X Analysis, providing comprehensive project evaluation when crypto calls come in.

## Test Results Summary

### ✅ Successful Tests
1. **Uniswap (UNI)**: Score 9/10 - Correctly identified as major DeFi protocol
2. **KROM**: Score 3/10 - Identified minimal website with no documentation
3. **CLIPPY**: Score 1/10 - Detected redirect-only site (red flag)

### Key Findings
- Kimi K2 effectively analyzes website content for legitimacy
- Can extract social links, documentation presence, team info
- Provides structured scoring (1-10) matching existing system
- Fast response time (~2-3 seconds per analysis)

## Implementation Approach

### Option 1: Edge Function Integration (Recommended)
Create `crypto-website-analyzer` Edge Function that:
1. Runs after `crypto-analyzer` in the orchestrator pipeline
2. Extracts website URL from call message or tries common domains
3. Fetches content via ScraperAPI (already configured)
4. Analyzes with Kimi K2 via OpenRouter
5. Stores results in new database columns

**Pros:**
- Runs automatically for every new call
- Parallel with X analysis for efficiency
- Uses existing infrastructure (ScraperAPI)
- No additional cron jobs needed

**Cons:**
- Adds 3-5 seconds to pipeline
- Not all tokens have websites

### Option 2: Batch Processing via API
Add endpoint to `krom-analysis-app`:
- `/api/website-analyze` - Batch process unanalyzed websites
- Cron job runs every 5 minutes
- Processes 5-10 tokens per run

**Pros:**
- Doesn't slow down main pipeline
- Can retry failed fetches
- Easier to monitor/debug

**Cons:**
- Delayed analysis (not real-time)
- Requires another cron job

## Database Schema Updates

```sql
-- Add website analysis columns to crypto_calls table
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_url TEXT;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_score INTEGER CHECK (website_score >= 1 AND website_score <= 10);
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_tier TEXT CHECK (website_tier IN ('ALPHA', 'SOLID', 'BASIC', 'TRASH'));
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_analysis JSONB;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_analyzed_at TIMESTAMPTZ;

-- The JSONB will store:
{
  "project_category": "meme/utility/defi/gaming",
  "has_utility": true/false,
  "utility_description": "...",
  "team_transparency": "visible/partial/anonymous",
  "documentation_level": "comprehensive/basic/minimal/none",
  "social_presence": {
    "twitter": "@handle",
    "telegram": "t.me/group",
    "discord": true/false
  },
  "technical_indicators": {
    "has_whitepaper": true/false,
    "has_roadmap": true/false,
    "has_tokenomics": true/false,
    "has_audit": true/false
  },
  "red_flags": ["array", "of", "concerns"],
  "green_flags": ["array", "of", "positives"],
  "key_findings": "summary text"
}
```

## Edge Function Code Structure

```typescript
// supabase/functions/crypto-website-analyzer/index.ts

async function analyzeWebsite(call: CryptoCall) {
  // 1. Extract or discover website URL
  const websiteUrl = extractWebsiteUrl(call.raw_data?.message) 
    || await tryCommonDomains(call.ticker)
  
  if (!websiteUrl) return null
  
  // 2. Fetch website content via ScraperAPI
  const content = await fetchViaScraperAPI(websiteUrl)
  
  // 3. Analyze with Kimi K2
  const analysis = await analyzeWithKimi({
    ticker: call.ticker,
    contract: call.contract_address,
    content: content,
    url: websiteUrl
  })
  
  // 4. Store results
  await supabase.from('crypto_calls').update({
    website_url: websiteUrl,
    website_score: analysis.website_score,
    website_tier: analysis.website_tier,
    website_analysis: analysis,
    website_analyzed_at: new Date()
  }).eq('id', call.id)
  
  return analysis
}
```

## Integration Points

### 1. Orchestrator Update
```typescript
// crypto-orchestrator/index.ts
// Run website analysis in parallel with X analysis
const [callAnalysis, xAnalysis, websiteAnalysis] = await Promise.all([
  fetch('crypto-analyzer', { body: calls }),
  fetch('crypto-x-analyzer-nitter', { body: calls }),
  fetch('crypto-website-analyzer', { body: calls }) // NEW
])
```

### 2. Notification Enhancement
Include website score in Telegram notifications:
```
📊 Analysis Ratings:
• Call Quality: SOLID
• X Research: BASIC
• Website: TRASH (Score: 2/10) ⚠️

🌐 Website Issues:
• No documentation
• Anonymous team
• Minimal content
```

### 3. UI Display
Add Website column to analyzed calls table showing:
- Score badge (color-coded)
- Tier label
- Click for detailed analysis modal

## Testing Strategy

### Phase 1: Standalone Testing
1. ✅ Create test scripts (COMPLETED)
2. ✅ Test with various project types
3. ✅ Verify Kimi K2 accuracy

### Phase 2: Edge Function Testing
1. Deploy `crypto-website-analyzer` function
2. Test with recent calls manually
3. Verify ScraperAPI integration
4. Check database updates

### Phase 3: Full Integration
1. Update orchestrator
2. Monitor full pipeline performance
3. Adjust timeouts if needed
4. Deploy to production

## Cost Analysis

### API Costs
- **Kimi K2**: ~$0.001 per analysis (very cheap)
- **ScraperAPI**: Within existing 1000/month limit
- **Total**: ~$1.50/month for 1500 analyses

### Performance Impact
- **Added latency**: 3-5 seconds per call
- **Can run parallel**: No impact if done alongside X analysis
- **Database storage**: Minimal (JSONB field)

## Success Metrics
- 60%+ of tokens have discoverable websites
- 80%+ accuracy in legitimacy assessment
- <5 second analysis time
- Zero impact on main pipeline performance

## Next Steps

1. **Immediate**: 
   - Create database columns
   - Deploy Edge Function
   - Test with 10 recent calls

2. **This Week**:
   - Integrate into orchestrator
   - Update notification format
   - Monitor performance

3. **Future**:
   - Add website monitoring for changes
   - Track correlation between website quality and token performance
   - Build website quality dashboard

## Conclusion
Website analysis using Kimi K2 is highly feasible and adds significant value to the crypto monitoring system. The test results show accurate scoring and useful insights that complement existing call and X analysis.

**Recommendation**: Implement as Edge Function (Option 1) for real-time analysis integrated into the existing pipeline.