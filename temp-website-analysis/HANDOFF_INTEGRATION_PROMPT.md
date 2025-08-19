# 🚀 CRITICAL HANDOFF: Website Analysis Integration into Crypto Monitoring System

## Current Situation Overview
We have built a powerful website analysis system (Stage 1 complete with 401+ projects analyzed) that needs to be integrated into the existing crypto monitoring orchestration pipeline. This is a CRITICAL and DELICATE operation that will replace existing analysis functions and add new website analysis capabilities.

## System Architecture Context

### Current Crypto Monitoring Pipeline (As of Aug 16, 2025)
1. **crypto-orchestrator** (Runs every minute via Supabase cron)
   - Calls crypto-poller → Gets new KROM calls
   - Calls crypto-analyzer → Basic call analysis (TO BE REPLACED)
   - Calls crypto-x-analyzer-nitter → X/Twitter analysis (TO BE REPLACED)
   - Calls crypto-notifier → Sends Telegram notifications

2. **Separate Cron Jobs** (Running on Netlify - TO BE DISCONTINUED)
   - `krom-call-analysis-every-minute` → Better call analysis
   - `krom-x-analysis-every-minute` → Better X analysis
   - These run separately and update the database

3. **crypto-ultra-tracker** (Monitors for new data)
   - Checks for new websites/social links
   - Currently does NOT analyze websites when found

### New Website Analysis System Built
- Location: `/temp-website-analysis/`
- Core file: `comprehensive_website_analyzer.py`
- Database: `website_analysis_new.db` (401+ analyzed projects)
- Scoring: 21-point system across 7 categories
- Success rate: ~30% score ≥10/21 (worthy of notification)
- Cost: $0.003 per analysis (Kimi K2 model)

## 🎯 Integration Requirements

### Phase 1: Replace Existing Analyzers
1. **Replace crypto-analyzer** with the better Netlify version
2. **Replace crypto-x-analyzer** with the better Netlify version
3. **Disable the separate Netlify cron jobs** (no longer needed)

### Phase 2: Add Website Analysis to Orchestrator
1. **In crypto-orchestrator**, after call and X analysis:
   - Check if `website_url` exists
   - If yes, call new `crypto-website-analyzer` edge function
   - Store results in new columns (see schema below)
   - If score ≥10/21, include in notification

### Phase 3: Handle Ultra-Tracker Website Discovery
1. **In crypto-ultra-tracker**, when new website found:
   - Call `crypto-website-analyzer` 
   - Store results
   - Send notification if score ≥10/21

## 📊 Database Schema Updates Needed

Add these columns to `crypto_calls` table in Supabase:
```sql
-- Website analysis columns
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_analyzed BOOLEAN DEFAULT FALSE;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_score INTEGER; -- 0-21
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_tier TEXT; -- HIGH/MEDIUM/LOW
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_category_scores JSONB; -- 7 categories
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_stage2_qualified BOOLEAN DEFAULT FALSE;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_auto_qualifiers JSONB; -- Array of qualifiers
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_analysis_reasoning TEXT;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_analyzed_at TIMESTAMPTZ;
```

## 🔧 Edge Function to Create: crypto-website-analyzer

```typescript
// Basic structure - needs full implementation
import { comprehensive_website_analyzer } from './comprehensive_website_analyzer.py'

export async function analyzeWebsite(url: string, ticker: string) {
  // 1. Parse website with Playwright (handles loading screens)
  // 2. Extract all content, links, documents
  // 3. Analyze with Kimi K2 AI model
  // 4. Return scored results
  
  return {
    score: 0-21,
    tier: 'HIGH/MEDIUM/LOW',
    categoryScores: {...},
    stage2Qualified: boolean,
    autoQualifiers: [...],
    reasoning: '...'
  }
}
```

## ⚠️ CRITICAL CONSIDERATIONS

### Order of Operations (VERY IMPORTANT)
1. **TEST EVERYTHING LOCALLY FIRST**
2. **Deploy new functions BEFORE modifying orchestrator**
3. **Keep old functions as backups** (rename, don't delete)
4. **Implement killswitch** - environment variable to disable website analysis
5. **Monitor closely** after deployment

### Risk Mitigation
- **Timeout protection**: Website analysis can take 15-30 seconds
- **Error handling**: Don't let website analysis failure break the pipeline
- **Rate limiting**: Max 1 website analysis per second
- **Cost control**: Track API usage ($0.003 per analysis)

### Testing Checklist
- [ ] Test website analyzer edge function standalone
- [ ] Test modified orchestrator with website analysis
- [ ] Test ultra-tracker website discovery flow
- [ ] Test notification formatting with website scores
- [ ] Test database updates are correct
- [ ] Test error scenarios (timeout, API failure, etc.)

## 📝 Implementation Steps (DISCUSS FIRST)

### Step 1: Create Edge Function (LOW RISK)
- Port `comprehensive_website_analyzer.py` to TypeScript
- Deploy as `crypto-website-analyzer`
- Test independently

### Step 2: Update Database Schema (LOW RISK)
- Add new columns to Supabase
- Won't affect existing functions

### Step 3: Replace Analyzers (MEDIUM RISK)
- Copy better analyzers from Netlify to Edge Functions
- Test thoroughly
- Deploy but don't activate yet

### Step 4: Modify Orchestrator (HIGH RISK)
- Add website analysis step
- Add feature flag to enable/disable
- Test in development first

### Step 5: Update Ultra-Tracker (MEDIUM RISK)
- Add website analysis for new discoveries
- Test with known websites first

## 🔍 Key Files to Reference

### Website Analysis System
- `/temp-website-analysis/comprehensive_website_analyzer.py` - Core analyzer
- `/temp-website-analysis/CLAUDE.md` - Full documentation
- `/temp-website-analysis/website_analysis_new.db` - Results database

### Existing Edge Functions
- `/supabase/functions/crypto-orchestrator-fast/` - Main orchestrator
- `/supabase/functions/crypto-analyzer/` - To be replaced
- `/supabase/functions/crypto-x-analyzer-nitter/` - To be replaced
- `/supabase/functions/crypto-ultra-tracker/` - Needs website analysis

### Netlify Functions (Better versions)
- `/krom-analysis-app/app/api/analyze/route.ts` - Better call analyzer
- `/krom-analysis-app/app/api/x-analyze/route.ts` - Better X analyzer

## 🚨 DO NOT START IMPLEMENTATION YET

**FIRST**: Confirm you understand the plan
**SECOND**: Discuss which part to implement first
**THIRD**: Agree on risk mitigation strategies
**FOURTH**: Only then begin careful implementation

## Questions to Answer Before Starting

1. Should we test with a subset of tokens first?
2. What score threshold triggers notifications? (10/21?)
3. How to handle websites that timeout?
4. Should we analyze retroactively or only new calls?
5. What's our rollback plan if something breaks?

## Success Metrics

- Website analysis adds <30 seconds to pipeline
- No increase in failed orchestrations
- Notification quality improves (fewer false positives)
- ~30% of websites score ≥10/21

---
**CRITICAL**: This integration touches the CORE monitoring system. One mistake could break all crypto call notifications. Proceed with EXTREME CAUTION and TEST EVERYTHING.

**Next Instance**: Read this entire document, confirm understanding, then propose implementation order based on risk assessment.