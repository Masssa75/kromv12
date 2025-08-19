# Website Analysis System Documentation

## Overview
This folder contains a comprehensive website analysis system for evaluating cryptocurrency projects. The system performs two-stage analysis to identify legitimate, high-potential projects from thousands of tokens.

**Created**: August 15, 2025  
**Purpose**: Analyze crypto project websites to identify investment-worthy tokens  
**Current Status**: Stage 1 complete (400+ projects analyzed), Stage 2 in planning  

## System Architecture

### Stage 1: Quick Triage Analysis
- **Goal**: Rapidly assess projects to identify those worth deeper investigation
- **Scoring**: 21-point system (7 categories × 3 points each)
- **Processing**: ~15 seconds per website using Kimi K2 model ($0.003/analysis)
- **Success Rate**: ~30% of projects score ≥10/21 (Stage 2 threshold)

### Stage 2: Deep Investment Analysis (Planned)
- **Goal**: Comprehensive evaluation of high-scoring projects
- **Components**: GitHub analysis, documentation parsing, team research
- **Scoring**: 100-point investment potential system
- **Model**: Claude 3.5 Sonnet for advanced reasoning

## Key Files

### Core Analysis System
- `comprehensive_website_analyzer.py` - Main analyzer with smart loading detection
- `website_analysis_new.db` - SQLite database with all results (100MB+)
- `fixed_results_server.py` - Web UI for viewing results (runs on port 5006)

### Batch Processing
- `run_full_batch.py` - Batch analyzer for processing multiple tokens
- `batch_analyze_supabase_utility.py` - Fetches utility tokens from Supabase

### Testing & Debugging
- `test_loading_screens.py` - Tests websites with loading screens (PHI, VIRUS)
- `update_phi_virus.py` - Manual updater for specific tokens
- `test_batch_small.py` - Tests with 10 tokens for debugging

### Logs
- `full_batch_final.log` - Latest batch processing log
- `full_batch_fixed.log` - Log after API key fix
- `full_batch_working.log` - Current batch operations

## Database Schema

**Table: `website_analysis`** (401+ records as of Aug 16, 2025)

### Key Columns:
- `ticker` - Token symbol
- `url` - Website URL
- `parsed_content` - Full JSON of extracted content & navigation
- `total_score` - Overall score (0-21)
- `proceed_to_stage_2` - Boolean recommendation
- `automatic_stage_2_qualifiers` - JSON array of qualifying features
- `category_scores` - JSON with 7 category breakdowns
- `exceptional_signals` - Positive indicators found
- `missing_elements` - Critical missing components

### Score Categories (each 0-3):
1. **technical_infrastructure** - Code repos, APIs, technical depth
2. **business_utility** - Real use case, market fit
3. **documentation_quality** - Whitepapers, docs, guides
4. **community_social** - Social presence, engagement
5. **security_trust** - Security measures, audits
6. **team_transparency** - Team info, backgrounds
7. **website_presentation** - Professional design, functionality

## Critical Features & Fixes

### Smart Loading Screen Detection ✅
**Problem**: Sites like PHI showed loading screens (16 chars: "65% SCROLL DOWN")  
**Solution**: Implemented retry mechanism in lines 54-80 of analyzer
- Detects content <100 chars
- Waits additional 3 seconds
- Retries up to 3 times
- Successfully extracts real content (PHI: 16→3,709 chars)

### API Configuration
**OpenRouter API Key**: Hardcoded in analyzer line 23
- Model: `moonshotai/kimi-k2` (not `kimi/kimi-k2`)
- Cost: $0.003 per analysis
- Rate limit: 2 second delay between calls

### Navigation Link Extraction
All links are extracted and categorized:
- High priority: Documentation, GitHub, Whitepapers
- Medium priority: PDFs, technical resources  
- Low priority: Social media, external links
- Stored in `parsed_content['navigation']['all_links']`

## Key Findings

