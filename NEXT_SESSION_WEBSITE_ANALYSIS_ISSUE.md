# HANDOFF PROMPT - Website Analysis False Negatives

## Critical Issue to Fix

**Problem**: Website analysis is incorrectly marking legitimate tokens as TRASH tier, claiming "No Documentation links" when documentation clearly exists on their websites.

**Affected Tokens**:
- **MYX** (UTILITY token on BSC) - Marked as TRASH with score 6/21
- **LOOP** (likely has documentation) - Marked as TRASH

**Specific Issue**: The CONS tooltip shows:
- ❌ No GitHub repositories
- ❌ No Documentation links  
- ❌ No Team information
- ❌ No Social media presence

But these tokens likely have these elements on their websites.

## Investigation Steps

### 1. Check the Actual Websites
```bash
# Get the website URLs for these tokens
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?ticker=in.(MYX,LOOP)&select=ticker,website_url,website_score,website_tier,website_analysis_full" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'
```

### 2. Manually Visit the Websites
- Visit MYX website and check for:
  - Documentation/Docs section
  - GitHub links
  - Team/About page
  - Social media links (Twitter, Telegram, Discord)
- Do the same for LOOP

### 3. Check the Website Parser Output
```bash
# See what the parser actually captured
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?ticker=eq.MYX&select=website_parsed_content,website_analysis_full" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'
```

### 4. Test the Edge Function Directly
```bash
# Re-analyze MYX website
curl -X POST "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-website-analyzer" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "[MYX_WEBSITE_URL]",
    "ticker": "MYX"
  }'
```

## Likely Root Causes

### 1. Parser Not Following Navigation Links
The website parser might only be analyzing the landing page and not following navigation links to documentation sections.

**Files to check**:
- `/supabase/functions/crypto-website-analyzer/index.ts` - Main analyzer
- Look for how it handles navigation link discovery

### 2. Documentation Detection Logic
The scoring logic might be too strict about what qualifies as "documentation".

**Check the scoring criteria**:
- What patterns does it look for? ("docs", "documentation", "whitepaper"?)
- Does it follow relative links like `/docs` or `https://docs.subdomain.com`?

### 3. JavaScript-Rendered Content
If the websites are SPAs (Single Page Applications), the parser might not be executing JavaScript to see the full content.

**Test with**:
- Check if parser uses Playwright or just fetches HTML
- See if content is visible in "view source" vs rendered page

## Files to Review

1. **Edge Function**: `/supabase/functions/crypto-website-analyzer/index.ts`
   - Check the `analyzeWebsite` function
   - Look at navigation link extraction logic
   - Review documentation detection patterns

2. **Database Records**:
   - Check `website_parsed_content` - What did it actually capture?
   - Check `website_category_scores` - How did it score each category?
   - Check `website_analysis_full` - Full analysis details

3. **Recent Changes**:
   - The website analyzer was recently updated (August 19-20)
   - Check if scoring criteria changed
   - Look for any regression in link following

## Quick Fix Options

### Option 1: Improve Link Following
```typescript
// In the analyzer, ensure it follows navigation links
const navLinks = parsedContent.navigation.all_links.filter(link => 
  link.includes('/docs') || 
  link.includes('/documentation') ||
  link.includes('gitbook') ||
  link.includes('github.com')
);
```

### Option 2: Re-analyze with Deeper Crawling
Add a parameter to follow links more deeply:
```typescript
{
  "url": "website_url",
  "ticker": "MYX",
  "followDepth": 2  // Follow links 2 levels deep
}
```

### Option 3: Manual Override
If the parser can't be fixed quickly, add a manual review process for utility tokens.

## Testing After Fix

1. Re-analyze MYX and LOOP
2. Check if documentation is now detected
3. Verify scores improve from TRASH to appropriate tier
4. Test on other recently added tokens

## Context from Previous Session

- Website analysis was integrated on August 19-20, 2025
- Uses Kimi K2 model for analysis ($0.003 per analysis)
- Scoring: 7 categories, each 0-3 points, total 0-21
- Tiers: TRASH (0-7), BASIC (8-11), SOLID (12-15), ALPHA (16-21)
- Currently ~3,700 tokens being analyzed

## Priority
**HIGH** - This affects the credibility of the analysis system. If legitimate utility tokens with documentation are marked as TRASH, users will lose trust in the ratings.

---
**Note**: The website analysis system is critical for identifying quality projects. False negatives (marking good projects as TRASH) are worse than false positives.