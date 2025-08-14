# Next Session Prompt - Website Investment Analysis

## Context
You're continuing work on the website investment analysis system in `/temp-website-analysis/`. The system analyzes crypto project websites using the same scoring philosophy as the KROM call analyzer.

## Current State

### ✅ What's Complete
1. **Investment Scoring System** (`website_investment_analyzer.py`)
   - Analyzes websites for investment legitimacy (1-10 score)
   - Uses KROM call analyzer philosophy: 8-10 EXCEPTIONAL, 6-7 STRONG, 4-5 MODERATE, 1-3 LOW
   - Configured to use Kimi K2 model (100x cheaper than GPT-4o-mini)
   - Provides detailed analysis with green flags, red flags, and reasoning

2. **UI Dashboard** (`investment_ui.html` + `investment_server.py`)
   - Running at http://localhost:5002
   - Shows top 20 tokens with investment scores
   - Click on score badge to see detailed analysis
   - Color-coded scores: Purple (EXCEPTIONAL), Green (STRONG), Orange (MODERATE), Red (LOW)

3. **Database Integration** (`analyze_top20_supabase.py`)
   - Fetches top tokens from Supabase
   - Stores in local SQLite database (`analysis_results.db`)
   - Analyzes websites and updates scores

### 🚧 Current Status
- Server is running at http://localhost:5002
- 8 out of 14 tokens analyzed successfully
- Using Kimi K2 model for all analysis

## Key Files to Work With

```
/temp-website-analysis/
├── website_investment_analyzer.py  # Core analyzer with KROM philosophy
├── investment_ui.html              # Dashboard UI
├── investment_server.py            # Flask server & API
├── analyze_top20_supabase.py      # Fetches from Supabase & analyzes
└── analysis_results.db            # Local database with results
```

## API Endpoints
- `GET /` - Dashboard UI
- `GET /api/tokens` - Get all tokens with scores
- `GET /api/analyze/<ticker>` - Analyze single token
- `GET /api/analyze-all` - Analyze top 20 tokens

## To Continue Working

### Start the Server
```bash
cd /Users/marcschwyn/Desktop/projects/KROMV12/temp-website-analysis
python3 investment_server.py
# Visit http://localhost:5002
```

### Re-run Analysis
```bash
# To analyze more tokens or refresh scores
curl -X GET http://localhost:5002/api/analyze-all
```

## Key Concepts Used

### Investment Scoring Philosophy (from KROM)
- **Focus on LEGITIMACY** - Verifiable teams, real products, transparent operations
- **"When in doubt" rule** - Err on side of higher score (5-7) for unusual but potentially significant projects
- **Discourse quality** - How information is presented reflects legitimacy
- **Verification over claims** - Prioritize verifiable information

### Scoring Signals
**8-10 EXCEPTIONAL**: Verifiable high-profile backing, working product, multiple audits, innovation
**6-7 STRONG**: Professional operation, transparent team, clear roadmap, some verification
**4-5 MODERATE**: Some credible elements, basic documentation, partial transparency
**1-3 LOW**: Template website, minimal information, no team details

## Next Steps Suggestions

1. **Analyze remaining tokens** - Some tokens didn't have valid URLs
2. **Add to production** - Deploy as Supabase Edge Function for automated analysis
3. **Integrate with main system** - Add website scores to main KROM dashboard
4. **Batch processing** - Analyze all tokens in database, not just top 20
5. **Improve CA verification** - Combine with CA verification work from earlier

## Important Notes
- Using Kimi K2 model (moonshotai/kimi-k2) - 100x cheaper than GPT-4o
- Investment scores complement existing call/X analysis scores
- System designed to identify legitimate projects worth Telegram notifications
- All work stays in `/temp-website-analysis/` directory

## Quick Test
To verify everything is working:
```bash
curl http://localhost:5002/api/tokens | python3 -m json.tool | head -30
```

This should show tokens with investment scores and analysis data.