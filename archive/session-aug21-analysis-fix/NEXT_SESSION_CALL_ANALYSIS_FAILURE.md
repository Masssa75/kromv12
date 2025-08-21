# HANDOFF PROMPT - Call Analysis Failures for Recent KROM Calls

## Critical Issue to Fix

**Problem**: Call analysis is failing for all recent KROM calls, showing "Analysis failed" with score of 1.

**Symptoms**:
- `analysis_score`: 1
- `analysis_reasoning`: "Analysis failed"
- `analysis_tier`: "TRASH" 
- `analysis_duration_ms`: 0
- All recent KROM calls affected (not gecko_trending tokens)

## Investigation Steps

### 1. Check Recent Failed Analyses
```bash
# Get recent KROM calls with failed analysis
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?source=eq.krom&analysis_reasoning=eq.Analysis%20failed&select=ticker,created_at,analysis_score,analysis_reasoning,analysis_model,analyzed_at&order=created_at.desc&limit=10" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'

# Count total failed analyses
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?select=count&analysis_reasoning=eq.Analysis%20failed" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'
```

### 2. Check When Failures Started
```bash
# Find the earliest failed analysis
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?analysis_reasoning=eq.Analysis%20failed&select=ticker,analyzed_at,created_at&order=analyzed_at.asc&limit=5" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'
```

### 3. Test the Analysis Endpoint Directly
```bash
# Try to analyze a specific failed call
curl -X POST "https://lively-torrone-8199e0.netlify.app/api/analyze" \
  -H "Content-Type: application/json" \
  -H "x-cron-secret: $CRON_SECRET" \
  -d '{
    "limit": 1,
    "model": "moonshotai/kimi-k2"
  }'
```

### 4. Check API Keys and Environment
```bash
# Verify OpenRouter API key is set in Netlify
netlify api listAccountsForUser | jq '.[0].id' | xargs -I {} netlify api getSiteEnvironmentVariables --data '{"account_id": "{}", "site_id": "8ff019b3-29ef-4223-b6ad-2cc46e91807e"}' | jq '.[] | select(.key=="OPEN_ROUTER_API_KEY")'
```

## Likely Root Causes

### 1. OpenRouter API Key Issue
- **Previous incident**: On August 5, 2025, OpenRouter API key stopped working, preventing analysis
- **Check**: Is the API key still valid?
- **Test**: Try calling OpenRouter directly with the key

### 2. Kimi K2 Model Issue
The system uses `moonshotai/kimi-k2` as the default model.
- Model might be unavailable or rate limited
- OpenRouter might have changed the model name
- Check if switching to backup model (GPT-4) works

### 3. Request Format Changed
The raw_data structure from KROM API might have changed:
```javascript
// Expected structure
{
  text: "call message",
  group: { name: "group name" },
  token: { symbol: "TICKER", network: "ethereum" }
}
```

### 4. Timeout or Rate Limiting
- Netlify functions have 10-second timeout
- OpenRouter might be rate limiting
- Check for 429 errors or timeouts

## Files to Check

### 1. Analysis API Route
**File**: `/krom-analysis-app/app/api/analyze/route.ts`
- Check error handling around line where it sets "Analysis failed"
- Look for try-catch blocks that might be swallowing errors
- Add console.error() to see actual error messages

### 2. Cron Endpoint
**File**: `/krom-analysis-app/app/api/cron/analyze/route.ts`
- This runs every minute via Supabase cron
- Check if it's properly passing the API key

### 3. Environment Variables
Check Netlify dashboard for:
- `OPEN_ROUTER_API_KEY` - Must be set and valid
- `CRON_SECRET` - Required for cron endpoints

## Quick Diagnostic Tests

### Test 1: Check OpenRouter API Status
```bash
# Test OpenRouter API directly
curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPEN_ROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moonshotai/kimi-k2",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'
```

### Test 2: Check Recent Successful Analyses
```bash
# Find last successful analysis
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?analysis_score=neq.1&analysis_reasoning=neq.Analysis%20failed&select=ticker,analyzed_at,analysis_model&order=analyzed_at.desc&limit=5" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'
```

### Test 3: Manual Analysis Trigger
```bash
# Get an unanalyzed call and try to analyze it manually
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?analyzed_at=is.null&source=eq.krom&select=id,ticker,raw_data&limit=1" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY"
```

## Temporary Workarounds

### Option 1: Switch to Backup Model
Change the default model from `kimi-k2` to `gpt-4o-mini`:
```typescript
const model = searchParams.get('model') || 'openai/gpt-4o-mini'
```

### Option 2: Increase Timeout
Add retry logic with exponential backoff for OpenRouter calls

### Option 3: Use Different API Provider
If OpenRouter is down, switch to direct OpenAI or Anthropic API

## Historical Context

### Previous Failures
- **August 5, 2025**: OpenRouter API key issue caused analysis failures for 5 days
- **July 31, 2025**: Similar "Analysis failed" issue when rate limited
- System uses Kimi K2 ($0.003/analysis) as primary model

### Current Setup
- Analysis runs via Supabase cron every minute
- Processes 5 calls per batch
- Uses OpenRouter for model access
- Fallback to GPT-4 if Kimi fails

## Priority
**CRITICAL** - Call analysis is a core feature. Without it, new tokens aren't being scored, making the entire system less valuable.

## Success Criteria
- New KROM calls get analyzed within minutes of arrival
- Analysis scores between 2-10 (not defaulting to 1)
- No "Analysis failed" messages
- analysis_duration_ms > 0 (showing actual processing time)

---
**Note**: Check logs/SESSION-LOG-2025-08.md for previous OpenRouter issues and fixes. The system has recovered from similar failures before.