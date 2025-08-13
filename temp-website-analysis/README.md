# KROM Website Analysis - Temporary Development Environment

This is a temporary development folder for testing website analysis using Kimi K2 before integrating with production.

## Setup

1. **Install Dependencies** (if not already installed):
```bash
pip install flask flask-cors requests python-dotenv
```

2. **Environment Variables**:
The script uses the parent `.env` file for API keys and Supabase credentials.

## Files

- `website_analyzer.py` - Main analysis script that fetches tokens and analyzes websites
- `viewer.html` - Interactive HTML interface to view results
- `server.py` - Flask server to serve data to the HTML viewer
- `analysis_results.db` - Local SQLite database (created automatically)

## Usage

### Step 1: Run Website Analysis

Analyze a batch of websites (default 20):
```bash
python website_analyzer.py
```

Or specify a custom batch size:
```bash
python website_analyzer.py 50
```

### Step 2: View Results

1. Start the Flask server:
```bash
python server.py
```

2. Open your browser to: http://localhost:5000

The viewer will show:
- Statistics summary (total analyzed, tier breakdown, average score)
- Sortable table with all analyzed websites
- Expandable rows for detailed information
- Filters by tier, network, score, utility
- Export to CSV functionality
- Auto-refresh every 30 seconds

## Analysis Tiers

- **ALPHA** (9-10): Exceptional projects with clear utility and strong fundamentals
- **SOLID** (7-8): Good projects with working products or clear roadmaps
- **BASIC** (4-6): Standard projects that may lack some key elements
- **TRASH** (1-3): Poor quality, likely scams or abandoned

## Database Schema

The local SQLite database stores:
- Token information (ticker, network, contract, website URL)
- Analysis scores and tiers
- Project details (utility, documentation, team, audits)
- Red and green flags
- Full analysis JSON
- Timestamps and error messages

## Notes

- Analysis takes ~7-10 seconds per website
- Many crypto websites may be offline or redirects
- The script prioritizes utility tokens first (more likely to have real websites)
- Results are stored locally and not pushed to production
- The viewer auto-refreshes to show new results as they come in

## Next Steps

Once we validate the analysis quality:
1. Review the results in the viewer
2. Adjust the analysis prompts if needed
3. Decide on integration approach (Edge Function vs batch script)
4. Update production database schema if needed
5. Deploy to production