### Stage 1 Results Summary
- **Total Analyzed**: 401 projects
- **High Scorers (≥10/21)**: 116 projects (29%)
- **Stage 2 Recommended**: 153 projects (38%)
- **Top Score**: 19/21 (OBS - GitHub agent project)

### Top Performing Projects
1. **OBS (19/21)** - GitHub-based OBS agent with comprehensive docs
2. **Base (16/21)** - Coinbase's Base.app with mobile apps
3. **PILSO (15/21)** - Has docs, GitHub, NPM package
4. **PARALLEL (15/21)** - AI project with documentation portal
5. **PLAI (15/21)** - PlayMind AI with GitHub and whitepaper

### Common Patterns
- **Successful projects have**: GitHub repos, documentation portals, clear use cases
- **Failed analyses**: Meme coins, pump.fun tokens, dead websites
- **Loading screen issues**: Fixed with retry mechanism

## Running the System

### Start Web UI
```bash
cd temp-website-analysis
python3 fixed_results_server.py
# Visit http://localhost:5006
```

### Run Batch Analysis
```bash
python3 run_full_batch.py
# Processes utility tokens from Supabase
# ~15 seconds per token
```

### Test Single Website
```python
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

analyzer = ComprehensiveWebsiteAnalyzer('website_analysis_new.db')
parsed = analyzer.parse_website_with_playwright('https://example.com')
ai_analyses = analyzer.analyze_with_models(parsed, models_to_test=[
    ("moonshotai/kimi-k2", "Kimi K2")
])
```

## Stage 2 Planning (Next Steps)

### Planned Components
1. **GitHub Analyzer**
   - Clone repositories
   - Analyze code quality
   - Check commit history
   - Count contributors

2. **Documentation Parser**
   - Extract whitepaper content
   - Verify technical claims
   - Cross-reference implementation

3. **Team Researcher**
   - LinkedIn verification
   - Background checks
   - Experience validation

4. **Community Analyzer**
   - Real engagement metrics
   - Discord/Telegram activity
   - News mentions

### Scoring System (100 points)
- Technical Implementation: 25 points
- Team & Expertise: 20 points
- Community & Adoption: 20 points
- Market Opportunity: 15 points
- Documentation Quality: 10 points
- Risk Assessment: 10 points

## Known Issues & Solutions

### Issue: Low scores for loading screen sites
**Solution**: Retry mechanism implemented, but only helps sites analyzed after fix

### Issue: 95% of "utility" tokens are actually memes
**Solution**: Stage 1 successfully filters these out (only 29% pass)

### Issue: API failures
**Solution**: Ensure model name is `moonshotai/kimi-k2` with correct API key

## Future Improvements

1. **Parallel Processing** - Speed up batch analysis
2. **Better Token Classification** - Pre-filter obvious memes
3. **Social Media Analysis** - Deeper Twitter/Discord analysis
4. **Price Correlation** - Compare scores with price performance
5. **Automated Monitoring** - Re-analyze projects periodically

## Important Notes

- Database has 401+ analyzed projects (100MB+)
- UI shows numbered list with total count
- All navigation links stored in parsed_content JSON
- Stage 2 candidates identified by `proceed_to_stage_2` flag
- Automatic qualifiers stored in `automatic_stage_2_qualifiers`

## Contract Address Integration (August 17, 2025)
Successfully added contract address copy functionality:
- All 401 analyzed tokens now display contract addresses
- One-click copy button with visual feedback
- Matched addresses from Supabase by ticker symbol (100% coverage)
- Cross-browser compatible clipboard functionality

## Contact & Session Info
**Session Date**: August 15-17, 2025  
**Key Achievements**: 
- Built complete Stage 1 triage system
- Analyzed 400+ projects
- Fixed loading screen detection
- Identified 116 high-potential projects for Stage 2
- Added contract address copy functionality

---
*Last Updated: August 17, 2025 20:40*