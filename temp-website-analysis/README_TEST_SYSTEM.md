# Website Analysis Testing System

## ✅ System Ready for Testing

### What We Built

1. **Comprehensive Website Analyzer** (`comprehensive_website_analyzer.py`)
   - Intelligent two-stage parsing with Playwright (JavaScript rendering)
   - Automatic team member extraction (names, roles, LinkedIn profiles)
   - Document discovery (whitepapers, GitBook, GitHub)
   - Multi-model AI analysis (Claude, GPT-4o, Gemini)
   - Database storage with full history

2. **Test Scripts**
   - `test_batch_analyzer.py` - Batch process multiple websites
   - `analyze_team_info.py` - Focus on team extraction
   - `smart_document_parser.py` - Intelligent document discovery

3. **Results Viewer**
   - Web UI at http://localhost:5004
   - View all analyzed websites with scores and details

## 📊 Current Status

- **Database**: `website_analysis_new.db`
- **Total websites**: 199 with URLs
- **Already analyzed**: 4 websites
- **Remaining**: 195 websites to analyze

### Recent Analysis Results

| Website | Score | Team Members | Documents | LinkedIn Profiles |
|---------|-------|--------------|-----------|-------------------|
| graphai.tech | 7.0/10 | 4 found | 1 | 4 |
| tharwa.finance | 6.7/10 | 5 found | 2 | 5 |
| blockstreet.xyz | 4.0/10 | 0 found | 0 | 0 |
| buildon.online | 2.5/10 | 0 found | 0 | 0 |

## 🚀 How to Use

### Quick Test (3 websites)
```bash
python3 test_batch_analyzer.py
```

### Analyze Single Website
```python
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

analyzer = ComprehensiveWebsiteAnalyzer()
result = analyzer.analyze_single_website("https://example.com")
```

### Batch Process (customize limit)
```python
analyzer = ComprehensiveWebsiteAnalyzer()
analyzer.batch_analyze(limit=10)  # Analyze 10 websites
```

### View Results
```bash
# If not already running:
python3 results_server.py

# Then open in browser:
open http://localhost:5004
```

## 🔍 Key Features

### Intelligent Parsing
- **Stage 1**: Full JavaScript rendering with Playwright
- **Stage 2**: Targeted extraction of team, documents, social links
- **Stage 3**: Multi-model AI analysis for consensus

### Team Extraction
- Finds full names (not just "team exists")
- Extracts roles/titles when available
- Links to LinkedIn profiles
- Matches names to profiles

### Document Discovery
- Finds whitepapers (PDF or web)
- Detects GitBook documentation
- Identifies GitHub repositories
- Recognizes documentation links

### Scoring System
- **8-10**: Professional with real team, docs, clear vision (ALPHA)
- **5-7**: Basic transparency, some team info (SOLID)
- **3-4**: Minimal info, anonymous team (BASIC)
- **1-2**: Red flags, no substance (TRASH)

## 📈 What Models See

When provided with parsed content, AI models can identify:
- **Specific team member names** (e.g., "Saeed Al Fahim")
- **Roles and titles** (CEO, CTO, Advisor)
- **LinkedIn verification** status
- **Document availability** and importance
- **Technical depth** from documentation
- **Red flags** (anonymous team, no docs, vague promises)

## 🎯 Key Discovery

**JavaScript rendering is ESSENTIAL:**
- Without JS: ~1,300 chars extracted, score 4-5/10
- With JS: ~7,000 chars extracted, score 6-8/10
- 5x more content = much better analysis

## 🔧 Customization

### Add More AI Models
Edit `comprehensive_website_analyzer.py`:
```python
models_to_test = [
    ("anthropic/claude-3.5-sonnet", "Claude 3.5"),
    ("openai/gpt-4o", "GPT-4o"),
    # Add more models here
]
```

### Adjust Parsing Timeout
```python
page.goto(url, wait_until='networkidle', timeout=30000)  # 30 seconds
```

### Change Database Path
```python
analyzer = ComprehensiveWebsiteAnalyzer(db_path="your_database.db")
```

## ⚠️ Notes

- Rate limited to avoid overwhelming servers (3 second delay between sites)
- Some sites may timeout or block automated access
- LinkedIn profiles may require additional verification
- PDF parsing requires separate libraries (not implemented yet)

## 📊 Database Schema

The `website_analysis` table stores:
- `url` - Website URL
- `parsed_content` - Full JSON of extracted content
- `documents_found` - Number of documents discovered
- `team_members_found` - Number of team members identified
- `linkedin_profiles` - Number of LinkedIn profiles found
- `score` - Average AI score (1-10)
- `tier` - Consensus tier (ALPHA/SOLID/BASIC/TRASH)
- `legitimacy_indicators` - Positive findings
- `red_flags` - Concerns identified
- `technical_depth` - Assessment of documentation
- `team_transparency` - Assessment of team info
- `reasoning` - AI explanation for score
- `analyzed_at` - Timestamp
- `parse_success` - Whether parsing succeeded
- `parse_error` - Error message if failed

## 🚦 Ready to Scale

The system is ready to:
1. Process all 195 remaining websites
2. Re-analyze existing sites for updates
3. Export results to CSV for analysis
4. Generate reports on patterns found

Start with `test_batch_analyzer.py` to process a few sites and verify everything works!